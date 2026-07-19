from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.ambiguity_guard import evaluate_ambiguity, prioritize_ambiguous_options  # noqa: E402
from src.config import CONFIG  # noqa: E402
from src.context_rewriter import normalize_payload, rewrite_follow_up_question, should_attempt_context_rewrite  # noqa: E402
from src.conversation_context import build_context_snapshot  # noqa: E402
from src.data_loader import (  # noqa: E402
    load_description_index,
    load_optimized_descriptions,
    load_repository,
    load_user_query_variations,
    merge_repository_with_optimized_descriptions,
)
from src.domain_guard import evaluate_domain  # noqa: E402
from src.multi_intent_guard import evaluate_multi_intent  # noqa: E402
from src.parameter_resolver import ParameterResolver  # noqa: E402
from src.retrieval import HybridRetriever  # noqa: E402
from src.runtime_logger import RuntimeLogger, base_event, dataframe_to_records  # noqa: E402
from src.sql_executor import SQLExecutor, validate_readonly_sql  # noqa: E402


EXPECTED_QUERY_COUNT = 56

SAMPLE_RETRIEVAL_CASES = [
    {"question": "What is the total revenue?", "query_id": "q001"},
    {"question": "Who are the top customers by spending?", "query_id": "q007"},
    {"question": "Show sales by country", "query_id": "q002"},
    {"question": "Which genres made the most money?", "query_id": "q017"},
    {"question": "playlist with most tracks", "query_id": "q024"},
    {"question": "revenue by support rep", "query_id": "q022"},
    {"question": "last moths sales", "query_id": "q026"},
    {"question": "last month sales", "query_id": "q026", "expected_first_row": {"month": "2025-12", "total_revenue": 38.62}},
    {"question": "monthly sales", "query_id": "q004"},
    {"question": "which month had highest sales", "query_id": "q030"},
    {"question": "sales in 2025", "query_id": "q028", "parameters": {"year": "2025"}},
    {"question": "customers from Brazil", "query_id": "q040", "parameters": {"country": "Brazil"}},
    {"question": "top customer in USA", "query_id": "q041", "parameters": {"country": "USA"}},
    {"question": "sales by genre in USA", "query_id": "q036", "parameters": {"country": "USA"}},
    {"question": "top tracks in Rock", "query_id": "q048", "parameters": {"genre_name": "Rock"}},
    {"question": "tracks never sold", "query_id": "q047"},
    {"question": "top selling albums", "query_id": "q044"},
    {"question": "employee sales last month", "query_id": "q049"},
    {"question": "which artist has most sales", "query_id": "q045"},
    {"question": "show top artists by revenue", "query_id": "q020"},
    {"question": "What is the revenue for Iron Maiden?", "query_id": "q051", "parameters": {"artist_name": "Iron Maiden"}},
    {"question": "What is the revenue rank for Iron Maiden?", "query_id": "q052", "parameters": {"artist_name": "Iron Maiden"}},
    {"question": "Is Iron Maiden the highest?", "query_id": "q052", "parameters": {"artist_name": "Iron Maiden"}},
    {"question": "when did I make most money?", "query_id": "q030"},
    {"question": "whern did I make most money?", "query_id": "q030"},
    {"question": "Which day sale was most", "query_id": "q055", "expected_first_row": {"revenue_day": "2025-11-13", "total_revenue": 25.86}},
    {"question": "who has not bought anything?", "query_id": "q042"},
    {
        "question": "what all file types we have and which one is the most common?",
        "query_id": "q056",
        "expected_first_row": {
            "file_type_name": "MPEG audio file",
            "track_count": 3034,
            "is_most_common_file_type": 1,
        },
    },
    {"question": "tell me all the artist", "query_id": "q053"},
    {"question": "all albums", "query_id": "q054"},
    {"question": "What artist has which albums", "query_id": "q054"},
    {"question": "How is my sales doing? going up or down?", "query_id": "q004"},
]


