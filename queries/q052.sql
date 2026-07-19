-- q052: revenue rank for specific artist
-- Category: artists
-- Description: Returns one requested artist's revenue rank and whether that artist is the highest revenue artist.
-- Parameter: artist_name (artist_name) - Artist name available in the database.

WITH artist_revenue AS (
  SELECT ar.ArtistId AS artist_id,
         ar.Name AS artist_name,
         ROUND(COALESCE(SUM(il.UnitPrice * il.Quantity), 0), 2) AS total_revenue
  FROM Artist ar
  LEFT JOIN Album a ON ar.ArtistId = a.ArtistId
  LEFT JOIN Track t ON a.AlbumId = t.AlbumId
  LEFT JOIN InvoiceLine il ON t.TrackId = il.TrackId
  GROUP BY ar.ArtistId
),
ranked_artists AS (
  SELECT artist_id,
         artist_name,
         total_revenue,
         RANK() OVER (ORDER BY total_revenue DESC, artist_name ASC) AS revenue_rank
  FROM artist_revenue
),
top_artist AS (
  SELECT artist_name AS top_artist_name,
         total_revenue AS top_artist_revenue
  FROM ranked_artists
  ORDER BY revenue_rank ASC, artist_name ASC
  LIMIT 1
)
SELECT ra.artist_name,
       ra.total_revenue,
       ra.revenue_rank,
       ta.top_artist_name,
       ta.top_artist_revenue,
       CASE WHEN ra.revenue_rank = 1 THEN 1 ELSE 0 END AS is_highest_revenue_artist
FROM ranked_artists ra
CROSS JOIN top_artist ta
WHERE ra.artist_name = :artist_name;
