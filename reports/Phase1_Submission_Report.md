# PulseIQ Phase 1 — Submission Report

## 1. Project overview
PulseIQ is a workforce and operational analytics project based on the supplied fictional Zenith Nova Technologies / Aura Workforce workbook. The source README identifies a data cut-off of **30 September 2026**.

## 2. Source inventory
- Workbook sheets exported to CSV: **30**
- Data dictionary rows: **371**
- Data contracts rows: **42**
- Metric dictionary rows: **28**
- DQ catalog rows: **14**

The full sheet-by-sheet inventory is in `source_inventory.csv`. Source tables are retained unchanged as CSV exports and the original workbook is included.

## 3. Implemented package components
1. **ETL:** CSV ingestion, column-name normalization, exact-duplicate quarantine, table profiles, audit log, and run metadata.
2. **Warehouse foundation:** PostgreSQL canonical dimension/fact DDL and illustrative monthly analytical views in `sql/warehouse.sql`.
3. **Data quality:** automated checks for exact duplicates, null employee identifiers, negative numeric values where fields can be inferred, ledger debit/credit equality when available, and payroll-to-employee referential integrity when fields can be inferred. Unresolved checks are marked `REVIEW`, not falsely marked as passed.
4. **Metric catalog:** workbook metric dictionary is preserved and available in the dashboard.
5. **Dashboard:** Streamlit app with KPI row counts, table explorer, headcount chart when numeric/date fields are detectable, metric dictionary, and DQ catalog.
6. **Packaging:** requirements, Dockerfile, tests, documentation, and source inventory.

## 4. Data-quality interpretation
Run `python src/quality_checks.py` to produce `outputs/dq_results.csv` and `outputs/dq_summary.json`. Results distinguish `PASS`, `FAIL`, and `REVIEW`. A `REVIEW` result means the expected field could not be safely inferred from the workbook's actual column names; it is not evidence of a pass.

The workbook's `dq_checks_catalog` is included in full. The implemented checks are a runnable baseline and should be mapped to every official catalog rule using the workbook's actual field names and business logic before representing the package as fully validated.

## 5. How to run
See the repository `README.md`. In brief:
- `pip install -r requirements.txt`
- `python src/etl_pipeline.py`
- `python src/quality_checks.py`
- `streamlit run app.py`
- `pytest -q`

## 6. Known limitations / evidence required
The original project starter ZIP, validation vault, and official report template were not present in the materials supplied in this chat. Accordingly:
- The SQL DDL is a canonical warehouse foundation; CSV headers must be mapped to it before loading.
- The 28 metric definitions are retained in the metric catalog, but their formulas must be implemented and reconciled individually against the official metric definitions before claiming all metrics are calculated.
- The DQ checks are a baseline; compare them with all 14 catalog checks and complete any domain-specific logic.
- This package does not include fabricated screenshots, claimed execution logs, or claims that tests have passed. Run the commands in the target environment and attach genuine outputs/screenshots if required by the assessor.

## 7. Deliverable structure
- `data/`: source workbook and CSV exports
- `src/`: ETL, quality checks, metric catalog helpers
- `sql/`: PostgreSQL warehouse foundation
- `app.py`: Streamlit dashboard
- `tests/`: smoke tests
- `reports/`: this report and source inventory
