-- q041: top customers by spend in specific country
-- Category: customers
-- Description: Ranks customers by total spending within one requested country.
-- Parameter: country (country) - Customer country available in the database.

SELECT c.FirstName AS first_name,
       c.LastName AS last_name,
       c.Country AS country,
       ROUND(SUM(i.Total), 2) AS total_spend
FROM Customer c
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE c.Country = :country
GROUP BY c.CustomerId
ORDER BY total_spend DESC, c.LastName ASC, c.FirstName ASC
LIMIT 10;
