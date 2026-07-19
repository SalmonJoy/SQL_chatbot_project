-- q003: yearly revenue
-- Category: sales
-- Description: Calculates the total revenue generated from invoices for each year.

SELECT strftime('%Y', Invoice.InvoiceDate) AS year, SUM(Invoice.Total) AS total_revenue FROM Invoice GROUP BY strftime('%Y', Invoice.InvoiceDate) ORDER BY year;
