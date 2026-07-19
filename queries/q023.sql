-- q023: employee reporting hierarchy
-- Category: employees
-- Description: Lists all employees along with their direct manager's name to visualize the reporting structure.

SELECT e.EmployeeId AS employee_id, e.FirstName AS employee_first_name, e.LastName AS employee_last_name, m.EmployeeId AS manager_id, m.FirstName AS manager_first_name, m.LastName AS manager_last_name FROM Employee e LEFT JOIN Employee m ON e.ReportsTo = m.EmployeeId ORDER BY m.EmployeeId, e.EmployeeId;
