-- q009: customer purchase frequency
-- Category: customers
-- Description: Returns the top 10 customers ranked by the number of invoices they have generated, showing their first name, last name, and total purchase count.

SELECT c.FirstName AS customer_first_name, c.LastName AS customer_last_name, COUNT(i.InvoiceId) AS purchase_count FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.CustomerId ORDER BY purchase_count DESC LIMIT 10;
