-- q037: monthly revenue by billing country
-- Category: sales
-- Description: Shows monthly invoice revenue split by billing country.

SELECT strftime('%Y-%m', InvoiceDate) AS month,
       BillingCountry AS billing_country,
       ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY strftime('%Y-%m', InvoiceDate), BillingCountry
ORDER BY month ASC, billing_country ASC;