AMBIGUITY_GUARD_CASES = [
    {
        "question": "who sold most?",
        "should_block": True,
        "reason_code": "ambiguous_entity_type",
        "expected_options": {"q045", "q011", "q044"},
    },
    {
        "question": "tell me the person",
        "should_block": True,
        "reason_code": "vague_query",
    },
    {
        "question": "person whose tracks are sold most",
        "should_block": False,
        "top_query_id": "q045",
    },
    {
        "question": "how much is his revenue",
        "should_block": True,
        "reason_code": "unresolved_pronoun",
    },
    {
        "question": "is he the highest?",
        "should_block": True,
        "reason_code": "unresolved_pronoun",
    },
    {
        "question": "last month sales",
        "should_block": False,
        "top_query_id": "q026",
    },
    {
        "question": "total revenue",
        "should_block": False,
        "top_query_id": "q001",
    },
    {
        "question": "top tracks in Rock",
        "should_block": False,
        "top_query_id": "q048",
    },
]


DOMAIN_GUARD_CASES = [
    {"question": "who is india's president?", "should_block": True, "reason_code": "out_of_domain"},
    {"question": "what is 3x4?", "should_block": True, "reason_code": "math_out_of_domain"},
    {"question": "what is 3 * 4?", "should_block": True, "reason_code": "math_out_of_domain"},
    {"question": "multiply 3 and 4", "should_block": True, "reason_code": "math_out_of_domain"},
    {
        "question": "which artist has most sales and give an explanation on gravitational force and also information on blue whale",
        "should_block": True,
        "reason_code": "mixed_out_of_domain",
        "offending_contains": {"give an explanation on gravitational force", "information on blue whale"},
    },
    {
        "question": "total revenue and what is 3 * 4",
        "should_block": True,
        "reason_code": "mixed_out_of_domain",
        "offending_contains": {"what is 3 4"},
    },
    {"question": "total revenue", "should_block": False},
    {"question": "last month sales", "should_block": False},
    {"question": "top tracks in Rock", "should_block": False},
    {"question": "sales by country and city", "should_block": False},
    {"question": "Is Iron Maiden the highest?", "should_block": False},
    {"question": "is he the highest?", "should_block": False},
    {"question": "when did I make most money?", "should_block": False},
    {"question": "whern did I make most money?", "should_block": False},
    {"question": "who has not bought anything?", "should_block": False},
    {"question": "what all file types we have and which one is the most common?", "should_block": False},
    {
        "question": "What do the artists have for lunch?",
        "should_block": True,
        "reason_code": "domain_entity_unrelated_attribute",
    },
]


MULTI_INTENT_GUARD_CASES = [
    {
        "question": "Who bought most and who sold most?",
        "should_block": True,
        "reason_code": "multiple_database_intents",
    },
    {
        "question": "Artist who sold most album and customer who bought most albums",
        "should_block": True,
        "reason_code": "multiple_database_intents",
    },
    {
        "question": "sales by country and city",
        "should_block": False,
    },
    {
        "question": "which day sale was most",
        "should_block": False,
    },
]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_runtime_logging() -> None:
    test_config = replace(CONFIG, log_file="smoke_test_events.jsonl", log_sql_result_rows="all")
    log_path = test_config.log_dir / test_config.log_file
    if log_path.exists():
        log_path.unlink()

    result_df = pd.DataFrame(
        [
            {"metric": "total_revenue", "value": 123.45},
            {"metric": "row_with_null", "value": None},
        ]
    )
    event = base_event("smoke-test-request", "What is the total revenue?", False, test_config)
    event["retrieval"] = {
        "status": "success",
        "matches": [
            {
                "query_id": "q001",
                "intent": "total revenue",
                "hybrid_score": 0.99,
                "dense_score": 0.88,
                "lexical_score": 1.23,
            }
        ],
        "decision": {
            "should_execute": True,
            "reason": "synthetic smoke test",
        },
    }
    event["sql"] = {
        "status": "success",
        "sql": "SELECT SUM(Total) AS total_revenue FROM Invoice",
        "result_columns": list(result_df.columns),
        "result_row_count": len(result_df),
        "result_rows": dataframe_to_records(result_df, test_config),
    }
    event["answer"] = {
        "status": "success",
        "source": "fallback_no_gemini_api_key",
        "gemini_model": test_config.gemini_model,
        "text": "The result is 123.45.",
    }

    RuntimeLogger(test_config).write(event)
    assert_true(log_path.exists(), "runtime log file should be created")

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert_true(len(lines) == 1, "runtime log should contain one JSONL line")
    parsed = json.loads(lines[0])
    for field in ["request_id", "timestamp", "question", "config", "retrieval", "sql", "answer"]:
        assert_true(field in parsed, f"runtime log is missing {field}")
    assert_true(parsed["sql"]["result_row_count"] == 2, "runtime log should include row count")
    assert_true(len(parsed["sql"]["result_rows"]) == 2, "runtime log should include all rows")

    secret = os.getenv("GEMINI_API_KEY")
    if secret:
        assert_true(secret not in lines[0], "runtime log must not contain GEMINI_API_KEY")


