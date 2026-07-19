from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .retrieval import normalize_phrase_text, tokenize


CONNECTOR_PATTERN = r"\b(?:as well as|along with|and then|and also|and|also|then|plus)\b"

ACTION_TERMS = {
    "average",
    "buy",
    "common",
    "count",
    "created",
    "display",
    "distinct",
    "duration",
    "earn",
    "fewest",
    "find",
    "greater",
    "highest",
    "list",
    "longer",
    "make",
    "money",
    "most",
    "name",
    "names",
    "number",
    "price",
    "purchase",
    "rank",
    "released",
    "retrieve",
    "revenue",
    "sale",
    "sell",
    "shorter",
    "sold",
    "spend",
    "total",
    "top",
}

ENTITY_GROUPS = {
    "artist": {"artist", "artists", "seller", "singer", "band"},
    "album": {"album", "albums"},
    "customer": {"customer", "customers", "buyer", "buyers"},
    "employee": {"employee", "employees", "rep", "representative", "support"},
    "invoice": {"invoice", "invoices"},
    "track": {"track", "tracks", "song", "songs"},
    "genre": {"genre", "genres"},
    "media": {"media", "file", "format", "type"},
    "sales_time": {"day", "date", "month", "year", "when"},
    "geography": {"city", "country"},
    "price": {"price", "amount", "total"},
    "state": {"state"},
}


@dataclass(frozen=True)
class MultiIntentGuardResult:
    should_block: bool
    reason_code: str
    message: str
    intent_clauses: list[str]

    def to_log(self) -> dict[str, Any]:
        return {
            "should_block": self.should_block,
            "reason_code": self.reason_code,
            "message": self.message,
            "intent_clauses": self.intent_clauses,
        }


def split_clauses(question: str) -> list[str]:
    normalized = normalize_phrase_text(question)
    return [
        re.sub(r"\s+", " ", clause).strip()
        for clause in re.split(CONNECTOR_PATTERN, normalized)
        if clause.strip()
    ]


def clause_entity_groups(tokens: set[str]) -> set[str]:
    groups = {
        group
        for group, candidates in ENTITY_GROUPS.items()
        if tokens.intersection(candidates)
    }
    if tokens.intersection({"buy", "purchase"}) and tokens.intersection({"most", "top"}):
        groups.add("customer")
    if tokens.intersection({"sell", "sold", "sale"}) and tokens.intersection({"most", "top"}):
        groups.add("seller_or_product")
    return groups


def is_actionable_clause(clause: str) -> bool:
    tokens = set(tokenize(clause))
    if len(tokens) < 2:
        return False

    has_action = bool(tokens.intersection(ACTION_TERMS))
    has_entity = bool(clause_entity_groups(tokens))
    has_metric = bool(tokens.intersection({"revenue", "sale", "sales", "money", "invoice", "count", "total", "price", "duration"}))
    return has_action and (has_entity or has_metric or tokens.intersection({"buy", "purchase", "sell", "sold"}))


def clause_signature(clause: str) -> tuple[frozenset[str], frozenset[str]]:
    tokens = set(tokenize(clause))
    entities = clause_entity_groups(tokens)
    actions = tokens.intersection(ACTION_TERMS)
    return frozenset(entities), frozenset(actions)


def evaluate_multi_intent(question: str) -> MultiIntentGuardResult:
    normalized = normalize_phrase_text(question)
    if (
        ("city and country" in normalized or "country and city" in normalized)
        and set(tokenize(question)).intersection({"revenue", "sale", "sales", "billing"})
        and not re.search(r"\b(?:also|plus|then|along with|as well as|and then|and also)\b", normalized)
    ):
        return MultiIntentGuardResult(
            False,
            "single_intent_city_country_breakdown",
            "City and country are part of one geographic breakdown intent.",
            [],
        )
    if (
        ("name and track count" in normalized or "name and total track count" in normalized)
        and set(tokenize(question)).intersection({"genre", "media", "type"})
        and not re.search(r"\b(?:also|plus|then|along with|as well as|and then|and also)\b", normalized)
    ):
        return MultiIntentGuardResult(
            False,
            "single_intent_name_count_breakdown",
            "Name and count fields are part of one breakdown intent.",
            [],
        )

    clauses = split_clauses(question)
    actionable = [clause for clause in clauses if is_actionable_clause(clause)]

    if len(actionable) < 2:
        return MultiIntentGuardResult(
            False,
            "single_intent",
            "No multi-intent guard triggered.",
            [],
        )

    signatures = {clause_signature(clause) for clause in actionable}
    if len(signatures) < 2:
        return MultiIntentGuardResult(
            False,
            "single_intent_repeated",
            "Clauses appear to ask for the same repository intent.",
            actionable,
        )

    return MultiIntentGuardResult(
        True,
        "multiple_database_intents",
        "This asks for multiple database intents. Please choose one repository query to execute at a time.",
        actionable,
    )
