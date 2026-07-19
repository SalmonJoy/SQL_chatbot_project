-- q030: highest revenue month
-- Category: sales
-- Description: Finds the invoice month with the highest total revenue.

SELECT strftime('%Y-%m', InvoiceDate) AS month, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY strftime('%Y-%m', InvoiceDate)
ORDER BY total_revenue DESC, month ASC
LIMIT 1;
