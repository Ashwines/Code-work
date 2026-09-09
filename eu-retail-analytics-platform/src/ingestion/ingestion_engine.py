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

# MinIO Client Configuration
S3_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://minio:9000")
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

# Postgres Configuration
PG_HOST = os.getenv("SOURCE_DB_HOST", "postgres")
PG_PORT = int(os.getenv("SOURCE_DB_PORT", 5432))
PG_DB = os.getenv("SOURCE_DB_NAME", "retail_source")
PG_USER = os.getenv("SOURCE_DB_USER", "retail")
PG_PASS = os.getenv("SOURCE_DB_PASSWORD", "retail")

# ClickHouse Configuration
CH_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CH_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", 8123))
CH_USER = os.getenv("CLICKHOUSE_USER", "default")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "clickhouse")


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def extract_table_to_landing(table_name: str, ds: str) -> str:
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )
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
            elif hasattr(v, "__float__"):
                record[k] = float(v)
        record["_ingested_at"] = now_iso
        record["_source_table"] = f"oltp.{table_name}"
        lines.append(json.dumps(record))

    payload = "\n".join(lines).encode("utf-8")
    s3_key = f"oltp/{table_name}/snapshot_date={ds}/data.jsonl"

    s3 = get_s3_client()
    s3.put_object(Bucket="landing", Key=s3_key, Body=payload)
    print(f"Extracted {len(rows)} records from oltp.{table_name} to landing/{s3_key}")
    return s3_key


def convert_landing_to_raw_parquet(table_name: str, ds: str):
    s3 = get_s3_client()
    landing_key = f"oltp/{table_name}/snapshot_date={ds}/data.jsonl"
    obj = s3.get_object(Bucket="landing", Key=landing_key)
    body = obj["Body"].read().decode("utf-8")

    records = [json.loads(line) for line in body.strip().split("\n") if line.strip()]
    if not records:
        print(f"No records found for {table_name}")
        return

    arrow_table = pa.Table.from_pylist(records)
    parquet_buffer = pa.BufferOutputStream()
    pq.write_table(arrow_table, parquet_buffer, compression="snappy")

    raw_key = f"oltp/{table_name}/ingestion_date={ds}/data.parquet"
    s3.put_object(Bucket="raw", Key=raw_key, Body=parquet_buffer.getvalue().to_pybytes())
    print(f"Converted landing to raw/{raw_key} with {arrow_table.num_rows} rows.")


def refresh_clickhouse_marts():
    client = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD
    )

    client.command("CREATE DATABASE IF NOT EXISTS analytics_marts;")

    queries = [
        # dim_customers
        """
        CREATE TABLE IF NOT EXISTS analytics_marts.dim_customers ENGINE = MergeTree()
        ORDER BY customer_id AS
        SELECT assumeNotNull(toInt64(customer_id)) AS customer_id,
               customer_code, full_name, email, city, country_code,
               parseDateTimeBestEffortOrNull(created_at) AS created_at
        FROM lake_raw.raw_customers WHERE customer_id IS NOT NULL;
        """,
        # dim_stores
        """
        CREATE TABLE IF NOT EXISTS analytics_marts.dim_stores ENGINE = MergeTree()
        ORDER BY store_id AS
        SELECT assumeNotNull(toInt64(store_id)) AS store_id,
               store_code, store_name, city, country_code
        FROM lake_raw.raw_stores WHERE store_id IS NOT NULL;
        """,
        # dim_products
        """
        CREATE TABLE IF NOT EXISTS analytics_marts.dim_products ENGINE = MergeTree()
        ORDER BY product_id AS
        SELECT assumeNotNull(toInt64(product_id)) AS product_id,
               sku, product_name, category,
               round(unit_price, 2) AS unit_price,
               toUInt8(active) AS is_active
        FROM lake_raw.raw_products WHERE product_id IS NOT NULL;
        """,
        # fct_daily_sales
        """
        CREATE TABLE IF NOT EXISTS analytics_marts.fct_daily_sales ENGINE = MergeTree()
        PARTITION BY toYYYYMM(order_ts)
        ORDER BY (store_id, product_id, order_ts) AS
        SELECT assumeNotNull(toInt64(oi.order_item_id)) AS order_item_id,
               assumeNotNull(toInt64(o.order_id)) AS order_id,
               toInt64(o.customer_id) AS customer_id,
               assumeNotNull(toInt64(o.store_id)) AS store_id,
               assumeNotNull(toInt64(oi.product_id)) AS product_id,
               assumeNotNull(parseDateTimeBestEffort(o.order_ts)) AS order_ts,
               toDate(parseDateTimeBestEffort(o.order_ts)) AS order_date,
               o.order_status, o.currency_code,
               toInt32(oi.quantity) AS quantity,
               round(oi.unit_price, 2) AS unit_price,
               round(oi.line_total, 2) AS line_total,
               p.payment_method, p.payment_status
        FROM lake_raw.raw_orders AS o
        INNER JOIN lake_raw.raw_order_items AS oi ON o.order_id = oi.order_id
        LEFT JOIN lake_raw.raw_payments AS p ON o.order_id = p.order_id
        WHERE o.order_id IS NOT NULL;
        """
    ]

    for q in queries:
        client.command(q)
    print("ClickHouse analytical marts successfully synced.")