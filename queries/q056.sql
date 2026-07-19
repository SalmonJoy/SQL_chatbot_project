-- Query ID: q056
-- Intent: most common file types by track count
-- Description: Ranks media or file types by the number of tracks and marks the most common type.

WITH media_type_counts AS (
  SELECT mt.MediaTypeId AS media_type_id,
         mt.Name AS file_type_name,
         COUNT(t.TrackId) AS track_count
  FROM MediaType mt
  LEFT JOIN Track t ON mt.MediaTypeId = t.MediaTypeId
  GROUP BY mt.MediaTypeId, mt.Name
),
ranked_media_types AS (
  SELECT media_type_id,
         file_type_name,
         track_count,
         RANK() OVER (ORDER BY track_count DESC, file_type_name ASC) AS track_count_rank
  FROM media_type_counts
)
SELECT file_type_name,
       track_count,
       track_count_rank,
       CASE WHEN track_count_rank = 1 THEN 1 ELSE 0 END AS is_most_common_file_type
FROM ranked_media_types
ORDER BY track_count_rank ASC, file_type_name ASC
