from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from src.config import CONFIG  # noqa: E402
from src.data_loader import load_optimized_descriptions, load_repository, write_json  # noqa: E402


EXPECTED_QUERY_COUNT = 56


def validate_inputs(repository: list[dict], descriptions: list[dict]) -> list[dict]:
    if len(repository) != EXPECTED_QUERY_COUNT:
        raise ValueError(f"Expected {EXPECTED_QUERY_COUNT} repository entries, found {len(repository)}")
    if len(descriptions) != EXPECTED_QUERY_COUNT:
        raise ValueError(f"Expected {EXPECTED_QUERY_COUNT} optimized descriptions, found {len(descriptions)}")

    descriptions_by_id = {entry["query_id"]: entry for entry in descriptions}
    records: list[dict] = []

    for entry in repository:
        query_id = entry["query_id"]
        description_entry = descriptions_by_id.get(query_id)
        if description_entry is None:
            raise ValueError(f"Missing optimized description for {query_id}")
        description = description_entry.get("description", "").strip()
        if not description:
            raise ValueError(f"Optimized description for {query_id} is empty")
        records.append(
            {
                "query_id": query_id,
                "category": entry["category"],
                "intent": entry["intent"],
                "description": description,
                "selected_strategy": description_entry.get("selected_strategy"),
                "source": description_entry.get("source"),
            }
        )

    return records


def main() -> None:
    repository = load_repository(CONFIG)
    optimized_descriptions = load_optimized_descriptions(CONFIG)
    records = validate_inputs(repository, optimized_descriptions)

    CONFIG.index_dir.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(CONFIG.embedding_model)
    texts = [record["description"] for record in records]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    matrix = np.asarray(embeddings, dtype=np.float32)

    if matrix.ndim != 2 or matrix.shape[0] != EXPECTED_QUERY_COUNT:
        raise ValueError(f"Unexpected embedding matrix shape: {matrix.shape}")

    np.save(CONFIG.embedding_path, matrix)
    write_json(
        CONFIG.embedding_metadata_path,
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "embedding_model": CONFIG.embedding_model,
            "embedding_dimensions": int(matrix.shape[1]),
            "description_source": str(CONFIG.optimized_descriptions_path.relative_to(CONFIG.project_root)),
            "record_count": len(records),
            "records": records,
        },
    )

    print(f"Wrote embeddings: {CONFIG.embedding_path.relative_to(CONFIG.project_root)}")
    print(f"Wrote metadata: {CONFIG.embedding_metadata_path.relative_to(CONFIG.project_root)}")
    print(f"Shape: {matrix.shape[0]} descriptions x {matrix.shape[1]} dimensions")


if __name__ == "__main__":
    main()
