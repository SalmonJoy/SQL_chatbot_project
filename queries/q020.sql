-- q020: artists with highest revenue
-- Category: artists
-- Description: Returns the top 10 artists ranked by total revenue generated from track sales.

SELECT a.Name AS artist_name, SUM(il.UnitPrice * il.Quantity) AS total_revenue FROM Artist a JOIN Album al ON a.ArtistId = al.ArtistId JOIN Track t ON al.AlbumId = t.AlbumId JOIN InvoiceLine il ON t.TrackId = il.TrackId GROUP BY a.ArtistId, a.Name ORDER BY total_revenue DESC LIMIT 10;
