-- q024: largest playlists by track count
-- Category: playlists
-- Description: Returns the top 10 playlists with the highest number of tracks, showing the playlist name and the count of tracks in each.

SELECT p.Name AS playlist_name, COUNT(pt.TrackId) AS track_count FROM Playlist p JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId GROUP BY p.PlaylistId, p.Name ORDER BY track_count DESC LIMIT 10;
