"""
Olist Lakehouse DAG
-------------------
landing (CSV → MinIO) → raw (Delta) → refined (Delta)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

JAVA_ENV = "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64"

with DAG(
    dag_id="olist_lakehouse_pipeline",
    default_args=default_args,
    description="Olist medallion pipeline: landing → raw → refined",
    schedule=None,  # manual trigger for now
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["olist", "lakehouse", "minio", "delta"],
) as dag:

    landing = BashOperator(
        task_id="upload_to_landing",
        bash_command=f"""
        {JAVA_ENV}
        cd /opt/airflow
        python -m src.jobs.landing.upload_to_landing
        """,
    )

    raw = BashOperator(
        task_id="ingest_to_raw",
        bash_command=f"""
        {JAVA_ENV}
        cd /opt/airflow
        python -m src.jobs.raw.ingest_to_raw
        """,
    )

    refined = BashOperator(
        task_id="clean_to_refined",
        bash_command=f"""
        {JAVA_ENV}
        cd /opt/airflow
        python -m src.jobs.refined.clean_to_refined
        """,
    )

    marts = BashOperator(
    task_id="build_marts",
    bash_command=f"""
    {JAVA_ENV}
    cd /opt/airflow
    python -m src.jobs.marts.build_marts
    """,
    )

    landing >> raw >> refined >> marts