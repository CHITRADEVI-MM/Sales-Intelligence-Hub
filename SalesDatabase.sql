#DATABASE CREATE
CREATE DATABASE sales_db;
USE sales_db;

# CREATE TABLES 
CREATE TABLE branches (
    branch_id INT PRIMARY KEY AUTO_INCREMENT,
    branch_name VARCHAR(100) NOT NULL,
    branch_admin_name VARCHAR(100)
);

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    branch_id INT,
    role ENUM('Super Admin', 'Admin') DEFAULT 'Admin',
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

CREATE TABLE customer_sales (
    sale_id INT PRIMARY KEY AUTO_INCREMENT,
    branch_id INT,
    sale_date DATE,
    customer_name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL UNIQUE,
    product_name VARCHAR(30),
    gross_sales DECIMAL(12,2) NOT NULL CHECK (gross_sales > 0),
    received_amount DECIMAL(12,2) DEFAULT 0,
    pending_amount DECIMAL(12,2) GENERATED ALWAYS AS (gross_sales - received_amount) STORED,
    payment_status VARCHAR(20) DEFAULT 'Open',
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

CREATE TABLE payment_splits (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount_paid DECIMAL(12,2) NOT NULL CHECK (amount_paid > 0),
    payment_method ENUM('Cash', 'Card', 'UPI', 'Bank Transfer') NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES customer_sales(sale_id) ON DELETE CASCADE
);

#BRANCHES DATA
INSERT INTO branches (branch_name, branch_admin_name) VALUES
('Coimbatore', 'Priya'),
('Pune', 'Vikram'),
('Kolkata', 'Neha'),
('Jaipur', 'Karan'),
('Lucknow', 'Divya');

#USERS DATA 
INSERT INTO users (username, email, password, branch_id, role) VALUES
('priya_sa', 'priya@hub.com', 'p@2026', NULL, 'Super Admin'),
('vikram_ad', 'vikram@hub.com', 'v@2026', 2, 'Admin'),
('neha_ad', 'neha@hub.com', 'n@2026', 3, 'Admin'),
('karan_ad', 'karan@hub.com', 'k@2026', 4, 'Admin'),
('divya_ad', 'divya@hub.com', 'd@2026', 5, 'Admin');

# SALES DATA 
INSERT INTO customer_sales 
(branch_id, sale_date, customer_name, mobile_number, product_name, gross_sales) 
VALUES
(1, '2026-06-01', 'Arjun Reddy', '9876501234', 'DATA SCI', 92000.00),
(2, '2026-06-03', 'Sneha Iyer', '9876501235', 'CLOUD', 45000.00),
(3, '2026-06-05', 'Rohan Das', '9876501236', 'AI/ML', 120000.00),
(4, '2026-06-07', 'Kavya Nair', '9876501237', 'WEB DEV', 67000.00),
(5, '2026-06-08', 'Manish Jain', '9876501238', 'CYBERSEC', 88000.00),
(1, '2026-06-10', 'Zara Khan', '9876501239', 'BA', 35000.00),
(2, '2026-06-11', 'Aditya Roy', '9876501240', 'DA', 56000.00);

#PAYMENT DATA 
INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
VALUES 
(1, '2026-06-02', 50000.00, 'UPI'),
(1, '2026-06-05', 42000.00, 'Bank Transfer'), 
(2, '2026-06-04', 45000.00, 'Card'), 
(3, '2026-06-06', 60000.00, 'UPI'), 
(3, '2026-06-09', 40000.00, 'Cash'),
(4, '2026-06-08', 67000.00, 'UPI'), 
(5, '2026-06-09', 30000.00, 'Card'), 
(6, '2026-06-11', 15000.00, 'Cash'), 
(7, '2026-06-12', 56000.00, 'UPI');

INSERT INTO users (username, email, password, branch_id, role) 
VALUES ('chitra', 'chitra@hub.com', 'chiththu1', NULL, 'Super Admin');

DROP TRIGGER IF EXISTS trg_payment_insert;
DROP TRIGGER IF EXISTS trg_payment_update;
DROP TRIGGER IF EXISTS trg_payment_delete;

USE sales_db;

DROP TRIGGER IF EXISTS trg_payment_insert;
DROP TRIGGER IF EXISTS trg_payment_update;
DROP TRIGGER IF EXISTS trg_payment_delete;

DELIMITER //

CREATE TRIGGER trg_payment_insert
AFTER INSERT ON payment_splits
FOR EACH ROW
BEGIN
    DECLARE v_gross DECIMAL(12,2);
    DECLARE v_total_received DECIMAL(12,2);

    SELECT cs.gross_sales, IFNULL(SUM(ps.amount_paid), 0)
    INTO v_gross, v_total_received
    FROM customer_sales cs
    LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
    WHERE cs.sale_id = NEW.sale_id
    GROUP BY cs.sale_id, cs.gross_sales;

    IF v_total_received > v_gross THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Payment exceeds gross sales. Overpayment blocked.';
    END IF;

    UPDATE customer_sales
    SET received_amount = v_total_received,
        payment_status = IF(v_total_received >= v_gross, 'Close', 'Open')
    WHERE sale_id = NEW.sale_id;
END//

CREATE TRIGGER trg_payment_update
AFTER UPDATE ON payment_splits
FOR EACH ROW
BEGIN
    DECLARE v_gross DECIMAL(12,2);
    DECLARE v_total_received DECIMAL(12,2);

    SELECT cs.gross_sales, IFNULL(SUM(ps.amount_paid), 0)
    INTO v_gross, v_total_received
    FROM customer_sales cs
    LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
    WHERE cs.sale_id = NEW.sale_id
    GROUP BY cs.sale_id, cs.gross_sales;

    IF v_total_received > v_gross THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error: Updated payment exceeds gross sales.';
    END IF;

    UPDATE customer_sales
    SET received_amount = v_total_received,
        payment_status = IF(v_total_received >= v_gross, 'Close', 'Open')
    WHERE sale_id = NEW.sale_id;
END//

CREATE TRIGGER trg_payment_delete
AFTER DELETE ON payment_splits
FOR EACH ROW
BEGIN
    DECLARE v_gross DECIMAL(12,2);
    DECLARE v_total_received DECIMAL(12,2);

    SELECT cs.gross_sales, IFNULL(SUM(ps.amount_paid), 0)
    INTO v_gross, v_total_received
    FROM customer_sales cs
    LEFT JOIN payment_splits ps ON cs.sale_id = ps.sale_id
    WHERE cs.sale_id = OLD.sale_id
    GROUP BY cs.sale_id, cs.gross_sales;

    UPDATE customer_sales
    SET received_amount = v_total_received,
        payment_status = IF(v_total_received >= v_gross, 'Close', 'Open')
    WHERE sale_id = OLD.sale_id;
END//

DELIMITER ;

SET SQL_SAFE_UPDATES = 0;

UPDATE customer_sales cs
LEFT JOIN (
    SELECT sale_id, SUM(amount_paid) AS total_paid
    FROM payment_splits
    GROUP BY sale_id
) ps ON cs.sale_id = ps.sale_id
SET cs.received_amount = IFNULL(ps.total_paid, 0),
    cs.payment_status = IF(IFNULL(ps.total_paid, 0) >= cs.gross_sales, 'Close', 'Open');

SET SQL_SAFE_UPDATES = 1;

SHOW TRIGGERS;
SELECT sale_id, customer_name, gross_sales, received_amount, pending_amount, payment_status FROM customer_sales;

SET SQL_SAFE_UPDATES = 0;

-- 1. Clear old payment and sales records
DELETE FROM payment_splits;
DELETE FROM customer_sales;

-- 2. Reset auto-increment IDs back to 1
ALTER TABLE customer_sales AUTO_INCREMENT = 1;
ALTER TABLE payment_splits AUTO_INCREMENT = 1;

-- 3. Re-insert clean sales records
INSERT INTO customer_sales 
(branch_id, sale_date, customer_name, mobile_number, product_name, gross_sales) 
VALUES
(1, '2026-06-01', 'Arjun Reddy', '9876501234', 'DATA SCI', 92000.00),
(2, '2026-06-03', 'Sneha Iyer', '9876501235', 'CLOUD', 45000.00),
(3, '2026-06-05', 'Rohan Das', '9876501236', 'AI/ML', 120000.00),
(4, '2026-06-07', 'Kavya Nair', '9876501237', 'WEB DEV', 67000.00),
(5, '2026-06-08', 'Manish Jain', '9876501238', 'CYBERSEC', 88000.00),
(1, '2026-06-10', 'Zara Khan', '9876501239', 'BA', 35000.00),
(2, '2026-06-11', 'Aditya Roy', '9876501240', 'DA', 56000.00);

-- 4. Re-insert clean payments (your active triggers will auto-update pending_amount & status!)
INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
VALUES 
(1, '2026-06-02', 50000.00, 'UPI'),
(1, '2026-06-05', 42000.00, 'Bank Transfer'), 
(2, '2026-06-04', 45000.00, 'Card'), 
(3, '2026-06-06', 60000.00, 'UPI'), 
(3, '2026-06-09', 40000.00, 'Cash'),
(4, '2026-06-08', 67000.00, 'UPI'), 
(5, '2026-06-09', 30000.00, 'Card'), 
(6, '2026-06-11', 15000.00, 'Cash'), 
(7, '2026-06-12', 56000.00, 'UPI');

SET SQL_SAFE_UPDATES = 1;
SELECT * FROM payment_splits;