"""Task 17 · Export the published layer: aggregates only, small enough for free hosting.

    python scripts/export_published.py

Writes data/published/*.parquet (or .csv if pyarrow is not installed) plus a manifest with
row counts, sizes and the data cut-off. No employee names, salaries or person-level rows are
published here; groups smaller than the metric's minimum group size are blanked.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import views as v  # noqa: E402

OUT = ROOT / "data" / "published"


def write(df, name, manifest):
    try:
        import pyarrow  # noqa: F401
        path = OUT / f"{name}.parquet"
        df.to_parquet(path, index=False)
    except ImportError:
        path = OUT / f"{name}.csv"
        df.to_csv(path, index=False)
    manifest[name] = {"file": path.name, "rows": int(len(df)), "bytes": path.stat().st_size}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict = {}
    dept = v.dept_month_impact()
    small = dept["headcount_end"] < 5
    for c in ("employer_cost", "gross_pay", "overtime_pay", "cost_per_head"):
        dept.loc[small, c] = np.nan
    dept.loc[dept["headcount_start"] < 10, ["attrition_rate_pct"]] = np.nan
    write(dept, "dept_month", manifest)
    write(v.pnl_monthly(), "pnl_monthly", manifest)
    write(v.cash_in_out(), "cash_monthly", manifest)
    write(v.receivables_ageing(), "receivables_ageing", manifest)
    write(v.days_to_pay_by_client(), "client_days_to_pay", manifest)
    write(v.anomalies_by_type(), "anomalies_by_type", manifest)
    write(v.forecast_vs_actual("ALL"), "headcount_forecast", manifest)
    sc = [v.scorecard(m).assign(month=m) for m in v.months_available()]
    import pandas as pd
    write(pd.concat(sc, ignore_index=True), "scorecard", manifest)
    meta = {"data_cutoff": v.CUTOFF_LABEL, "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "total_bytes": sum(m["bytes"] for m in manifest.values()), "tables": manifest}
    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"total_bytes": meta["total_bytes"], "tables": len(manifest)}))


if __name__ == "__main__":
    main()
