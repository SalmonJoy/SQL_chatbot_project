-- q044: albums by quantity sold
-- Category: albums
-- Description: Ranks albums by the number of tracks sold.

SELECT a.Title AS album_title,
       ar.Name AS artist_name,
       SUM(il.Quantity) AS total_quantity_sold
FROM Album a
JOIN Artist ar ON a.ArtistId = ar.ArtistId
JOIN Track t ON a.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY a.AlbumId
ORDER BY total_quantity_sold DESC, album_title ASC
LIMIT 10;
