from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .retrieval import normalize_phrase_text, question_has_artist_name_hint, tokenize


DOMAIN_TERMS = {
    "album",
    "albums",
    "artist",
    "artists",
    "billing",
    "business",
    "buy",
    "bought",
    "buyer",
    "buyers",
    "city",
    "cities",
    "country",
    "countries",
    "customer",
    "customers",
    "employee",
    "employees",
    "earn",
    "earned",
    "earning",
    "date",
    "day",
    "days",
    "file",
    "files",
    "format",
    "formats",
    "genre",
    "genres",
    "invoice",
    "invoices",
    "make",
    "made",
    "making",
    "media",
    "money",
    "month",
    "monthly",
    "months",
    "music",
    "playlist",
    "playlists",
    "purchase",
    "purchased",
    "purchases",
    "quantity",
    "rank",
    "ranking",
    "rep",
    "reps",
    "representative",
    "representatives",
    "revenue",
    "sale",
    "sales",
    "sell",
    "seller",
    "selling",
    "sold",
    "song",
    "songs",
    "spend",
    "spending",
    "store",
    "support",
    "track",
    "tracks",
    "type",
    "types",
    "when",
    "year",
    "yearly",
    "years",
}

COMPARATIVE_TERMS = {
    "best",
    "highest",
    "largest",
    "lowest",
    "most",
    "rank",
    "ranking",
    "top",
}

FOLLOW_UP_OR_AMBIGUITY_TERMS = {
    "he",
    "her",
    "him",
    "his",
    "person",
    "people",
    "she",
    "their",
    "them",
    "these",
    "this",
    "those",
}

MATH_WORDS = {
    "add",
    "calculate",
    "calculator",
    "divide",
    "divided",
    "math",
    "minus",
    "multiply",
    "plus",
    "subtract",
    "times",
}

UNRELATED_ATTRIBUTE_TERMS = {
    "age",
    "bio",
    "biography",
    "born",
    "breakfast",
    "dinner",
    "eat",
    "food",
    "gravity",
    "gravitation",
    "lunch",
    "president",
    "whale",
}


@dataclass(frozen=True)
class DomainGuardResult:
    should_block: bool
    reason_code: str
    message: str
    matched_domain_terms: list[str] | None = None
    offending_clauses: list[str] | None = None

    def to_log(self) -> dict[str, Any]:
        return {
            "should_block": self.should_block,
            "reason_code": self.reason_code,
            "message": self.message,
            "matched_domain_terms": self.matched_domain_terms or [],
            "offending_clauses": self.offending_clauses or [],
        }


def has_math_shape(question: str) -> bool:
    normalized = normalize_phrase_text(question)
    raw_lower = question.lower()
    tokens = set(tokenize(question))
    has_operator_expression = bool(
        re.search(r"\b\d+(?:\.\d+)?\s*(?:x|\*|\+|-|/)\s*\d+(?:\.\d+)?\b", raw_lower)
    )
    has_math_word_with_number = bool(tokens.intersection(MATH_WORDS)) and bool(
        re.search(r"\b\d+(?:\.\d+)?\b", normalized)
    )
    return has_operator_expression or has_math_word_with_number


def matched_database_domain_terms(question: str) -> list[str]:
    tokens = set(tokenize(question))
    matched_terms = set(tokens.intersection(DOMAIN_TERMS))
    if question_has_artist_name_hint(question):
        matched_terms.add("artist_name")
    return sorted(matched_terms)


def has_database_domain_signal(question: str) -> bool:
    normalized = normalize_phrase_text(question)
    tokens = set(tokenize(question))
    if matched_database_domain_terms(question):
        return True
    if tokens.intersection(FOLLOW_UP_OR_AMBIGUITY_TERMS) and tokens.intersection(COMPARATIVE_TERMS):
        return True
    if "that person" in normalized or "that artist" in normalized:
        return True
    return False


