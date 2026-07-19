from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
QUERIES_DIR = PROJECT_ROOT / "queries"


ADDITIONAL_QUERIES = [
    {
        "query_id": "q026",
        "category": "sales",
        "intent": "latest available month revenue",
        "description": "Returns revenue for the latest invoice month available in the database, useful for last month or most recent month sales questions.",
        "sample_questions": [
            "What were sales in the latest available month?",
            "Show me last month sales.",
            "How much revenue was made in the most recent month?",
        ],
        "sql": """
WITH latest_month AS (
  SELECT strftime('%Y-%m', MAX(InvoiceDate)) AS month
  FROM Invoice
)
SELECT lm.month, ROUND(SUM(i.Total), 2) AS total_revenue
FROM Invoice i
JOIN latest_month lm
  ON strftime('%Y-%m', i.InvoiceDate) = lm.month
GROUP BY lm.month
""".strip(),
        "expected_columns": ["month", "total_revenue"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q027",
        "category": "sales",
        "intent": "latest available year revenue",
        "description": "Returns total revenue for the latest invoice year available in the database.",
        "sample_questions": [
            "What were sales in the latest available year?",
            "Show revenue for the most recent year.",
            "How much did we make in the latest year?",
        ],
        "sql": """
WITH latest_year AS (
  SELECT strftime('%Y', MAX(InvoiceDate)) AS year
  FROM Invoice
)
SELECT ly.year, ROUND(SUM(i.Total), 2) AS total_revenue
FROM Invoice i
JOIN latest_year ly
  ON strftime('%Y', i.InvoiceDate) = ly.year
GROUP BY ly.year
""".strip(),
        "expected_columns": ["year", "total_revenue"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q028",
        "category": "sales",
        "intent": "revenue for specific year",
        "description": "Returns total revenue for one requested invoice year.",
        "sample_questions": [
            "What was revenue in 2025?",
            "Show sales for 2024.",
            "How much did we make in a specific year?",
        ],
        "sql": """
SELECT :year AS year, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
WHERE strftime('%Y', InvoiceDate) = :year
""".strip(),
        "expected_columns": ["year", "total_revenue"],
        "tables_used": ["Invoice"],
        "parameters": [
            {
                "name": "year",
                "type": "year",
                "required": True,
                "description": "Four-digit invoice year available in the database.",
            }
        ],
    },
    {
        "query_id": "q029",
        "category": "sales",
        "intent": "revenue for specific month",
        "description": "Returns total revenue for one requested invoice month.",
        "sample_questions": [
            "What was revenue in 2025-12?",
            "Show sales for December 2025.",
            "How much did we make in a specific month?",
        ],
        "sql": """
SELECT :month AS month, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
WHERE strftime('%Y-%m', InvoiceDate) = :month
""".strip(),
        "expected_columns": ["month", "total_revenue"],
        "tables_used": ["Invoice"],
        "parameters": [
            {
                "name": "month",
                "type": "month",
                "required": True,
                "description": "Invoice month in YYYY-MM format available in the database.",
            }
        ],
    },
    {
        "query_id": "q030",
        "category": "sales",
        "intent": "highest revenue month",
        "description": "Finds the invoice month with the highest total revenue.",
        "sample_questions": [
            "Which month had the highest sales?",
            "Show me the best revenue month.",
            "What was the top month by revenue?",
        ],
        "sql": """
SELECT strftime('%Y-%m', InvoiceDate) AS month, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY strftime('%Y-%m', InvoiceDate)
ORDER BY total_revenue DESC, month ASC
LIMIT 1
""".strip(),
        "expected_columns": ["month", "total_revenue"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q031",
        "category": "sales",
        "intent": "lowest revenue month",
        "description": "Finds the invoice month with the lowest total revenue.",
        "sample_questions": [
            "Which month had the lowest sales?",
            "Show me the worst revenue month.",
            "What was the smallest month by revenue?",
        ],
        "sql": """
SELECT strftime('%Y-%m', InvoiceDate) AS month, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY strftime('%Y-%m', InvoiceDate)
ORDER BY total_revenue ASC, month ASC
LIMIT 1
""".strip(),
        "expected_columns": ["month", "total_revenue"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q032",
        "category": "sales",
        "intent": "total invoice count",
        "description": "Counts the total number of invoices in the database.",
        "sample_questions": [
            "How many invoices are there?",
            "What is the total invoice count?",
            "Count all orders.",
        ],
        "sql": "SELECT COUNT(*) AS invoice_count FROM Invoice",
        "expected_columns": ["invoice_count"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q033",
        "category": "sales",
        "intent": "highest value invoices",
        "description": "Lists the top invoices by total invoice amount.",
        "sample_questions": [
            "Show the highest value invoices.",
            "What are the biggest orders?",
            "List top invoices by total amount.",
        ],
        "sql": """
SELECT InvoiceId AS invoice_id,
       InvoiceDate AS invoice_date,
       BillingCountry AS billing_country,
       ROUND(Total, 2) AS invoice_total
FROM Invoice
ORDER BY Total DESC, InvoiceId ASC
LIMIT 10
""".strip(),
        "expected_columns": ["invoice_id", "invoice_date", "billing_country", "invoice_total"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q034",
        "category": "sales",
        "intent": "average invoice value by billing country",
        "description": "Calculates the average invoice amount for each billing country.",
        "sample_questions": [
            "What is average order value by country?",
            "Show average invoice value per billing country.",
            "Which countries have the highest average invoice value?",
        ],
        "sql": """
SELECT BillingCountry AS billing_country, ROUND(AVG(Total), 2) AS average_invoice_value
FROM Invoice
GROUP BY BillingCountry
ORDER BY average_invoice_value DESC, billing_country ASC
LIMIT 10
""".strip(),
        "expected_columns": ["billing_country", "average_invoice_value"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q035",
        "category": "sales",
        "intent": "revenue by billing city",
        "description": "Ranks billing cities by total invoice revenue.",
        "sample_questions": [
            "Show revenue by billing city.",
            "Which cities generated the most sales?",
            "Break down sales by city.",
        ],
        "sql": """
SELECT BillingCity AS billing_city,
       BillingCountry AS billing_country,
       ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY BillingCity, BillingCountry
ORDER BY total_revenue DESC, billing_city ASC
LIMIT 10
""".strip(),
        "expected_columns": ["billing_city", "billing_country", "total_revenue"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q036",
        "category": "genres",
        "intent": "best-selling genres by revenue in specific billing country",
        "description": "Ranks music genres by track sales revenue for one requested billing country.",
        "sample_questions": [
            "Which genres made the most revenue in USA?",
            "Show genre sales in Brazil.",
            "Best-selling genres by revenue for a country.",
        ],
        "sql": """
SELECT g.Name AS genre_name, ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS total_revenue
FROM Invoice i
JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
JOIN Track t ON il.TrackId = t.TrackId
JOIN Genre g ON t.GenreId = g.GenreId
WHERE i.BillingCountry = :country
GROUP BY g.Name
ORDER BY total_revenue DESC, genre_name ASC
LIMIT 10
""".strip(),
        "expected_columns": ["genre_name", "total_revenue"],
        "tables_used": ["Invoice", "InvoiceLine", "Track", "Genre"],
        "parameters": [
            {
                "name": "country",
                "type": "country",
                "required": True,
                "description": "Billing country available in the database.",
            }
        ],
    },
    {
        "query_id": "q037",
        "category": "sales",
        "intent": "monthly revenue by billing country",
        "description": "Shows monthly invoice revenue split by billing country.",
        "sample_questions": [
            "Show monthly revenue by billing country.",
            "Break down sales by month and country.",
            "How does country revenue change each month?",
        ],
        "sql": """
SELECT strftime('%Y-%m', InvoiceDate) AS month,
       BillingCountry AS billing_country,
       ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY strftime('%Y-%m', InvoiceDate), BillingCountry
ORDER BY month ASC, billing_country ASC
""".strip(),
        "expected_columns": ["month", "billing_country", "total_revenue"],
        "tables_used": ["Invoice"],
    },
    {
        "query_id": "q038",
        "category": "customers",
        "intent": "total customer count",
        "description": "Counts the total number of customers in the database.",
        "sample_questions": [
            "How many customers do we have?",
            "What is the total customer count?",
            "Count all customers.",
        ],
        "sql": "SELECT COUNT(*) AS customer_count FROM Customer",
        "expected_columns": ["customer_count"],
        "tables_used": ["Customer"],
    },
    {
        "query_id": "q039",
        "category": "customers",
        "intent": "customer count by country",
        "description": "Counts customers in each country.",
        "sample_questions": [
            "How many customers are in each country?",
            "Show customer count by country.",
            "Which countries have the most customers?",
        ],
        "sql": """
SELECT Country AS country, COUNT(*) AS customer_count
FROM Customer
GROUP BY Country
ORDER BY customer_count DESC, country ASC
""".strip(),
        "expected_columns": ["country", "customer_count"],
        "tables_used": ["Customer"],
    },
    {
        "query_id": "q040",
        "category": "customers",
        "intent": "customers in specific country",
        "description": "Lists customers from one requested country.",
        "sample_questions": [
            "Show customers from Brazil.",
            "List customers in USA.",
            "Who are the customers in a specific country?",
        ],
        "sql": """
SELECT FirstName AS first_name,
       LastName AS last_name,
       Email AS email,
       City AS city,
       Country AS country
FROM Customer
WHERE Country = :country
ORDER BY LastName ASC, FirstName ASC
LIMIT 50
""".strip(),
        "expected_columns": ["first_name", "last_name", "email", "city", "country"],
        "tables_used": ["Customer"],
        "parameters": [
            {
                "name": "country",
                "type": "country",
                "required": True,
                "description": "Customer country available in the database.",
            }
        ],
    },
    {
        "query_id": "q041",
        "category": "customers",
        "intent": "top customers by spend in specific country",
        "description": "Ranks customers by total spending within one requested country.",
        "sample_questions": [
            "Who is the top customer in USA?",
            "Show best customers by spend in Brazil.",
            "Top spending customers for a specific country.",
        ],
        "sql": """
SELECT c.FirstName AS first_name,
       c.LastName AS last_name,
       c.Country AS country,
       ROUND(SUM(i.Total), 2) AS total_spend
FROM Customer c
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE c.Country = :country
GROUP BY c.CustomerId
ORDER BY total_spend DESC, c.LastName ASC, c.FirstName ASC
LIMIT 10
""".strip(),
        "expected_columns": ["first_name", "last_name", "country", "total_spend"],
        "tables_used": ["Customer", "Invoice"],
        "parameters": [
            {
                "name": "country",
                "type": "country",
                "required": True,
                "description": "Customer country available in the database.",
            }
        ],
    },
    {
        "query_id": "q042",
        "category": "customers",
        "intent": "customers with no purchases",
        "description": "Lists customers who do not have any invoices.",
        "sample_questions": [
            "Which customers never bought anything?",
            "Show customers with no purchases.",
            "List customers without invoices.",
        ],
        "sql": """
SELECT c.CustomerId AS customer_id,
       c.FirstName AS first_name,
       c.LastName AS last_name,
       c.Email AS email,
       c.Country AS country
FROM Customer c
LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE i.InvoiceId IS NULL
ORDER BY c.LastName ASC, c.FirstName ASC
LIMIT 50
""".strip(),
        "expected_columns": ["customer_id", "first_name", "last_name", "email", "country"],
        "tables_used": ["Customer", "Invoice"],
    },
    {
        "query_id": "q043",
        "category": "albums",
        "intent": "albums by revenue",
        "description": "Ranks albums by total track sales revenue.",
        "sample_questions": [
            "Which albums made the most revenue?",
            "Show top revenue albums.",
            "Album sales by revenue.",
        ],
        "sql": """
SELECT a.Title AS album_title,
       ar.Name AS artist_name,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS total_revenue
FROM Album a
JOIN Artist ar ON a.ArtistId = ar.ArtistId
JOIN Track t ON a.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY a.AlbumId
ORDER BY total_revenue DESC, album_title ASC
LIMIT 10
""".strip(),
        "expected_columns": ["album_title", "artist_name", "total_revenue"],
        "tables_used": ["Album", "Artist", "Track", "InvoiceLine"],
    },
    {
        "query_id": "q044",
        "category": "albums",
        "intent": "albums by quantity sold",
        "description": "Ranks albums by the number of tracks sold.",
        "sample_questions": [
            "What are the top selling albums?",
            "Which albums sold the most tracks?",
            "Show albums by quantity sold.",
        ],
        "sql": """
SELECT a.Title AS album_title,
       ar.Name AS artist_name,
       SUM(il.Quantity) AS total_quantity_sold
FROM Album a
JOIN Artist ar ON a.ArtistId = ar.ArtistId
JOIN Track t ON a.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY a.AlbumId
ORDER BY total_quantity_sold DESC, album_title ASC
LIMIT 10
""".strip(),
        "expected_columns": ["album_title", "artist_name", "total_quantity_sold"],
        "tables_used": ["Album", "Artist", "Track", "InvoiceLine"],
    },
    {
        "query_id": "q045",
        "category": "artists",
        "intent": "artists by quantity sold",
        "description": "Ranks artists by the number of tracks sold.",
        "sample_questions": [
            "Which artists sold the most tracks?",
            "Show top selling artists by quantity.",
            "Best-selling artists by units sold.",
        ],
        "sql": """
SELECT ar.Name AS artist_name,
       SUM(il.Quantity) AS total_quantity_sold
FROM Artist ar
JOIN Album a ON ar.ArtistId = a.ArtistId
JOIN Track t ON a.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY ar.ArtistId
ORDER BY total_quantity_sold DESC, artist_name ASC
LIMIT 10
""".strip(),
        "expected_columns": ["artist_name", "total_quantity_sold"],
        "tables_used": ["Artist", "Album", "Track", "InvoiceLine"],
    },
    {
        "query_id": "q046",
        "category": "products",
        "intent": "media types by revenue",
        "description": "Ranks media types by total track sales revenue.",
        "sample_questions": [
            "Which media types made the most revenue?",
            "Show sales by media type.",
            "Top selling media type by revenue.",
        ],
        "sql": """
SELECT mt.Name AS media_type_name,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS total_revenue
FROM MediaType mt
JOIN Track t ON mt.MediaTypeId = t.MediaTypeId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY mt.MediaTypeId
ORDER BY total_revenue DESC, media_type_name ASC
""".strip(),
        "expected_columns": ["media_type_name", "total_revenue"],
        "tables_used": ["MediaType", "Track", "InvoiceLine"],
    },
    {
        "query_id": "q047",
        "category": "products",
        "intent": "tracks never sold",
        "description": "Lists tracks that have never appeared on an invoice line.",
        "sample_questions": [
            "Which tracks never sold?",
            "Show tracks with no sales.",
            "List unsold tracks.",
        ],
        "sql": """
SELECT t.TrackId AS track_id,
       t.Name AS track_name,
       a.Title AS album_title,
       ar.Name AS artist_name
FROM Track t
LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
LEFT JOIN Album a ON t.AlbumId = a.AlbumId
LEFT JOIN Artist ar ON a.ArtistId = ar.ArtistId
WHERE il.InvoiceLineId IS NULL
ORDER BY t.Name ASC
LIMIT 50
""".strip(),
        "expected_columns": ["track_id", "track_name", "album_title", "artist_name"],
        "tables_used": ["Track", "InvoiceLine", "Album", "Artist"],
    },
    {
        "query_id": "q048",
        "category": "products",
        "intent": "tracks in specific genre ranked by quantity sold",
        "description": "Ranks tracks within one requested genre by quantity sold.",
        "sample_questions": [
            "Show top tracks in Rock.",
            "Which Jazz tracks sold the most?",
            "Best-selling tracks for a specific genre.",
        ],
        "sql": """
SELECT t.Name AS track_name,
       g.Name AS genre_name,
       COALESCE(SUM(il.Quantity), 0) AS total_quantity_sold
FROM Genre g
JOIN Track t ON g.GenreId = t.GenreId
LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
WHERE g.Name = :genre_name
GROUP BY t.TrackId
ORDER BY total_quantity_sold DESC, track_name ASC
LIMIT 10
""".strip(),
        "expected_columns": ["track_name", "genre_name", "total_quantity_sold"],
        "tables_used": ["Genre", "Track", "InvoiceLine"],
        "parameters": [
            {
                "name": "genre_name",
                "type": "genre_name",
                "required": True,
                "description": "Genre name available in the database.",
            }
        ],
    },
    {
        "query_id": "q049",
        "category": "employees",
        "intent": "support rep revenue for latest available month",
        "description": "Shows employee or support representative sales revenue for the latest invoice month available in the database.",
        "sample_questions": [
            "Show employee sales last month.",
            "Revenue by support rep for the latest month.",
            "Which support rep had the most recent monthly revenue?",
        ],
        "sql": """
WITH latest_month AS (
  SELECT strftime('%Y-%m', MAX(InvoiceDate)) AS month
  FROM Invoice
)
SELECT e.FirstName || ' ' || e.LastName AS support_rep_name,
       lm.month,
       ROUND(SUM(i.Total), 2) AS total_revenue
FROM Employee e
JOIN Customer c ON e.EmployeeId = c.SupportRepId
JOIN Invoice i ON c.CustomerId = i.CustomerId
JOIN latest_month lm ON strftime('%Y-%m', i.InvoiceDate) = lm.month
GROUP BY e.EmployeeId, lm.month
ORDER BY total_revenue DESC, support_rep_name ASC
""".strip(),
        "expected_columns": ["support_rep_name", "month", "total_revenue"],
        "tables_used": ["Employee", "Customer", "Invoice"],
    },
    {
        "query_id": "q050",
        "category": "employees",
        "intent": "support rep revenue for specific year",
        "description": "Shows support representative revenue for one requested invoice year.",
        "sample_questions": [
            "Show support rep revenue in 2025.",
            "Employee sales for 2024.",
            "Which support rep made the most revenue in a specific year?",
        ],
        "sql": """
SELECT e.FirstName || ' ' || e.LastName AS support_rep_name,
       :year AS year,
       ROUND(SUM(i.Total), 2) AS total_revenue
FROM Employee e
JOIN Customer c ON e.EmployeeId = c.SupportRepId
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE strftime('%Y', i.InvoiceDate) = :year
GROUP BY e.EmployeeId
ORDER BY total_revenue DESC, support_rep_name ASC
""".strip(),
        "expected_columns": ["support_rep_name", "year", "total_revenue"],
        "tables_used": ["Employee", "Customer", "Invoice"],
        "parameters": [
            {
                "name": "year",
                "type": "year",
                "required": True,
                "description": "Four-digit invoice year available in the database.",
            }
        ],
    },
]


USER_QUERY_VARIATIONS = {
    "q026": [
        "What were sales in the latest available month?",
        "Show me last month sales.",
        "How much revenue was made in the most recent month?",
        "latest month revenue",
        "last month sales",
        "sales for the newest month in the data",
        "revenue in the latest invoice month",
        "how much did we make last month",
        "most recent month sales total",
        "latest monthly revenue number",
        "last moth sales",
        "last months sale",
        "latest mnth revenue",
        "recent month sales pls",
        "sales in latest data month",
        "how much revenue last mont",
        "last month how much sold",
    ],
    "q027": [
        "What were sales in the latest available year?",
        "Show revenue for the most recent year.",
        "How much did we make in the latest year?",
        "latest year revenue",
        "last year sales in the data",
        "revenue for newest invoice year",
        "most recent year sales total",
        "latest annual revenue",
        "how much revenue in latest year",
        "sales for the latest data year",
        "last yer revenue",
        "latest year sales pls",
        "recent annual sales",
        "newest year money made",
        "what did we earn latest year",
        "last available year revenue",
        "latest yr sales",
    ],
    "q028": [
        "What was revenue in 2025?",
        "Show sales for 2024.",
        "How much did we make in a specific year?",
        "revenue for 2023",
        "sales in 2022",
        "total revenue for year 2021",
        "how much money in 2025",
        "annual sales for a given year",
        "show me revenue in 2024",
        "what did we earn in 2023",
        "sales 2025",
        "revnue in 2024",
        "money made year 2022",
        "for 2021 sales",
        "2025 revenue total",
        "how much sale in 2023",
        "year 2024 earning",
    ],
    "q029": [
        "What was revenue in 2025-12?",
        "Show sales for December 2025.",
        "How much did we make in a specific month?",
        "revenue for January 2024",
        "sales in 2023-06",
        "total revenue for March 2022",
        "show me monthly revenue for 2025-11",
        "how much money in April 2023",
        "sales for a given month",
        "revenue in Dec 2025",
        "sale 2025-12",
        "revnue for february 2022",
        "money made in jun 2023",
        "month 2024-08 sales",
        "how much in november 2025",
        "sales specific mnth",
        "jan 2021 revenue",
    ],
    "q030": [
        "Which month had the highest sales?",
        "Show me the best revenue month.",
        "What was the top month by revenue?",
        "highest revenue month",
        "month with maximum sales",
        "best sales month overall",
        "which month made most money",
        "top performing month",
        "peak monthly revenue",
        "biggest month for sales",
        "highest sale mnth",
        "best month money wise",
        "month that sold most",
        "max monthly revenue",
        "which mnth had high sales",
        "biggest revenue month pls",
        "top month sales",
    ],
    "q031": [
        "Which month had the lowest sales?",
        "Show me the worst revenue month.",
        "What was the smallest month by revenue?",
        "lowest revenue month",
        "month with minimum sales",
        "worst sales month overall",
        "which month made least money",
        "lowest performing month",
        "smallest monthly revenue",
        "weakest month for sales",
        "lowest sale mnth",
        "worst month money wise",
        "month that sold least",
        "min monthly revenue",
        "which mnth had low sales",
        "smallest revenue month pls",
        "bottom month sales",
    ],
    "q032": [
        "How many invoices are there?",
        "What is the total invoice count?",
        "Count all orders.",
        "total number of invoices",
        "how many sales transactions",
        "number of orders in the database",
        "invoice count overall",
        "count every invoice",
        "how many bills were issued",
        "total invoice records",
        "total invoices",
        "invoices count",
        "how many invoice",
        "order count pls",
        "num invoices",
        "overall bills count",
        "count orders",
    ],
    "q033": [
        "Show the highest value invoices.",
        "What are the biggest orders?",
        "List top invoices by total amount.",
        "largest invoices by value",
        "highest invoice totals",
        "top orders by amount",
        "which invoices are most expensive",
        "biggest bills",
        "rank invoices by total",
        "top invoice amounts",
        "big orders",
        "highest bills pls",
        "invoice with max amount",
        "top invoice value",
        "biggest order totals",
        "high value invoices",
        "show costly invoices",
    ],
    "q034": [
        "What is average order value by country?",
        "Show average invoice value per billing country.",
        "Which countries have the highest average invoice value?",
        "average invoice amount by country",
        "avg sales value for each country",
        "average order total per billing country",
        "country wise average invoice",
        "average purchase amount by country",
        "AOV by billing country",
        "avg invoice by location",
        "avg order country",
        "average bill value by country",
        "avrage invoice country wise",
        "country avg sales amount",
        "average order value location",
        "avg country invoice total",
        "which country has biggest avg order",
    ],
    "q035": [
        "Show revenue by billing city.",
        "Which cities generated the most sales?",
        "Break down sales by city.",
        "revenue by city",
        "sales totals per billing city",
        "top cities by revenue",
        "city wise sales",
        "which billing city made most money",
        "revenue split by city",
        "sales by customer city",
        "city sales",
        "billing city revenue pls",
        "sales per city",
        "top city money",
        "revnue by city",
        "city wise earnings",
        "show cities sales",
    ],
    "q036": [
        "Which genres made the most revenue in USA?",
        "Show genre sales in Brazil.",
        "Best-selling genres by revenue for a country.",
        "top genres by revenue in Canada",
        "sales by genre for Germany",
        "which genre made most money in France",
        "genre revenue for a billing country",
        "best music genres in United Kingdom by sales",
        "revenue by genre in India",
        "country specific genre sales",
        "genre sales USA",
        "top genres in us",
        "sales genre brazil",
        "which genre sold in canada",
        "country genre revenue pls",
        "best genres by money in germany",
        "usa genre revnue",
    ],
    "q037": [
        "Show monthly revenue by billing country.",
        "Break down sales by month and country.",
        "How does country revenue change each month?",
        "month wise revenue per country",
        "monthly sales split by billing country",
        "revenue by country for each month",
        "country monthly sales trend",
        "sales per month per location",
        "billing country revenue by month",
        "monthly country sales table",
        "monthly sales country",
        "month country revenue",
        "sales by mnth and country",
        "country wise monthly money",
        "monthly revnue by location",
        "each month country sales",
        "month over country revenue",
    ],
    "q038": [
        "How many customers do we have?",
        "What is the total customer count?",
        "Count all customers.",
        "number of customers",
        "total customers in database",
        "how many customer records",
        "customer count overall",
        "count the users",
        "total people buying",
        "how many clients",
        "customers count",
        "num customers",
        "total custmers",
        "count customers pls",
        "all customer number",
        "how many clients we have",
        "customer total",
    ],
    "q039": [
        "How many customers are in each country?",
        "Show customer count by country.",
        "Which countries have the most customers?",
        "customers per country",
        "country wise customer count",
        "number of customers by country",
        "customer distribution by country",
        "where are customers located",
        "rank countries by customer count",
        "clients by country",
        "customers country count",
        "custmers by country",
        "how many clients per country",
        "country customer numbers",
        "customer count location wise",
        "which country has more customers",
        "customer split by country",
    ],
    "q040": [
        "Show customers from Brazil.",
        "List customers in USA.",
        "Who are the customers in a specific country?",
        "customers from Canada",
        "show clients in Germany",
        "list customers for France",
        "which customers are in United Kingdom",
        "customers living in India",
        "customer list by country",
        "people from Australia",
        "customers brazil",
        "clients in usa",
        "show custmers from canada",
        "people in germany",
        "customer names france",
        "brazil customers list",
        "who is from india",
    ],
    "q041": [
        "Who is the top customer in USA?",
        "Show best customers by spend in Brazil.",
        "Top spending customers for a specific country.",
        "highest value customers in Canada",
        "best customers in Germany by money",
        "top customers by revenue in France",
        "biggest spenders in United Kingdom",
        "customer spend ranking for India",
        "top paying customers by country",
        "highest spend customer in Australia",
        "top customer usa",
        "best spender brazil",
        "highest custmer in canada",
        "who spent most in germany",
        "top clients france money",
        "usa best customers by spend",
        "country top spenders",
    ],
    "q042": [
        "Which customers never bought anything?",
        "Show customers with no purchases.",
        "List customers without invoices.",
        "customers who never purchased",
        "customers with zero orders",
        "which clients have no sales",
        "people who did not buy",
        "customer accounts with no invoices",
        "inactive customers with no purchases",
        "customers never billed",
        "customers no purchase",
        "never bought customers",
        "custmers with no order",
        "clients not buying",
        "zero invoice customers",
        "who never paid",
        "customers without sales",
    ],
    "q043": [
        "Which albums made the most revenue?",
        "Show top revenue albums.",
        "Album sales by revenue.",
        "albums by total sales revenue",
        "highest earning albums",
        "top albums by money made",
        "which albums generated most sales",
        "album revenue ranking",
        "best revenue albums",
        "albums with highest sales value",
        "album revenue",
        "top money albums",
        "albums revnue ranking",
        "which album made money most",
        "best album sales amount",
        "sales by album revenue",
        "top albums dollars",
    ],
    "q044": [
        "What are the top selling albums?",
        "Which albums sold the most tracks?",
        "Show albums by quantity sold.",
        "best-selling albums by units",
        "albums with most track sales",
        "top albums by copies sold",
        "which albums sold most",
        "album quantity ranking",
        "albums ranked by sold tracks",
        "most purchased albums",
        "top selling album",
        "albums sold most",
        "best albums by qty",
        "which album sold more",
        "album units sold",
        "top albums quantity",
        "albums sale count",
    ],
    "q045": [
        "Which artists sold the most tracks?",
        "Show top selling artists by quantity.",
        "Best-selling artists by units sold.",
        "artists by number of tracks sold",
        "top artists by quantity sold",
        "which artists sold most copies",
        "artist sales count ranking",
        "most purchased artists",
        "artists with highest units sold",
        "top artists by track sales volume",
        "best selling artists by quantity",
        "artist sold count",
        "top artist qty",
        "which artist sold more",
        "artists units sold",
        "artist sale count",
        "top selling artist",
    ],
    "q046": [
        "Which media types made the most revenue?",
        "Show sales by media type.",
        "Top selling media type by revenue.",
        "media type revenue",
        "revenue by format",
        "which file formats generated most sales",
        "sales revenue per media type",
        "top media types by money",
        "media type sales ranking",
        "revenue split by media type",
        "media sales",
        "media type revnue",
        "top format revenue",
        "sales per media",
        "which media made money",
        "format sales total",
        "media type money",
    ],
    "q047": [
        "Which tracks never sold?",
        "Show tracks with no sales.",
        "List unsold tracks.",
        "tracks that were never purchased",
        "songs with zero sales",
        "which tracks have no invoice lines",
        "tracks not sold at all",
        "music never bought",
        "items with no purchases",
        "unsold songs",
        "tracks never sold",
        "track no sales",
        "unsold traks",
        "songs not bought",
        "zero sale tracks",
        "which songs never sell",
        "tracks with no orders",
    ],
    "q048": [
        "Show top tracks in Rock.",
        "Which Jazz tracks sold the most?",
        "Best-selling tracks for a specific genre.",
        "top songs in Metal by quantity sold",
        "tracks in Pop ranked by sales count",
        "best tracks for Classical genre",
        "which Rock tracks sold most",
        "genre specific track sales",
        "top tracks within Blues",
        "most sold tracks in Latin",
        "top tracks rock",
        "jazz tracks sold most",
        "best songs in metal",
        "rock track sales",
        "tracks in genre qty",
        "top pop songs sold",
        "rock best selling tracks",
    ],
    "q049": [
        "Show employee sales last month.",
        "Revenue by support rep for the latest month.",
        "Which support rep had the most recent monthly revenue?",
        "support rep sales in latest month",
        "employee revenue for last month",
        "latest monthly sales by support representative",
        "last month revenue by employee",
        "support reps most recent month sales",
        "rep revenue in latest data month",
        "recent month sales by staff",
        "employee sales last moth",
        "support rep latest mnth revenue",
        "last month employee revnue",
        "rep sales latest month",
        "staff sales last month",
        "recent monthly rep money",
        "support revenue last mont",
    ],
    "q050": [
        "Show support rep revenue in 2025.",
        "Employee sales for 2024.",
        "Which support rep made the most revenue in a specific year?",
        "support rep sales by year 2023",
        "employee revenue in 2022",
        "rep revenue for 2021",
        "sales by support representative in 2025",
        "staff revenue for a given year",
        "which employee sold most in 2024",
        "support rep yearly revenue",
        "employee sales 2025",
        "rep revnue 2024",
        "support sales year 2023",
        "staff money in 2022",
        "which rep made most 2025",
        "employee yearly sales",
        "support revenue specific year",
    ],
}


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


def sql_comment(entry: dict) -> str:
    parameter_lines = []
    for parameter in entry.get("parameters", []):
        parameter_lines.append(
            f"-- Parameter: {parameter['name']} ({parameter['type']}) - {parameter['description']}"
        )
    parameters = "\n".join(parameter_lines)
    if parameters:
        parameters = f"\n{parameters}"
    return (
        f"-- {entry['query_id']}: {entry['intent']}\n"
        f"-- Category: {entry['category']}\n"
        f"-- Description: {entry['description']}{parameters}\n\n"
        f"{entry['sql'].strip().rstrip(';')};\n"
    )


def description_entry(entry: dict) -> dict:
    return {
        "query_id": entry["query_id"],
        "category": entry["category"],
        "intent": entry["intent"],
        "selected_candidate_id": f"{entry['query_id']}_manual",
        "selected_strategy": "manual_broad_coverage",
        "source": "manual_broad_pack",
        "description": entry["description"],
        "original_description": entry["description"],
        "sql": entry["sql"],
        "expected_columns": entry["expected_columns"],
        "tables_used": entry["tables_used"],
    }


def variation_entry(entry: dict) -> dict:
    queries = USER_QUERY_VARIATIONS[entry["query_id"]]
    if len(queries) != 17:
        raise ValueError(f"{entry['query_id']} must have 17 user-query variations")
    return {
        "query_id": entry["query_id"],
        "category": entry["category"],
        "intent": entry["intent"],
        "description": entry["description"],
        "user_queries": queries,
    }


def merge_by_query_id(existing: list[dict], additions: list[dict]) -> list[dict]:
    addition_ids = {entry["query_id"] for entry in additions}
    merged = [entry for entry in existing if entry.get("query_id") not in addition_ids]
    merged.extend(additions)
    return sorted(merged, key=lambda entry: int(entry["query_id"][1:]))


def main() -> None:
    expected_ids = {f"q{index:03d}" for index in range(26, 51)}
    actual_ids = {entry["query_id"] for entry in ADDITIONAL_QUERIES}
    if actual_ids != expected_ids:
        raise ValueError(f"Additional query IDs are incomplete: {sorted(expected_ids - actual_ids)}")

    repository = read_json(DATA_DIR / "query_repository.json")
    optimized_descriptions = read_json(DATA_DIR / "optimized_descriptions.json")
    variations = read_json(DATA_DIR / "user_query_variations.json")

    repository = merge_by_query_id(repository, ADDITIONAL_QUERIES)
    optimized_descriptions = merge_by_query_id(
        optimized_descriptions,
        [description_entry(entry) for entry in ADDITIONAL_QUERIES],
    )
    variations = merge_by_query_id(
        variations,
        [variation_entry(entry) for entry in ADDITIONAL_QUERIES],
    )

    write_json(DATA_DIR / "query_repository.json", repository)
    write_json(DATA_DIR / "optimized_descriptions.json", optimized_descriptions)
    write_json(DATA_DIR / "user_query_variations.json", variations)

    QUERIES_DIR.mkdir(parents=True, exist_ok=True)
    for entry in ADDITIONAL_QUERIES:
        (QUERIES_DIR / f"{entry['query_id']}.sql").write_text(sql_comment(entry), encoding="utf-8")

    print("Synced broad query pack")
    print(f"Repository entries: {len(repository)}")
    print(f"Optimized descriptions: {len(optimized_descriptions)}")
    print(f"User-query variation entries: {len(variations)}")
    print(f"SQL files written: {len(ADDITIONAL_QUERIES)}")


if __name__ == "__main__":
    main()
