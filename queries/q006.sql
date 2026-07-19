-- q006: invoice count by billing country
-- Category: sales
-- Description: Returns the number of invoices grouped by the billing country, sorted from highest to lowest count.

SELECT BillingCountry AS billing_country, COUNT(*) AS invoice_count FROM Invoice GROUP BY BillingCountry ORDER BY invoice_count DESC LIMIT 10;
