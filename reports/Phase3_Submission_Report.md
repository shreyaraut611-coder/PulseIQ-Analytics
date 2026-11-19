# PulseIQ — Phase 3 Submission Report
**Name:** Shreya Raut · **Track:** Aura Workforce by Growmar — Data Analytics · **Tasks:** 11–15 · **Tag:** `phase-3`
**Repo:** https://github.com/shreyaraut611-coder/PulseIQ-Analytics · **Live app:** `<add link>`

## 1. Summary
Phase 3 turns the people dashboard into a company-health product. It adds five pages on top of one governed metric layer (`src/views.py`), so every number on every page comes from the same code and ties back to the ledger.

## 2. Task 11 — Profit & loss
- Monthly P&L from ledger accounts: revenue 4001–4004, payroll 5001–5005, expenses 5101–5112.
- Expense bills tie to the ledger in all 18 months. Clean payroll ties in 17 of 18 months; June 2026 differs by ₹18,450 (logged as an open item).
- Manual journals MJ-0001/0002: an ₹18 lakh accrual in March 2026, reversed in April 2026.
- **Finding:** payroll takes 61–75% of revenue, so bonus months pull margin down to 8–14%.
`<Screenshot: Profit & loss page>`

## 3. Task 12 — Receivables & cash
- Open statuses: SENT, OVERDUE, PARTIALLY_PAID. Open receivables ₹13.94 Cr; ageing buckets add up exactly.
- ₹2.71 Cr overdue at the cut-off; one invoice is 548 days past due (Siruvani Agro Tech).
- Cash in vs out from bank account 1001: net cash flow was negative in 5 of 18 months.
`<Screenshot: Receivables & cash page>`

## 4. Task 13 — Department view
- Each fact is aggregated to department × month first, then joined (headcount → payroll → attendance → leave), so rows never multiply.
- Comparison with the vault's `reference_summary_dept_month` runs when that file is in `data/vault/`. `<Add result after placing the file>`
`<Screenshot: Department view>`

## 5. Task 14 — AI signals
- 405 anomaly flags; payroll money at risk about ₹3.14 Cr. All AI output is labelled "AI-generated, for human review".
- Supplied forecasts start October 2026, after the cut-off, so I back-tested a headcount trend instead: MAPE about 2.3%, 5 of 6 months inside the band.
- Attrition risk by department: Customer Support has the highest high-risk share (34.5%).
`<Screenshot: AI signals page>`

## 6. Task 15 — Executive scorecard
8 KPIs with value, last month, target and traffic light. Print-friendly. In September 2026, attendance, attrition, overtime, payroll vs budget and task completion are all green.
`<Screenshot: Executive scorecard>`

## 7. Testing
15 new tests in `tests/test_phase3.py` (ledger tie-outs, ageing check, no row blow-up in joins, scorecard). `<Screenshot: pytest result>`

## 8. What I learned
`<Write 4–6 lines in your own words>`
