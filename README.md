# PulseIQ Analytics — Complete Submission Package

## What's included
- `data/PulseIQ_Dataset.xlsx`: original supplied workbook.
- `data/tables/*.csv`: one CSV export per workbook sheet, including the dictionaries, contracts, DQ catalog, dimensions, and facts.
- `src/etl_pipeline.py`: ingestion, normalization, profiling, and quarantine/audit outputs.
- `src/quality_checks.py`: automated checks based on the workbook's DQ catalog, where the relevant fields can be inferred.
- `src/metrics.py`: metric catalog loader and metric evaluation helpers.
- `app.py`: Streamlit dashboard over the exported source tables.
- `sql/warehouse.sql`: PostgreSQL staging/star-schema foundation and example analytical views.
- `tests/`: smoke tests.
- `reports/Phase1_Submission_Report.md`: report and implementation notes.
- `reports/source_inventory.csv`: workbook sheet inventory.

## Run locally (Windows)
1. Install Python 3.11+.
2. Open a terminal in this folder.
3. Create an environment and install dependencies:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run ETL and quality checks:
   ```bash
   python src/etl_pipeline.py
   python src/quality_checks.py
   ```
5. Start the dashboard:
   ```bash
   streamlit run app.py
   ```

## Important integrity note
This package is generated from the provided `PulseIQ_Dataset.xlsx`. The original starter ZIP, validation vault, and any official grading rubric/report template were not supplied in this chat, so this package does not claim to reproduce those missing files. Some DQ checks use conservative field-name inference; inspect `outputs/dq_results.csv` and the report before submission. Run the commands locally and include genuine screenshots/logs if your program requires execution evidence. Do not claim a check passed unless the generated result says it passed.

## Output folders
ETL creates `outputs/processed/`, `outputs/quarantine/`, `outputs/audit/`, `outputs/profile/`.
Quality checks create `outputs/dq_results.csv` and `outputs/dq_summary.json`.

## Phase 2 (Days 6–10)
The Streamlit app now includes pages for attendance/leave, attrition, team productivity, payroll cost, budget variance and KPI traffic lights. Additional automated tests are in `tests/test_phase2.py`; Phase 2 summaries are under `outputs/phase2/` and the report is `reports/DataAnalytics_ShreyaRaut_Phase2_Report.pdf`.

Run checks:
```bash
python -m pytest -q
python -m py_compile app.py
```
Run the app after installing dependencies:
```bash
pip install -r requirements.txt
streamlit run app.py
```

**Before final portal submission:** replace the report's placeholder with your real GitHub repository URL; create and push the `phase-2` Git tag; capture genuine screenshots after running the dashboard. The official `unlock_PQ-09` answer key was not in the supplied files, so official payroll answer-key reconciliation remains pending. Do not claim it is complete until the key is used.
