# PulseIQ — Phase 4 Report

| | |
|---|---|
| **Name** | Shreya Sanjay Raut |
| **Track** | Data Analytics (Aura Workforce by Growmar) |
| **Phase** | Phase 4 · Tasks 16–20 (Days 16–20) |
| **GitHub repository** | https://github.com/shreyaraut611-coder/PulseIQ-Analytics |
| **Git tags** | `phase-4` · https://github.com/shreyaraut611-coder/PulseIQ-Analytics/releases/tag/phase-4; `v1.0.0` · https://github.com/shreyaraut611-coder/PulseIQ-Analytics/releases/tag/v1.0.0 |
| **Live dashboard** | https://pulseiq-shreya.streamlit.app |

## 1. Tasks

| Task | Done? | Evidence |
|---|---|---|
| 16 · Monthly report pack | Done | `python build_report.py --month YYYY-MM` builds a 5-section PDF for any month, stamped with the period, the cut-off and the build time |
| 17 · Automation and going live | Done | Live link above; GitHub Actions: tests on every push, monthly PDF on the 2nd, data refresh every Monday |
| 18 · Self-service and privacy | Done | KPI explorer page; `docs/privacy_tests.md` (8 break-it attempts, all blocked) |
| 19 · Metrics API and lineage | Done (runs locally; Render blueprint ready) | `api/main.py`, `docs/API.md`, `docs/lineage.md` |
| 20 · Release and board pack | Done | Tag `v1.0.0`, `RELEASE_NOTES.md`, 10-slide board deck, final challenge on branch `final-challenge` |

## 2. Proof it works

- **Tests:** `pytest -q` → **36 passed** on a fresh clone and on every push.
- **Report test:** one test adds a brand-new department to a copy of the data and checks that the PDF and every view pick it up, with nothing hard-coded.
- **Privacy:**
  - Groups under 5 people (10 for attrition) are hidden.
  - One extra group is hidden too, so a hidden value cannot be worked out from the total.
  - Checking the live app, I found the one-person Executive Office's pay still visible on two pages. I fixed both pages and redeployed.
- **API vs dashboard:** a test confirms the API returns the same values as the dashboard. September 2026: revenue ₹80,268,200 and headcount 441.



## 3. Board story and final challenge

- **Decisions the deck asks for:**
  1. Collect the ₹2.71 Cr of overdue invoices.
  2. Review staffing in Customer Support.
  3. Spread bonus costs across the year so margin stops swinging between 8% and 27%.
- **A recommendation I would not give yet:** cutting overtime to stop attrition. Overtime and attrition are high in the same departments, but the data does not prove that one causes the other.
- **Final challenge (branch `final-challenge`):** a collections priority list that ranks invoices by balance × age × client payment history. The top 10 invoices cover about 89% of overdue money.

## 4. What I learned

- A report must rebuild for any month with one command and still work when the data changes.
- A hidden number can come back by subtraction from a total, so privacy needs a second hidden cell.
- Testing on the live app found a leak that my local tests missed.
- In a board deck, the recommendation I hold back shows judgement as much as the ones I make.

## 5. Problems and how I solved them

- **Python version on Streamlit Cloud:** the default Python 3.14 could not install my pinned packages, so I chose Python 3.11.
- **Uploading to GitHub:** uploading files from the browser was blocked, so the files were created one by one in the GitHub web editor, and every file size was then compared with the local copy.
- **Forecast accuracy:** the forecasts start after the cut-off, so I measured accuracy with a back-test.

## 6. What I would improve next

- Host the API on Render.
- Add a real sign-in instead of demo users.
- Fit the collections weights on real payment data.
- Run the vault reference comparison once `reference_summary_dept_month.csv` is added.
