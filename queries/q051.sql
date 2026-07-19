-- q051: revenue for specific artist
-- Category: artists
-- Description: Returns total track sales revenue for one requested artist.
-- Parameter: artist_name (artist_name) - Artist name available in the database.

SELECT ar.Name AS artist_name,
       ROUND(COALESCE(SUM(il.UnitPrice * il.Quantity), 0), 2) AS total_revenue
FROM Artist ar
LEFT JOIN Album a ON ar.ArtistId = a.ArtistId
LEFT JOIN Track t ON a.AlbumId = t.AlbumId
LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
WHERE ar.Name = :artist_name
GROUP BY ar.ArtistId;
