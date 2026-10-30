"""Metric dictionary loader and lightweight metric evaluation helpers."""
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "data" / "tables"

def metric_catalog():
    path = TABLES / "metric_dictionary.csv"
    if not path.exists(): return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def table_catalog():
    result = []
    for path in sorted(TABLES.glob("*.csv")):
        df = pd.read_csv(path, nrows=5, low_memory=False)
        result.append({"table": path.stem, "columns": ", ".join(map(str, df.columns)), "sample_rows": len(df)})
    return pd.DataFrame(result)

if __name__ == "__main__":
    cat = metric_catalog()
    print(cat.to_string(index=False) if not cat.empty else "No metric dictionary found.")
