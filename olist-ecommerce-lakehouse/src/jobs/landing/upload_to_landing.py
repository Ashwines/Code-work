"""
Landing Layer Job
-----------------
Uploads local CSV files to MinIO landing bucket.
"""

import os
from pathlib import Path

import boto3
from botocore.client import Config


LANDING_DIR = Path("/opt/airflow/data/landing")
BUCKET = "landing"

OLIST_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv",
]


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL", "http://minio:9000"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def upload_file(s3, file_name: str) -> None:
    local_path = LANDING_DIR / file_name
    if not local_path.exists():
        raise FileNotFoundError(f"Missing file: {local_path}")

    key = file_name
    print(f"Uploading {file_name} → s3://{BUCKET}/{key}")
    s3.upload_file(str(local_path), BUCKET, key)
    print(f"Uploaded: {file_name}")


def main():
    s3 = get_s3_client()

    # Ensure bucket exists
    try:
        s3.head_bucket(Bucket=BUCKET)
    except Exception:
        print(f"Creating bucket: {BUCKET}")
        s3.create_bucket(Bucket=BUCKET)

    for file_name in OLIST_FILES:
        upload_file(s3, file_name)

    print("Landing upload completed.")


if __name__ == "__main__":
    main()