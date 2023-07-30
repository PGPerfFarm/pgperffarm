CREATE TABLE employees (
  emp_id int NOT NULL,
  emp_name varchar(255) NOT NULL,
  emp_department varchar(255) NOT NULL,
  emp_salary int NOT NULL
);

INSERT INTO employees (emp_id, emp_name, emp_department, emp_salary) VALUES
(1, 'John Doe', 'Sales', 100000),
(2, 'Jane Doe', 'Marketing', 80000),
(3, 'Bill Smith', 'IT', 60000);