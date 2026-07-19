from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from .config import CONFIG, AppConfig


VALID_ACTIONS = {
    "execute_repository_query",
    "ask_clarification",
    "block_domain",
    "block_multi_intent",
}

VALID_CONFIDENCE = {"low", "medium", "high"}

CONFUSION_FAMILIES = [
    {"q016", "q056", "q046"},
    {"q004", "q026", "q029", "q037"},
    {"q002", "q006", "q010", "q034", "q037"},
    {"q011", "q012", "q048"},
    {"q008", "q038", "q039", "q040", "q041"},
    {"q043", "q044", "q054"},
]


@dataclass(frozen=True)
class DecisionReviewResult:
    status: str
    source: str
    action: str
    query_id: str | None
    confidence: str
    reason: str
    raw_response: str | None = None

    @property
    def usable(self) -> bool:
        return self.status == "success" and self.confidence in {"medium", "high"}

    def to_log(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source": self.source,
            "action": self.action,
            "query_id": self.query_id,
            "confidence": self.confidence,
            "reason": self.reason,
            "used_review": self.usable,
            "raw_response": self.raw_response,
        }


def skipped_result(source: str, reason: str) -> DecisionReviewResult:
    return DecisionReviewResult(
        status="skipped",
        source=source,
        action="ask_clarification",
        query_id=None,
        confidence="low",
        reason=reason,
    )


def error_result(source: str, reason: str) -> DecisionReviewResult:
    return DecisionReviewResult(
        status="error",
        source=source,
        action="ask_clarification",
        query_id=None,
        confidence="low",
        reason=reason,
    )


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


def known_confusion_present(matches: list[dict[str, Any]]) -> bool:
    top_ids = {match.get("query_id") for match in matches[:5]}
    return any(len(top_ids.intersection(family)) >= 2 for family in CONFUSION_FAMILIES)


def should_review_decision(
    matches: list[dict[str, Any]],
    deterministic_should_execute: bool,
    ambiguity_guard: Any,
    multi_intent_guard: Any,
    config: AppConfig = CONFIG,
) -> bool:
    if not config.enable_gemini_decision_review or not matches:
        return False

    top_score = float(matches[0].get("hybrid_score", 0.0))
    second_score = float(matches[1].get("hybrid_score", 0.0)) if len(matches) > 1 else 0.0
    margin = top_score - second_score

    if margin <= config.gemini_decision_review_margin_threshold:
        return True
    if known_confusion_present(matches):
        return True
    if getattr(ambiguity_guard, "should_block", False) or getattr(multi_intent_guard, "should_block", False):
        return True
    if not deterministic_should_execute and top_score >= config.auto_execute_min_score:
        return True
    return False


def build_review_prompt(
    question: str,
    matches: list[dict[str, Any]],
    domain_guard: Any,
    ambiguity_guard: Any,
    multi_intent_guard: Any,
    parameter_resolution: Any,
    deterministic_should_execute: bool,
    config: AppConfig,
) -> str:
    candidates = []
    for match in matches[: config.gemini_decision_review_top_k]:
        candidates.append(
            {
                "query_id": match.get("query_id"),
                "intent": match.get("intent"),
                "category": match.get("category"),
                "parameters": match.get("parameters", []),
                "expected_columns": match.get("expected_columns", []),
                "tables_used": match.get("tables_used", []),
                "sql": match.get("sql"),
            }
        )

    payload = {
        "task": "Choose the safest action for a SQL chatbot that can only execute vetted repository SQL.",
        "rules": [
            "Do not write SQL.",
            "Select query_id only from the provided candidates.",
            "Use execute_repository_query only when one candidate clearly answers the user question.",
            "Use ask_clarification when the question is vague, ambiguous, missing a required parameter, or asks multiple plausible database intents.",
            "Use block_domain for non-database or mixed unrelated requests.",
            "Use block_multi_intent when the user asks for multiple distinct database outputs.",
        ],
        "question": question,
        "deterministic_should_execute": deterministic_should_execute,
        "guards": {
            "domain": domain_guard.to_log() if hasattr(domain_guard, "to_log") else None,
            "ambiguity": ambiguity_guard.to_log() if hasattr(ambiguity_guard, "to_log") else None,
            "multi_intent": multi_intent_guard.to_log() if hasattr(multi_intent_guard, "to_log") else None,
            "parameter_resolution": parameter_resolution.to_log() if hasattr(parameter_resolution, "to_log") else None,
        },
        "candidates": candidates,
        "return_json_shape": {
            "action": "execute_repository_query | ask_clarification | block_domain | block_multi_intent",
            "query_id": "candidate query_id or null",
            "confidence": "low | medium | high",
            "reason": "short reason",
        },
    }

    return json.dumps(payload, ensure_ascii=False)


def normalize_review_payload(
    payload: dict[str, Any],
    raw_response: str,
    allowed_query_ids: set[str],
) -> DecisionReviewResult:
    action = str(payload.get("action") or "ask_clarification").strip()
    if action not in VALID_ACTIONS:
        action = "ask_clarification"

    query_id = payload.get("query_id")
    if not isinstance(query_id, str) or query_id not in allowed_query_ids:
        query_id = None
    if action == "execute_repository_query" and query_id is None:
        action = "ask_clarification"

    confidence = str(payload.get("confidence") or "low").strip().lower()
    if confidence not in VALID_CONFIDENCE:
        confidence = "low"

    return DecisionReviewResult(
        status="success",
        source="gemini",
        action=action,
        query_id=query_id,
        confidence=confidence,
        reason=str(payload.get("reason") or "").strip(),
        raw_response=raw_response,
    )


def review_decision(
    question: str,
    matches: list[dict[str, Any]],
    domain_guard: Any,
    ambiguity_guard: Any,
    multi_intent_guard: Any,
    parameter_resolution: Any,
    deterministic_should_execute: bool,
    config: AppConfig = CONFIG,
) -> DecisionReviewResult:
    if not should_review_decision(matches, deterministic_should_execute, ambiguity_guard, multi_intent_guard, config):
        return skipped_result("not_needed", "Deterministic decision did not need review.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return skipped_result("no_gemini_api_key", "Gemini API key is not configured.")

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = build_review_prompt(
            question,
            matches,
            domain_guard,
            ambiguity_guard,
            multi_intent_guard,
            parameter_resolution,
            deterministic_should_execute,
            config,
        )
        response = client.models.generate_content(model=config.gemini_model, contents=prompt)
        raw_text = str(getattr(response, "text", "") or "").strip()
        if not raw_text:
            return error_result("empty_gemini_response", "Gemini returned an empty decision-review response.")
        payload = extract_json_object(raw_text)
        return normalize_review_payload(raw_text=raw_text, payload=payload, allowed_query_ids={m["query_id"] for m in matches[: config.gemini_decision_review_top_k]})
    except Exception as exc:  # pragma: no cover - protects demo flow from API/runtime issues
        return error_result("gemini_error", f"Gemini decision review failed: {exc}")
