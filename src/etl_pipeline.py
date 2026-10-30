"""PulseIQ ETL pipeline: exports source tables, normalizes headers, profiles rows,
and writes processed/quarantine/audit artifacts. Run from repository root."""
from pathlib import Path
import json, re, hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "data" / "tables"
OUT = ROOT / "outputs"
PROCESSED = OUT / "processed"
QUARANTINE = OUT / "quarantine"
AUDIT = OUT / "audit"
PROFILE = OUT / "profile"

def normalize_name(name):
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")

def load_tables():
    tables = {}
    for path in sorted(TABLES.glob("*.csv")):
        try:
            tables[path.stem] = pd.read_csv(path, low_memory=False)
        except Exception as exc:
            print(f"Skipping {path.name}: {exc}")
    return tables

def main():
    for folder in (PROCESSED, QUARANTINE, AUDIT, PROFILE):
        folder.mkdir(parents=True, exist_ok=True)
    tables = load_tables()
    audit = []
    profiles = []
    for name, df in tables.items():
        original_rows = len(df)
        df.columns = [normalize_name(c) for c in df.columns]
        # Conservative duplicate-row quarantine; do not silently discard records.
        dup_mask = df.duplicated(keep="first")
        quarantine = df.loc[dup_mask].copy()
        clean = df.loc[~dup_mask].copy()
        clean.to_csv(PROCESSED / f"{name}.csv", index=False)
        if not quarantine.empty:
            quarantine.to_csv(QUARANTINE / f"{name}_duplicate_rows.csv", index=False)
        profiles.append({
            "table": name, "source_rows": original_rows, "processed_rows": len(clean),
            "duplicate_rows_quarantined": int(dup_mask.sum()), "column_count": len(df.columns),
            "null_cells": int(df.isna().sum().sum())
        })
        audit.append({
            "table": name, "source_rows": original_rows, "processed_rows": len(clean),
            "quarantined_rows": int(dup_mask.sum()), "status": "completed"
        })
    pd.DataFrame(audit).to_csv(AUDIT / "etl_audit.csv", index=False)
    pd.DataFrame(profiles).to_csv(PROFILE / "table_profiles.csv", index=False)
    (AUDIT / "run_metadata.json").write_text(json.dumps({
        "tables_processed": len(tables),
        "source_directory": "data/tables",
        "duplicate_policy": "Exact duplicate rows are quarantined; first occurrence retained.",
        "note": "Business-key and schema-specific rules should be configured against the supplied data contracts."
    }, indent=2), encoding="utf-8")
    print(f"ETL complete: {len(tables)} tables. Outputs: {OUT}")

if __name__ == "__main__":
    main()
