-- q049: support rep revenue for latest available month
-- Category: employees
-- Description: Shows employee or support representative sales revenue for the latest invoice month available in the database.

WITH latest_month AS (
  SELECT strftime('%Y-%m', MAX(InvoiceDate)) AS month
  FROM Invoice
)
SELECT e.FirstName || ' ' || e.LastName AS support_rep_name,
       lm.month,
       ROUND(SUM(i.Total), 2) AS total_revenue
FROM Employee e
JOIN Customer c ON e.EmployeeId = c.SupportRepId
JOIN Invoice i ON c.CustomerId = i.CustomerId
JOIN latest_month lm ON strftime('%Y-%m', i.InvoiceDate) = lm.month
GROUP BY e.EmployeeId, lm.month
ORDER BY total_revenue DESC, support_rep_name ASC;
