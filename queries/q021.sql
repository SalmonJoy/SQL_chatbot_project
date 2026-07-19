-- q021: customers assigned to each support rep
-- Category: employees
-- Description: Lists each support representative and the count of customers assigned to them.

SELECT e.FirstName || ' ' || e.LastName AS support_rep_name, COUNT(c.CustomerId) AS customer_count FROM Employee e LEFT JOIN Customer c ON e.EmployeeId = c.SupportRepId GROUP BY e.EmployeeId ORDER BY customer_count DESC;
