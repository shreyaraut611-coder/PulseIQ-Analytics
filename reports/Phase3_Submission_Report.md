# PulseIQ — Phase 3 Report

| | |
|---|---|
| **Name** | Shreya Sanjay Raut |
| **Track** | Data Analytics (Aura Workforce by Growmar) |
| **Phase** | Phase 3 · Tasks 11–15 (Days 11–15) |
| **GitHub repository** | https://github.com/shreyaraut611-coder/PulseIQ-Analytics |
| **Git tag** | `phase-3` · https://github.com/shreyaraut611-coder/PulseIQ-Analytics/releases/tag/phase-3 |
| **Live dashboard** | https://pulseiq-shreya.streamlit.app |

## 1. Tasks

| Task | Done? | Evidence |
|---|---|---|
| 11 · Profit & loss and expense analytics | Done | Profit & loss page (live link); ledger tie-out table on the page |
| 12 · Invoices, receivables and cash | Done | Receivables & cash page: ageing check "passed", DSO 48 days |
| 13 · Cross-department impact view | Done | Department view page: one row per department × month |
| 14 · AI signals | Done | AI signals page: anomalies by money at risk, forecast back-test |
| 15 · Executive scorecard | Done | Executive scorecard page: 8 KPIs with target and status |

## 2. Proof it works

- **Tests:** `pytest -q` → **36 passed**, including 15 new Phase 3 tests in `tests/test_phase3.py`. They also run on every push in GitHub Actions, and all runs are green.
- **Ledger tie-out:**
  - The trial balance balances (debits = credits) in all 18 months.
  - Expense bills = ledger accounts 5101–5112 in all 18 months.
  - Clean payroll = ledger accounts 5001–5005 in 17 of 18 months. June 2026 differs by ₹18,450, which is logged as an open item.
- **Receivables:** open receivables of ₹13.94 Cr are exactly equal to the sum of the four ageing buckets.
- **Department grain:** a test confirms there are no duplicate department-month rows, so the joins never multiply rows.
- **Forecast back-test:** a trend trained to Mar 2026 and tested on Apr–Sep 2026 gives MAPE ≈ 2.3%, with 5 of 6 months inside the 80% band.


## 3. Key findings

- **Payroll and margin:** payroll takes 61–75% of revenue, so bonus months pull margin down to 8–14%.
- **Overdue money:** ₹2.71 Cr is overdue. One invoice is 548 days late, and two clients pay after more than 100 days.
- **Customer Support:** it has the highest overtime share and the highest AI attrition-risk share (34.5%).

## 4. What I learned

- Money numbers must use only detail accounts. Adding a heading account to its children double counts.
- Tying the P&L back to the ledger finds problems a chart hides, such as the ₹18,450 payroll gap.
- I aggregate each source to the same grain before joining, so rows never multiply.
- An AI forecast is only useful when its error can be measured, so I back-tested it.

## 5. Problems and how I solved them

- **Forecasts had no actuals:** the supplied forecasts start after the cut-off. I added a transparent back-test instead of claiming an accuracy figure.
- **Overdue history used today's status:** past-month overdue figures used today's invoice status. I added `overdue_at(date)`, which rebuilds the balance from invoice and payment dates.
- **Small departments exposed pay:** a one-person department showed one person's pay. I hid small groups and also hid one extra group, so the hidden value cannot be worked out from the total.

## 6. Plan for the next phase

- Build the one-command monthly PDF pack.
- Schedule tests and data refresh with GitHub Actions.
- Deploy the dashboard live.
- Add a self-service KPI explorer with role-based privacy.
- Publish metrics through an API.
- Release v1.0.0 with a board deck.
