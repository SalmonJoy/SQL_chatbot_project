-- Query ID: q053
-- Intent: list all artists
-- Description: Lists every artist in the Chinook database alphabetically.

SELECT ArtistId AS artist_id,
       Name AS artist_name
FROM Artist
ORDER BY artist_name ASC
