-- q015: track count by genre
-- Category: genres
-- Description: Returns the number of tracks for each genre, sorted from the most popular to the least popular.

SELECT g.Name AS genre_name, COUNT(t.TrackId) AS track_count FROM Genre g LEFT JOIN Track t ON g.GenreId = t.GenreId GROUP BY g.GenreId, g.Name ORDER BY track_count DESC LIMIT 10;
