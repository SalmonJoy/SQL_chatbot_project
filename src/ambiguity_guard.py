from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .retrieval import normalize_phrase_text, tokenize


UNRESOLVED_PRONOUNS = {
    "he",
    "her",
    "him",
    "his",
    "she",
    "their",
    "them",
}


EXPLICIT_ENTITY_TOKENS = {
    "album",
    "artist",
    "customer",
    "employee",
    "genre",
    "invoice",
    "media",
    "month",
    "playlist",
    "rep",
    "representative",
    "song",
    "support",
    "track",
    "year",
    "amount",
    "country",
    "total",
    "value",
}


SAFE_POSSESSIVE_CONTEXT_TOKENS = {
    "album",
    "artist",
    "average",
    "billing",
    "country",
    "customer",
    "employee",
    "genre",
    "invoice",
    "media",
    "revenue",
    "sale",
    "sales",
    "track",
    "total",
    "value",
}


PERSON_QUERY_IDS = {
    "q007",
    "q009",
    "q021",
    "q022",
    "q040",
    "q041",
    "q045",
    "q049",
    "q050",
}


@dataclass(frozen=True)
class AmbiguityGuardResult:
    should_block: bool
    reason_code: str
    message: str

    def to_log(self) -> dict[str, Any]:
        return {
            "should_block": self.should_block,
            "reason_code": self.reason_code,
            "message": self.message,
        }


def has_unresolved_pronoun(question: str) -> bool:
    normalized = normalize_phrase_text(question)
    tokens = set(tokenize(question))
    if "that person" in normalized:
        return True
    if tokens.intersection({"he", "him", "his", "she", "her"}):
        return True
    if tokens.intersection({"their", "them"}) and not tokens.intersection(SAFE_POSSESSIVE_CONTEXT_TOKENS):
        return True
    if "what about them" in normalized or "total for them" in normalized:
        return True
    return False


def is_person_tracks_question(question: str) -> bool:
    tokens = set(tokenize(question))
    normalized = normalize_phrase_text(question)
    has_person = "person" in tokens or "people" in tokens or "artist" in tokens
    has_track = bool(tokens.intersection({"track", "song"}))
    has_sold = bool(tokens.intersection({"sold", "sell", "sale", "quantity"})) or "sold most" in normalized
    return has_person and has_track and has_sold


def is_ambiguous_selling_question(question: str) -> bool:
    normalized = normalize_phrase_text(question)
    tokens = set(tokenize(question))
    explicit_entity_tokens = tokens.intersection(EXPLICIT_ENTITY_TOKENS)
    selling_phrase = (
        bool(re.search(r"\bwho\s+sold(?:\s+the)?\s+most\b", normalized))
        or "best seller" in normalized
        or "best selling" in normalized
        or bool(re.search(r"\bwho\s+(?:made|make)\s+(?:the\s+)?most\s+money\b", normalized))
        or bool(re.search(r"\bwho\s+has\s+(?:the\s+)?highest\s+total\b", normalized))
        or bool(re.search(r"\bwho\s+is\s+(?:the\s+)?(?:top\s+earner|most\s+popular|most\s+active)\b", normalized))
    )
    return selling_phrase and not explicit_entity_tokens


def is_too_vague(question: str) -> bool:
    normalized = normalize_phrase_text(question)
    tokens = set(tokenize(question))

    if normalized in {"total", "person", "who", "tell me person", "tell me the person"}:
        return True
    if normalized in {
        "top one",
        "show top one",
        "show me top one",
        "best ones",
        "list best ones",
        "list the best ones",
        "winner",
        "show winner",
        "show the winner",
        "leader",
        "who leader",
        "who is leader",
        "who is the leader",
        "champion",
        "who is champion",
        "who is the champion",
        "number one",
        "who is number one",
        "who is the number one",
        "biggest one",
        "give me biggest one",
        "give me the biggest one",
    }:
        return True
    if tokens == {"total"} or tokens == {"person"}:
        return True
    if len(tokens) <= 2 and tokens.intersection({"person", "who"}):
        return True
    if "person" in tokens and tokens.intersection({"highest", "count", "total", "top", "most"}):
        return True
    return False


def evaluate_ambiguity(question: str, top_match: dict[str, Any], matches: list[dict[str, Any]]) -> AmbiguityGuardResult:
    _ = top_match
    _ = matches

    if is_person_tracks_question(question):
        return AmbiguityGuardResult(False, "clear_person_tracks_intent", "Question explicitly asks for the person or artist whose tracks sold most.")

    if has_unresolved_pronoun(question):
        return AmbiguityGuardResult(
            True,
            "unresolved_pronoun",
            "The question contains an unresolved pronoun. Please specify the person, artist, employee, customer, or query intent.",
        )

    if is_ambiguous_selling_question(question):
        return AmbiguityGuardResult(
            True,
            "ambiguous_entity_type",
            "The question asks who sold most but does not specify whether to rank artists, tracks, albums, customers, or employees.",
        )

    if is_too_vague(question):
        return AmbiguityGuardResult(
            True,
            "vague_query",
            "The question is too vague to safely choose one repository query.",
        )

    return AmbiguityGuardResult(False, "clear_enough", "No ambiguity guard triggered.")


def prioritize_ambiguous_options(question: str, matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not (is_ambiguous_selling_question(question) or "person" in set(tokenize(question))):
        return matches

    def sort_key(match: dict[str, Any]) -> tuple[int, float, str]:
        person_priority = 0 if match.get("query_id") in PERSON_QUERY_IDS else 1
        return (person_priority, -float(match.get("hybrid_score", 0.0)), str(match.get("query_id")))

    return sorted(matches, key=sort_key)
