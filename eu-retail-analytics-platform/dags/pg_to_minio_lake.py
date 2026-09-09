"""
Daily pipeline:
  Postgres oltp → MinIO landing → MinIO raw (parquet) → ClickHouse marts
"""

from datetime import datetime, timedelta
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.append("/opt/airflow/src/ingestion")
from ingestion_engine import (
    extract_table_to_landing,
    convert_landing_to_raw_parquet,
    refresh_clickhouse_marts,
)

TABLES_TO_INGEST = [
    "stores",
    "products",
    "customers",
    "orders",
    "order_items",
    "payments",
]

default_args = {
    "owner": "retail_analytics",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="pg_to_minio_lakehouse",
    default_args=default_args,
    description="Ingest PostgreSQL OLTP → MinIO lake → ClickHouse marts",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ingestion", "lakehouse", "minio", "clickhouse"],
) as dag:

    extract_tasks = []
    convert_tasks = []

    for table in TABLES_TO_INGEST:
        extract_task = PythonOperator(
            task_id=f"extract_{table}_to_landing",
            python_callable=extract_table_to_landing,
            op_kwargs={"table_name": table, "ds": "{{ ds }}"},
        )
        convert_task = PythonOperator(
            task_id=f"convert_{table}_to_raw_parquet",
            python_callable=convert_landing_to_raw_parquet,
            op_kwargs={"table_name": table, "ds": "{{ ds }}"},
        )
        extract_task >> convert_task
        extract_tasks.append(extract_task)
        convert_tasks.append(convert_task)

    refresh_marts_task = PythonOperator(
        task_id="refresh_clickhouse_marts",
        python_callable=refresh_clickhouse_marts,
    )

    # All converts complete, then rebuild ClickHouse once
    convert_tasks >> refresh_marts_task
