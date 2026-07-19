-- q002: revenue by billing country
-- Category: sales
-- Description: Returns the total revenue generated per billing country, sorted from highest to lowest revenue.

SELECT BillingCountry AS billing_country, SUM(Total) AS total_revenue FROM Invoice GROUP BY BillingCountry ORDER BY total_revenue DESC LIMIT 10;
