-- q043: albums by revenue
-- Category: albums
-- Description: Ranks albums by total track sales revenue.

SELECT a.Title AS album_title,
       ar.Name AS artist_name,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS total_revenue
FROM Album a
JOIN Artist ar ON a.ArtistId = ar.ArtistId
JOIN Track t ON a.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY a.AlbumId
ORDER BY total_revenue DESC, album_title ASC
LIMIT 10;
