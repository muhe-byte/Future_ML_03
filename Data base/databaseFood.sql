-- 1. Create the Database
CREATE DATABASE habesha_bites;
USE habesha_bites;

-- 2. Create Food Items Table
-- This stores the menu items mentioned in your new order intent [cite: 9, 10]
CREATE TABLE food_items (
    item_id INT,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY(item_id)
);

-- 3. Create Orders Table
-- This stores the high-level order information and links to the track order intent [cite: 15]
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    status VARCHAR(100) NOT NULL
);

-- 4. Create Order Details Table
-- This handles the "order.add" intent, allowing multiple items per order [cite: 11]
CREATE TABLE order_details (
    order_id INT,
    item_id INT,
    quantity INT NOT NULL,
    total_price DECIMAL(10, 2),
    PRIMARY KEY (order_id, item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (item_id) REFERENCES food_items(item_id)
);

-- 5. Insert Ethiopian Menu Items
INSERT INTO food_items (item_id,name, price) VALUES 
(1,'Doro Wat', 150.00),
(2,'Kitfo', 180.00),
(3,'Beyaynetu', 120.00),
(4,'Shiro Wat', 90.00),
(5,'Tibs', 160.00),
(6,'Gomen', 70.00),
(7,'Firfir', 100.00);

-- 6. Insert Sample Tracking Data
-- To test your "track.order" intent with IDs like 63321 or 5521 [cite: 15, 17]
INSERT INTO orders (order_id, status) VALUES 
(63321, 'delivered'),
(5521, 'in progress'),
(123, 'picked up');

INSERT INTO order_details(order_id,item_id,quantity,total_price) values
(10,2,3,540),
(20,1,2,300),
(30,6,1,70);