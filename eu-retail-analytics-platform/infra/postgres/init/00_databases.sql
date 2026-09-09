-- Create roles/DBs for Airflow and Superset
-- Note: CREATE DATABASE cannot run inside a DO block; use simple statements.
-- If role/db already exists on re-run of a fresh volume only this file runs once.

CREATE ROLE airflow LOGIN PASSWORD 'airflow';

-- These run only on first empty data volume.
-- If init fails because objects exist, ignore and use manual commands in README.

CREATE DATABASE airflow OWNER airflow;
CREATE DATABASE superset_metadata OWNER retail;
