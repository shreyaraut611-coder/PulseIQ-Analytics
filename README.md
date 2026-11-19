# PulseIQ Analytics

A people, payroll and finance analytics product for **Zenith Nova Technologies** (a fictional company), built for the Aura Workforce by Growmar Data Analytics Track.

Data runs from April 2025 to the **30 Sep 2026 cut-off**. Every page, report and API answer shows that date.

| Phase | What it adds | Tag |
|---|---|---|
| 1 | Ingestion, profiling, data-quality checks, quarantine | – |
| 2 | Governed metrics and the people & payroll dashboard | `phase-2` |
| 3 | Profit & loss, receivables & cash, department view, AI signals, executive scorecard | `phase-3` |
| 4 | Monthly PDF pack, scheduled jobs, KPI explorer with privacy, metrics API, board deck | `phase-4`, `v1.0.0` |

## Live links
- Dashboard: `<add your Streamlit Community Cloud link>`
- Metrics API: `<add your Render link>/docs`
- Demo video: `<add your video link>`

## Quick start (Windows)
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
On Mac/Linux use `python3 -m venv .venv` and `source .venv/bin/activate`.

| Task | Command |
|---|---|
| Run the dashboard | `streamlit run app.py` |
| Build the monthly PDF (latest month) | `python build_report.py` |
| Build the PDF for any month | `python build_report.py --month 2025-08` |
| Build the board deck | `python scripts/build_board_deck.py` |
| Refresh the published (privacy-safe) tables | `python scripts/export_published.py` |
| Run the metrics API | `uvicorn api.main:app --reload` then open http://127.0.0.1:8000/docs |
| Run all tests | `pytest -q` |

## Dashboard pages
| Page | Answers |
|---|---|
| Home (`app.py`) | What is PulseIQ, and the four headline numbers |
| 1 People & payroll | Headcount, attrition, payroll cost, attendance, overtime |
| 2 Profit & loss | Monthly P&L, expenses by category, top vendors, ledger tie-out |
| 3 Receivables & cash | Open invoices, ageing, slow payers, cash in vs out, DSO |
| 4 Department view | Payroll, attendance, leave and headcount per department and month |
| 5 AI signals | Anomaly flags, forecasts, back-test accuracy, attrition risk (labelled AI-generated, for human review) |
| 6 Executive scorecard | 8 KPIs vs target with traffic lights; print-friendly |
| 7 KPI explorer | Self-service metrics by role, with small-group suppression |

## Project structure
```
app.py                    landing page
pages/                    the 7 dashboard pages
src/views.py              governed metric layer (every number comes from here)
src/ui.py                 shared page header, month picker, formatting
src/etl_pipeline.py       Phase 1 ingestion and quarantine
src/quality_checks.py     Phase 1 data-quality checks
build_report.py           monthly PDF pack
scripts/                  board deck builder, published-table export
api/main.py               FastAPI metrics API
tests/                    pytest suite (phases 1-4)
docs/                     API, lineage, hosting, privacy tests, clean-machine test
.github/workflows/        CI, monthly report, weekly data refresh
data/tables/              source tables (CSV) from the supplied workbook
data/published/           aggregated, privacy-safe tables used by the hosted app
data/vault/, data/starter/  put the kit's validation-vault and starter files here
reports/                  phase reports, monthly PDFs, board deck
```

## Privacy
- Groups smaller than 5 people (10 for attrition) are hidden, with a second cell hidden where needed so the small group cannot be worked out by subtraction.
- Roles: Admin, HR, Manager, Executive. Each role sees only the metrics and levels it is allowed. See `docs/privacy_tests.md`.
- No employee-level data is published or served by the API.

## Data trust
- Ledger debits equal credits in all 18 months.
- Expense bills tie to ledger accounts 5101-5112 in all months.
- Clean payroll ties to ledger accounts 5001-5005 in 17 of 18 months. June 2026 differs by ₹18,450, which is logged as an open item.
- Planted bad payroll rows are quarantined, not deleted.

See `RELEASE_NOTES.md` for what v1.0.0 includes and its known limits.

*All data is fictional and for training only.*
