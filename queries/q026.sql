-- q026: latest available month revenue
-- Category: sales
-- Description: Returns revenue for the latest invoice month available in the database, useful for last month or most recent month sales questions.

WITH latest_month AS (
  SELECT strftime('%Y-%m', MAX(InvoiceDate)) AS month
  FROM Invoice
)
SELECT lm.month, ROUND(SUM(i.Total), 2) AS total_revenue
FROM Invoice i
JOIN latest_month lm
  ON strftime('%Y-%m', i.InvoiceDate) = lm.month
GROUP BY lm.month;
