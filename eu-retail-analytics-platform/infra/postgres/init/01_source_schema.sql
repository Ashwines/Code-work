-- EU Retail Analytics Platform - Source OLTP schema
-- Runs automatically on first Postgres start (init folder)

CREATE SCHEMA IF NOT EXISTS oltp;

-- Customers
CREATE TABLE oltp.customers (
    customer_id        SERIAL PRIMARY KEY,
    customer_code      VARCHAR(32) NOT NULL UNIQUE,
    full_name          VARCHAR(200) NOT NULL,
    email              VARCHAR(200),
    city               VARCHAR(100),
    country_code       CHAR(2) NOT NULL DEFAULT 'AE',
    created_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Products
CREATE TABLE oltp.products (
    product_id         SERIAL PRIMARY KEY,
    sku                VARCHAR(64) NOT NULL UNIQUE,
    product_name       VARCHAR(200) NOT NULL,
    category           VARCHAR(100) NOT NULL,
    unit_price         NUMERIC(12,2) NOT NULL,
    active             BOOLEAN NOT NULL DEFAULT TRUE
);

-- Stores / channels
CREATE TABLE oltp.stores (
    store_id           SERIAL PRIMARY KEY,
    store_code         VARCHAR(32) NOT NULL UNIQUE,
    store_name         VARCHAR(200) NOT NULL,
    city               VARCHAR(100),
    country_code       CHAR(2) NOT NULL DEFAULT 'AE'
);

-- Orders
CREATE TABLE oltp.orders (
    order_id           SERIAL PRIMARY KEY,
    order_number       VARCHAR(32) NOT NULL UNIQUE,
    customer_id        INT NOT NULL REFERENCES oltp.customers(customer_id),
    store_id           INT NOT NULL REFERENCES oltp.stores(store_id),
    order_status       VARCHAR(30) NOT NULL,
    order_ts           TIMESTAMP NOT NULL,
    currency_code      CHAR(3) NOT NULL DEFAULT 'AED'
);

-- Order lines
CREATE TABLE oltp.order_items (
    order_item_id      SERIAL PRIMARY KEY,
    order_id           INT NOT NULL REFERENCES oltp.orders(order_id),
    product_id         INT NOT NULL REFERENCES oltp.products(product_id),
    quantity           INT NOT NULL CHECK (quantity > 0),
    unit_price         NUMERIC(12,2) NOT NULL,
    line_total         NUMERIC(12,2) NOT NULL
);

-- Payments
CREATE TABLE oltp.payments (
    payment_id         SERIAL PRIMARY KEY,
    order_id           INT NOT NULL REFERENCES oltp.orders(order_id),
    payment_method     VARCHAR(30) NOT NULL,
    payment_status     VARCHAR(30) NOT NULL,
    amount             NUMERIC(12,2) NOT NULL,
    paid_at            TIMESTAMP
);

CREATE INDEX idx_orders_customer ON oltp.orders(customer_id);
CREATE INDEX idx_orders_ts ON oltp.orders(order_ts);
CREATE INDEX idx_order_items_order ON oltp.order_items(order_id);
CREATE INDEX idx_payments_order ON oltp.payments(order_id);