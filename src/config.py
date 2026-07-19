from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppConfig:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    queries_dir: Path = PROJECT_ROOT / "queries"
    query_repository_path: Path = PROJECT_ROOT / "data" / "query_repository.json"
    optimized_descriptions_path: Path = PROJECT_ROOT / "data" / "optimized_descriptions.json"
    user_query_variations_path: Path = PROJECT_ROOT / "data" / "user_query_variations.json"
    sqlite_path: Path = PROJECT_ROOT / "data" / "Chinook_Sqlite.sqlite"
    index_dir: Path = PROJECT_ROOT / "data" / "index"
    embedding_path: Path = PROJECT_ROOT / "data" / "index" / "description_embeddings.npy"
    embedding_metadata_path: Path = PROJECT_ROOT / "data" / "index" / "description_embedding_metadata.json"
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    dense_weight: float = float(os.getenv("HYBRID_DENSE_WEIGHT", "0.70"))
    lexical_weight: float = float(os.getenv("HYBRID_LEXICAL_WEIGHT", "0.30"))
    bm25_k1: float = float(os.getenv("BM25_K1", "1.5"))
    bm25_b: float = float(os.getenv("BM25_B", "0.75"))
    auto_execute_min_score: float = float(os.getenv("AUTO_EXECUTE_MIN_SCORE", "0.55"))
    auto_execute_min_margin: float = float(os.getenv("AUTO_EXECUTE_MIN_MARGIN", "0.05"))
    max_result_rows_for_llm: int = int(os.getenv("MAX_RESULT_ROWS_FOR_LLM", "200"))
    max_result_rows_display: int = int(os.getenv("MAX_RESULT_ROWS_DISPLAY", "100"))
    enable_context_rewrite: bool = os.getenv("ENABLE_CONTEXT_REWRITE", "true").lower() in {"1", "true", "yes", "on"}
    max_context_result_rows: int = int(os.getenv("MAX_CONTEXT_RESULT_ROWS", "20"))
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    log_dir: Path = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")
    log_file: str = os.getenv("LOG_FILE", "chatbot_events.jsonl")
    log_sql_result_rows: str = os.getenv("LOG_SQL_RESULT_ROWS", "all")


CONFIG = AppConfig()
