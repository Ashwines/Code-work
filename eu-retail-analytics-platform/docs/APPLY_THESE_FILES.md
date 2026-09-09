# How to apply these files into your GitHub repo

Copy everything under this folder into:

```text
Code-work/eu-retail-analytics-platform/
```

Overwrite when paths match.

## Required compose edits

In `docker-compose.yml`, change the Airflow image block:

**From:**
```yaml
image: olist-airflow:3.3.1
```

**To:**
```yaml
build:
  context: .
  dockerfile: Dockerfile.airflow
image: eu-retail-airflow:3.3.1
```

Add ClickHouse env to Airflow common environment:

```yaml
CLICKHOUSE_HOST: clickhouse
CLICKHOUSE_HTTP_PORT: "8123"
CLICKHOUSE_USER: default
CLICKHOUSE_PASSWORD: clickhouse
```

## After copy

```bash
cd eu-retail-analytics-platform
docker compose down
docker compose build
docker compose up -d

# Create Airflow + Superset DBs if volume already exists
docker compose exec postgres psql -U retail -d postgres -c "CREATE USER airflow WITH PASSWORD 'airflow';" || true
docker compose exec postgres psql -U retail -d postgres -c "CREATE DATABASE airflow OWNER airflow;" || true
docker compose exec postgres psql -U retail -d postgres -c "CREATE DATABASE superset_metadata OWNER retail;" || true

docker compose run --rm data-seeder
# Trigger DAG pg_to_minio_lakehouse in Airflow UI (port 8082)
```

## Files included

| Path | Purpose |
|------|---------|
| `Dockerfile.airflow` | Standalone Airflow image with deps |
| `infra/postgres/init/00_databases.sql` | airflow + superset_metadata DBs |
| `infra/postgres/init/00_databases_simple.sql` | Manual fallback SQL |
| `infra/clickhouse/init/01_databases.sql` | CH databases |
| `src/ingestion/ingestion_engine.py` | Fixed lake + CH marts |
| `dags/pg_to_minio_lake.py` | DAG waits for all converts then refresh |
| `docs/architecture.md` | Architecture notes |
| `README.md` | Updated runbook |
| `dbt/*` | Scaffold only |

## Verify

```bash
docker compose exec clickhouse clickhouse-client --query "SELECT count() FROM analytics_marts.fct_daily_sales"
```