def split_prompt_clauses(question: str) -> list[str]:
    normalized = normalize_phrase_text(question)
    split_pattern = r"\b(?:as well as|along with|and|also|plus)\b"
    clauses = [
        re.sub(r"\s+", " ", clause).strip()
        for clause in re.split(split_pattern, normalized)
    ]
    return [clause for clause in clauses if clause]


def is_substantive_clause(clause: str) -> bool:
    if has_math_shape(clause):
        return True
    if len(re.findall(r"\b\d+(?:\.\d+)?\b", clause)) >= 2:
        return True
    return len(tokenize(clause)) >= 2


def is_same_subject_followup_clause(clause: str) -> bool:
    tokens = set(tokenize(clause))
    return bool(tokens) and tokens.issubset({"common", "highest", "largest", "lowest", "most", "one", "top"})


def mixed_prompt_details(question: str) -> tuple[bool, list[str], list[str]]:
    clauses = split_prompt_clauses(question)
    matched_terms = matched_database_domain_terms(question)
    if len(clauses) <= 1:
        return False, matched_terms, []

    has_domain_clause = any(has_database_domain_signal(clause) for clause in clauses)
    if not has_domain_clause:
        return False, matched_terms, []

    offending_clauses = [
        clause
        for clause in clauses
        if is_substantive_clause(clause)
        and not is_same_subject_followup_clause(clause)
        and (has_math_shape(clause) or not has_database_domain_signal(clause))
    ]
    return bool(offending_clauses), matched_terms, offending_clauses


def unrelated_domain_attribute_terms(question: str) -> list[str]:
    matched_terms = matched_database_domain_terms(question)
    if not matched_terms:
        return []

    tokens = set(tokenize(question))
    unrelated = sorted(tokens.intersection(UNRELATED_ATTRIBUTE_TERMS))
    if unrelated:
        return unrelated

    normalized = normalize_phrase_text(question)
    phrase_terms = []
    for phrase in [
        "for lunch",
        "for dinner",
        "for breakfast",
        "have for lunch",
        "have for dinner",
        "have for breakfast",
    ]:
        if phrase in normalized:
            phrase_terms.append(phrase)
    return phrase_terms


def evaluate_domain(question: str) -> DomainGuardResult:
    is_mixed, matched_terms, offending_clauses = mixed_prompt_details(question)
    if is_mixed:
        return DomainGuardResult(
            True,
            "mixed_out_of_domain",
            "This question mixes a Chinook database request with unrelated content. Please ask one Chinook-only database question at a time.",
            matched_domain_terms=matched_terms,
            offending_clauses=offending_clauses,
        )

    unrelated_terms = unrelated_domain_attribute_terms(question)
    if unrelated_terms:
        return DomainGuardResult(
            True,
            "domain_entity_unrelated_attribute",
            "This question mentions Chinook database entities but asks for information that is not in the database. Please ask about sales, revenue, invoices, customers, artists, albums, tracks, genres, media types, employees, support reps, playlists, countries, months, or years.",
            matched_domain_terms=matched_terms or matched_database_domain_terms(question),
            offending_clauses=unrelated_terms,
        )

    if has_math_shape(question):
        return DomainGuardResult(
            True,
            "math_out_of_domain",
            "This chatbot only answers questions about the Chinook music store database, so I will not run SQL for a calculator/math question.",
            matched_domain_terms=matched_terms,
        )

    if has_database_domain_signal(question):
        return DomainGuardResult(
            False,
            "in_domain",
            "Question has Chinook database domain signals.",
            matched_domain_terms=matched_database_domain_terms(question),
        )

    return DomainGuardResult(
        True,
        "out_of_domain",
        "This chatbot only answers questions about the Chinook music store database: sales, revenue, invoices, customers, artists, albums, tracks, genres, media types, employees, support reps, playlists, countries, months, and years.",
        matched_domain_terms=matched_terms,
    )