def validate_domain_guard() -> None:
    for case in DOMAIN_GUARD_CASES:
        guard = evaluate_domain(case["question"])
        assert_true(
            guard.should_block == case["should_block"],
            f"{case['question']!r}: expected domain should_block={case['should_block']}, got {guard.should_block}",
        )
        if "reason_code" in case:
            assert_true(
                guard.reason_code == case["reason_code"],
                f"{case['question']!r}: expected domain reason_code={case['reason_code']}, got {guard.reason_code}",
            )
        log_payload = guard.to_log()
        assert_true("matched_domain_terms" in log_payload, "domain guard log should include matched_domain_terms")
        assert_true("offending_clauses" in log_payload, "domain guard log should include offending_clauses")
        if "offending_contains" in case:
            offending_clauses = set(log_payload["offending_clauses"])
            missing_clauses = case["offending_contains"] - offending_clauses
            assert_true(
                not missing_clauses,
                f"{case['question']!r}: missing offending clauses {sorted(missing_clauses)}",
            )


def validate_multi_intent_guard() -> None:
    for case in MULTI_INTENT_GUARD_CASES:
        guard = evaluate_multi_intent(case["question"])
        assert_true(
            guard.should_block == case["should_block"],
            f"{case['question']!r}: expected multi-intent should_block={case['should_block']}, got {guard.should_block}",
        )
        if "reason_code" in case:
            assert_true(
                guard.reason_code == case["reason_code"],
                f"{case['question']!r}: expected multi-intent reason_code={case['reason_code']}, got {guard.reason_code}",
            )
        log_payload = guard.to_log()
        assert_true("intent_clauses" in log_payload, "multi-intent guard log should include intent_clauses")


def sample_parameters_for(entry: dict) -> dict:
    values = {
        "year": "2025",
        "month": "2025-12",
        "country": "USA",
        "genre_name": "Rock",
        "artist_name": "Iron Maiden",
    }
    return {
        parameter["name"]: values[parameter["type"]]
        for parameter in entry.get("parameters", [])
    }


