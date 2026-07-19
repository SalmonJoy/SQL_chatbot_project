from __future__ import annotations

import math
import os
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

from sentence_transformers import SentenceTransformer

from .config import CONFIG, AppConfig
from .parameter_resolver import ARTIST_ALIASES


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "each",
    "for",
    "from",
    "give",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "list",
    "me",
    "need",
    "of",
    "on",
    "or",
    "per",
    "show",
    "the",
    "this",
    "that",
    "to",
    "was",
    "were",
    "what",
    "which",
    "who",
    "with",
}


TOKEN_REWRITES = {
    "whern": "when",
    "moth": "month",
    "mnth": "month",
    "mont": "month",
    "yer": "year",
    "yr": "year",
    "revnue": "revenue",
    "reveune": "revenue",
    "mak": "make",
    "made": "make",
    "earned": "earn",
    "bought": "purchase",
    "purchas": "purchase",
    "custmer": "customer",
    "pric": "price",
    "trak": "track",
    "traks": "track",
    "qty": "quantity",
}


SCHEMA_GENERIC_TOKENS = {
    "id",
    "first",
    "last",
    "name",
}


SQL_KEYWORDS = {
    "as",
    "by",
    "count",
    "desc",
    "from",
    "group",
    "join",
    "left",
    "limit",
    "on",
    "order",
    "round",
    "select",
    "strftime",
    "sum",
}


COUNTRY_HINTS = {
    "argentina",
    "australia",
    "austria",
    "belgium",
    "brazil",
    "canada",
    "chile",
    "czech republic",
    "denmark",
    "finland",
    "france",
    "germany",
    "hungary",
    "india",
    "ireland",
    "italy",
    "netherlands",
    "norway",
    "poland",
    "portugal",
    "spain",
    "sweden",
    "usa",
    "us",
    "united states",
    "america",
    "united kingdom",
    "uk",
}


GENRE_HINTS = {
    "alternative",
    "alternative punk",
    "blues",
    "bossa nova",
    "classical",
    "comedy",
    "drama",
    "easy listening",
    "electronica dance",
    "heavy metal",
    "hip hop rap",
    "hip hop",
    "jazz",
    "latin",
    "metal",
    "opera",
    "pop",
    "r b soul",
    "rnb",
    "reggae",
    "rock",
    "rock and roll",
    "sci fi fantasy",
    "science fiction",
    "soundtrack",
    "tv shows",
    "world",
}


MONTH_HINTS = {
    "jan",
    "january",
    "feb",
    "february",
    "mar",
    "march",
    "apr",
    "april",
    "may",
    "jun",
    "june",
    "jul",
    "july",
    "aug",
    "august",
    "sep",
    "sept",
    "september",
    "oct",
    "october",
    "nov",
    "november",
    "dec",
    "december",
}


@lru_cache(maxsize=4)
def artist_hint_phrases(sqlite_path: str) -> tuple[str, ...]:
    db_path = Path(sqlite_path).resolve()
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        raw_artist_names = {
            str(row[0])
            for row in connection.execute("SELECT Name FROM Artist WHERE Name IS NOT NULL")
            if row[0] is not None
        }
    finally:
        connection.close()

    hints = {normalize_phrase_text(artist_name) for artist_name in raw_artist_names}
    for alias, value in ARTIST_ALIASES.items():
        if value in raw_artist_names:
            hints.add(normalize_phrase_text(alias))
            hints.add(normalize_phrase_text(value))

    return tuple(sorted((hint for hint in hints if hint), key=lambda hint: (-len(hint), hint)))


@dataclass(frozen=True)
class RetrievalDecision:
    should_execute: bool
    reason: str


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def minmax(values: list[float]) -> list[float]:
    min_value = min(values)
    max_value = max(values)
    spread = max_value - min_value
    if spread <= 1e-12:
        return [0.0 for _ in values]
    return [(value - min_value) / spread for value in values]


def normalize_token(token: str) -> str:
    token = token.lower()
    if token.endswith("'s"):
        token = token[:-2]
    if len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("ies"):
        token = f"{token[:-3]}y"
    elif len(token) > 3 and token not in {"this"} and token.endswith("s"):
        token = token[:-1]
    return TOKEN_REWRITES.get(token, token)


def tokenize(text: str) -> list[str]:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    spaced = re.sub(r"[_-]+", " ", spaced)
    tokens = re.findall(r"[a-z0-9]+", spaced.lower())
    return [
        normalize_token(token)
        for token in tokens
        if len(normalize_token(token)) > 1 and normalize_token(token) not in STOPWORDS
    ]


