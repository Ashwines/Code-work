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
```

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Source OLTP | PostgreSQL 16 |
| Orchestration | Apache Airflow 3.3 |
| Object storage | MinIO (S3-compatible) |
| Lake formats | JSONL (landing), Parquet (raw) |
| Analytics DB | ClickHouse 24.x |
| BI | Apache Superset |
| API | Hasura GraphQL |
| Containers | Docker Compose |
| Synthetic data | Python + Faker (EU/UAE regions) |

---

## What this project demonstrates

- Medallion-style lake path (landing → raw) plus analytical marts
- Separation of **OLTP**, **lake**, and **warehouse/serve** layers
- Orchestrated daily pipeline with Airflow
- Fast analytics on ClickHouse for BI
- GraphQL access pattern for application consumers (Hasura)
- Multi-region retail model (AE, GB, DE, FR, NL) and multi-currency

---

## Services & ports

| Service | URL / Port | Credentials |
|---------|------------|-------------|
| Airflow | http://localhost:8082 | See container logs (SimpleAuth) |
| Superset | http://localhost:8088 | `admin` / `admin` |
| Hasura | http://localhost:8085 | Admin secret: `hasura_admin_secret` |
| MinIO Console | http://localhost:9011 | `minioadmin` / `minioadmin` |
| Postgres | localhost:5433 | `retail` / `retail` |
| ClickHouse HTTP | http://localhost:8123 | `default` / `clickhouse` |

---

## Quick start

```bash
git clone https://github.com/Ashwines/Code-work.git
cd Code-work/eu-retail-analytics-platform

cp .env.example .env   # if present

docker compose build
docker compose up -d
```

### Bootstrap databases (if volumes already existed)

```bash
docker compose exec postgres psql -U retail -d postgres -c "CREATE USER airflow WITH PASSWORD 'airflow';"
docker compose exec postgres psql -U retail -d postgres -c "CREATE DATABASE airflow OWNER airflow;"
docker compose exec postgres psql -U retail -d postgres -c "CREATE DATABASE superset_metadata OWNER retail;"
```

### Seed retail data

```bash
docker compose run --rm data-seeder
```

### Run the pipeline

1. Open Airflow → unpause **`pg_to_minio_lakehouse`** → Trigger
2. Confirm MinIO buckets `landing` / `raw`
3. Confirm ClickHouse:

```bash
docker compose exec clickhouse clickhouse-client --query "SELECT count() FROM analytics_marts.fct_daily_sales"
```

### Superset

1. Add database URI, e.g.
   `clickhouse+http://default:clickhouse@clickhouse:8123/analytics_marts`
2. Dataset: `analytics_marts.v_retail_executive_sales`
3. Build KPI + trend + breakdown charts

### Hasura

1. Open console → admin secret `hasura_admin_secret`
2. Track schema **`oltp`**
3. Add relationships (orders ↔ customers, items, products, payments)
4. Query from the **API** (GraphiQL) tab — not SQL

```graphql
query {
  orders(limit: 5, order_by: { order_ts: desc }) {
    order_number
    order_status
    customer { full_name country_code }
    order_items { quantity line_total product { product_name } }
  }
}
```

---

## Analytical model (ClickHouse)

| Object | Type | Grain / role |
|--------|------|----------------|
| `dim_customers` | Dimension | customer_id |
| `dim_stores` | Dimension | store_id |
| `dim_products` | Dimension | product_id |
| `fct_daily_sales` | Fact | order line |
| `v_retail_executive_sales` | View | denormalized for BI |

---

## Repository layout

```text
eu-retail-analytics-platform/
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
```

---

## Design notes

- **Postgres** is the system of record for operational retail data.
- **MinIO** stores durable lake snapshots (audit / reprocessing).
- **ClickHouse** serves fast aggregates for Superset.
- **Hasura** exposes a governed GraphQL API without custom BFF code.
- Airflow owns the scheduled contract between systems.

---

## Status

| Capability | Status |
|------------|--------|
| OLTP schema + multi-region seeder | Done |
| Airflow ingest to MinIO | Done |
| ClickHouse marts + executive view | Done |
| Superset connected to ClickHouse | Done |
| Hasura on OLTP | Done |
| dbt full models | Scaffold only |
| Extra dashboards (Sales / Ops / Customer) | Optional next |

---

## Possible extensions

- dbt models replacing hand-written mart SQL
- Refined lake layer and data quality checks
- Additional Superset dashboards (customer, operations, product)
- CI for compose/config validation
- Kubernetes deployment (follow-up project)
