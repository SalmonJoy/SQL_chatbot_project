-- q039: customer count by country
-- Category: customers
-- Description: Counts customers in each country.

SELECT Country AS country, COUNT(*) AS customer_count
FROM Customer
GROUP BY Country
ORDER BY customer_count DESC, country ASC;
