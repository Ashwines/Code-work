"""
Raw Layer Job
-------------
Reads CSV files from landing and writes them as Delta tables to the raw layer in MinIO.
"""

from pyspark.sql import SparkSession
from src.utils.spark_session import get_spark_session
import os


# List of Olist tables
OLIST_TABLES = [
    "olist_orders_dataset",
    "olist_order_items_dataset",
    "olist_order_payments_dataset",
    "olist_order_reviews_dataset",
    "olist_customers_dataset",
    "olist_products_dataset",
    "olist_sellers_dataset",
    "olist_geolocation_dataset",
    "product_category_name_translation",
]


def ingest_table(spark: SparkSession, table_name: str) -> None:
    """Read one CSV from landing and write it to raw as Delta."""

    landing_path = f"/opt/airflow/data/landing/{table_name}.csv"
    raw_path = f"/opt/airflow/data/raw/{table_name}"   # local path instead of s3a

    print(f"Ingesting: {table_name}")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(landing_path)
    )

    # Add metadata columns (professional practice)
    from pyspark.sql import functions as F
    df = (
        df
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.lit(f"{table_name}.csv"))
    )

    (
    df.write
    .mode("overwrite")
    .parquet(raw_path)
)

    print(f"Successfully written to: {raw_path}")
    print(f"Row count: {df.count()}")


def main():
    spark = get_spark_session("olist-raw-ingestion")

    for table in OLIST_TABLES:
        try:
            ingest_table(spark, table)
        except Exception as e:
            print(f"Failed to ingest {table}: {str(e)}")
            raise

    spark.stop()
    print("Raw layer ingestion completed successfully.")


if __name__ == "__main__":
    main()