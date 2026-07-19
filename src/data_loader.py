from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .config import CONFIG, AppConfig


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")


def load_repository(config: AppConfig = CONFIG) -> list[dict[str, Any]]:
    repository = load_json(config.query_repository_path)
    if not isinstance(repository, list) or not repository:
        raise ValueError("query_repository.json must contain a non-empty array")
    return repository


def load_optimized_descriptions(config: AppConfig = CONFIG) -> list[dict[str, Any]]:
    descriptions = load_json(config.optimized_descriptions_path)
    if not isinstance(descriptions, list) or not descriptions:
        raise ValueError("optimized_descriptions.json must contain a non-empty array")
    return descriptions


def load_user_query_variations(config: AppConfig = CONFIG) -> list[dict[str, Any]]:
    variations = load_json(config.user_query_variations_path)
    if not isinstance(variations, list) or not variations:
        raise ValueError("user_query_variations.json must contain a non-empty array")
    return variations


def load_description_index(config: AppConfig = CONFIG) -> tuple[np.ndarray, list[dict[str, Any]]]:
    if not config.embedding_path.exists() or not config.embedding_metadata_path.exists():
        raise FileNotFoundError(
            "MiniLM description index is missing. Run `python scripts/build_index.py` first."
        )

    embeddings = np.load(config.embedding_path)
    metadata = load_json(config.embedding_metadata_path)
    records = metadata.get("records", [])

    if embeddings.ndim != 2:
        raise ValueError("description_embeddings.npy must be a 2D matrix")
    if len(records) != embeddings.shape[0]:
        raise ValueError("embedding metadata record count does not match embedding matrix")
    return embeddings, records


def merge_repository_with_optimized_descriptions(
    repository: list[dict[str, Any]],
    optimized_descriptions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    optimized_by_id = {entry["query_id"]: entry for entry in optimized_descriptions}
    merged: list[dict[str, Any]] = []

    for entry in repository:
        query_id = entry["query_id"]
        optimized = optimized_by_id.get(query_id)
        if optimized is None:
            raise ValueError(f"missing optimized description for {query_id}")

        merged.append(
            {
                **entry,
                "optimized_description": optimized["description"],
                "optimized_description_source": optimized.get("source"),
                "optimized_description_strategy": optimized.get("selected_strategy"),
            }
        )

    return merged

