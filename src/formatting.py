from __future__ import annotations

from typing import Any

import pandas as pd


def format_score(value: float) -> str:
    return f"{value:.3f}"


def retrieval_rows_for_display(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": match["rank"],
            "query_id": match["query_id"],
            "intent": match["intent"],
            "hybrid_score": round(match["hybrid_score"], 4),
            "parameter_hint_penalty": round(match.get("parameter_hint_penalty", 0.0), 4),
            "routing_adjustment": round(match.get("routing_adjustment", 0.0), 4),
            "dense_score": round(match["dense_score"], 4),
            "lexical_score": round(match["lexical_score"], 4),
            "dense_rank": match["dense_rank"],
            "lexical_rank": match["lexical_rank"],
            "parameters": ", ".join(parameter["name"] for parameter in match.get("parameters", [])),
        }
        for match in matches
    ]


def truncate_dataframe(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    if len(df) <= max_rows:
        return df
    return df.head(max_rows)
