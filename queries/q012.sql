-- q012: best-selling tracks by revenue
-- Category: products
-- Description: Returns the top 10 tracks ranked by total revenue generated from sales.

SELECT t.Name AS track_name, SUM(il.UnitPrice * il.Quantity) AS total_revenue FROM Track t JOIN InvoiceLine il ON t.TrackId = il.TrackId GROUP BY t.TrackId ORDER BY total_revenue DESC LIMIT 10;
