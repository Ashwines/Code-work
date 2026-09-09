"""
Ingestion engine:
  1) Extract oltp.* from Postgres → MinIO landing (JSONL)
  2) Convert landing → MinIO raw (Parquet)
  3) Rebuild ClickHouse lake_raw + analytics_marts from Postgres (reliable path)
"""

import os
import json
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from botocore.client import Config
import clickhouse_connect

# MinIO
S3_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

# Postgres source
PG_HOST = os.getenv("SOURCE_DB_HOST", "postgres")
PG_PORT = int(os.getenv("SOURCE_DB_PORT", 5432))
PG_DB = os.getenv("SOURCE_DB_NAME", "retail_source")
PG_USER = os.getenv("SOURCE_DB_USER", "retail")
PG_PASS = os.getenv("SOURCE_DB_PASSWORD", "retail")

# ClickHouse
CH_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CH_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", 8123))
CH_USER = os.getenv("CLICKHOUSE_USER", "default")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "clickhouse")

TABLES = [
    "stores",
    "products",
    "customers",
    "orders",
    "order_items",
    "payments",
]


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def get_pg_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
    )


def extract_table_to_landing(table_name: str, ds: str) -> str:
    """Extract one oltp table to MinIO landing as JSONL."""
    conn = get_pg_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM oltp.{table_name};")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    now_iso = datetime.utcnow().isoformat()
    lines = []
    for row in rows:
        record = dict(row)
        for k, v in record.items():
            if isinstance(v, datetime):
                record[k] = v.isoformat()
            elif hasattr(v, "__float__") and not isinstance(v, bool):
                try:
                    record[k] = float(v)
                except Exception:
                    pass
        record["_ingested_at"] = now_iso
        record["_source_table"] = f"oltp.{table_name}"
        lines.append(json.dumps(record, default=str))

    payload = "\n".join(lines).encode("utf-8")
    s3_key = f"oltp/{table_name}/snapshot_date={ds}/data.jsonl"

    s3 = get_s3_client()
    s3.put_object(Bucket="landing", Key=s3_key, Body=payload)
    print(f"Extracted {len(rows)} rows from oltp.{table_name} → landing/{s3_key}")
    return s3_key


def convert_landing_to_raw_parquet(table_name: str, ds: str):
    """Convert landing JSONL to raw Parquet on MinIO."""
    s3 = get_s3_client()
    landing_key = f"oltp/{table_name}/snapshot_date={ds}/data.jsonl"
    obj = s3.get_object(Bucket="landing", Key=landing_key)
    body = obj["Body"].read().decode("utf-8")

    records = [json.loads(line) for line in body.strip().split("\n") if line.strip()]
    if not records:
        print(f"No records for {table_name}")
        return

    arrow_table = pa.Table.from_pylist(records)
    parquet_buffer = pa.BufferOutputStream()
    pq.write_table(arrow_table, parquet_buffer, compression="snappy")

    raw_key = f"oltp/{table_name}/ingestion_date={ds}/data.parquet"
    s3.put_object(
        Bucket="raw",
        Key=raw_key,
        Body=parquet_buffer.getvalue().to_pybytes(),
    )
    print(f"Wrote raw/{raw_key} ({arrow_table.num_rows} rows)")


def _ch_client():
    return clickhouse_connect.get_client(
        host=CH_HOST,
        port=CH_PORT,
        username=CH_USER,
        password=CH_PASSWORD,
    )


def _sync_postgres_to_lake_raw(client):
    """
    Build lake_raw.* in ClickHouse from Postgres using the PostgreSQL table function.
    This replaces the missing Parquet→CH loader and unblocks marts.
    """
    client.command("CREATE DATABASE IF NOT EXISTS lake_raw")

    # Drop + recreate for idempotent daily runs
    for table in TABLES:
        client.command(f"DROP TABLE IF EXISTS lake_raw.raw_{table}")

    # Map: ClickHouse table ← Postgres oltp table
    # postgresql(host:port, database, table, user, password, schema)
    pg = f"postgresql('{PG_HOST}:{PG_PORT}', '{PG_DB}', '{{table}}', '{PG_USER}', '{PG_PASS}', 'oltp')"

    client.command(
        f"""
        CREATE TABLE lake_raw.raw_customers
        ENGINE = MergeTree()
        ORDER BY customer_id AS
        SELECT
            toInt64(customer_id) AS customer_id,
            customer_code,
            full_name,
            email,
            city,
            country_code,
            created_at
        FROM {pg.format(table='customers')}
        """
    )

    client.command(
        f"""
        CREATE TABLE lake_raw.raw_stores
        ENGINE = MergeTree()
        ORDER BY store_id AS
        SELECT
            toInt64(store_id) AS store_id,
            store_code,
            store_name,
            city,
            country_code
        FROM {pg.format(table='stores')}
        """
    )

    client.command(
        f"""
        CREATE TABLE lake_raw.raw_products
        ENGINE = MergeTree()
        ORDER BY product_id AS
        SELECT
            toInt64(product_id) AS product_id,
            sku,
            product_name,
            category,
            toFloat64(unit_price) AS unit_price,
            active
        FROM {pg.format(table='products')}
        """
    )

    client.command(
        f"""
        CREATE TABLE lake_raw.raw_orders
        ENGINE = MergeTree()
        ORDER BY order_id AS
        SELECT
            toInt64(order_id) AS order_id,
            order_number,
            toInt64(customer_id) AS customer_id,
            toInt64(store_id) AS store_id,
            order_status,
            order_ts,
            currency_code
        FROM {pg.format(table='orders')}
        """
    )

    client.command(
        f"""
        CREATE TABLE lake_raw.raw_order_items
        ENGINE = MergeTree()
        ORDER BY order_item_id AS
        SELECT
            toInt64(order_item_id) AS order_item_id,
            toInt64(order_id) AS order_id,
            toInt64(product_id) AS product_id,
            toInt32(quantity) AS quantity,
            toFloat64(unit_price) AS unit_price,
            toFloat64(line_total) AS line_total
        FROM {pg.format(table='order_items')}
        """
    )

    client.command(
        f"""
        CREATE TABLE lake_raw.raw_payments
        ENGINE = MergeTree()
        ORDER BY payment_id AS
        SELECT
            toInt64(payment_id) AS payment_id,
            toInt64(order_id) AS order_id,
            payment_method,
            payment_status,
            toFloat64(amount) AS amount,
            paid_at
        FROM {pg.format(table='payments')}
        """
    )

    print("lake_raw.* synced from Postgres")


