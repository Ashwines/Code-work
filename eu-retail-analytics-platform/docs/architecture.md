# Architecture — EU Retail Analytics Platform

## Overview

Multi-source style retail analytics platform for EU + UAE operations:

- **OLTP source**: PostgreSQL (`oltp` schema)
- **Lake**: MinIO (`landing` JSONL, `raw` Parquet)
- **Analytics**: ClickHouse (`lake_raw`, `analytics_marts`)
- **Orchestration**: Apache Airflow 3
- **API**: Hasura GraphQL on Postgres
- **BI**: Apache Superset on ClickHouse

## Data flow

```text
Postgres (oltp.*)
    │
    ├─(Airflow extract)──► MinIO landing (JSONL)
    │                           │
    │                      convert
    │                           ▼
    │                      MinIO raw (Parquet)
    │
    └─(Airflow refresh)──► ClickHouse lake_raw.*
                                │
                                ▼
                           analytics_marts.*
                           (dims + fct_daily_sales + executive view)
                                │
                    ┌───────────┴────────────┐
                    ▼                        ▼
              Apache Superset            (future dbt models)
              dashboards
```

Hasura exposes Postgres `oltp` (and later serve views) via GraphQL for applications.

## Key metrics

| Metric | Definition |
|--------|------------|
| Revenue / GMV | Sum of `line_total` on completed/shipped sales |
| Orders | Count distinct `order_id` |
| AOV | Revenue / Orders |
| Units | Sum of `quantity` |

## Services (local ports)

| Service | Host port |
|---------|-----------|
| Postgres | 5433 |
| MinIO API / Console | 9010 / 9011 |
| ClickHouse HTTP | 8123 |
| Hasura | 8085 |
| Superset | 8088 |
| Airflow | 8082 |
