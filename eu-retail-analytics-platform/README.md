# EU Retail Analytics Platform

Architect-level retail analytics platform (EU + UAE):

**Postgres OLTP → MinIO lake → ClickHouse marts → Superset + Hasura**

## Stack

| Layer | Technology |
|-------|------------|
| Source OLTP | PostgreSQL 16 (`oltp` schema) |
| Orchestration | Apache Airflow 3.3.1 |
| Lake | MinIO (landing JSONL, raw Parquet) |
| Analytics | ClickHouse 24.x |
| GraphQL API | Hasura |
| BI | Apache Superset |
| Transform (next) | dbt (scaffold) |

## Quick start

```bash
cd eu-retail-analytics-platform
cp .env.example .env

# Build Airflow image with Python deps
docker compose build

docker compose up -d
```

### One-time DB bootstrap (if volumes already existed)

```bash
docker compose exec postgres psql -U retail -d retail_source -c "CREATE USER airflow WITH PASSWORD 'airflow';"
docker compose exec postgres psql -U retail -d retail_source -c "CREATE DATABASE airflow OWNER airflow;"
docker compose exec postgres psql -U retail -d retail_source -c "CREATE DATABASE superset_metadata OWNER retail;"
```

### Seed data

```bash
docker compose run --rm data-seeder
```

### Run pipeline

1. Open Airflow: http://localhost:8082  
2. Trigger DAG: `pg_to_minio_lakehouse`  
3. Check MinIO: http://localhost:9011  
4. Superset: http://localhost:8088 (admin / admin)  
5. Hasura: http://localhost:8085  

### ClickHouse check

```bash
docker compose exec clickhouse clickhouse-client --query "SHOW TABLES FROM analytics_marts"
```

## Ports

| Service | Port |
|---------|------|
| Postgres | 5433 |
| MinIO | 9010 / 9011 |
| ClickHouse | 8123 |
| Airflow | 8082 |
| Hasura | 8085 |
| Superset | 8088 |

## Project layout

See `docs/architecture.md`.

## Status

- [x] Source schema + seeder  
- [x] MinIO landing/raw ingest  
- [x] ClickHouse lake_raw + marts (from Postgres sync)  
- [x] Airflow DAG  
- [x] Superset + Hasura in compose  
- [ ] dbt models (scaffold only)  
- [ ] Full multi-dashboard suite  
- [ ] Hasura metadata in git  
