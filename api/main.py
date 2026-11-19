"""Task 19 · PulseIQ metrics API.

Run locally:   uvicorn api.main:app --reload
Then open:     http://127.0.0.1:8000/docs   (interactive documentation)

Every response carries the metric value, its official definition and formula (from the metric
dictionary), its source table, the lineage from raw table to dashboard, the data cut-off and the
last refresh time.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi import FastAPI, HTTPException, Query  # noqa: E402

import views as v  # noqa: E402

app = FastAPI(title="PulseIQ Metrics API", version="1.0.0",
              description="Five governed company metrics with definitions, sources, lineage and freshness. "
                          "Fictional training data (Zenith Nova Technologies).")


@app.get("/")
def root():
    return {"service": "PulseIQ Metrics API", "metrics": sorted(v.LINEAGE), "docs": "/docs",
            "freshness": v.freshness()}


@app.get("/health")
def health():
    return {"status": "ok", **v.freshness()}


@app.get("/freshness")
def freshness():
    return v.freshness()


@app.get("/metrics")
def list_metrics():
    md = v.load("metric_dictionary").set_index("metric_id")
    return [{"metric": name, "metric_id": lin["metric_id"], "name": md["metric_name"].get(lin["metric_id"]),
             "unit": md["unit"].get(lin["metric_id"]), "endpoint": f"/metrics/{name}?month=YYYY-MM"}
            for name, lin in v.LINEAGE.items()]


@app.get("/metrics/{name}")
def get_metric(name: str, month: str = Query(None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM; default latest")):
    if name not in v.LINEAGE:
        raise HTTPException(404, f"Unknown metric '{name}'. Try one of {sorted(v.LINEAGE)}")
    months = v.months_available()
    month = month or months[-1]
    if month not in months:
        raise HTTPException(404, f"No data for {month}. Available: {months[0]} to {months[-1]}")
    return v.api_metric(name, month)


@app.get("/lineage/{name}")
def lineage(name: str):
    if name not in v.LINEAGE:
        raise HTTPException(404, f"Unknown metric '{name}'")
    return v.LINEAGE[name]
