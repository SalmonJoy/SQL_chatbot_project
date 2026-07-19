-- q048: tracks in specific genre ranked by quantity sold
-- Category: products
-- Description: Ranks tracks within one requested genre by quantity sold.
-- Parameter: genre_name (genre_name) - Genre name available in the database.

SELECT t.Name AS track_name,
       g.Name AS genre_name,
       COALESCE(SUM(il.Quantity), 0) AS total_quantity_sold
FROM Genre g
JOIN Track t ON g.GenreId = t.GenreId
LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
WHERE g.Name = :genre_name
GROUP BY t.TrackId
ORDER BY total_quantity_sold DESC, track_name ASC
LIMIT 10;
