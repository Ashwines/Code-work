"""
Marts Layer Job
---------------
Builds star schema tables from refined layer into s3a://marts/ (Delta).
"""

from pyspark.sql import functions as F
from src.utils.spark_session import get_spark_session


def read_refined(spark, table: str):
    return spark.read.format("delta").load(f"s3a://refined/{table}")


def write_mart(df, name: str):
    path = f"s3a://marts/{name}"
    (
        df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(path)
    )
    print(f"Mart written: {path} | rows={df.count()}")


def build_dim_customer(spark):
    customers = read_refined(spark, "olist_customers_dataset")
    return (
        customers
        .select(
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        )
        .dropDuplicates(["customer_id"])
        .withColumn("updated_at", F.current_timestamp())
    )


def build_dim_product(spark):
    products = read_refined(spark, "olist_products_dataset")
    translation = read_refined(spark, "product_category_name_translation")

    return (
        products
        .join(translation, on="product_category_name", how="left")
        .select(
            "product_id",
            "product_category_name",
            "product_category_name_english",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        )
        .dropDuplicates(["product_id"])
        .withColumn("updated_at", F.current_timestamp())
    )


def build_dim_seller(spark):
    sellers = read_refined(spark, "olist_sellers_dataset")
    return (
        sellers
        .select(
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        )
        .dropDuplicates(["seller_id"])
        .withColumn("updated_at", F.current_timestamp())
    )


def build_fact_order_items(spark):
    orders = read_refined(spark, "olist_orders_dataset")
    items = read_refined(spark, "olist_order_items_dataset")
    payments = read_refined(spark, "olist_order_payments_dataset")

    # Total payment per order
    pay = (
        payments
        .groupBy("order_id")
        .agg(
            F.sum("payment_value").alias("total_payment_value"),
            F.count("*").alias("payment_count"),
        )
    )

    fact = (
        items
        .join(orders, on="order_id", how="inner")
        .join(pay, on="order_id", how="left")
        .select(
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "price",
            "freight_value",
            (F.col("price") + F.col("freight_value")).alias("item_total"),
            "total_payment_value",
            "payment_count",
        )
        .withColumn("loaded_at", F.current_timestamp())
    )
    return fact


def main():
    spark = get_spark_session("olist-marts")

    print("Building dim_customer...")
    write_mart(build_dim_customer(spark), "dim_customer")

    print("Building dim_product...")
    write_mart(build_dim_product(spark), "dim_product")

    print("Building dim_seller...")
    write_mart(build_dim_seller(spark), "dim_seller")

    print("Building fact_order_items...")
    write_mart(build_fact_order_items(spark), "fact_order_items")

    spark.stop()
    print("Marts layer completed.")


if __name__ == "__main__":
    main()