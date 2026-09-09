-- Seed sample retail data (UAE / EU flavored)

INSERT INTO oltp.stores (store_code, store_name, city, country_code) VALUES
('DXB01', 'Dubai Mall Flagship', 'Dubai', 'AE'),
('AUH01', 'Yas Mall Store', 'Abu Dhabi', 'AE'),
('BER01', 'Berlin Mitte', 'Berlin', 'DE'),
('AMS01', 'Amsterdam Central', 'Amsterdam', 'NL');

INSERT INTO oltp.customers (customer_code, full_name, email, city, country_code) VALUES
('C-1001', 'Aisha Al Maktoum', 'aisha@example.com', 'Dubai', 'AE'),
('C-1002', 'Omar Hassan', 'omar@example.com', 'Abu Dhabi', 'AE'),
('C-1003', 'Anna Schmidt', 'anna@example.com', 'Berlin', 'DE'),
('C-1004', 'Lars de Vries', 'lars@example.com', 'Amsterdam', 'NL'),
('C-1005', 'Fatima Khan', 'fatima@example.com', 'Dubai', 'AE');

INSERT INTO oltp.products (sku, product_name, category, unit_price) VALUES
('SKU-TEE-01', 'Cotton T-Shirt', 'Apparel', 79.00),
('SKU-JKT-01', 'Light Jacket', 'Apparel', 249.00),
('SKU-SHO-01', 'Running Shoes', 'Footwear', 399.00),
('SKU-BAG-01', 'City Backpack', 'Accessories', 179.00),
('SKU-WTCH-01', 'Sport Watch', 'Electronics', 549.00),
('SKU-EAR-01', 'Wireless Earbuds', 'Electronics', 299.00);

-- Orders (spread over recent dates)
INSERT INTO oltp.orders (order_number, customer_id, store_id, order_status, order_ts, currency_code) VALUES
('ORD-5001', 1, 1, 'delivered',  NOW() - INTERVAL '10 days', 'AED'),
('ORD-5002', 2, 2, 'delivered',  NOW() - INTERVAL '8 days',  'AED'),
('ORD-5003', 3, 3, 'shipped',    NOW() - INTERVAL '5 days',  'EUR'),
('ORD-5004', 4, 4, 'delivered',  NOW() - INTERVAL '4 days',  'EUR'),
('ORD-5005', 5, 1, 'processing', NOW() - INTERVAL '2 days',  'AED'),
('ORD-5006', 1, 1, 'delivered',  NOW() - INTERVAL '1 days',  'AED'),
('ORD-5007', 3, 3, 'cancelled',  NOW() - INTERVAL '3 days',  'EUR'),
('ORD-5008', 2, 1, 'delivered',  NOW() - INTERVAL '6 days',  'AED');

INSERT INTO oltp.order_items (order_id, product_id, quantity, unit_price, line_total) VALUES
(1, 1, 2, 79.00, 158.00),
(1, 4, 1, 179.00, 179.00),
(2, 3, 1, 399.00, 399.00),
(3, 2, 1, 249.00, 249.00),
(3, 6, 1, 299.00, 299.00),
(4, 5, 1, 549.00, 549.00),
(5, 1, 3, 79.00, 237.00),
(6, 3, 1, 399.00, 399.00),
(6, 6, 2, 299.00, 598.00),
(7, 2, 1, 249.00, 249.00),
(8, 4, 1, 179.00, 179.00),
(8, 1, 1, 79.00, 79.00);

INSERT INTO oltp.payments (order_id, payment_method, payment_status, amount, paid_at) VALUES
(1, 'card', 'captured', 337.00, NOW() - INTERVAL '10 days'),
(2, 'card', 'captured', 399.00, NOW() - INTERVAL '8 days'),
(3, 'paypal', 'captured', 548.00, NOW() - INTERVAL '5 days'),
(4, 'card', 'captured', 549.00, NOW() - INTERVAL '4 days'),
(5, 'card', 'pending', 237.00, NULL),
(6, 'apple_pay', 'captured', 997.00, NOW() - INTERVAL '1 days'),
(7, 'card', 'refunded', 249.00, NOW() - INTERVAL '3 days'),
(8, 'card', 'captured', 258.00, NOW() - INTERVAL '6 days');