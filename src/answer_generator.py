from __future__ import annotations

import os
from typing import Any

import pandas as pd

from .config import CONFIG, AppConfig


def dataframe_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    safe_df = df.where(pd.notnull(df), None)
    return safe_df.to_dict(orient="records")


def dataframe_grounding_rows(df: pd.DataFrame, max_rows: int) -> tuple[list[dict[str, Any]], str]:
    if len(df) <= max_rows:
        return dataframe_records(df.copy()), "all_rows"

    head_count = max(max_rows // 2, 1)
    tail_count = max(max_rows - head_count, 1)
    preview = pd.concat([df.head(head_count), df.tail(tail_count)])
    return dataframe_records(preview.copy()), f"head_{head_count}_and_tail_{tail_count}"


def fallback_answer(question: str, match: dict[str, Any], result_df: pd.DataFrame) -> str:
    row_count = len(result_df)
    column_names = ", ".join(str(column) for column in result_df.columns)
    if row_count == 0:
        return (
            f"I matched your question to **{match['intent']}**, but the SQL query returned no rows."
        )

    if row_count == 1 and len(result_df.columns) == 1:
        value = result_df.iloc[0, 0]
        return (
            f"I matched your question to **{match['intent']}**. "
            f"The result is **{value}**."
        )

    return (
        f"I matched your question to **{match['intent']}**. "
        f"The query returned **{row_count} row(s)** with columns: {column_names}. "
        "See the table below for the exact values."
    )


def build_grounded_prompt(
    question: str,
    match: dict[str, Any],
    result_df: pd.DataFrame,
    config: AppConfig,
) -> str:
    rows, row_sample_strategy = dataframe_grounding_rows(result_df, config.max_result_rows_for_llm)
    return f"""You are answering a business user's natural-language question using only SQL query results.

Rules:
- Answer strictly from the returned data below.
- Do not invent numbers, rows, dates, entities, or explanations not present in the result.
- If the result is a table, summarize the key finding and mention that the table contains the exact values.
- If all rows are shown, base the answer on all returned rows.
- If only head and tail rows are shown, say that only a sample is available and do not claim latest, earliest, highest, or lowest values unless those rows are explicitly present in the sample or the SQL itself asks for that value.
- Rows may be sorted by the SQL. Respect the returned order and never infer unseen first or last rows.
- Keep the answer concise and business-friendly.

User question:
{question}

Matched intent:
{match["intent"]}

Executed SQL:
{match["sql"]}

Returned row count:
{len(result_df)}

Row sample strategy:
{row_sample_strategy}

Returned columns:
{list(result_df.columns)}

Rows for grounding:
{rows}
"""


def generate_answer(
    question: str,
    match: dict[str, Any],
    result_df: pd.DataFrame,
    config: AppConfig = CONFIG,
) -> tuple[str, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback_answer(question, match, result_df), "fallback_no_gemini_api_key"

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = build_grounded_prompt(question, match, result_df, config)
        response = client.models.generate_content(
            model=config.gemini_model,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            return fallback_answer(question, match, result_df), "fallback_empty_gemini_response"
        return text.strip(), "gemini"
    except Exception as exc:  # pragma: no cover - protects demo flow from API/runtime issues
        return (
            fallback_answer(question, match, result_df)
            + f"\n\n_Gemini answer generation was unavailable: {exc}_",
            "fallback_gemini_error",
        )
