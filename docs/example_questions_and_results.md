# Example Questions and Results

This page shows representative questions the chatbot can handle on the Chinook SQLite database. The app always retrieves from a vetted SQL repository; Gemini may help rewrite follow-ups, review uncertain top-k matches in Thinking mode, or phrase the final answer, but it never generates SQL.

## Happy-path analytics

| User question | App behavior | Selected repository query | Representative result | Why it matters |
| --- | --- | --- | --- | --- |
| `What is the total revenue?` | Executes the total revenue query. | `q001` - total revenue | `total_revenue = 2328.60` | Direct business KPI. |
| `Show sales by country` | Returns countries ranked by invoice revenue. | `q002` - revenue by billing country | Top rows: USA `523.06`, Canada `303.96`, France `195.10` | Common geographic revenue breakdown. |
| `Who are the top customers by spending?` | Returns customers ranked by lifetime spend. | `q007` - top customers by spend | Top rows: Helena Holý `49.62`, Richard Cunningham `47.62`, Luis Rojas `46.62` | Customer value ranking. |
| `Which genres made the most money?` | Returns genres ranked by revenue. | `q017` - best-selling genres by revenue | Top rows: Rock `826.65`, Latin `382.14`, Metal `261.36` | Product/category revenue insight. |
| `playlist with most tracks` | Returns playlists by track count. | `q024` - largest playlists by track count | Top row: Music `3290` tracks | Works with short phrase-style questions. |

## Parameterized questions

| User question | Resolved parameters | Selected repository query | Representative result | Why it matters |
| --- | --- | --- | --- | --- |
| `sales in 2025` | `year = 2025` | `q028` - revenue for specific year | `total_revenue = 450.58` | Year extraction and validation. |
| `revenue 2025-12` | `month = 2025-12` | `q029` - revenue for specific month | `total_revenue = 38.62` | Month extraction from compact date text. |
| `customers from Brazil` | `country = Brazil` | `q040` - customers in specific country | Roberto Almeida, Luís Gonçalves, Eduardo Martins, Fernanda Ramos, Alexandre Rocha | Country-specific listing. |
| `top tracks in Rock` | `genre_name = Rock` | `q048` - tracks in specific genre ranked by quantity sold | Top rows include All Along The Watchtower, Balls to the Wall, Binky The Doormat | Genre parameter routing. |
| `What is the revenue for Iron Maiden?` | `artist_name = Iron Maiden` | `q051` - revenue for specific artist | `total_revenue = 138.60` | Artist entity validation. |

## Natural phrasing and typo handling

| User question | App behavior | Selected repository query | Representative result | Why it matters |
| --- | --- | --- | --- | --- |
| `last moths sales` | Normalizes the typo and treats "last month" as the latest available data month. | `q026` - latest available month revenue | Month `2025-12`, revenue `38.62` | Realistic typo handling. |
| `whern did I make most money?` | Normalizes the typo and routes to highest revenue month. | `q030` - highest revenue month | Month `2022-01`, revenue `52.62` | Spoken/lazy phrasing still maps correctly. |
| `How is my sales doing? going up or down?` | Routes to monthly revenue trend. | `q004` - monthly revenue | First rows: 2021-01 `35.64`, 2021-02 `37.62`, 2021-03 `37.62` | Trend-style intent. |

## Special-case safety behavior

| User question | App behavior | SQL executed? | Representative response | Why it matters |
| --- | --- | ---: | --- | --- |
| `what is 3x4?` | Blocks as out-of-domain math. | No | Asks for a Chinook database question. | Prevents the app from acting as a general chatbot. |
| `which artist has most sales and explain gravity` | Blocks as mixed in-domain/out-of-domain. | No | Asks for one Chinook-only database question. | Avoids answering unrelated prompt injections or mixed tasks. |
| `who sold most?` | Blocks auto-execution and shows clickable repository choices. | No, unless user clicks an option | Options include artist quantity, track quantity, and album quantity queries. | Avoids guessing the entity type. |
| `top customer plus top artist` | Blocks as multiple database intents. | No | Asks the user to choose one query at a time. | Avoids executing a partial answer. |
| `how much is his revenue` without prior context | Blocks as unresolved pronoun. | No | Asks who "his" refers to or shows relevant options. | Avoids unsafe context-free guessing. |

## Conversational follow-up example

| Turn | User question | App behavior | Selected repository query | Representative result |
| --- | --- | --- | --- | --- |
| 1 | `person whose tracks are sold most` | Finds the artist with the most sold tracks. | `q045` - artists by quantity sold | Iron Maiden, `140` tracks sold |
| 2 | `how much is his revenue` | With prior context, Gemini may rewrite this as an Iron Maiden revenue question. | `q051` - revenue for specific artist | Iron Maiden revenue `138.60` |
| 3 | `is he the highest?` | With prior context, Gemini may rewrite this as an Iron Maiden revenue-rank question. | `q052` - revenue rank for specific artist | Revenue rank `1`; `is_highest_revenue_artist = 1` |

The follow-up rewrite step only produces a standalone natural-language question. The final SQL still comes from the vetted repository and uses validated parameters.

