-- q050: support rep revenue for specific year
-- Category: employees
-- Description: Shows support representative revenue for one requested invoice year.
-- Parameter: year (year) - Four-digit invoice year available in the database.

SELECT e.FirstName || ' ' || e.LastName AS support_rep_name,
       :year AS year,
       ROUND(SUM(i.Total), 2) AS total_revenue
FROM Employee e
JOIN Customer c ON e.EmployeeId = c.SupportRepId
JOIN Invoice i ON c.CustomerId = i.CustomerId
WHERE strftime('%Y', i.InvoiceDate) = :year
GROUP BY e.EmployeeId
ORDER BY total_revenue DESC, support_rep_name ASC;
