-- q042: customers with no purchases
-- Category: customers
-- Description: Lists customers who do not have any invoices.

SELECT c.CustomerId AS customer_id,
       c.FirstName AS first_name,
       c.LastName AS last_name,
       c.Email AS email,
       c.Country AS country
FROM Customer c
LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE i.InvoiceId IS NULL
ORDER BY c.LastName ASC, c.FirstName ASC
LIMIT 50;
