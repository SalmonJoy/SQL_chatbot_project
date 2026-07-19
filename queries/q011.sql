-- q011: best-selling tracks by quantity
-- Category: products
-- Description: Returns the top 10 tracks ranked by the total quantity sold across all invoices.

SELECT t.Name AS track_name, SUM(il.Quantity) AS total_quantity_sold FROM Track t JOIN InvoiceLine il ON t.TrackId = il.TrackId GROUP BY t.TrackId ORDER BY total_quantity_sold DESC LIMIT 10;
