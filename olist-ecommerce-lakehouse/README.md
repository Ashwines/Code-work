# Olist E-Commerce Data Lakehouse

End-to-end **Data Engineering** project built on the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

Demonstrates a practical **medallion architecture** (landing → raw → refined → marts) with orchestration, object storage, and analytics-ready star schema tables.

---

## Architecture

```text
Local CSVs
    │
    ▼
┌─────────────────┐
│  landing (MinIO)│  CSV objects
└────────┬────────┘
         ▼
┌─────────────────┐
│  raw (Delta)    │  Append-style ingest + metadata
└────────┬────────┘
         ▼
┌─────────────────┐
│ refined (Delta) │  Cleaned, typed, deduplicated
└────────┬────────┘
         ▼
┌─────────────────┐
│  marts (Delta)  │  Star schema (dims + fact)
└─────────────────┘

Orchestration: Apache Airflow 3

Processing: PySpark (local) + Delta Lake

Storage: MinIO (S3-compatible)

Metadata DB: PostgreSQL

Tech Stack

































LayerTechnologyOrchestrationApache Airflow 3.3.1ComputePySpark 3.5 + Delta LakeObject storageMinIOMetadataPostgreSQL 16ContainersDocker + Docker ComposeLanguagePython 3.12

Marts (Star Schema)






























TableTypeDescriptiondim_customerDimensionCustomer attributesdim_productDimensionProducts + English categorydim_sellerDimensionSeller location attributesfact_order_itemsFactOrder line items + payment stats

Project Structure
textolist-ecommerce-lakehouse/
├── dags/
│   └── olist_lakehouse_dag.py      # landing → raw → refined → marts
├── src/
│   ├── jobs/
│   │   ├── landing/                # Upload CSVs to MinIO
│   │   ├── raw/                    # CSV → Delta (raw)
│   │   ├── refined/                # Clean / type / dedupe
│   │   └── marts/                  # Star schema
│   └── utils/
│       └── spark_session.py        # Spark + Delta + MinIO config
├── data/landing/                   # Place Olist CSVs here first
├── docker-compose.yml
├── Dockerfile                      # Airflow + Java + PySpark
├── .env.example
└── README.md

Prerequisites

Docker Desktop (running)
Git
~8–10 GB free disk (images + data)


Quick Start
1. Clone
Bashgit clone https://github.com/Ashwines/Code-work.git
cd Code-work/olist-ecommerce-lakehouse
2. Environment
Bashcp .env.example .env
3. Dataset

Download from Kaggle – Brazilian E-Commerce (Olist)
Extract all CSV files into data/landing/

4. Start the stack
Bashdocker compose up -d --build
First build may take several minutes (Java + PySpark image).
5. Access services




















ServiceURLCredentialsAirflow UIhttp://localhost:8080See container logs for SimpleAuth password (admin)MinIO Consolehttp://localhost:9001minioadmin / minioadmin
Tip: password is printed in api-server logs on first start:
docker logs <airflow-api-server-container> 2>&1 | findstr Password
6. Run the pipeline

Open Airflow UI
Unpause DAG: olist_lakehouse_pipeline
Trigger DAG

Tasks run in order:
textupload_to_landing → ingest_to_raw → clean_to_refined → build_marts
7. Verify in MinIO
Buckets should contain:

landing → CSV files
raw → Delta tables
refined → cleaned Delta tables
marts → dim_* and fact_order_items


Day-to-day commands
Bash# Start
docker compose up -d

# Stop (keep data)
docker compose down

# Reset DB + MinIO volumes (destructive)
docker compose down -v

# Update after code changes
git pull
docker compose up -d --build

Design notes

Medallion layers separate ingest, cleaning, and analytics models
Delta Lake provides reliable table storage on object storage
MinIO mimics S3 for local development
Airflow orchestrates the full path as one pipeline
Jobs are modular (landing / raw / refined / marts) for clarity and reuse


Status
Core pipeline is complete and runnable locally with Docker.
Possible extensions: data quality checks, scheduled runs, more fact/dim tables, or a Kubernetes deployment in a follow-up project.
text---

Commit this to GitHub so recruiters see a clear story.

If you want, next we can do **option B (data quality checks)** or a short **“What I learned”** section for LinkedIn/GitHub.