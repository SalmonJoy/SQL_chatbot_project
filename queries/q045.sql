-- q045: artists by quantity sold
-- Category: artists
-- Description: Ranks artists by the number of tracks sold.

SELECT ar.Name AS artist_name,
       SUM(il.Quantity) AS total_quantity_sold
FROM Artist ar
JOIN Album a ON ar.ArtistId = a.ArtistId
JOIN Track t ON a.AlbumId = t.AlbumId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY ar.ArtistId
ORDER BY total_quantity_sold DESC, artist_name ASC
LIMIT 10;