def validate_context_rewrite(
    retriever: HybridRetriever,
    executor: SQLExecutor,
    parameter_resolver: ParameterResolver,
) -> None:
    first_question = "person whose tracks are sold most"
    first_matches = retriever.retrieve(first_question, top_k=5)
    assert_true(first_matches[0]["query_id"] == "q045", "context seed question should retrieve q045")
    first_result = executor.execute_query_id("q045")
    context = build_context_snapshot(
        original_question=first_question,
        effective_question=first_question,
        match=first_matches[0],
        sql_parameters={},
        result_df=first_result,
        answer="The artist whose tracks are sold the most is Iron Maiden.",
        config=CONFIG,
    )

    follow_up = "how much is his revenue"
    assert_true(should_attempt_context_rewrite(follow_up, context), "follow-up rewrite should be attempted")
    simulated_payload = {
        "is_follow_up": True,
        "standalone_question": "What is the revenue for Iron Maiden?",
        "resolved_references": {"his": "Iron Maiden"},
        "confidence": "high",
        "reason": "The previous result identified Iron Maiden as the top artist.",
    }
    rewrite = normalize_payload(follow_up, simulated_payload, json.dumps(simulated_payload))
    assert_true(rewrite.use_rewrite, "simulated Gemini rewrite should be used")
    rewritten_matches = retriever.retrieve(rewrite.effective_question, top_k=5)
    assert_true(
        rewritten_matches[0]["query_id"] == "q051",
        f"rewritten follow-up should retrieve q051, got {rewritten_matches[0]['query_id']}",
    )
    rewritten_parameters = parameter_resolver.resolve(rewritten_matches[0], rewrite.effective_question)
    assert_true(
        rewritten_parameters.parameters == {"artist_name": "Iron Maiden"},
        f"rewritten follow-up should resolve artist_name=Iron Maiden, got {rewritten_parameters.parameters}",
    )

    comparative_follow_up = "is he the highest?"
    assert_true(
        should_attempt_context_rewrite(comparative_follow_up, context),
        "comparative follow-up rewrite should be attempted",
    )
    comparative_payload = {
        "is_follow_up": True,
        "standalone_question": "What is the revenue rank for Iron Maiden?",
        "resolved_references": {"he": "Iron Maiden"},
        "confidence": "high",
        "reason": "The previous result identified Iron Maiden as the top artist.",
    }
    comparative_rewrite = normalize_payload(
        comparative_follow_up,
        comparative_payload,
        json.dumps(comparative_payload),
    )
    assert_true(comparative_rewrite.use_rewrite, "simulated comparative Gemini rewrite should be used")
    comparative_matches = retriever.retrieve(comparative_rewrite.effective_question, top_k=5)
    assert_true(
        comparative_matches[0]["query_id"] == "q052",
        f"comparative follow-up should retrieve q052, got {comparative_matches[0]['query_id']}",
    )
    comparative_parameters = parameter_resolver.resolve(
        comparative_matches[0],
        comparative_rewrite.effective_question,
    )
    assert_true(
        comparative_parameters.parameters == {"artist_name": "Iron Maiden"},
        f"comparative follow-up should resolve artist_name=Iron Maiden, got {comparative_parameters.parameters}",
    )
    comparative_result = executor.execute_query_id("q052", comparative_parameters.parameters)
    for column in [
        "artist_name",
        "total_revenue",
        "revenue_rank",
        "top_artist_name",
        "top_artist_revenue",
        "is_highest_revenue_artist",
    ]:
        assert_true(column in comparative_result.columns, f"q052 result should include {column}")
    assert_true(len(comparative_result) == 1, "q052 should return one row for a specific artist")

    old_key = os.environ.pop("GEMINI_API_KEY", None)
    try:
        skipped = rewrite_follow_up_question(follow_up, context, CONFIG)
        assert_true(
            skipped.source == "no_gemini_api_key",
            f"missing Gemini key should skip rewrite safely, got {skipped.source}",
        )
        assert_true(not skipped.use_rewrite, "missing Gemini key must not use rewrite")
    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key


