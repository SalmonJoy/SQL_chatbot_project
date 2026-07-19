-- q016: track count by media type
-- Category: products
-- Description: Returns the count of tracks grouped by their media type name.

SELECT mt.Name AS media_type_name, COUNT(t.TrackId) AS track_count FROM MediaType mt JOIN Track t ON mt.MediaTypeId = t.MediaTypeId GROUP BY mt.MediaTypeId, mt.Name ORDER BY track_count DESC;
