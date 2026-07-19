-- q027: latest available year revenue
-- Category: sales
-- Description: Returns total revenue for the latest invoice year available in the database.

WITH latest_year AS (
  SELECT strftime('%Y', MAX(InvoiceDate)) AS year
  FROM Invoice
)
SELECT ly.year, ROUND(SUM(i.Total), 2) AS total_revenue
FROM Invoice i
JOIN latest_year ly
  ON strftime('%Y', i.InvoiceDate) = ly.year
GROUP BY ly.year;
