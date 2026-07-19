-- q017: best-selling genres by revenue
-- Category: genres
-- Description: Returns the top 10 music genres ranked by total revenue generated from track sales.

SELECT g.Name AS genre_name, SUM(il.UnitPrice * il.Quantity) AS total_revenue FROM Genre g JOIN Track t ON g.GenreId = t.GenreId JOIN InvoiceLine il ON t.TrackId = il.TrackId GROUP BY g.GenreId, g.Name ORDER BY total_revenue DESC LIMIT 10;
