-- q019: albums with most tracks
-- Category: albums
-- Description: Returns the top 10 albums ranked by the number of tracks they contain.

SELECT a.Title AS album_title, COUNT(t.TrackId) AS track_count FROM Album a LEFT JOIN Track t ON a.AlbumId = t.AlbumId GROUP BY a.AlbumId, a.Title ORDER BY track_count DESC LIMIT 10;
