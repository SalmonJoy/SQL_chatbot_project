from __future__ import annotations

import json
import math
import os
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import CONFIG, AppConfig


def new_request_id() -> str:
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(child) for child in value]
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def dataframe_to_records(df: pd.DataFrame, config: AppConfig = CONFIG) -> list[dict[str, Any]]:
    safe_df = df.where(pd.notnull(df), None)
    records = safe_df.to_dict(orient="records")
    if config.log_sql_result_rows.lower() == "all":
        return json_safe(records)

    try:
        limit = int(config.log_sql_result_rows)
    except ValueError:
        limit = 0
    if limit <= 0:
        return []
    return json_safe(records[:limit])


def config_snapshot(config: AppConfig = CONFIG) -> dict[str, Any]:
    return {
        "embedding_model": config.embedding_model,
        "dense_weight": config.dense_weight,
        "lexical_weight": config.lexical_weight,
        "bm25_k1": config.bm25_k1,
        "bm25_b": config.bm25_b,
        "auto_execute_min_score": config.auto_execute_min_score,
        "auto_execute_min_margin": config.auto_execute_min_margin,
        "max_result_rows_for_llm": config.max_result_rows_for_llm,
        "max_result_rows_display": config.max_result_rows_display,
        "enable_context_rewrite": config.enable_context_rewrite,
        "enable_gemini_decision_review": config.enable_gemini_decision_review,
        "gemini_decision_review_top_k": config.gemini_decision_review_top_k,
        "gemini_decision_review_margin_threshold": config.gemini_decision_review_margin_threshold,
        "max_context_result_rows": config.max_context_result_rows,
        "gemini_model": config.gemini_model,
        "gemini_api_key_present": bool(os.getenv("GEMINI_API_KEY")),
        "log_sql_result_rows": config.log_sql_result_rows,
    }


def retrieval_matches_for_log(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": match.get("rank"),
            "query_id": match.get("query_id"),
            "category": match.get("category"),
            "intent": match.get("intent"),
            "description": match.get("description"),
            "dense_score": match.get("dense_score"),
            "lexical_score": match.get("lexical_score"),
            "dense_score_normalized": match.get("dense_score_normalized"),
            "lexical_score_normalized": match.get("lexical_score_normalized"),
            "base_hybrid_score": match.get("base_hybrid_score"),
            "parameter_hint_penalty": match.get("parameter_hint_penalty"),
            "routing_adjustment": match.get("routing_adjustment"),
            "hybrid_score": match.get("hybrid_score"),
            "dense_rank": match.get("dense_rank"),
            "lexical_rank": match.get("lexical_rank"),
            "tables_used": match.get("tables_used", []),
            "expected_columns": match.get("expected_columns", []),
            "parameters": match.get("parameters", []),
        }
        for match in matches
    ]


def selected_match_for_log(match: dict[str, Any] | None) -> dict[str, Any] | None:
    if match is None:
        return None
    return {
        "query_id": match.get("query_id"),
        "category": match.get("category"),
        "intent": match.get("intent"),
        "description": match.get("description"),
        "dense_score": match.get("dense_score"),
        "lexical_score": match.get("lexical_score"),
        "dense_score_normalized": match.get("dense_score_normalized"),
        "lexical_score_normalized": match.get("lexical_score_normalized"),
        "base_hybrid_score": match.get("base_hybrid_score"),
        "parameter_hint_penalty": match.get("parameter_hint_penalty"),
        "routing_adjustment": match.get("routing_adjustment"),
        "hybrid_score": match.get("hybrid_score"),
        "dense_rank": match.get("dense_rank"),
        "lexical_rank": match.get("lexical_rank"),
        "sql": match.get("sql"),
        "tables_used": match.get("tables_used", []),
        "expected_columns": match.get("expected_columns", []),
        "parameters": match.get("parameters", []),
    }


def error_for_log(error: BaseException | None) -> dict[str, Any] | None:
    if error is None:
        return None
    return {
        "type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exception_only(type(error), error),
    }


class RuntimeLogger:
    def __init__(self, config: AppConfig = CONFIG) -> None:
        self.config = config
        self.log_path = config.log_dir / config.log_file

    def write(self, event: dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json_safe(event)
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            file.write("\n")


def base_event(
    request_id: str,
    question: str,
    force_execute: bool,
    config: AppConfig = CONFIG,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "timestamp": utc_now_iso(),
        "event_type": "chatbot_request",
        "question": question,
        "force_execute": force_execute,
        "config": config_snapshot(config),
    }
