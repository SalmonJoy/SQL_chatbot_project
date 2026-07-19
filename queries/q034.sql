-- q034: average invoice value by billing country
-- Category: sales
-- Description: Calculates the average invoice amount for each billing country.

SELECT BillingCountry AS billing_country, ROUND(AVG(Total), 2) AS average_invoice_value
FROM Invoice
GROUP BY BillingCountry
ORDER BY average_invoice_value DESC, billing_country ASC
LIMIT 10;
