-- Optional ClickHouse bootstrap (HTTP init support varies by image).
-- Marts are primarily created by ingestion_engine.refresh_clickhouse_marts().

CREATE DATABASE IF NOT EXISTS lake_raw;
CREATE DATABASE IF NOT EXISTS analytics_marts;
