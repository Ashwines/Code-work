# EU Retail Analytics Platform

End-to-end **data platform** for multi-region retail analytics (UAE + Europe).

Covers the full path from operational source data to lake storage, analytical marts, BI dashboards, and a GraphQL API for applications.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  Source: PostgreSQL (schema: oltp)                          │
│  customers · stores · products · orders · order_items ·     │
│  payments                                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Orchestration: Apache Airflow 3                            │
│  DAG: pg_to_minio_lakehouse                                 │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────┐    ┌─────────────────────────────┐
│  Data Lake (MinIO)       │    │  Analytics (ClickHouse)     │
│  landing → JSONL         │    │  lake_raw.*                 │
│  raw → Parquet           │    │  analytics_marts.*          │
└──────────────────────────┘    │  dims + fct_daily_sales     │
                                │  v_retail_executive_sales   │
                                └──────────────┬──────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                                                     ▼
        ┌───────────────────────┐                         ┌───────────────────────┐
        │  Apache Superset      │                         │  Hasura GraphQL       │
        │  Executive dashboards │                         │  API on Postgres OLTP │
        └───────────────────────┘                         └───────────────────────┘

Tech stack













































LayerTechnologySource OLTPPostgreSQL 16OrchestrationApache Airflow 3.3Object storageMinIO (S3-compatible)Lake formatsJSONL (landing), Parquet (raw)Analytics DBClickHouse 24.xBIApache SupersetAPIHasura GraphQLContainersDocker ComposeSynthetic dataPython + Faker (EU/UAE regions)

What this project demonstrates

Medallion-style lake path (landing → raw) plus analytical marts
Separation of OLTP, lake, and warehouse/serve layers
Orchestrated daily pipeline with Airflow
Fast analytics on ClickHouse for BI
GraphQL access pattern for application consumers (Hasura)
Multi-region retail model (AE, GB, DE, FR, NL) and multi-currency


Services & ports








































ServiceURL / PortCredentialsAirflowhttp://localhost:8082See container logs (SimpleAuth)Supersethttp://localhost:8088admin / adminHasurahttp://localhost:8085Admin secret: hasura_admin_secretMinIO Consolehttp://localhost:9011minioadmin / minioadminPostgreslocalhost:5433retail / retailClickHouse HTTPhttp://localhost:8123default / clickhouse

Quick start
Bashgit clone https://github.com/Ashwines/Code-work.git
cd Code-work/eu-retail-analytics-platform

cp .env.example .env   # if present

docker compose build
docker compose up -d
Bootstrap databases (if volumes already existed)
Bashdocker compose exec postgres psql -U retail -d postgres -c "CREATE USER airflow WITH PASSWORD 'airflow';"
docker compose exec postgres psql -U retail -d postgres -c "CREATE DATABASE airflow OWNER airflow;"
docker compose exec postgres psql -U retail -d postgres -c "CREATE DATABASE superset_metadata OWNER retail;"
Seed retail data
Bashdocker compose run --rm data-seeder
Run the pipeline

Open Airflow → unpause pg_to_minio_lakehouse → Trigger
Confirm MinIO buckets landing / raw
Confirm ClickHouse:

Bashdocker compose exec clickhouse clickhouse-client --query "SELECT count() FROM analytics_marts.fct_daily_sales"
Superset

Add database URI, e.g.
clickhouse+http://default:clickhouse@clickhouse:8123/analytics_marts
Dataset: analytics_marts.v_retail_executive_sales
Build KPI + trend + breakdown charts

Hasura

Open console → admin secret hasura_admin_secret
Track schema oltp
Add relationships (orders ↔ customers, items, products, payments)
Query from the API (GraphiQL) tab — not SQL

graphqlquery {
  orders(limit: 5, order_by: { order_ts: desc }) {
    order_number
    order_status
    customer { full_name country_code }
    order_items { quantity line_total product { product_name } }
  }
}

Analytical model (ClickHouse)



































ObjectTypeGrain / roledim_customersDimensioncustomer_iddim_storesDimensionstore_iddim_productsDimensionproduct_idfct_daily_salesFactorder linev_retail_executive_salesViewdenormalized for BI

Repository layout
texteu-retail-analytics-platform/
├── dags/                      # Airflow DAGs
├── src/ingestion/             # Extract → lake → ClickHouse refresh
├── data_generator/            # Synthetic EU/UAE retail seeder
├── infra/postgres/init/       # OLTP schema + seed SQL
├── infra/clickhouse/init/     # CH bootstrap
├── dbt/                       # dbt scaffold (future models)
├── dashboards/                # Superset exports / screenshots
├── docs/                      # Architecture & Hasura notes
├── docker-compose.yml
├── Dockerfile.airflow
└── README.md

Design notes

Postgres is the system of record for operational retail data.
MinIO stores durable lake snapshots (audit / reprocessing).
ClickHouse serves fast aggregates for Superset.
Hasura exposes a governed GraphQL API without custom BFF code.
Airflow owns the scheduled contract between systems.


Status





































CapabilityStatusOLTP schema + multi-region seederDoneAirflow ingest to MinIODoneClickHouse marts + executive viewDoneSuperset connected to ClickHouseDoneHasura on OLTPDonedbt full modelsScaffold onlyExtra dashboards (Sales / Ops / Customer)Optional next

Possible extensions

dbt models replacing hand-written mart SQL
Refined lake layer and data quality checks
Additional Superset dashboards (customer, operations, product)
CI for compose/config validation
Kubernetes deployment (follow-up project)

text---

Commit and push when ready:

```bash
git add README.md
git commit -m "docs: portfolio README for EU retail analytics platform"
git push