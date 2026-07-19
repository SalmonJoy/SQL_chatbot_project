-- q018: artists with most albums
-- Category: artists
-- Description: Returns the top 10 artists ranked by the number of albums they have released.

SELECT a.Name AS artist_name, COUNT(al.AlbumId) AS album_count FROM Artist a JOIN Album al ON a.ArtistId = al.ArtistId GROUP BY a.ArtistId, a.Name ORDER BY album_count DESC LIMIT 10;
