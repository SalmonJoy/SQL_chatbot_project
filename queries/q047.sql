-- q047: tracks never sold
-- Category: products
-- Description: Lists tracks that have never appeared on an invoice line.

SELECT t.TrackId AS track_id,
       t.Name AS track_name,
       a.Title AS album_title,
       ar.Name AS artist_name
FROM Track t
LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
LEFT JOIN Album a ON t.AlbumId = a.AlbumId
LEFT JOIN Artist ar ON a.ArtistId = ar.ArtistId
WHERE il.InvoiceLineId IS NULL
ORDER BY t.Name ASC
LIMIT 50;
