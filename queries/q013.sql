-- q013: longest tracks
-- Category: products
-- Description: Returns the top 10 longest tracks by duration in milliseconds, including their name, album title, and artist name.

SELECT t.Name AS track_name, a.Title AS album_title, ar.Name AS artist_name, t.Milliseconds AS duration_ms FROM Track t JOIN Album a ON t.AlbumId = a.AlbumId JOIN Artist ar ON a.ArtistId = ar.ArtistId ORDER BY t.Milliseconds DESC LIMIT 10;
