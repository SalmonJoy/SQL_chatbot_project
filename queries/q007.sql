-- q007: top customers by spend
-- Category: customers
-- Description: Returns the top 10 customers ranked by their total spending across all invoices.

SELECT c.FirstName AS first_name, c.LastName AS last_name, SUM(i.Total) AS total_spend FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.CustomerId ORDER BY total_spend DESC LIMIT 10;
