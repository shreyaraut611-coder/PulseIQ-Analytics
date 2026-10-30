from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]

def test_dataset_and_metric_catalog_exist():
    assert (ROOT / "data" / "PulseIQ_Dataset.xlsx").exists()
    assert (ROOT / "data" / "tables" / "metric_dictionary.csv").exists()

def test_expected_source_tables_exist():
    for name in ["dim_employee", "fact_payroll", "fact_headcount_monthly", "dq_checks_catalog"]:
        assert (ROOT / "data" / "tables" / f"{name}.csv").exists()

def test_metric_dictionary_is_nonempty():
    df = pd.read_csv(ROOT / "data" / "tables" / "metric_dictionary.csv")
    assert len(df) > 0
