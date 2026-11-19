# PulseIQ v1.0.0 — release notes

Release date: `<add the date you publish the release>` · Data cut-off: 30 Sep 2026

## Included
- **Dashboard**: landing page and 7 pages (people & payroll, P&L, receivables & cash, department view, AI signals, executive scorecard, KPI explorer). Every page shows the data cut-off and the last refresh time.
- **Monthly PDF pack**: `python build_report.py --month YYYY-MM` builds a 5-section report for any month, stamped with the cut-off and build time.
- **Scheduled jobs** (GitHub Actions):
  - `ci.yml` runs the tests on every push.
  - `monthly_report.yml` builds the PDF on the 2nd of each month and saves it as a download.
  - `refresh_data.yml` refreshes the published tables every Monday.
- **KPI explorer**: self-service metrics by role, with small-group suppression.
- **Metrics API** (FastAPI): `/metrics`, `/metrics/{name}?month=`, `/lineage/{name}`, `/freshness`, `/health`. Every answer carries definition, source, lineage and cut-off.
- **Board deck**: `python scripts/build_board_deck.py` builds a 10-slide pack from live numbers.
- **Docs**: API guide, lineage diagram, hosting choice, privacy break-it log, clean-machine test.
- **Tests**: pytest suite covering metric tie-outs, report for any month, a new department appearing automatically, privacy rules, roles and API answers.

## Not included
- Real company data. Everything is fictional training data.
- Logins. Roles are picked from a demo-user list, not a sign-in system.
- Employee-level views on the hosted app. Only aggregated, privacy-safe tables are published.
- A trained machine-learning model. The forecast check is a simple back-test, and the risk scores are the supplied baseline.

## Known limits
- The supplied forecasts start in October 2026, after the cut-off, so forecast accuracy cannot be measured yet. A back-test is shown instead (headcount, linear trend trained to March 2026: MAPE about 2.3%).
- Payroll in June 2026 is ₹18,450 higher in the ledger than in the payroll facts. It is logged as an open item for Finance.
- The comparison with the validation vault's `reference_summary_dept_month` runs only when that file is placed in `data/vault/`.
- Free hosting sleeps when idle, so the first page load or API call can take up to a minute.
- Attrition rates in small departments move a lot from month to month; read them over 12 months.

## How to verify this release
```bash
pip install -r requirements.txt
pytest -q
python build_report.py --month 2026-09
python scripts/build_board_deck.py
```