def normalize_phrase_text(text: str) -> str:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def phrase_in_text(text: str, phrase: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


def question_has_artist_name_hint(question: str, config: AppConfig = CONFIG) -> bool:
    normalized_question = normalize_phrase_text(question)
    return any(
        phrase_in_text(normalized_question, artist_hint)
        for artist_hint in artist_hint_phrases(str(config.sqlite_path))
    )


def question_has_parameter_hint(question: str, parameter_type: str, config: AppConfig = CONFIG) -> bool:
    normalized_question = normalize_phrase_text(question)
    tokens = set(tokenize(question))

    if parameter_type == "year":
        return re.search(r"\b(?:19|20)\d{2}\b", question) is not None

    if parameter_type == "month":
        has_direct_month = re.search(r"\b(?:19|20)\d{2}[-/](?:0?[1-9]|1[0-2])\b", question) is not None
        has_named_month = bool(tokens.intersection(MONTH_HINTS))
        has_year = question_has_parameter_hint(question, "year", config)
        return has_direct_month or (has_named_month and has_year)

    if parameter_type == "country":
        return any(phrase_in_text(normalized_question, hint) for hint in COUNTRY_HINTS)

    if parameter_type == "genre_name":
        return any(phrase_in_text(normalized_question, hint) for hint in GENRE_HINTS)

    if parameter_type == "artist_name":
        return question_has_artist_name_hint(question, config)

    return False


def parameter_hint_penalty(question: str, parameters: list[dict[str, Any]], config: AppConfig = CONFIG) -> float:
    missing_hint_count = sum(
        1
        for parameter in parameters
        if parameter.get("required") and not question_has_parameter_hint(question, parameter.get("type", ""), config)
    )
    return 0.35 * missing_hint_count


def has_any_token(tokens: set[str], candidates: set[str]) -> bool:
    return bool(tokens.intersection(candidates))


def has_any_phrase(normalized_question: str, phrases: set[str]) -> bool:
    return any(phrase in normalized_question for phrase in phrases)


def retrieval_routing_adjustment(question: str, row: dict[str, Any]) -> float:
    """Small deterministic correction for known Chinook business phrasing.

    The embedding/BM25 score remains the base signal. These adjustments only fix
    recurring logged cases where a phrase is clearly in-domain but the nearest
    repository description is a neighboring ranked/breakdown query.
    """

    query_id = row["query_id"]
    normalized = normalize_phrase_text(question)
    tokens = set(tokenize(question))
    adjustment = 0.0

    has_sales_or_money = has_any_token(tokens, {"revenue", "sale", "money", "earn", "make"})
    has_geo = has_any_token(tokens, {"country", "city", "billing", "usa", "brazil", "canada", "france", "germany"})
    has_customer = has_any_token(tokens, {"customer", "buyer", "spender"})
    has_count = has_any_token(tokens, {"count", "how", "many", "number", "total"})
    has_invoice = has_any_token(tokens, {"invoice"})
    has_track = has_any_token(tokens, {"track", "song"})
    has_album = has_any_token(tokens, {"album"})
    has_artist = has_any_token(tokens, {"artist", "band"})
    has_quantity = has_any_token(tokens, {"quantity", "qty", "unit", "copy", "copies", "times", "volume"})
    has_money_metric = has_any_token(tokens, {"revenue", "money", "dollar", "amount", "earning", "earn", "price"})
    has_latest = has_any_token(tokens, {"last", "latest", "recent", "current"})
    has_direct_month_parameter = bool(re.search(r"\b(?:19|20)\d{2}[-/](?:0?[1-9]|1[0-2])\b", question))
    has_year_parameter = bool(re.search(r"\b(?:19|20)\d{2}\b", question))
    has_monthly_all = (
        has_any_token(tokens, {"month", "monthly"})
        and not has_latest
        and (
            has_any_token(tokens, {"per", "each", "every", "trend"})
            or has_any_phrase(normalized, {"per month", "each month", "every month", "by month", "sales per month"})
        )
    )

    if has_any_token(tokens, {"media", "file", "format", "type"}) and has_any_phrase(
        normalized,
        {"file type", "file format", "media type", "media format"},
    ):
        asks_most_common_type = has_any_token(tokens, {"most", "common", "largest", "top", "highest"})
        asks_simple_type_count = (
            has_track
            or has_count
            or has_any_phrase(normalized, {"tracks by media type", "media type count", "media type counts"})
        ) and not asks_most_common_type
        if query_id == "q016" and asks_simple_type_count:
            adjustment += 0.45
        elif query_id == "q056" and asks_simple_type_count:
            adjustment -= 0.25
        elif query_id == "q056":
            adjustment += 0.35
        elif query_id == "q016":
            adjustment += 0.20
        elif query_id == "q025" and not has_any_token(tokens, {"playlist", "genre"}):
            adjustment -= 0.25
        elif query_id == "q046" and not has_sales_or_money:
            adjustment -= 0.20

    if has_any_token(tokens, {"media", "file", "format", "type"}) and has_money_metric:
        if query_id == "q046":
            adjustment += 0.40
        elif query_id in {"q016", "q056"}:
            adjustment -= 0.20

    if has_artist and has_any_token(tokens, {"quantity", "qty", "sold", "sale"}) and not has_money_metric:
        if query_id == "q045":
            adjustment += 0.35
        elif query_id == "q053":
            adjustment -= 0.25

    if has_artist and (
        has_any_token(tokens, {"all", "every", "list", "name"})
        or has_any_phrase(normalized, {"all artist", "artist list", "artist names", "show me artists"})
    ) and not has_any_token(tokens, {"quantity", "qty", "sold", "sale", "album", "revenue", "money"}):
        if query_id == "q053":
            adjustment += 0.35
        elif query_id in {"q018", "q020", "q045", "q051", "q052"}:
            adjustment -= 0.15

    if has_album and (
        has_any_token(tokens, {"all", "every", "list", "name"})
        or has_any_phrase(normalized, {"all album", "album list", "which albums", "artist has which albums", "what albums"})
        or (has_any_token(tokens, {"artist"}) and has_any_phrase(normalized, {"artist has", "artist album"}))
    ) and not has_any_token(tokens, {"most", "highest", "revenue", "money", "sales", "sold", "quantity", "copy", "copies", "track", "song"}):
        if query_id == "q054":
            adjustment += 0.35
        elif query_id in {"q018", "q019", "q043", "q044"}:
            adjustment -= 0.15

    if has_album and has_any_token(tokens, {"most", "highest", "top"}) and has_any_token(tokens, {"track", "song"}):
        if query_id == "q019":
            adjustment += 0.35
        elif query_id == "q054":
            adjustment -= 0.20

    if has_album and has_money_metric:
        if query_id == "q043":
            adjustment += 0.40
        elif query_id in {"q020", "q054"}:
            adjustment -= 0.25

    if has_album and has_any_token(tokens, {"quantity", "qty", "sold", "copy", "copies", "volume"}):
        if query_id == "q044":
            adjustment += 0.40
        elif query_id in {"q011", "q054"}:
            adjustment -= 0.25

    if (
        has_sales_or_money
        and has_any_token(tokens, {"most", "highest", "maximum", "top", "peak"})
        and has_any_token(tokens, {"day", "date"})
    ):
        if query_id == "q055":
            adjustment += 0.35
        elif query_id in {"q011", "q012", "q030", "q044"}:
            adjustment -= 0.10

    if (
        has_sales_or_money
        and has_any_token(tokens, {"when"})
        and has_any_token(tokens, {"most", "highest", "maximum", "peak"})
        and not has_any_token(tokens, {"day", "date", "year"})
    ):
        if query_id == "q030":
            adjustment += 0.30
        elif query_id in {"q003", "q007", "q012", "q027"}:
            adjustment -= 0.12

    if has_any_token(tokens, {"customer", "who"}) and (
        has_any_phrase(normalized, {"not bought", "bought anything", "bought nothing", "no orders", "no purchases"})
        or (has_any_token(tokens, {"not", "nothing", "without"}) and has_any_token(tokens, {"purchase", "order", "invoice"}))
    ):
        if query_id == "q042":
            adjustment += 0.35
        elif query_id in {"q009", "q011", "q044", "q047"}:
            adjustment -= 0.10

    if has_sales_or_money and (
        has_any_token(tokens, {"trend", "doing"})
        or has_any_phrase(normalized, {"going up or down", "up or down", "over time"})
    ):
        if query_id == "q004":
            adjustment += 0.35
        elif query_id in {"q002", "q035", "q036", "q037"} and not has_geo:
            adjustment -= 0.20

    if has_monthly_all:
        if has_geo and query_id == "q037":
            adjustment += 0.55
        elif has_geo and query_id == "q004":
            adjustment -= 0.30
        elif query_id == "q004":
            adjustment += 0.45
        elif query_id in {"q026", "q029"}:
            adjustment -= 0.30

    if has_any_token(tokens, {"month", "monthly"}) and has_geo:
        if query_id == "q037":
            adjustment += 0.45
        elif query_id in {"q004", "q026"}:
            adjustment -= 0.20

    if has_latest and has_any_token(tokens, {"month", "monthly"}):
        if query_id == "q026":
            adjustment += 0.35
        elif query_id == "q004":
            adjustment -= 0.20

    if has_any_token(tokens, {"employee", "rep", "representative", "support"}) and has_latest and has_any_token(tokens, {"month", "monthly"}):
        if query_id == "q049":
            adjustment += 0.55
        elif query_id == "q026":
            adjustment -= 0.25

    if has_any_token(tokens, {"employee", "rep", "representative", "support"}) and has_year_parameter and has_sales_or_money:
        if query_id == "q050":
            adjustment += 0.45
        elif query_id in {"q028", "q022"}:
            adjustment -= 0.15

    if has_direct_month_parameter and has_sales_or_money:
        if query_id == "q029":
            adjustment += 0.45
        elif query_id in {"q004", "q026", "q028"}:
            adjustment -= 0.20

    if has_year_parameter and not has_direct_month_parameter and has_sales_or_money:
        if query_id == "q028":
            adjustment += 0.35
        elif query_id in {"q003", "q027", "q029"}:
            adjustment -= 0.15

    if has_any_token(tokens, {"year", "yearly", "max", "maximum"}) and not question_has_parameter_hint(question, "year"):
        if has_latest or has_any_token(tokens, {"max", "maximum"}):
            if query_id == "q027":
                adjustment += 0.45
            elif query_id == "q003":
                adjustment -= 0.25

    if has_any_token(tokens, {"year", "yearly"}) and not has_latest and not question_has_parameter_hint(question, "year") and not has_any_token(tokens, {"max", "maximum"}):
        if query_id == "q003":
            adjustment += 0.35
        elif query_id == "q027":
            adjustment -= 0.25

    if has_any_token(tokens, {"average", "avg", "mean"}) and has_invoice:
        if has_geo:
            if query_id == "q034":
                adjustment += 0.50
            elif query_id in {"q005", "q006"}:
                adjustment -= 0.20
        else:
            if query_id == "q005":
                adjustment += 0.35
            elif query_id == "q034":
                adjustment -= 0.25

    if has_geo and has_invoice and (has_count or has_any_token(tokens, {"top", "most", "highest"})):
        if query_id == "q006":
            adjustment += 0.40
        elif query_id in {"q002", "q010", "q034", "q037"}:
            adjustment -= 0.20

    if has_geo and has_sales_or_money and not has_customer and not has_invoice and not has_any_token(tokens, {"month", "monthly", "city"}):
        if query_id == "q002":
            adjustment += 0.40
        elif query_id in {"q006", "q010", "q034", "q037"}:
            adjustment -= 0.20

    if has_geo and has_customer:
        if has_any_token(tokens, {"top", "biggest", "spender", "spend", "revenue", "total"}):
            if query_id == "q041":
                adjustment += 0.45
            elif query_id in {"q007", "q009", "q010"}:
                adjustment -= 0.20
        elif has_count:
            if query_id == "q039":
                adjustment += 0.35
            elif query_id == "q008":
                adjustment -= 0.10
        elif has_any_token(tokens, {"list", "first", "name", "sorted"}):
            if query_id == "q008":
                adjustment += 0.35
            elif query_id == "q039":
                adjustment -= 0.20

    if has_customer and has_count and not has_geo:
        if has_any_phrase(normalized, {"how many customers", "customer total", "total customers"}):
            if query_id == "q038":
                adjustment += 0.35
            elif query_id == "q039":
                adjustment -= 0.20

    if has_track and has_any_token(tokens, {"genre", "rock", "metal", "jazz", "latin", "pop", "classical", "blues"}):
        if query_id == "q048" and has_any_token(tokens, {"top", "quantity", "qty", "sold", "sale"}):
            adjustment += 0.45
        elif query_id == "q011":
            adjustment -= 0.25

    if has_track and has_money_metric:
        if has_any_token(tokens, {"expensive", "highest", "price"}) and not has_any_token(tokens, {"sold", "sale", "quantity", "qty"}):
            if query_id == "q014":
                adjustment += 0.50
            elif query_id in {"q011", "q012"}:
                adjustment -= 0.25
        elif query_id == "q012":
            adjustment += 0.45
        elif query_id == "q011":
            adjustment -= 0.25

    if has_any_token(tokens, {"genre"}) and has_geo and has_sales_or_money:
        if query_id == "q036":
            adjustment += 0.50
        elif query_id in {"q002", "q017", "q037"}:
            adjustment -= 0.20

    if has_track and has_quantity and not has_money_metric and not has_any_token(tokens, {"genre", "rock", "metal", "jazz", "latin", "pop", "classical", "blues"}):
        if query_id == "q011":
            adjustment += 0.35

    if has_any_token(tokens, {"genre"}) and has_track and has_count and not has_any_token(tokens, {"playlist"}):
        if query_id == "q015":
            adjustment += 0.40
        elif query_id == "q025":
            adjustment -= 0.25

    if has_any_token(tokens, {"playlist"}) and has_any_token(tokens, {"genre"}):
        if query_id == "q025":
            adjustment += 0.35
        elif query_id == "q015":
            adjustment -= 0.20

    if has_any_token(tokens, {"employee", "rep", "representative", "support"}) and has_customer and has_count:
        if query_id == "q021":
            adjustment += 0.40
        elif query_id == "q038":
            adjustment -= 0.25

    if has_track and has_any_phrase(normalized, {"no sales", "never sold", "not sold", "without sales"}):
        if query_id == "q047":
            adjustment += 0.45
        elif query_id == "q054":
            adjustment -= 0.25

    return adjustment


def extract_sql_tokens(sql: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sql)
    tokens: list[str] = []
    for token in raw_tokens:
        tokens.extend(tokenize(token))
    return [token for token in tokens if token not in SQL_KEYWORDS]


class BM25Index:
    def __init__(self, documents: list[dict[str, Any]], config: AppConfig = CONFIG) -> None:
        self.documents = documents
        self.k1 = config.bm25_k1
        self.b = config.bm25_b
        self.doc_count = len(documents)
        self.avg_doc_len = sum(doc["token_count"] for doc in documents) / max(self.doc_count, 1)
        self.document_frequency: Counter[str] = Counter()
        for document in documents:
            self.document_frequency.update(document["term_frequency"].keys())

    def idf(self, token: str) -> float:
        frequency = self.document_frequency.get(token, 0)
        return math.log(1 + (self.doc_count - frequency + 0.5) / (frequency + 0.5))

    def score(self, query_tokens: list[str], document: dict[str, Any]) -> float:
        score = 0.0
        term_frequency: Counter[str] = document["term_frequency"]
        doc_length = document["token_count"]
        for token in query_tokens:
            frequency = term_frequency.get(token, 0)
            if frequency == 0:
                continue
            numerator = frequency * (self.k1 + 1)
            denominator = frequency + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_len))
            score += self.idf(token) * (numerator / denominator)
        return score


