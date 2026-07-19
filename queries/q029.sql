-- q029: revenue for specific month
-- Category: sales
-- Description: Returns total revenue for one requested invoice month.
-- Parameter: month (month) - Invoice month in YYYY-MM format available in the database.

SELECT :month AS month, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
WHERE strftime('%Y-%m', InvoiceDate) = :month;