def main() -> None:
    repository = load_repository(CONFIG)
    optimized = load_optimized_descriptions(CONFIG)
    variations = load_user_query_variations(CONFIG)
    merged = merge_repository_with_optimized_descriptions(repository, optimized)
    embeddings, embedding_records = load_description_index(CONFIG)

    assert_true(len(repository) == EXPECTED_QUERY_COUNT, f"repository must contain {EXPECTED_QUERY_COUNT} queries")
    assert_true(len(optimized) == EXPECTED_QUERY_COUNT, f"optimized descriptions must contain {EXPECTED_QUERY_COUNT} entries")
    assert_true(len(embedding_records) == EXPECTED_QUERY_COUNT, f"embedding metadata must contain {EXPECTED_QUERY_COUNT} entries")
    assert_true(embeddings.shape[0] == EXPECTED_QUERY_COUNT, f"embedding matrix must contain {EXPECTED_QUERY_COUNT} rows")
    assert_true(abs(CONFIG.dense_weight - 0.70) < 1e-9, "dense weight must be 0.70")
    assert_true(abs(CONFIG.lexical_weight - 0.30) < 1e-9, "lexical weight must be 0.30")

    executor = SQLExecutor(merged, CONFIG)
    for entry in merged:
        sql_file = CONFIG.queries_dir / f"{entry['query_id']}.sql"
        assert_true(sql_file.exists(), f"{entry['query_id']} should have a SQL file")
        validate_readonly_sql(entry["sql"])
        result = executor.execute_query_id(entry["query_id"], sample_parameters_for(entry))
        assert_true(result is not None, f"{entry['query_id']} should return a dataframe")

    retriever = HybridRetriever(merged, variations, embeddings, embedding_records, CONFIG)
    parameter_resolver = ParameterResolver(CONFIG)
    for case in SAMPLE_RETRIEVAL_CASES:
        question = case["question"]
        expected_query_id = case["query_id"]
        matches = retriever.retrieve(question, top_k=3)
        actual_query_id = matches[0]["query_id"]
        assert_true(
            actual_query_id == expected_query_id,
            f"{question!r}: expected {expected_query_id}, got {actual_query_id}",
        )
        parameter_resolution = parameter_resolver.resolve(matches[0], question)
        assert_true(parameter_resolution.can_execute, f"{question!r}: parameters should be executable")
        if "parameters" in case:
            assert_true(
                parameter_resolution.parameters == case["parameters"],
                f"{question!r}: expected parameters {case['parameters']}, got {parameter_resolution.parameters}",
            )
        if "expected_first_row" in case:
            result = executor.execute_query_id(actual_query_id, parameter_resolution.parameters)
            first_row = result.iloc[0].to_dict()
            for key, expected_value in case["expected_first_row"].items():
                actual_value = first_row[key]
                if isinstance(expected_value, float):
                    assert_true(abs(float(actual_value) - expected_value) < 1e-9, f"{question!r}: {key} mismatch")
                else:
                    assert_true(actual_value == expected_value, f"{question!r}: {key} mismatch")

    for case in AMBIGUITY_GUARD_CASES:
        question = case["question"]
        matches = retriever.retrieve(question, top_k=5)
        guard = evaluate_ambiguity(question, matches[0], matches)
        assert_true(
            guard.should_block == case["should_block"],
            f"{question!r}: expected should_block={case['should_block']}, got {guard.should_block}",
        )
        if "reason_code" in case:
            assert_true(
                guard.reason_code == case["reason_code"],
                f"{question!r}: expected reason_code={case['reason_code']}, got {guard.reason_code}",
            )
        if "top_query_id" in case:
            assert_true(
                matches[0]["query_id"] == case["top_query_id"],
                f"{question!r}: expected top {case['top_query_id']}, got {matches[0]['query_id']}",
            )
        if "expected_options" in case:
            option_ids = {match["query_id"] for match in prioritize_ambiguous_options(question, matches)}
            missing_options = case["expected_options"] - option_ids
            assert_true(
                not missing_options,
                f"{question!r}: missing expected clickable options {sorted(missing_options)}",
            )

    validate_domain_guard()
    validate_multi_intent_guard()
    validate_context_rewrite(retriever, executor, parameter_resolver)
    validate_runtime_logging()

    print("Smoke test passed")
    print(f"Validated {EXPECTED_QUERY_COUNT} SQL queries")
    print(f"Validated {len(SAMPLE_RETRIEVAL_CASES)} retrieval cases")
    print(f"Validated {len(DOMAIN_GUARD_CASES)} domain guard cases")
    print(f"Validated {len(MULTI_INTENT_GUARD_CASES)} multi-intent guard cases")
    print(f"Validated {len(AMBIGUITY_GUARD_CASES)} ambiguity guard cases")
    print("Validated context rewrite safety cases")
    print("Validated runtime JSONL logging")


if __name__ == "__main__":
    main()
