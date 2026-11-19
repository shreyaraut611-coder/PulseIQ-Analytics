# PulseIQ — Phase 4 Submission Report (Release)
**Name:** Shreya Raut · **Track:** Aura Workforce by Growmar — Data Analytics · **Tasks:** 16–20 · **Tags:** `phase-4`, `v1.0.0`
**Repo:** https://github.com/shreyaraut611-coder/PulseIQ-Analytics · **Live app:** `<add link>` · **API:** `<add link>/docs` · **Demo video:** `<add link>`

## 1. Summary
Phase 4 makes PulseIQ a released product: a monthly PDF pack built with one command, scheduled jobs, a self-service KPI explorer with privacy rules, a metrics API with lineage, hosting, and a board deck.

## 2. Task 16 — Monthly report pack
`python build_report.py --month YYYY-MM` builds a 5-section PDF for any month, stamped with the data cut-off and build time. Tested for 2026-09 and 2025-08, and in a test that adds a brand-new department (it appears automatically).
`<Screenshot: first page of the PDF>`

## 3. Task 17 — Automation and hosting
- GitHub Actions: tests on every push; monthly PDF on the 2nd of each month; data refresh every Monday.
- Dashboard on Streamlit Community Cloud, API on Render (free plans). Reasons in `docs/hosting.md`.
- Hosted app reads only aggregated tables in `data/published/` (57 KB), never employee rows.
`<Screenshot: green Actions run>` `<Screenshot: live app>`

## 4. Task 18 — KPI explorer and privacy
- Roles: Admin, HR, Manager, Executive. Each sees only its allowed metrics and levels.
- Groups under 5 people (10 for attrition) are hidden, plus a second cell where needed so totals cannot reveal them.
- I tried to break it 8 ways (`docs/privacy_tests.md`); all were blocked. Example: Executive Office has 1 person and never appears.
`<Screenshot: explorer with a suppressed cell>`

## 5. Task 19 — Metrics API and lineage
Endpoints `/metrics`, `/metrics/{name}?month=`, `/lineage/{name}`, `/freshness`, `/health`. Every answer includes definition, source tables, lineage and cut-off. Lineage diagram and "what breaks if a column is renamed" table in `docs/lineage.md`.
`<Screenshot: /docs page and one answer>`

## 6. Task 20 — Release and board pack
- `RELEASE_NOTES.md`: included, not included, known limits.
- Clean-machine test: fresh clone, 36 tests pass, PDF and deck build (`docs/clean_machine_test.md`).
- Board deck (10 slides) built from live numbers. Main asks: collections drive on ₹2.71 Cr overdue; staffing review in Customer Support; smooth bonus costs. It also states one recommendation I would **not** give yet (cutting overtime to stop attrition) because the data shows correlation, not cause.

## 7. Final challenge
Collections priority list on branch `final-challenge`: ranks overdue invoices by balance × age × client payment history. The top 10 invoices cover about 89% of overdue money. Details in `docs/final_challenge.md`.

## 8. What I learned
`<Write 4–6 lines in your own words>`
