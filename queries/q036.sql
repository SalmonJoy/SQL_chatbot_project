-- q036: best-selling genres by revenue in specific billing country
-- Category: genres
-- Description: Ranks music genres by track sales revenue for one requested billing country.
-- Parameter: country (country) - Billing country available in the database.

SELECT g.Name AS genre_name, ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS total_revenue
FROM Invoice i
JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
JOIN Track t ON il.TrackId = t.TrackId
JOIN Genre g ON t.GenreId = g.GenreId
WHERE i.BillingCountry = :country
GROUP BY g.Name
ORDER BY total_revenue DESC, genre_name ASC
LIMIT 10;
