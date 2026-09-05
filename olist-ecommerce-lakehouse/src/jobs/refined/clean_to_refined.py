"""
Refined Layer Job
-----------------
Reads Delta tables from raw, cleans them, writes to refined (Delta on MinIO).
"""

from pyspark.sql import functions as F
from src.utils.spark_session import get_spark_session


# Tables to process (same as raw)
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


def clean_orders(df):
    """Example cleaning for orders."""
    return (
        df
        .dropDuplicates(["order_id"])
        .withColumn("order_purchase_timestamp", F.to_timestamp("order_purchase_timestamp"))
        .withColumn("order_approved_at", F.to_timestamp("order_approved_at"))
        .withColumn("order_delivered_carrier_date", F.to_timestamp("order_delivered_carrier_date"))
        .withColumn("order_delivered_customer_date", F.to_timestamp("order_delivered_customer_date"))
        .withColumn("order_estimated_delivery_date", F.to_timestamp("order_estimated_delivery_date"))
        .withColumn("_refined_at", F.current_timestamp())
    )


def clean_generic(df, primary_keys=None):
    """Basic cleaning for other tables."""
    if primary_keys:
        df = df.dropDuplicates(primary_keys)
    return df.withColumn("_refined_at", F.current_timestamp())


CLEANERS = {
    "olist_orders_dataset": lambda df: clean_orders(df),
    "olist_order_items_dataset": lambda df: clean_generic(df, ["order_id", "order_item_id"]),
    "olist_order_payments_dataset": lambda df: clean_generic(df, ["order_id", "payment_sequential"]),
    "olist_order_reviews_dataset": lambda df: clean_generic(df, ["review_id"]),
    "olist_customers_dataset": lambda df: clean_generic(df, ["customer_id"]),
    "olist_products_dataset": lambda df: clean_generic(df, ["product_id"]),
    "olist_sellers_dataset": lambda df: clean_generic(df, ["seller_id"]),
    "olist_geolocation_dataset": lambda df: clean_generic(df),
    "product_category_name_translation": lambda df: clean_generic(df, ["product_category_name"]),
}


def process_table(spark, table_name: str) -> None:
    raw_path = f"s3a://raw/{table_name}"
    refined_path = f"s3a://refined/{table_name}"

    print(f"Refining: {table_name}")

    df = spark.read.format("delta").load(raw_path)
    cleaner = CLEANERS.get(table_name, lambda d: clean_generic(d))
    df_clean = cleaner(df)

    (
        df_clean.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(refined_path)
    )

    print(f"Written to: {refined_path} | rows: {df_clean.count()}")


def main():
    spark = get_spark_session("olist-refined")

    for table in OLIST_TABLES:
        try:
            process_table(spark, table)
        except Exception as e:
            print(f"Failed {table}: {e}")
            raise

    spark.stop()
    print("Refined layer completed.")


if __name__ == "__main__":
    main()