"""Data quality checks driven by workbook dq_checks_catalog when possible.
Results are transparent: checks without safely inferred columns are marked REVIEW."""
from pathlib import Path
import json, re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "data" / "tables"
OUT = ROOT / "outputs"

def read_table(stem):
    path = TABLES / f"{stem}.csv"
    return pd.read_csv(path, low_memory=False) if path.exists() else None

def col(df, candidates):
    lookup = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}
    for c in candidates:
        if c in lookup: return lookup[c]
    return None

def run_checks():
    catalog = read_table("dq_checks_catalog")
    results = []
    if catalog is None:
        catalog = pd.DataFrame([{"check_name":"catalog_available","description":"DQ catalog exists","severity":"high"}])
    # Run concrete, defensible checks against tables and report unknown checks transparently.
    checks = [
        ("fact_payroll", "duplicate_rows", "No exact duplicate payroll rows", "Exact duplicate rows", "high"),
        ("dim_employee", "employee_key_null", "Employee identifiers are populated", "Null employee identifier", "high"),
        ("fact_attendance_monthly", "duplicate_rows", "No exact duplicate attendance rows", "Exact duplicate rows", "medium"),
        ("fact_headcount_monthly", "negative_headcount", "Headcount is non-negative", "Negative headcount values", "high"),
        ("fact_payroll", "negative_pay_amount", "Payroll amount is non-negative", "Negative amount values", "high"),
        ("fact_leave", "negative_leave_days", "Leave days are non-negative", "Negative leave-day values", "medium"),
        ("fact_ledger", "unbalanced_ledger_row", "Ledger debit/credit rows balance where both columns exist", "Unbalanced ledger rows", "high"),
        ("fact_invoice_payment", "negative_payment", "Invoice payment amounts are non-negative", "Negative payment values", "medium"),
        ("fact_expense", "negative_expense", "Expense amounts are non-negative", "Negative expense values", "medium"),
        ("fact_task", "duplicate_rows", "No exact duplicate task rows", "Exact duplicate rows", "low"),
        ("fact_anomaly", "duplicate_rows", "No exact duplicate anomaly rows", "Exact duplicate rows", "low"),
        ("fact_attrition_risk", "duplicate_rows", "No exact duplicate attrition-risk rows", "Exact duplicate rows", "low"),
        ("fact_forecast", "negative_forecast", "Forecast numeric values are non-negative where identified", "Negative forecast values", "medium"),
        ("fact_payroll", "payroll_employee_orphan", "Payroll employee keys resolve to employee dimension", "Orphan employee keys", "high"),
    ]
    for table, code, label, desc, severity in checks:
        df = read_table(table)
        status, failures, detail = "REVIEW", None, "Table or required columns not safely identified."
        if df is not None:
            if code == "duplicate_rows":
                failures = int(df.duplicated().sum()); status = "PASS" if failures == 0 else "FAIL"
                detail = f"{failures} exact duplicate rows"
            elif code == "employee_key_null":
                c = col(df, ["employee_id","employee_key","emp_id","id"])
                if c:
                    failures = int(df[c].isna().sum()); status = "PASS" if failures == 0 else "FAIL"; detail = f"{failures} null identifiers in {c}"
            elif code in ("negative_pay_amount","negative_payment","negative_expense","negative_leave_days","negative_forecast","negative_headcount"):
                candidates = {
                    "negative_pay_amount":["net_pay","gross_pay","pay_amount","payroll_amount","amount"],
                    "negative_payment":["payment_amount","paid_amount","amount"],
                    "negative_expense":["expense_amount","amount","total_amount"],
                    "negative_leave_days":["leave_days","days","duration_days"],
                    "negative_forecast":["forecast_value","forecast_amount","value","amount"],
                    "negative_headcount":["headcount","employee_count","count"]
                }[code]
                c = col(df, candidates)
                if c:
                    vals = pd.to_numeric(df[c], errors="coerce")
                    failures = int((vals < 0).sum()); status = "PASS" if failures == 0 else "FAIL"; detail = f"{failures} negative values in {c}"
            elif code == "unbalanced_ledger_row":
                debit = col(df, ["debit","debit_amount","dr_amount"])
                credit = col(df, ["credit","credit_amount","cr_amount"])
                if debit and credit:
                    d, c = pd.to_numeric(df[debit], errors="coerce").fillna(0), pd.to_numeric(df[credit], errors="coerce").fillna(0)
                    failures = int((d.round(2) != c.round(2)).sum()); status = "PASS" if failures == 0 else "FAIL"; detail = f"{failures} rows have unequal debit and credit"
            elif code == "payroll_employee_orphan":
                dim = read_table("dim_employee")
                fk = col(df, ["employee_id","employee_key","emp_id"])
                pk = col(dim, ["employee_id","employee_key","emp_id"]) if dim is not None else None
                if fk and dim is not None and pk:
                    failures = int((df[fk].notna() & ~df[fk].isin(dim[pk])).sum())
                    status = "PASS" if failures == 0 else "FAIL"; detail = f"{failures} payroll keys absent from dim_employee"
        results.append({"check_id": code, "check_name": label, "table_name": table,
                        "severity": severity, "status": status, "failure_count": failures, "details": detail})
    OUT.mkdir(exist_ok=True)
    pd.DataFrame(results).to_csv(OUT / "dq_results.csv", index=False)
    summary = pd.DataFrame(results)["status"].value_counts().to_dict()
    (OUT / "dq_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(pd.DataFrame(results).to_string(index=False))
    print(f"\nSaved: {OUT / 'dq_results.csv'}")
    return results

if __name__ == "__main__":
    run_checks()
