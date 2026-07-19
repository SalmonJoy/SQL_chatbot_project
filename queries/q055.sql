-- Query ID: q055
-- Intent: highest revenue day
-- Description: Returns invoice dates ranked by daily revenue, with the highest sales day first.

SELECT DATE(InvoiceDate) AS revenue_day,
       ROUND(SUM(Total), 2) AS total_revenue,
       COUNT(*) AS invoice_count
FROM Invoice
GROUP BY DATE(InvoiceDate)
ORDER BY total_revenue DESC, revenue_day ASC
LIMIT 10
