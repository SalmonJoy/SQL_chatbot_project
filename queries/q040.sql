-- q040: customers in specific country
-- Category: customers
-- Description: Lists customers from one requested country.
-- Parameter: country (country) - Customer country available in the database.

SELECT FirstName AS first_name,
       LastName AS last_name,
       Email AS email,
       City AS city,
       Country AS country
FROM Customer
WHERE Country = :country
ORDER BY LastName ASC, FirstName ASC
LIMIT 50;
