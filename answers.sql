#question 1

-- Original table violates 1NF because Products column contains multiple values
-- Solution: Split the multi-valued Products column into separate rows

-- First, create a normalized version of the table
CREATE TABLE ProductDetail_1NF (
    OrderID INT,
    CustomerName VARCHAR(100),
    Product VARCHAR(50)
);

-- Insert data by splitting the Products column
INSERT INTO ProductDetail_1NF (OrderID, CustomerName, Product)
SELECT OrderID, CustomerName, 'Laptop' FROM ProductDetail WHERE Products LIKE '%Laptop%'
UNION ALL
SELECT OrderID, CustomerName, 'Mouse' FROM ProductDetail WHERE Products LIKE '%Mouse%'
UNION ALL
SELECT OrderID, CustomerName, 'Tablet' FROM ProductDetail WHERE Products LIKE '%Tablet%'
UNION ALL
SELECT OrderID, CustomerName, 'Keyboard' FROM ProductDetail WHERE Products LIKE '%Keyboard%'
UNION ALL
SELECT OrderID, CustomerName, 'Phone' FROM ProductDetail WHERE Products LIKE '%Phone%';

-- Resulting 1NF table:
-- | OrderID | CustomerName | Product  |
-- |---------|--------------|----------|
-- | 101     | John Doe     | Laptop   |
-- | 101     | John Doe     | Mouse    |
-- | 102     | Jane Smith   | Tablet   |
-- | 102     | Jane Smith   | Keyboard |
-- | 102     | Jane Smith   | Mouse    |
-- | 103     | Emily Clark  | Phone    |


--question 2

-- Current table has partial dependency: CustomerName depends only on OrderID (not the full PK)
-- Solution: Split into two tables - Orders and OrderItems

-- Create Orders table (contains OrderID as PK and CustomerName)
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    CustomerName VARCHAR(100)
);

-- Create OrderItems table (contains OrderID+Product as composite PK and Quantity)
CREATE TABLE OrderItems (
    OrderID INT,
    Product VARCHAR(50),
    Quantity INT,
    PRIMARY KEY (OrderID, Product),
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID)
);

-- Populate Orders table
INSERT INTO Orders (OrderID, CustomerName)
SELECT DISTINCT OrderID, CustomerName FROM OrderDetails;

-- Populate OrderItems table
INSERT INTO OrderItems (OrderID, Product, Quantity)
SELECT OrderID, Product, Quantity FROM OrderDetails;

-- Resulting 2NF schema:
-- Orders table:
-- | OrderID | CustomerName |
-- |---------|--------------|
-- | 101     | John Doe     |
-- | 102     | Jane Smith   |
-- | 103     | Emily Clark  |

-- OrderItems table:
-- | OrderID | Product  | Quantity |
-- |---------|----------|----------|
-- | 101     | Laptop   | 2        |
-- | 101     | Mouse    | 1        |
-- | 102     | Tablet   | 3        |
-- | 102     | Keyboard | 1        |
-- | 102     | Mouse    | 2        |
-- | 103     | Phone    | 1        |