# BFSI Data Engineering Project

A hands-on data engineering project for a **Banking, Financial Services, and Insurance (BFSI)**
data warehouse. The project implements a multi-layer ETL pipeline that moves data from
raw CSV sources through **Staging → ODS → EDW → Data Marts**, following a traditional
Inmon-style enterprise data warehouse architecture.

## 📂 Project Structure

```
BFSI/
├── README.md                     # This file
├── .gitignore
├── requirements.txt              # Python dependencies
├── config/
│   └── (pipeline configuration)
├── data/
│   ├── raw/                      # Original source CSV files (9 files)
│   ├── staging/                  # Staging layer output (intermediate CSVs)
│   └── edw/                      # EDW / data mart output (final deliverables)
├── ddl/
│   ├── bfsi_ddl.sql              # MySQL DDL (original)
│   └── bfsi_ddl_sqlite.sql       # SQLite-compatible DDL
├── docs/
│   ├── DFD Diagram.png           # Data Flow Diagram
│   ├── Conceptual Data Model.png # High-level conceptual model
│   └── Logical ER Diagram.png    # Detailed logical entity-relationship
├── notebooks/                    # Exploratory data analysis
├── src/
│   ├── pipelines/                # Layer-by-layer ETL orchestration scripts
│   ├── transforms/               # Pure transformation functions (unit-testable)
│   └── utils/                    # Shared utilities (logging, DB, validation)
└── tests/                        # Unit and integration tests
```

## 🗃️ Data Sources (in `data/raw/`)

| File              | Description                          |
|-------------------|--------------------------------------|
| `accounts.csv`    | Customer bank accounts               |
| `branches.csv`    | Branch locations                     |
| `creditcard.csv`  | Credit card accounts                 |
| `cust.csv`        | Customer profiles                    |
| `employee.csv`    | Branch employees                     |
| `loans.csv`       | Loan accounts                        |
| `payments.csv`    | Payment transactions                 |
| `transactions.csv`| General ledger / account transactions|
| `movies.csv`      | *(Duplicate of transactions — see notes)* |

> **Note:** `movies.csv` contains identical columns to `transactions.csv` and appears
> to be a naming artifact in the source dataset. It is retained in `data/raw/` but
> not used in the pipeline.

## 🏗️ Architecture

The warehouse follows a **3NF bottom-up / Inmon-style hybrid** layered design:

1. **Staging (`stg_*`)** — Raw CSV data loaded with cleaning (whitespace stripping,
   type casting, column-name standardisation).
2. **ODS (`ods_*`)** — Cleansed, integrated layer. Adds `load_dt` / `load_ts`
   metadata columns for traceability.
3. **EDW (`dim_*` / `fact_*`)** — Enterprise Data Warehouse with conformed
   dimensions (customers, branches, employees, loans) and the `fact_loans`
   fact table. `dim_branches` uses **SCD Type 2** (`start_date`, `end_date`,
   `is_current`).
4. **Data Marts (`*_mart`)** — Subject-area fact tables:
   - `trans_mart.fact_transactions`  — transactions with a `transaction_flag`
   - `payment_mart.fact_payments`      — payments enriched with `AmountInBaseCurrency`
   - `cc_mart.fact_creditcard`         — credit-card facts with `utilization_percent`

## ⚙️ Quick Start

```bash
cd BFSI
pip install -r requirements.txt

# Run the full pipeline (local SQLite DW)
python -m src.pipelines.run_pipeline

# Run a single layer
python -m src.pipelines.01_staging_pipeline
python -m src.pipelines.02_ods_pipeline
python -m src.pipelines.03_edw_pipeline
python -m src.pipelines.04_mart_pipeline

# Run tests
pytest tests/ -v
```

## 🛠️ Tech Stack

| Category   | Tool / Library  |
|------------|-----------------|
| Language   | Python 3.13     |
| Dataframes | pandas / numpy  |
| Database   | SQLite (local) / MySQL (target) |
| ORM        | SQLAlchemy 2.0  |
| Config     | YAML            |
| Testing    | pytest          |

## 📊 Key Transformations

- **Staging** — Column-name standardisation, whitespace trimming, type casting,
  null handling (`'null'` strings → `None`).
- **ODS** — Additive load metadata (`load_dt`, `load_ts`).
- **EDW** — Dimension builds from ODS, SCD Type-2 for `dim_branches`,
  derived columns in `fact_loans` (`LoanDurationMonths`, `RiskIndicator`,
  `HighValueFlag`, `OutstandingBalance`).
- **Data Marts** — Enrichment joins and derived metrics (e.g.
  `AmountInBaseCurrency = Amount * ExchangeRate`,
  `utilization_percent = Balance / CreditLimit * 100`).
