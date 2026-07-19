-- Query ID: q054
-- Intent: list all albums with artists
-- Description: Lists every album with its artist in the Chinook database.

SELECT a.AlbumId AS album_id,
       a.Title AS album_title,
       ar.Name AS artist_name
FROM Album a
JOIN Artist ar ON a.ArtistId = ar.ArtistId
ORDER BY artist_name ASC, album_title ASC
