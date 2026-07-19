from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
QUERIES_DIR = PROJECT_ROOT / "queries"


Q052 = {
    "query_id": "q052",
    "category": "artists",
    "intent": "revenue rank for specific artist",
    "description": "Returns one requested artist's revenue rank and whether that artist is the highest revenue artist.",
    "sample_questions": [
        "Is Iron Maiden the highest revenue artist?",
        "What is the revenue rank for U2?",
        "Is this artist the top earner?",
    ],
    "sql": """
WITH artist_revenue AS (
  SELECT ar.ArtistId AS artist_id,
         ar.Name AS artist_name,
         ROUND(COALESCE(SUM(il.UnitPrice * il.Quantity), 0), 2) AS total_revenue
  FROM Artist ar
  LEFT JOIN Album a ON ar.ArtistId = a.ArtistId
  LEFT JOIN Track t ON a.AlbumId = t.AlbumId
  LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
  GROUP BY ar.ArtistId
),
ranked_artists AS (
  SELECT artist_id,
         artist_name,
         total_revenue,
         RANK() OVER (ORDER BY total_revenue DESC, artist_name ASC) AS revenue_rank
  FROM artist_revenue
),
top_artist AS (
  SELECT artist_name AS top_artist_name,
         total_revenue AS top_artist_revenue
  FROM ranked_artists
  ORDER BY revenue_rank ASC, artist_name ASC
  LIMIT 1
)
SELECT ra.artist_name,
       ra.total_revenue,
       ra.revenue_rank,
       ta.top_artist_name,
       ta.top_artist_revenue,
       CASE WHEN ra.revenue_rank = 1 THEN 1 ELSE 0 END AS is_highest_revenue_artist
FROM ranked_artists ra
CROSS JOIN top_artist ta
WHERE ra.artist_name = :artist_name
""".strip(),
    "expected_columns": [
        "artist_name",
        "total_revenue",
        "revenue_rank",
        "top_artist_name",
        "top_artist_revenue",
        "is_highest_revenue_artist",
    ],
    "tables_used": ["Artist", "Album", "Track", "InvoiceLine"],
    "parameters": [
        {
            "name": "artist_name",
            "type": "artist_name",
            "required": True,
            "description": "Artist name available in the database.",
        }
    ],
}


Q052_VARIATIONS = [
    "Is Iron Maiden the highest revenue artist?",
    "What is the revenue rank for U2?",
    "Is this artist the top earner?",
    "is Iron Maiden the top artist by revenue",
    "does U2 have the highest revenue",
    "what rank is Metallica by revenue",
    "is he the highest revenue artist",
    "is she the top earning artist",
    "is that artist number one by sales",
    "artist revenue rank for Led Zeppelin",
    "is he the highest",
    "his revenue rank",
    "is that artist top earner",
    "does iron maiden rank first",
    "is this singer highest sales",
    "artist top revenue check",
    "what is his revenue rank",
]


def read_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON array")
    return payload


def write_json(path: Path, payload: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")


def merge_one(existing: list[dict], entry: dict) -> list[dict]:
    merged = [item for item in existing if item.get("query_id") != entry["query_id"]]
    merged.append(entry)
    return sorted(merged, key=lambda item: int(item["query_id"][1:]))


def description_entry() -> dict:
    return {
        "query_id": Q052["query_id"],
        "category": Q052["category"],
        "intent": Q052["intent"],
        "selected_candidate_id": "q052_manual",
        "selected_strategy": "manual_comparative_follow_up",
        "source": "manual_domain_guard_query_pack",
        "description": Q052["description"],
        "original_description": Q052["description"],
        "sql": Q052["sql"],
        "expected_columns": Q052["expected_columns"],
        "tables_used": Q052["tables_used"],
    }


def variation_entry() -> dict:
    return {
        "query_id": Q052["query_id"],
        "category": Q052["category"],
        "intent": Q052["intent"],
        "description": Q052["description"],
        "user_queries": Q052_VARIATIONS,
    }


def sql_file_text() -> str:
    return (
        f"-- {Q052['query_id']}: {Q052['intent']}\n"
        f"-- Category: {Q052['category']}\n"
        f"-- Description: {Q052['description']}\n"
        "-- Parameter: artist_name (artist_name) - Artist name available in the database.\n\n"
        f"{Q052['sql'].strip().rstrip(';')};\n"
    )


def main() -> None:
    if len(Q052_VARIATIONS) != 17:
        raise ValueError("q052 must have 17 user-query variations")

    repository = merge_one(read_json(DATA_DIR / "query_repository.json"), Q052)
    descriptions = merge_one(read_json(DATA_DIR / "optimized_descriptions.json"), description_entry())
    variations = merge_one(read_json(DATA_DIR / "user_query_variations.json"), variation_entry())

    write_json(DATA_DIR / "query_repository.json", repository)
    write_json(DATA_DIR / "optimized_descriptions.json", descriptions)
    write_json(DATA_DIR / "user_query_variations.json", variations)

    QUERIES_DIR.mkdir(parents=True, exist_ok=True)
    (QUERIES_DIR / "q052.sql").write_text(sql_file_text(), encoding="utf-8")

    print("Synced domain guard query pack")
    print(f"Repository entries: {len(repository)}")
    print(f"Optimized descriptions: {len(descriptions)}")
    print(f"User-query variation entries: {len(variations)}")
    print("SQL files written: 1")


if __name__ == "__main__":
    main()
