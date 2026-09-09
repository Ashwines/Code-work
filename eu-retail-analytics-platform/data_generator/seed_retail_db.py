import os
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker

fake = Faker(["en_GB", "de_DE", "fr_FR", "it_IT", "es_ES"])
Faker.seed(42)
random.seed(42)

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_NAME = os.getenv("POSTGRES_DB", "retail_source")
DB_USER = os.getenv("POSTGRES_USER", "retail")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "retail")

REGIONS = [
    {"country": "AE", "currency": "AED", "cities": ["Dubai", "Abu Dhabi", "Sharjah"]},
    {"country": "GB", "currency": "GBP", "cities": ["London", "Manchester", "Birmingham"]},
    {"country": "DE", "currency": "EUR", "cities": ["Berlin", "Munich", "Frankfurt"]},
    {"country": "FR", "currency": "EUR", "cities": ["Paris", "Lyon", "Marseille"]},
    {"country": "NL", "currency": "EUR", "cities": ["Amsterdam", "Rotterdam", "Utrecht"]},
]

CATEGORIES = {
    "Electronics": (49.99, 1200.00),
    "Apparel": (12.50, 250.00),
    "Home & Kitchen": (15.00, 450.00),
    "Beauty & Care": (8.00, 120.00),
    "Sports & Outdoors": (20.00, 600.00),
}

ORDER_STATUSES = ["COMPLETED", "COMPLETED", "COMPLETED", "SHIPPED", "PROCESSING", "CANCELLED", "REFUNDED"]
PAYMENT_METHODS = ["CREDIT_CARD", "DEBIT_CARD", "APPLE_PAY", "PAYPAL", "KLARNA"]

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def seed():
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM oltp.orders;")
        order_count = cur.fetchone()[0]

        if order_count > 0:
            print(f"[SKIP] Database already seeded ({order_count} orders present). Exiting cleanly.")
            return

        print("No orders detected. Proceeding with database seed...")

        print("[1/5] Seeding Stores...")
        stores_data = [
            ("STR_DXB_01", "Dubai Mall Flagship", "Dubai", "AE"),
            ("STR_AUH_01", "Yas Mall MegaStore", "Abu Dhabi", "AE"),
            ("STR_LDN_01", "Oxford Street Express", "London", "GB"),
            ("STR_BER_01", "Alexanderplatz Hub", "Berlin", "DE"),
            ("STR_PAR_01", "Champs-Élysées Gallery", "Paris", "FR"),
            ("STR_AMS_01", "Centraal Retail Outlet", "Amsterdam", "NL"),
            ("STR_WEB_01", "Global Web Store", "Online", "AE"),
        ]
        execute_values(
            cur,
            """
            INSERT INTO oltp.stores (store_code, store_name, city, country_code)
            VALUES %s ON CONFLICT (store_code) DO NOTHING;
            """,
            stores_data
        )

        print("[2/5] Seeding Products...")
        products = []
        sku_counter = 1000
        for category, (min_p, max_p) in CATEGORIES.items():
            for _ in range(25):
                sku = f"SKU-{category[:3].upper()}-{sku_counter}"
                name = f"{fake.word().capitalize()} {category[:-1] if category.endswith('s') else category}"
                price = round(random.uniform(min_p, max_p), 2)
                products.append((sku, name, category, price, True))
                sku_counter += 1

        execute_values(
            cur,
            """
            INSERT INTO oltp.products (sku, product_name, category, unit_price, active)
            VALUES %s ON CONFLICT (sku) DO NOTHING;
            """,
            products
        )

        print("[3/5] Seeding Customers...")
        customers = []
        for i in range(500):
            region = random.choice(REGIONS)
            cust_code = f"CUST-{10000 + i}"
            name = fake.name()
            email = f"{cust_code.lower()}@{fake.free_email_domain()}"
            city = random.choice(region["cities"])
            country = region["country"]
            created_at = datetime.now() - timedelta(days=random.randint(60, 365))
            customers.append((cust_code, name, email, city, country, created_at))

        execute_values(
            cur,
            """
            INSERT INTO oltp.customers (customer_code, full_name, email, city, country_code, created_at)
            VALUES %s ON CONFLICT (customer_code) DO NOTHING;
            """,
            customers
        )

        cur.execute("SELECT customer_id, country_code FROM oltp.customers;")
        customer_pool = cur.fetchall()

        cur.execute("SELECT store_id, country_code FROM oltp.stores;")
        store_pool = cur.fetchall()

        cur.execute("SELECT product_id, unit_price FROM oltp.products;")
        product_pool = cur.fetchall()

        print("[4/5] Generating Orders & Order Items...")
        start_date = datetime.now() - timedelta(days=90)
        order_items = []
        payments = []
        order_counter = 50001

        for day_offset in range(90):
            current_day = start_date + timedelta(days=day_offset)
            daily_order_count = random.randint(15, 35)

            for _ in range(daily_order_count):
                cust_id, cust_country = random.choice(customer_pool)
                matching_stores = [s[0] for s in store_pool if s[1] == cust_country]
                store_id = matching_stores[0] if matching_stores else store_pool[0][0]

                order_num = f"ORD-{order_counter}"
                status = random.choice(ORDER_STATUSES)
                order_time = current_day + timedelta(
                    hours=random.randint(8, 21),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59)
                )
                currency = "AED" if cust_country == "AE" else ("GBP" if cust_country == "GB" else "EUR")

                cur.execute(
                    """
                    INSERT INTO oltp.orders (order_number, customer_id, store_id, order_status, order_ts, currency_code)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING order_id;
                    """,
                    (order_num, cust_id, store_id, status, order_time, currency)
                )
                order_id = cur.fetchone()[0]

                order_total = 0.0
                num_items = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
                sampled_products = random.sample(product_pool, num_items)

                for prod_id, unit_price in sampled_products:
                    qty = random.randint(1, 3)
                    line_total = round(float(unit_price) * qty, 2)
                    order_total += line_total
                    order_items.append((order_id, prod_id, qty, unit_price, line_total))

                pay_method = random.choice(PAYMENT_METHODS)
                if status in ["COMPLETED", "SHIPPED"]:
                    pay_status = "SUCCESS"
                    paid_at = order_time + timedelta(minutes=random.randint(1, 10))
                elif status == "REFUNDED":
                    pay_status = "REFUNDED"
                    paid_at = order_time + timedelta(days=random.randint(2, 5))
                elif status == "CANCELLED":
                    pay_status = "FAILED" if random.random() < 0.5 else "CANCELLED"
                    paid_at = None
                else:
                    pay_status = "PENDING"
                    paid_at = None

                payments.append((order_id, pay_method, pay_status, round(order_total, 2), paid_at))
                order_counter += 1

        print("[5/5] Bulk-inserting Line Items and Payment Ledgers...")
        execute_values(
            cur,
            """
            INSERT INTO oltp.order_items (order_id, product_id, quantity, unit_price, line_total)
            VALUES %s;
            """,
            order_items
        )

        execute_values(
            cur,
            """
            INSERT INTO oltp.payments (order_id, payment_method, payment_status, amount, paid_at)
            VALUES %s;
            """,
            payments
        )

        conn.commit()
        print(f"Data Seeding Completed: Seeded {len(customers)} customers, {order_counter - 50001} orders, and {len(order_items)} line items.")

    except Exception as e:
        conn.rollback()
        print(f"Seeding Failed: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed()