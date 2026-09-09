-- Simpler init (no \gexec). Prefer this file if 00_databases.sql fails on init.
-- Rename to 00_databases.sql after removing the other, OR run manually once:

-- docker compose exec postgres psql -U retail -d retail_source -f /tmp/00_databases_simple.sql

CREATE ROLE airflow LOGIN PASSWORD 'airflow';
-- ignore error if role exists

CREATE DATABASE airflow OWNER airflow;
CREATE DATABASE superset_metadata OWNER retail;
