# Phase 3 — Company Health: Finance, Departments, AI and Scorecard (Days 11–15)

PulseIQ is one application that grows phase by phase, so the code stays at the repository root. This folder is the index for Phase 3. Git tag: [`phase-3`](https://github.com/shreyaraut611-coder/PulseIQ-Analytics/releases/tag/phase-3)

## What was built
| Task | What | Live page |
|---|---|---|
| 11 | Profit & loss from detail ledger accounts, expenses, vendors, ledger tie-out | https://pulseiq-shreya.streamlit.app/Profit_and_loss |
| 12 | Open invoices, receivables ageing, slow payers, cash in vs out, DSO | https://pulseiq-shreya.streamlit.app/Receivables_and_cash |
| 13 | Department × month view (aggregate first, then join) | https://pulseiq-shreya.streamlit.app/Department_view |
| 14 | AI signals: anomalies by money at risk, forecast back-test, attrition risk by group | https://pulseiq-shreya.streamlit.app/AI_signals |
| 15 | Executive scorecard: 8 KPIs with target and status | https://pulseiq-shreya.streamlit.app/Executive_scorecard |

## Files for this phase
| File | Purpose |
|---|---|
| [`src/views.py`](../src/views.py) | Governed metric layer (every number is defined once here) |
| [`src/ui.py`](../src/ui.py) | Shared page header and formatting |
| [`app.py`](../app.py) | Landing page |
| [`pages/2_Profit_and_loss.py`](../pages/2_Profit_and_loss.py) … [`pages/6_Executive_scorecard.py`](../pages/6_Executive_scorecard.py) | Phase 3 pages |
| [`tests/test_phase3.py`](../tests/test_phase3.py) | 15 Phase 3 tests (tie-outs, ageing, grain, scorecard) |

## Report
- [Phase 3 report](../reports/Phase3_Submission_Report.md)

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
pytest -q
```
