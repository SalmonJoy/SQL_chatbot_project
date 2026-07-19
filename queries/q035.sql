-- q035: revenue by billing city
-- Category: sales
-- Description: Ranks billing cities by total invoice revenue.

SELECT BillingCity AS billing_city,
       BillingCountry AS billing_country,
       ROUND(SUM(Total), 2) AS total_revenue
FROM Invoice
GROUP BY BillingCity, BillingCountry
ORDER BY total_revenue DESC, billing_city ASC
LIMIT 10;
