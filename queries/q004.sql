-- q004: monthly revenue
-- Category: sales
-- Description: Calculates the total revenue generated for each month by summing the invoice totals.

SELECT strftime('%Y-%m', InvoiceDate) AS month, SUM(Total) AS total_revenue FROM Invoice GROUP BY strftime('%Y-%m', InvoiceDate) ORDER BY month;
