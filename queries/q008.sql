-- q008: customers by country
-- Category: customers
-- Description: Lists the first and last names of customers along with their country, sorted by country and limited to the first 10 results.

SELECT c.FirstName AS first_name, c.LastName AS last_name, c.Country AS country FROM Customer c ORDER BY c.Country LIMIT 10;