def refresh_clickhouse_marts():
    """Idempotent rebuild of lake_raw + analytics_marts."""
    client = _ch_client()
    _sync_postgres_to_lake_raw(client)

    client.command("CREATE DATABASE IF NOT EXISTS analytics_marts")

    # Idempotent marts
    client.command("DROP TABLE IF EXISTS analytics_marts.dim_customers")
    client.command("DROP TABLE IF EXISTS analytics_marts.dim_stores")
    client.command("DROP TABLE IF EXISTS analytics_marts.dim_products")
    client.command("DROP TABLE IF EXISTS analytics_marts.fct_daily_sales")

    client.command(
        """
        CREATE TABLE analytics_marts.dim_customers
        ENGINE = MergeTree()
        ORDER BY customer_id AS
        SELECT
            customer_id,
            customer_code,
            full_name,
            email,
            city,
            country_code,
            created_at
        FROM lake_raw.raw_customers
        WHERE customer_id IS NOT NULL
        """
    )

    client.command(
        """
        CREATE TABLE analytics_marts.dim_stores
        ENGINE = MergeTree()
        ORDER BY store_id AS
        SELECT
            store_id,
            store_code,
            store_name,
            city,
            country_code
        FROM lake_raw.raw_stores
        WHERE store_id IS NOT NULL
        """
    )

    client.command(
        """
        CREATE TABLE analytics_marts.dim_products
        ENGINE = MergeTree()
        ORDER BY product_id AS
        SELECT
            product_id,
            sku,
            product_name,
            category,
            round(unit_price, 2) AS unit_price,
            toUInt8(active) AS is_active
        FROM lake_raw.raw_products
        WHERE product_id IS NOT NULL
        """
    )

    client.command(
        """
        CREATE TABLE analytics_marts.fct_daily_sales
        ENGINE = MergeTree()
        PARTITION BY toYYYYMM(order_ts)
        ORDER BY (store_id, product_id, order_ts) AS
        SELECT
            oi.order_item_id AS order_item_id,
            o.order_id AS order_id,
            o.customer_id AS customer_id,
            o.store_id AS store_id,
            oi.product_id AS product_id,
            o.order_ts AS order_ts,
            toDate(o.order_ts) AS order_date,
            o.order_status AS order_status,
            o.currency_code AS currency_code,
            oi.quantity AS quantity,
            round(oi.unit_price, 2) AS unit_price,
            round(oi.line_total, 2) AS line_total,
            p.payment_method AS payment_method,
            p.payment_status AS payment_status
        FROM lake_raw.raw_orders AS o
        INNER JOIN lake_raw.raw_order_items AS oi ON o.order_id = oi.order_id
        LEFT JOIN lake_raw.raw_payments AS p ON o.order_id = p.order_id
        WHERE o.order_id IS NOT NULL
        """
    )

    # Convenience view for Superset executive dashboard
    client.command("DROP VIEW IF EXISTS analytics_marts.v_retail_executive_sales")
    client.command(
        """
        CREATE VIEW analytics_marts.v_retail_executive_sales AS
        SELECT
            f.order_date,
            f.order_ts,
            f.order_id,
            f.order_item_id,
            f.order_status,
            f.currency_code,
            f.quantity,
            f.unit_price,
            f.line_total,
            f.payment_method,
            f.payment_status,
            c.customer_code,
            c.full_name AS customer_name,
            c.city AS customer_city,
            c.country_code AS customer_country,
            s.store_code,
            s.store_name,
            s.city AS store_city,
            s.country_code AS store_country,
            p.sku,
            p.product_name,
            p.category
        FROM analytics_marts.fct_daily_sales f
        LEFT JOIN analytics_marts.dim_customers c ON f.customer_id = c.customer_id
        LEFT JOIN analytics_marts.dim_stores s ON f.store_id = s.store_id
        LEFT JOIN analytics_marts.dim_products p ON f.product_id = p.product_id
        """
    )

    print("ClickHouse lake_raw + analytics_marts refreshed successfully")
