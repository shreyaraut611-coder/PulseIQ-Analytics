# PulseIQ Metrics API (Task 19)

A small FastAPI service in `api/main.py`. It exposes 5 governed metrics. Every answer includes the value,
the official definition and formula (from `metric_dictionary`), the source table, the lineage
(raw table → ETL → warehouse → metric view → dashboard), the data cut-off and the last refresh time.

## Run locally

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
# open http://127.0.0.1:8000/docs for the interactive documentation
```

## Endpoints

| Method | Path | What it returns |
|---|---|---|
| GET | `/` | Service info, list of metrics, freshness |
| GET | `/health` | `{"status": "ok"}` plus freshness |
| GET | `/freshness` | Data cut-off, last refresh, plain-language statement |
| GET | `/metrics` | The 5 metrics with id, name, unit and endpoint |
| GET | `/metrics/{name}?month=YYYY-MM` | Value + definition + source + lineage + freshness (default month = latest) |
| GET | `/lineage/{name}` | Lineage of one metric |

Metric names: `revenue` (M16), `operating_margin_pct` (M18), `payroll_cost` (M09), `headcount` (M01),
`overdue_receivables` (M21).

## Examples

```bash
curl "http://127.0.0.1:8000/metrics/revenue?month=2026-09"
```

```json
{
  "metric": "revenue",
  "metric_id": "M16",
  "month": "2026-09",
  "value": 80268200.0,
  "unit": "INR",
  "definition": "Income booked in the ledger (accounts 4001-4004).",
  "formula": "-SUM(signed_amount) for accounts 4001-4004",
  "source": "fact_ledger",
  "lineage": {
    "metric_id": "M16",
    "raw": "PulseIQ_Dataset.xlsx › fact_ledger",
    "etl": "src/etl_pipeline.py (export + normalise)",
    "warehouse": "fact_ledger ⋈ dim_account (detail accounts only)",
    "view": "src/views.py › pnl_monthly()",
    "dashboard": "pages/2_Profit_and_loss.py, Scorecard"
  },
  "data_cutoff": "30 Sep 2026",
  "last_refresh": "<time the data files were last refreshed>"
}
```

Other values for September 2026 (checked by `tests/test_phase4.py`):

| Metric | Value (Sep 2026) |
|---|---|
| revenue | 80,268,200 INR |
| operating_margin_pct | 18.67 % |
| payroll_cost | 55,519,621.87 INR |
| headcount | 441 |
| overdue_receivables | 27,110,866 INR (point in time at 30 Sep 2026) |

Errors: an unknown metric or a month outside Apr 2025 – Sep 2026 returns HTTP 404 with a clear message.

## Deploying the API

Streamlit Community Cloud can only run Streamlit apps, so the API is a **second service from the same GitHub
repository**. `render.yaml` describes it for Render's free web service:
build `pip install -r requirements.txt`, start `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.
On the free plan the service sleeps after inactivity, so the first call can take about a minute.
