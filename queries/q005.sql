-- q005: average invoice value
-- Category: sales
-- Description: Calculates the average total value of all invoices in the system.

SELECT AVG([Total]) AS average_invoice_value FROM [Invoice];
