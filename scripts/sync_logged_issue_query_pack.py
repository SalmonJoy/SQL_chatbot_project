from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
QUERIES_DIR = PROJECT_ROOT / "queries"


NEW_QUERIES: list[dict[str, Any]] = [
    {
        "query_id": "q053",
        "category": "artists",
        "intent": "list all artists",
        "description": "Lists every artist in the Chinook database alphabetically.",
        "sample_questions": [
            "List all artists.",
            "Tell me all the artists.",
            "Show every artist in the database.",
        ],
        "sql": """SELECT ArtistId AS artist_id,
       Name AS artist_name
FROM Artist
ORDER BY artist_name ASC""",
        "expected_columns": ["artist_id", "artist_name"],
        "tables_used": ["Artist"],
    },
    {
        "query_id": "q054",
        "category": "albums",
        "intent": "list all albums with artists",
        "description": "Lists every album with its artist in the Chinook database.",
        "sample_questions": [
            "List all albums.",
            "Show albums with their artists.",
            "What artist has which albums?",
        ],
        "sql": """SELECT a.AlbumId AS album_id,
       a.Title AS album_title,
       ar.Name AS artist_name
FROM Album a
JOIN Artist ar ON a.ArtistId = ar.ArtistId
ORDER BY artist_name ASC, album_title ASC""",
        "expected_columns": ["album_id", "album_title", "artist_name"],
        "tables_used": ["Album", "Artist"],
    },
    {
        "query_id": "q055",
        "category": "sales",
        "intent": "highest revenue day",
        "description": "Returns invoice dates ranked by daily revenue, with the highest sales day first.",
        "sample_questions": [
            "Which day had the most sales?",
            "What date made the most money?",
            "Show the highest revenue day.",
        ],
        "sql": """SELECT DATE(InvoiceDate) AS revenue_day,
       ROUND(SUM(Total), 2) AS total_revenue,
       COUNT(*) AS invoice_count
FROM Invoice
GROUP BY DATE(InvoiceDate)
ORDER BY total_revenue DESC, revenue_day ASC
LIMIT 10""",
        "expected_columns": ["revenue_day", "total_revenue", "invoice_count"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q056",
        "category": "products",
        "intent": "most common file types by track count",
        "description": "Ranks media or file types by the number of tracks and marks the most common type.",
        "sample_questions": [
            "What file types do we have?",
            "Which media type is most common?",
            "Show track formats ranked by count.",
        ],
        "sql": """WITH media_type_counts AS (
  SELECT mt.MediaTypeId AS media_type_id,
         mt.Name AS file_type_name,
         COUNT(t.TrackId) AS track_count
  FROM MediaType mt
  LEFT JOIN Track t ON mt.MediaTypeId = t.MediaTypeId
  GROUP BY mt.MediaTypeId, mt.Name
),
ranked_media_types AS (
  SELECT media_type_id,
         file_type_name,
         track_count,
         RANK() OVER (ORDER BY track_count DESC, file_type_name ASC) AS track_count_rank
  FROM media_type_counts
)
SELECT file_type_name,
       track_count,
       track_count_rank,
       CASE WHEN track_count_rank = 1 THEN 1 ELSE 0 END AS is_most_common_file_type
FROM ranked_media_types
ORDER BY track_count_rank ASC, file_type_name ASC""",
        "expected_columns": [
            "file_type_name",
            "track_count",
            "track_count_rank",
            "is_most_common_file_type",
        ],
        "tables_used": ["MediaType", "Track"],
    },
]


NEW_VARIATIONS: dict[str, list[str]] = {
    "q053": [
        "List all artists.",
        "Tell me all the artists.",
        "Show every artist in the database.",
        "all artists",
        "artist list",
        "give me artist names",
        "show complete artist catalogue",
        "which artists are available",
        "names of all artists",
        "every artist we have",
        "all artist pls",
        "artists list",
        "artist names only",
        "show me artists",
        "who are the artists",
        "all singers and bands",
        "full artist list",
    ],
    "q054": [
        "List all albums.",
        "Show albums with their artists.",
        "What artist has which albums?",
        "all albums",
        "album list",
        "show every album",
        "albums and artist names",
        "which albums belong to which artists",
        "full album catalogue",
        "give me album titles with artists",
        "all albms",
        "albums by artist",
        "what albums do artists have",
        "artist album mapping",
        "show album names and artists",
        "list the albums we have",
        "which artist has what albums",
    ],
    "q055": [
        "Which day had the most sales?",
        "What date made the most money?",
        "Show the highest revenue day.",
        "which day sale was most",
        "top sales day",
        "highest earning date",
        "day with maximum revenue",
        "when was daily sales highest",
        "what was the best sales date",
        "show daily revenue top day",
        "which day made most money",
        "best revenue day",
        "top invoice date by sales",
        "day sales peaked",
        "highest sales date",
        "most money by day",
        "sales best day",
    ],
    "q056": [
        "What file types do we have?",
        "Which media type is most common?",
        "Show track formats ranked by count.",
        "what all file types we have",
        "most common file type",
        "which format has most tracks",
        "show audio file types by count",
        "media formats count",
        "file type list and counts",
        "common media type",
        "file types we have",
        "formats by track count",
        "which file format is used most",
        "media type popularity",
        "track file format counts",
        "what format are tracks in",
        "most used media format",
    ],
}


EXTRA_VARIATIONS: dict[str, list[str]] = {
    "q004": [
        "sales trend",
        "revenue trend",
        "how are sales doing",
        "how is my sales doing",
        "are sales going up or down",
        "monthly sales trend",
        "show sales over time by month",
    ],
    "q016": [
        "file types by track count",
        "media formats by count",
        "how many tracks per file type",
        "track count by file format",
        "audio formats count",
    ],
    "q030": [
        "when did I make most money",
        "when was revenue highest",
        "which month made most money",
        "highest earning month",
        "when did sales peak",
    ],
    "q042": [
        "who has not bought anything",
        "customers with no orders",
        "customers who never purchased",
        "who bought nothing",
        "customers without invoices",
    ],
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")


def merge_entries(existing: list[dict[str, Any]], new_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {entry["query_id"]: entry for entry in existing}
    for entry in new_entries:
        by_id[entry["query_id"]] = entry
    return sorted(by_id.values(), key=lambda entry: entry["query_id"])


def optimized_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_id": entry["query_id"],
        "category": entry["category"],
        "intent": entry["intent"],
        "selected_candidate_id": f"{entry['query_id']}_manual",
        "selected_strategy": "manual_logged_issue_coverage",
        "source": "manual_logged_issue_query_pack",
        "description": entry["description"],
        "original_description": entry["description"],
        "sql": entry["sql"],
        "expected_columns": entry["expected_columns"],
        "tables_used": entry["tables_used"],
    }


def variation_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_id": entry["query_id"],
        "category": entry["category"],
        "intent": entry["intent"],
        "description": entry["description"],
        "user_queries": NEW_VARIATIONS[entry["query_id"]],
    }


def extend_variations(variations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for entry in variations:
        extras = EXTRA_VARIATIONS.get(entry["query_id"], [])
        if not extras:
            continue
        existing = entry.setdefault("user_queries", [])
        seen = {question.strip().lower() for question in existing}
        for question in extras:
            if question.strip().lower() not in seen:
                existing.append(question)
                seen.add(question.strip().lower())
    return variations


def write_sql_file(entry: dict[str, Any]) -> None:
    sql_path = QUERIES_DIR / f"{entry['query_id']}.sql"
    sql_path.write_text(
        "\n".join(
            [
                f"-- Query ID: {entry['query_id']}",
                f"-- Intent: {entry['intent']}",
                f"-- Description: {entry['description']}",
                "",
                entry["sql"],
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    repository = read_json(DATA_DIR / "query_repository.json")
    optimized = read_json(DATA_DIR / "optimized_descriptions.json")
    variations = read_json(DATA_DIR / "user_query_variations.json")

    repository = merge_entries(repository, NEW_QUERIES)
    optimized = merge_entries(optimized, [optimized_entry(entry) for entry in NEW_QUERIES])
    variations = merge_entries(extend_variations(variations), [variation_entry(entry) for entry in NEW_QUERIES])

    write_json(DATA_DIR / "query_repository.json", repository)
    write_json(DATA_DIR / "optimized_descriptions.json", optimized)
    write_json(DATA_DIR / "user_query_variations.json", variations)

    for entry in NEW_QUERIES:
        write_sql_file(entry)

    print("Synced logged issue query pack")
    print(f"Repository entries: {len(repository)}")
    print(f"Optimized descriptions: {len(optimized)}")
    print(f"User query variation entries: {len(variations)}")


if __name__ == "__main__":
    main()
