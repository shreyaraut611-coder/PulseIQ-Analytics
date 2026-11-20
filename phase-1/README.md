# Phase 1 — Data Foundations and Governance (Days 1–5)

PulseIQ is one application that grows phase by phase, so the code stays at the repository root (moving it would break the live app and the automated tests). This folder is the index for Phase 1: what was built and where to find it.

## What was built
- Export of all 30 workbook sheets to CSV, profiling, audit log and run metadata
- Data-quality checks with PASS / FAIL / REVIEW results
- Quarantine of bad rows (kept and labelled, never silently deleted)
- PostgreSQL warehouse foundation (star-schema DDL)
- Metric dictionary and DQ catalog kept from the workbook

## Files for this phase
| File | Purpose |
|---|---|
| [`src/etl_pipeline.py`](../src/etl_pipeline.py) | Ingestion, normalisation, quarantine, audit |
| [`src/quality_checks.py`](../src/quality_checks.py) | Data-quality checks |
| [`src/metrics.py`](../src/metrics.py) | Metric catalog helpers |
| [`sql/warehouse.sql`](../sql/warehouse.sql) | Warehouse DDL and views |
| [`data/PulseIQ_Dataset.xlsx`](../data/PulseIQ_Dataset.xlsx), [`data/tables/`](../data/tables) | Source workbook and CSV exports |
| [`tests/test_smoke.py`](../tests/test_smoke.py) | Smoke tests |

## Report
- [Phase 1 report (PDF)](../reports/Phase1_Submission_Report.pdf) · [Markdown](../reports/Phase1_Submission_Report.md)
- [Source inventory](../reports/source_inventory.csv)

## Run
```bash
pip install -r requirements.txt
python src/etl_pipeline.py
python src/quality_checks.py
```
