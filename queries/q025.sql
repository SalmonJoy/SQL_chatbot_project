-- q025: most common playlist track genres
-- Category: playlists
-- Description: Returns the top 10 music genres that appear most frequently across all tracks in playlists.

SELECT g.Name AS genre_name, COUNT(*) AS track_count FROM Track t JOIN PlaylistTrack pt ON t.TrackId = pt.TrackId JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.Name ORDER BY track_count DESC LIMIT 10;
