# Olist E-Commerce Data Lakehouse

Professional end-to-end Data Engineering project using the **Brazilian E-Commerce Public Dataset by Olist**.

## Architecture
Landing (CSV files)
↓
raw         → Minimal processing + metadata (Delta Lake)
↓
refined       → Cleaned, typed, deduplicated, quality checked
↓
marts        → Star Schema (Facts + Dimensions) - Analytics ready


## Tech Stack

| Layer              | Technology                     |
|--------------------|--------------------------------|
| Orchestration      | Apache Airflow 3.3.1           |
| Processing         | PySpark (local) + Delta Lake   |
| Object Storage     | MinIO (S3-compatible)          |
| Metadata DB        | PostgreSQL 16                  |
| CI/CD              | GitHub Actions                 |
| Language           | Python 3.12                    |
| Containerization   | Docker + Docker Compose        |

## Prerequisites

- Docker Desktop installed and running
- Git installed

## Quick Start

### 1. Clone the repository

git clone https://github.com/Ashwines/Code-work.git
cd Code-work/olist-ecommerce-lakehouse