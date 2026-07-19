-- q031: lowest revenue month
-- Category: sales
-- Description: Finds the invoice month with the lowest total revenue.

SELECT strftime('%Y-%m', InvoiceDate) AS month, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY strftime('%Y-%m', InvoiceDate)
ORDER BY total_revenue ASC, month ASC
LIMIT 1;
