-- q010: customers with highest lifetime value by country
-- Category: customers
-- Description: Returns the top 10 countries ranked by the total lifetime revenue generated from their customers.

SELECT i.BillingCountry AS country, SUM(i.Total) AS total_lifetime_value FROM Invoice i GROUP BY i.BillingCountry ORDER BY total_lifetime_value DESC LIMIT 10;
