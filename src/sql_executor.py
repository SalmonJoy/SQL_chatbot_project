from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .config import CONFIG, AppConfig


UNSAFE_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma|vacuum)\b",
    re.IGNORECASE,
)


def validate_readonly_sql(sql: str) -> str:
    stripped = sql.strip().rstrip(";").strip()
    lowered = stripped.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Only SELECT/WITH repository queries are allowed.")
    if ";" in stripped:
        raise ValueError("Multiple SQL statements are not allowed.")
    if UNSAFE_SQL_PATTERN.search(stripped):
        raise ValueError("Unsafe SQL keyword found.")
    return stripped


class SQLExecutor:
    def __init__(self, repository: list[dict[str, Any]], config: AppConfig = CONFIG) -> None:
        self.config = config
        self.repository_by_id = {entry["query_id"]: entry for entry in repository}

    def execute_query_id(self, query_id: str, parameters: dict[str, Any] | None = None) -> pd.DataFrame:
        entry = self.repository_by_id.get(query_id)
        if entry is None:
            raise KeyError(f"Unknown query_id: {query_id}")
        return self.execute_sql(entry["sql"], parameters)

    def execute_sql(self, sql: str, parameters: dict[str, Any] | None = None) -> pd.DataFrame:
        safe_sql = validate_readonly_sql(sql)
        db_path = Path(self.config.sqlite_path).resolve()
        connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            return pd.read_sql_query(safe_sql, connection, params=parameters or {})
        finally:
            connection.close()
