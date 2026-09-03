"""
Olist Raw Layer Ingestion DAG
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="olist_raw_ingestion",
    default_args=default_args,
    description="Ingest Olist CSVs from landing to raw layer",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["olist", "raw"],
) as dag:

    ingest_raw = BashOperator(
        task_id="ingest_to_raw",
        bash_command="""
        export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
        cd /opt/airflow
        python -m src.jobs.raw.ingest_to_raw
        """,
    )