def build_lexical_documents(
    repository: list[dict[str, Any]],
    user_query_variations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    variations_by_id = {entry["query_id"]: entry.get("user_queries", []) for entry in user_query_variations}
    documents: list[dict[str, Any]] = []

    for entry in repository:
        tokens: list[str] = []

        def add_parts(
            parts: list[Any],
            *,
            repeat: int = 1,
            excluded_tokens: set[str] | None = None,
        ) -> None:
            excluded_tokens = excluded_tokens or set()
            for _ in range(repeat):
                for part in parts:
                    tokens.extend(
                        token
                        for token in tokenize(str(part))
                        if token not in excluded_tokens
                    )

        add_parts([entry["optimized_description"]], repeat=2)
        add_parts([entry["intent"]], repeat=2)
        add_parts([entry["category"], entry["description"]])
        add_parts(entry.get("sample_questions", []))
        add_parts(variations_by_id.get(entry["query_id"], []))
        add_parts(
            entry.get("expected_columns", []),
            repeat=2,
            excluded_tokens=SCHEMA_GENERIC_TOKENS,
        )
        add_parts(entry.get("tables_used", []), repeat=2)
        add_parts(
            extract_sql_tokens(entry["sql"]),
            excluded_tokens=SCHEMA_GENERIC_TOKENS,
        )
        for parameter in entry.get("parameters", []):
            add_parts(
                [
                    parameter.get("name", ""),
                    parameter.get("type", ""),
                    parameter.get("description", ""),
                ]
            )

        term_frequency = Counter(tokens)
        documents.append(
            {
                "query_id": entry["query_id"],
                "category": entry["category"],
                "intent": entry["intent"],
                "tokens": tokens,
                "token_count": len(tokens),
                "term_frequency": term_frequency,
            }
        )
    return documents


class HybridRetriever:
    def __init__(
        self,
        repository: list[dict[str, Any]],
        user_query_variations: list[dict[str, Any]],
        description_embeddings: np.ndarray,
        embedding_records: list[dict[str, Any]],
        config: AppConfig = CONFIG,
    ) -> None:
        self.repository = repository
        self.config = config
        self.model = SentenceTransformer(config.embedding_model)
        self.embedding_by_id = {
            record["query_id"]: normalize_vector(description_embeddings[index].astype(np.float32))
            for index, record in enumerate(embedding_records)
        }
        self.lexical_documents = build_lexical_documents(repository, user_query_variations)
        self.lexical_by_id = {document["query_id"]: document for document in self.lexical_documents}
        self.bm25 = BM25Index(self.lexical_documents, config)

    def embed_question(self, question: str) -> np.ndarray:
        vector = self.model.encode([question], normalize_embeddings=True)[0]
        return normalize_vector(np.asarray(vector, dtype=np.float32))

    def retrieve(self, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        question_embedding = self.embed_question(question)
        query_tokens = tokenize(question)

        dense_scores: list[float] = []
        lexical_scores: list[float] = []
        base_rows: list[dict[str, Any]] = []

        for entry in self.repository:
            query_id = entry["query_id"]
            dense_score = float(np.dot(question_embedding, self.embedding_by_id[query_id]))
            lexical_score = self.bm25.score(query_tokens, self.lexical_by_id[query_id])
            dense_scores.append(dense_score)
            lexical_scores.append(lexical_score)
            base_rows.append(
                {
                    "query_id": query_id,
                    "category": entry["category"],
                    "intent": entry["intent"],
                    "description": entry["optimized_description"],
                    "sql": entry["sql"],
                    "expected_columns": entry.get("expected_columns", []),
                    "tables_used": entry.get("tables_used", []),
                    "parameters": entry.get("parameters", []),
                    "dense_score": dense_score,
                    "lexical_score": lexical_score,
                }
            )

        dense_normalized = minmax(dense_scores)
        lexical_normalized = minmax(lexical_scores)

        for index, row in enumerate(base_rows):
            row["dense_score_normalized"] = dense_normalized[index]
            row["lexical_score_normalized"] = lexical_normalized[index]
            row["base_hybrid_score"] = (
                self.config.dense_weight * row["dense_score_normalized"]
                + self.config.lexical_weight * row["lexical_score_normalized"]
            )
            row["parameter_hint_penalty"] = parameter_hint_penalty(question, row.get("parameters", []), self.config)
            row["routing_adjustment"] = retrieval_routing_adjustment(question, row)
            row["hybrid_score"] = row["base_hybrid_score"] - row["parameter_hint_penalty"] + row["routing_adjustment"]

        dense_ranks = {
            row["query_id"]: index + 1
            for index, row in enumerate(sorted(base_rows, key=lambda item: (-item["dense_score"], item["query_id"])))
        }
        lexical_ranks = {
            row["query_id"]: index + 1
            for index, row in enumerate(sorted(base_rows, key=lambda item: (-item["lexical_score"], item["query_id"])))
        }

        ranked = sorted(base_rows, key=lambda item: (-item["hybrid_score"], item["query_id"]))
        for index, row in enumerate(ranked):
            row["rank"] = index + 1
            row["dense_rank"] = dense_ranks[row["query_id"]]
            row["lexical_rank"] = lexical_ranks[row["query_id"]]

        return ranked[:top_k]

    def decide(self, matches: list[dict[str, Any]]) -> RetrievalDecision:
        if not matches:
            return RetrievalDecision(False, "No repository match was found.")

        top_score = matches[0]["hybrid_score"]
        second_score = matches[1]["hybrid_score"] if len(matches) > 1 else 0.0
        margin = top_score - second_score

        if top_score < self.config.auto_execute_min_score:
            return RetrievalDecision(
                False,
                f"Top score {top_score:.3f} is below threshold {self.config.auto_execute_min_score:.3f}.",
            )
        if margin < self.config.auto_execute_min_margin:
            return RetrievalDecision(
                False,
                f"Top match margin {margin:.3f} is below threshold {self.config.auto_execute_min_margin:.3f}.",
            )
        return RetrievalDecision(True, "Top match is strong enough to execute.")
