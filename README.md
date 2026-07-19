# Natural Language to SQL Insight Chatbot

Streamlit chatbot for the Agentic AI case study. The app lets business users ask questions in plain English, retrieves the closest vetted SQL query, executes it on Chinook SQLite, and uses Gemini to rewrite follow-ups and generate grounded natural-language answers.

## Why this design

This project uses the strongest retrieval setup from the experiments done before submission:

| Retrieval setup | 100-query holdout strict accuracy |
| --- | ---: |
| MiniLM dense-only | 0.73 |
| MiniLM + BM25 normalized score fusion | 0.89 |
| MiniLM + BM25 RRF | 0.79 |

Final runtime choice:

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Descriptions: MiniLM-tuned optimized descriptions
- Retrieval: dense MiniLM similarity + BM25-style lexical score
- Fusion: `0.70 * dense_score + 0.30 * lexical_score`
- SQL: fixed vetted repository, no free-form SQL generation
- Specific filters: safe vetted SQL templates with validated parameters for year, month, country, genre, and artist
- LLM: Gemini for follow-up rewriting and final answer wording only
- Domain guard: calculator/math, non-Chinook, and mixed in-domain/out-of-domain questions are blocked before retrieval/SQL
- Runtime control: no LLM-generated SQL and no separate query-generation service

## Project structure

```text
chatbot_project/
  app.py
  requirements.txt
  queries/                     # one vetted SQL file per query_id
  data/
    Chinook_Sqlite.sqlite
    Chinook_Sqlite.md
    query_repository.json
    optimized_descriptions.json
    user_query_variations.json
    index/
      description_embeddings.npy
      description_embedding_metadata.json
  scripts/
    build_index.py
    smoke_test.py
  src/
    retrieval.py
    sql_executor.py
    answer_generator.py
    domain_guard.py
    ambiguity_guard.py
    context_rewriter.py
    conversation_context.py
```

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Optional Gemini setup:

```bash
cp .env.example .env
# edit .env and set GEMINI_API_KEY
```

If `GEMINI_API_KEY` is not set, the app still works with deterministic retrieval and fallback answers. Follow-up rewriting is skipped.

## Build or refresh the MiniLM index

The repository includes a prebuilt MiniLM description index. To regenerate it:

```bash
python scripts/build_index.py
```

This embeds the 56 optimized query descriptions and writes:

- `data/index/description_embeddings.npy`
- `data/index/description_embedding_metadata.json`

## Run validation

```bash
python scripts/smoke_test.py
```

The smoke test checks:

- 56 SQL queries are present.
- Every repository SQL query is read-only and executable.
- MiniLM embeddings match the 56 query descriptions.
- Sample user questions retrieve the expected query IDs.
- Parameterized templates resolve only validated years, months, countries, genres, and artists from the SQLite data.
- Out-of-domain math and mixed in-domain/out-of-domain questions are blocked before retrieval or SQL.
- Artist comparative follow-ups can route to the vetted artist revenue-rank query.
- Context rewrite safety cases pass without requiring live Gemini access.
- Hybrid weights are fixed at dense `0.70`, lexical `0.30`.

## Run the chatbot

```bash
streamlit run app.py
```

Try:

- `What is the total revenue?`
- `best customers by spending`
- `sales by country`
- `which genres made most money`
- `playlist with most tracks`
- `revenue by support rep`
- `last month sales`
- `last moths sales`
- `sales in 2025`
- `customers from Brazil`
- `top tracks in Rock`
- `employee sales last month`
- `person whose tracks are sold most`
- Then ask: `how much is his revenue`
- Then ask: `is he the highest?`
- `what is 3x4?` should be blocked as out-of-domain.
- `which artist has most sales and explain gravity` should be blocked as a mixed-domain prompt.

## Runtime workflow

1. User asks a question.
2. If the question looks like a follow-up and prior context exists, Gemini may rewrite it into a standalone natural-language question.
3. The domain guard blocks obvious math/calculator, non-Chinook, or mixed-domain questions before retrieval.
4. The app embeds the effective question with MiniLM.
5. The app computes semantic similarity against optimized description embeddings.
6. The app computes BM25-style lexical scores using optimized descriptions, query intents, expected columns, table names, SQL tokens, and user-query variations.
7. The app combines scores using fixed `0.70/0.30` normalized score fusion.
8. Parameterized templates are penalized unless the user question includes the required value type.
9. If the selected query needs a parameter, the app resolves it locally against known SQLite values.
10. If the match is confident and all required parameters are valid, the selected vetted SQL query is executed against SQLite.
11. Gemini receives only the user question, selected intent, executed SQL, SQL parameters, and SQL result rows to produce a grounded answer.
12. The app stores compact context from the successful turn for one-turn follow-up rewriting.

## Safety controls

- The app never asks Gemini to generate SQL.
- Gemini follow-up rewriting outputs only a standalone natural-language question.
- Only repository SQL can be executed.
- Obvious out-of-domain questions, including calculator/math prompts like `what is 3x4?`, are blocked before retrieval and do not show repository buttons.
- Mixed prompts that combine a Chinook request with unrelated content are blocked completely; the app asks for one Chinook-only database question.
- Multi-intent prompts that ask for multiple database answers at once are blocked from auto-execution and shown as clickable repository options.
- Parameterized questions use SQLite named parameters; raw user text is never interpolated into SQL.
- Country, genre, artist, year, and month parameters must match values available in the Chinook database.
- SQL is validated as read-only `SELECT`/`WITH`.
- Multiple SQL statements and unsafe keywords are blocked.
- If retrieval confidence is low or ambiguous, the app asks for clarification and shows the top candidate intents.
- Ambiguous matches are clickable: the user can run a specific repository query from the top candidates.
- Vague or pronoun-based questions such as `who sold most?`, `tell me the person`, or `how much is his revenue` are blocked from auto-execution and shown as clickable repository options.
- If a parameterized query is selected but a valid parameter cannot be resolved, the app asks for clarification instead of executing SQL.

## Runtime logs

Every chatbot request is written as one JSON object per line:

```text
logs/chatbot_events.jsonl
```

Each event includes the user question, context rewrite result, effective question, domain-guard result, multi-intent guard result, retrieval scores, routing adjustments, parameter penalties, selected SQL, resolved parameters, execution decision, SQL result columns, row count, all returned rows, answer source, final answer text, and any safe error details. Logs never include `GEMINI_API_KEY`; they only record whether a key was present.

Logging is controlled by:

```text
LOG_DIR=logs
LOG_FILE=chatbot_events.jsonl
LOG_SQL_RESULT_ROWS=all
MAX_RESULT_ROWS_FOR_LLM=200
ENABLE_CONTEXT_REWRITE=true
MAX_CONTEXT_RESULT_ROWS=20
```

The `logs/` directory is excluded from Git.

## Dataset

The project uses the open-source Chinook digital music store SQLite database. It has 11 tables and over 15k rows across artists, albums, tracks, invoices, customers, employees, playlists, and invoice lines.

## Notes for evaluators

The PDF asks for at least 10 SQL queries and clear descriptions. This project includes 56 vetted SQL queries covering revenue, customers, products, artists, genres, support reps, playlists, latest-period sales, country/year/month/artist filters, direct artist revenue, artist revenue rank, unsold tracks, no-purchase customers, full artist/album listings, highest-revenue days, and common file/media types.
