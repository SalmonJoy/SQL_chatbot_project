-- q028: revenue for specific year
-- Category: sales
-- Description: Returns total revenue for one requested invoice year.
-- Parameter: year (year) - Four-digit invoice year available in the database.

SELECT :year AS year, ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
WHERE strftime('%Y', InvoiceDate) = :year;
