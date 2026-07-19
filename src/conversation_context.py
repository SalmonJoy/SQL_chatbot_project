from __future__ import annotations

from typing import Any

import pandas as pd

from .config import CONFIG, AppConfig
from .runtime_logger import json_safe


ENTITY_COLUMN_SUFFIXES = (
    "_name",
    "_title",
    "_country",
)


def dataframe_records(df: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    safe_df = df.head(limit).where(pd.notnull(df.head(limit)), None)
    return json_safe(safe_df.to_dict(orient="records"))


def extract_entities(df: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    entity_columns = [
        column
        for column in df.columns
        if str(column).endswith(ENTITY_COLUMN_SUFFIXES)
        or str(column) in {"artist_name", "track_name", "album_title", "customer_first_name", "customer_last_name"}
    ]

    for row_index, row in df.head(limit).iterrows():
        for column in entity_columns:
            value = row.get(column)
            if pd.isna(value):
                continue
            text = str(value).strip()
            if not text:
                continue
            entities.append(
                {
                    "column": str(column),
                    "value": text,
                    "row_index": int(row_index),
                }
            )
    return entities[:limit]


def build_context_snapshot(
    *,
    original_question: str,
    effective_question: str,
    match: dict[str, Any],
    sql_parameters: dict[str, Any],
    result_df: pd.DataFrame,
    answer: str,
    config: AppConfig = CONFIG,
) -> dict[str, Any]:
    return {
        "last_user_question": original_question,
        "last_effective_question": effective_question,
        "last_query_id": match.get("query_id"),
        "last_intent": match.get("intent"),
        "last_category": match.get("category"),
        "last_sql_parameters": sql_parameters,
        "last_expected_columns": match.get("expected_columns", []),
        "last_tables_used": match.get("tables_used", []),
        "last_answer": answer,
        "last_result_row_count": len(result_df),
        "last_result_rows": dataframe_records(result_df, config.max_context_result_rows),
        "last_entities": extract_entities(result_df, config.max_context_result_rows),
    }


def compact_context_for_rewrite(context: dict[str, Any] | None) -> dict[str, Any] | None:
    if not context:
        return None
    return {
        "last_user_question": context.get("last_user_question"),
        "last_effective_question": context.get("last_effective_question"),
        "last_query_id": context.get("last_query_id"),
        "last_intent": context.get("last_intent"),
        "last_sql_parameters": context.get("last_sql_parameters", {}),
        "last_answer": context.get("last_answer"),
        "last_entities": context.get("last_entities", []),
        "last_result_rows": context.get("last_result_rows", []),
    }
