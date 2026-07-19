from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from .config import CONFIG, AppConfig
from .conversation_context import compact_context_for_rewrite
from .retrieval import normalize_phrase_text, tokenize


FOLLOW_UP_PRONOUNS = {
    "he",
    "her",
    "him",
    "his",
    "it",
    "its",
    "she",
    "their",
    "them",
    "these",
    "this",
    "those",
}


@dataclass(frozen=True)
class ContextRewriteResult:
    status: str
    source: str
    original_question: str
    effective_question: str
    is_follow_up: bool
    standalone_question: str
    resolved_references: dict[str, Any]
    confidence: str
    reason: str
    raw_response: str | None = None

    @property
    def use_rewrite(self) -> bool:
        return (
            self.status == "success"
            and self.is_follow_up
            and self.confidence in {"medium", "high"}
            and bool(self.standalone_question.strip())
            and self.standalone_question.strip() != self.original_question.strip()
        )

    def to_log(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source": self.source,
            "original_question": self.original_question,
            "effective_question": self.effective_question,
            "is_follow_up": self.is_follow_up,
            "standalone_question": self.standalone_question,
            "resolved_references": self.resolved_references,
            "confidence": self.confidence,
            "reason": self.reason,
            "used_rewrite": self.use_rewrite,
            "raw_response": self.raw_response,
        }


def skipped_result(question: str, status: str, source: str, reason: str) -> ContextRewriteResult:
    return ContextRewriteResult(
        status=status,
        source=source,
        original_question=question,
        effective_question=question,
        is_follow_up=False,
        standalone_question=question,
        resolved_references={},
        confidence="low",
        reason=reason,
    )


def should_attempt_context_rewrite(question: str, context: dict[str, Any] | None) -> bool:
    if not context:
        return False

    normalized = normalize_phrase_text(question)
    tokens = set(tokenize(question))
    if tokens.intersection(FOLLOW_UP_PRONOUNS):
        return True
    if any(phrase in normalized for phrase in ["what about", "how much", "same", "that one", "that artist", "that person"]):
        return True
    if len(tokens) <= 3:
        return True
    return False


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def normalize_payload(question: str, payload: dict[str, Any], raw_response: str) -> ContextRewriteResult:
    is_follow_up = bool(payload.get("is_follow_up"))
    standalone_question = str(payload.get("standalone_question") or question).strip()
    confidence = str(payload.get("confidence") or "low").strip().lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "low"
    resolved_references = payload.get("resolved_references")
    if not isinstance(resolved_references, dict):
        resolved_references = {}
    reason = str(payload.get("reason") or "").strip()

    result = ContextRewriteResult(
        status="success",
        source="gemini",
        original_question=question,
        effective_question=standalone_question if is_follow_up and confidence in {"medium", "high"} else question,
        is_follow_up=is_follow_up,
        standalone_question=standalone_question,
        resolved_references=resolved_references,
        confidence=confidence,
        reason=reason,
        raw_response=raw_response,
    )
    if not result.use_rewrite:
        return ContextRewriteResult(
            **{
                **result.__dict__,
                "effective_question": question,
            }
        )
    return result


def build_rewrite_prompt(question: str, context: dict[str, Any]) -> str:
    compact_context = compact_context_for_rewrite(context)
    return f"""You rewrite follow-up questions for a SQL-retrieval chatbot.

Task:
- Decide whether the current user question is a follow-up to the previous result.
- If it is a follow-up, rewrite it as a standalone natural-language business question.
- Use only the provided previous-turn context.
- Do not write SQL.
- Do not invent entities, dates, countries, artists, customers, or metrics.
- If a pronoun like "his", "her", "that", or "their" clearly refers to a top entity in the previous result, resolve it.
- If the follow-up asks whether the prior artist is highest/top/best/number one or asks for rank, rewrite it as a revenue-rank question such as "What is the revenue rank for Iron Maiden?"
- If the follow-up directly asks "how much revenue" for the prior artist, rewrite it as a direct artist-revenue question such as "What is the revenue for Iron Maiden?"
- If the reference is unclear, set confidence to "low" and keep the original question.

Return exactly one JSON object with this shape:
{{
  "is_follow_up": true,
  "standalone_question": "What is the revenue rank for Iron Maiden?",
  "resolved_references": {{"his": "Iron Maiden"}},
  "confidence": "high",
  "reason": "The previous result identified Iron Maiden as the top artist."
}}

Previous-turn context:
{json.dumps(compact_context, ensure_ascii=False)}

Current user question:
{question}
"""


def rewrite_follow_up_question(
    question: str,
    context: dict[str, Any] | None,
    config: AppConfig = CONFIG,
) -> ContextRewriteResult:
    if not config.enable_context_rewrite:
        return skipped_result(question, "skipped", "disabled", "Context rewrite is disabled.")
    if not context:
        return skipped_result(question, "skipped", "no_context", "No prior successful turn is available.")
    if not should_attempt_context_rewrite(question, context):
        return skipped_result(question, "skipped", "not_follow_up_shape", "Question does not look like a follow-up.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return skipped_result(question, "skipped", "no_gemini_api_key", "Gemini API key is not configured.")

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=config.gemini_model,
            contents=build_rewrite_prompt(question, context),
        )
        raw_text = str(getattr(response, "text", "") or "").strip()
        if not raw_text:
            return skipped_result(question, "error", "empty_gemini_response", "Gemini returned an empty rewrite response.")
        payload = extract_json_object(raw_text)
        return normalize_payload(question, payload, raw_text)
    except Exception as exc:  # pragma: no cover - protects demo flow from API/runtime issues
        return skipped_result(question, "error", "gemini_error", f"Gemini context rewrite failed: {exc}")
