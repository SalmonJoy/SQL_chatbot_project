-- q046: media types by revenue
-- Category: products
-- Description: Ranks media types by total track sales revenue.

SELECT mt.Name AS media_type_name,
       ROUND(SUM(il.UnitPrice * il.Quantity), 2) AS total_revenue
FROM MediaType mt
JOIN Track t ON mt.MediaTypeId = t.MediaTypeId
JOIN InvoiceLine il ON t.TrackId = il.TrackId
GROUP BY mt.MediaTypeId
ORDER BY total_revenue DESC, media_type_name ASC;
