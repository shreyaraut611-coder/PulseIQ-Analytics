"""PulseIQ governed metric views (Phase 3 and Phase 4).

Every page, the report builder, the scorecard and the API read numbers from the
functions in this file, so each number has exactly one definition.

Rules used everywhere:
* Data cut-off: 30 Sep 2026 (see the README sheet of the workbook).
* Only DETAIL ledger accounts are summed (is_group = N), so a heading account and
  its children are never counted together.
* Planted payroll rows (ids starting with "PI-X": duplicates and unknown
  employees) are removed before any payroll metric is calculated.
* Each source is aggregated to department x month BEFORE it is joined.
"""
from __future__ import annotations

from pathlib import Path
import os

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "data" / "tables"
VAULT = ROOT / "data" / "vault"          # put files from 04_Validation_Vault here
STARTER = ROOT / "data" / "starter"      # put files from 05_Starter here

CUTOFF = pd.Timestamp("2026-09-30")
CUTOFF_LABEL = "30 Sep 2026"
OPEN_INVOICE_STATUSES = ["SENT", "OVERDUE", "PARTIALLY_PAID"]
AGEING_BUCKETS = ["0-30", "31-60", "61-90", "90+"]
AI_LABEL = "AI-generated, for human review"

_cache: dict[str, pd.DataFrame] = {}


# --------------------------------------------------------------------------- loading
def load(name: str) -> pd.DataFrame:
    """Read one exported workbook sheet (cached). Returns an empty frame if missing."""
    if name not in _cache:
        folder = Path(os.environ.get("PULSEIQ_TABLES", TABLES))
        path = folder / f"{name}.csv"
        _cache[name] = pd.read_csv(path, low_memory=False) if path.exists() else pd.DataFrame()
    return _cache[name].copy()


def clear_cache() -> None:
    _cache.clear()


def departments() -> pd.DataFrame:
    return load("dim_department")[["department_id", "department_name"]]


def add_dept_name(df: pd.DataFrame, key: str = "department_id") -> pd.DataFrame:
    d = departments().rename(columns={"department_id": key})
    out = df.merge(d, on=key, how="left")
    out["department_name"] = out["department_name"].fillna(out[key].astype(str))
    return out


def months_available() -> list[str]:
    led = load("fact_ledger")
    return sorted(led["posting_period"].dropna().unique().tolist())


# --------------------------------------------------------------------------- cleaning
def clean_payroll() -> pd.DataFrame:
    p = load("fact_payroll")
    bad = p["payroll_item_id"].astype(str).str.startswith("PI-X") | (p["employee_key"] < 0)
    p = p.loc[~bad].drop_duplicates(["employee_id", "date_key"], keep="first").copy()
    p["month"] = p["period_end_date"].astype(str).str[:7]
    return p


def payroll_quarantine() -> pd.DataFrame:
    p = load("fact_payroll")
    bad = p["payroll_item_id"].astype(str).str.startswith("PI-X") | (p["employee_key"] < 0)
    return p.loc[bad, ["payroll_item_id", "employee_id", "employee_key", "date_key", "department_id", "employer_cost"]]


# --------------------------------------------------------------------------- Task 11: P&L
def account_hierarchy() -> pd.DataFrame:
    a = load("dim_account")
    a["level"] = np.where(a["is_group"].eq("Y"), "Group (heading)", "Detail")
    return a


def _pl_lines() -> pd.DataFrame:
    led = load("fact_ledger")
    acc = load("dim_account")
    detail = acc.loc[acc["is_group"].eq("N"), ["account_code", "account_name", "account_type"]]
    pl = led.merge(detail, on="account_code", how="inner")          # inner join drops group accounts
    pl = pl[pl["account_type"].isin(["INCOME", "EXPENSE"])].copy()
    # income is a credit (negative signed amount); show it as a positive number
    pl["amount"] = np.where(pl["account_type"].eq("INCOME"), -pl["signed_amount_debit_positive"],
                            pl["signed_amount_debit_positive"])
    pl["month"] = pl["posting_period"]
    return pl


def expense_group(code: int) -> str:
    if 5001 <= code <= 5005:
        return "Payroll cost"
    if code == 5201:
        return "Depreciation"
    if code == 5301:
        return "Bank charges"
    return "Operating expenses"


def pnl_monthly() -> pd.DataFrame:
    """Revenue (4001-4004), other income (4900), expenses (5xxx detail), net profit and margin."""
    pl = _pl_lines()
    pl["line"] = np.select(
        [pl["account_code"].between(4001, 4004), pl["account_code"].eq(4900)],
        ["revenue", "other_income"], default="expenses")
    m = pl.pivot_table(index="month", columns="line", values="amount", aggfunc="sum", fill_value=0).reset_index()
    for c in ("revenue", "other_income", "expenses"):
        if c not in m:
            m[c] = 0.0
    m["net_profit"] = m["revenue"] + m["other_income"] - m["expenses"]
    m["operating_margin_pct"] = np.where(m["revenue"] != 0, m["net_profit"] / m["revenue"] * 100, np.nan)
    payroll = pl[pl["account_code"].between(5001, 5005)].groupby("month")["amount"].sum()
    m["payroll_cost_ledger"] = m["month"].map(payroll).fillna(0)
    m["payroll_pct_of_revenue"] = np.where(m["revenue"] != 0, m["payroll_cost_ledger"] / m["revenue"] * 100, np.nan)
    return m[["month", "revenue", "other_income", "expenses", "payroll_cost_ledger", "net_profit",
              "operating_margin_pct", "payroll_pct_of_revenue"]]


def pnl_table(month: str) -> pd.DataFrame:
    """A simple P&L for one month: one row per detail account, with section subtotals."""
    pl = _pl_lines()
    pl = pl[pl["month"] == month]
    lines = pl.groupby(["account_code", "account_name", "account_type"], as_index=False)["amount"].sum()
    lines["section"] = np.where(lines["account_type"].eq("INCOME"), "Income",
                                lines["account_code"].map(expense_group))
    order = {"Income": 0, "Payroll cost": 1, "Operating expenses": 2, "Depreciation": 3, "Bank charges": 4}
    lines["o"] = lines["section"].map(order)
    lines = lines.sort_values(["o", "account_code"]).drop(columns="o")
    income = lines.loc[lines["section"].eq("Income"), "amount"].sum()
    expense = lines.loc[~lines["section"].eq("Income"), "amount"].sum()
    totals = pd.DataFrame([
        {"account_code": "", "account_name": "TOTAL INCOME", "account_type": "", "amount": income, "section": "Total"},
        {"account_code": "", "account_name": "TOTAL EXPENSES", "account_type": "", "amount": expense, "section": "Total"},
        {"account_code": "", "account_name": "NET PROFIT", "account_type": "", "amount": income - expense, "section": "Total"},
    ])
    return pd.concat([lines, totals], ignore_index=True)[["section", "account_code", "account_name", "amount"]]


def expense_by_category(month: str | None = None) -> pd.DataFrame:
    e = load("fact_expense")
    if month:
        e = e[e["expense_date"].astype(str).str[:7] == month]
    acc = load("dim_account")[["account_code", "account_name"]].rename(
        columns={"account_code": "category_account", "account_name": "category"})
    out = e.merge(acc, on="category_account", how="left").groupby("category", as_index=False).agg(
        amount_excl_gst=("amount_excl_gst", "sum"), bills=("expense_id", "count"))
    return out.sort_values("amount_excl_gst", ascending=False)


def top_vendors(n: int = 10, month: str | None = None) -> pd.DataFrame:
    e = load("fact_expense")
    if month:
        e = e[e["expense_date"].astype(str).str[:7] == month]
    v = load("dim_vendor")[["vendor_id", "vendor_name"]]
    out = e.merge(v, on="vendor_id", how="left").groupby(["vendor_id", "vendor_name"], as_index=False).agg(
        amount_excl_gst=("amount_excl_gst", "sum"), bills=("expense_id", "count"))
    out["share_pct"] = out["amount_excl_gst"] / max(out["amount_excl_gst"].sum(), 1) * 100
    return out.sort_values("amount_excl_gst", ascending=False).head(n)


def pnl_tieout() -> pd.DataFrame:
    """Tie the P&L back to the books and to the detail facts, month by month."""
    led = load("fact_ledger")
    bal = led.groupby("posting_period").agg(debits=("debit", "sum"), credits=("credit", "sum"))
    bal["trial_balance_diff"] = (bal["debits"] - bal["credits"]).round(2)
    pl = _pl_lines()
    ledger_payroll = pl[pl["account_code"].between(5001, 5005)].groupby("month")["amount"].sum()
    fact_payroll = clean_payroll().groupby("month")["employer_cost"].sum()
    opex = pl[pl["account_code"].between(5101, 5112) & pl["source_type"].eq("EXPENSE")].groupby("month")["amount"].sum()
    e = load("fact_expense")
    fact_exp = e.groupby(e["expense_date"].astype(str).str[:7])["amount_excl_gst"].sum()
    out = pd.DataFrame({
        "trial_balance_diff": bal["trial_balance_diff"],
        "payroll_ledger_5001_5005": ledger_payroll,
        "payroll_fact_employer_cost": fact_payroll,
        "expense_ledger_5101_5112": opex,
        "expense_fact_excl_gst": fact_exp,
    }).fillna(0)
    out["payroll_diff"] = (out["payroll_ledger_5001_5005"] - out["payroll_fact_employer_cost"]).round(2)
    out["expense_diff"] = (out["expense_ledger_5101_5112"] - out["expense_fact_excl_gst"]).round(2)
    out.index.name = "month"
    return out.reset_index()


def manual_journals() -> pd.DataFrame:
    led = load("fact_ledger")
    return led[led["source_type"].eq("MANUAL")][["entry_id", "entry_date", "account_code", "debit", "credit",
                                                   "cost_center_department_id", "source_id"]]


# --------------------------------------------------------------------------- Task 12: receivables & cash
def _bucket(days: float) -> str:
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def open_invoices(as_of: pd.Timestamp = CUTOFF) -> pd.DataFrame:
    inv = load("fact_invoice")
    inv = inv[inv["status"].isin(OPEN_INVOICE_STATUSES)].copy()
    inv["due_date"] = pd.to_datetime(inv["due_date"])
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"])
    inv["days_past_due"] = (as_of - inv["due_date"]).dt.days.clip(lower=0)
    inv["age_bucket"] = inv["days_past_due"].map(_bucket)
    inv = inv.merge(load("dim_client")[["client_id", "client_name"]], on="client_id", how="left")
    return inv


def receivables_ageing(as_of: pd.Timestamp = CUTOFF) -> pd.DataFrame:
    inv = open_invoices(as_of)
    out = inv.groupby("age_bucket")["balance_due"].agg(["sum", "count"]).reindex(AGEING_BUCKETS, fill_value=0)
    out = out.rename(columns={"sum": "balance_due", "count": "invoices"}).reset_index()
    return out


def ageing_check(as_of: pd.Timestamp = CUTOFF) -> dict:
    buckets = receivables_ageing(as_of)["balance_due"].sum()
    total = open_invoices(as_of)["balance_due"].sum()
    return {"bucket_total": float(buckets), "open_receivables": float(total),
            "difference": float(round(buckets - total, 2)), "passes": abs(buckets - total) < 0.5}


def overdue_by_client(n: int = 10, as_of: pd.Timestamp = CUTOFF) -> pd.DataFrame:
    inv = open_invoices(as_of)
    inv = inv[inv["days_past_due"] > 0]
    out = inv.groupby(["client_id", "client_name"], as_index=False).agg(
        overdue_balance=("balance_due", "sum"), invoices=("invoice_id", "count"), oldest_days=("days_past_due", "max"))
    return out.sort_values(["overdue_balance", "oldest_days"], ascending=False).head(n)


def days_to_pay_by_client() -> pd.DataFrame:
    """Average days from invoice date to the LAST payment, for fully paid invoices (from the payment table)."""
    inv = load("fact_invoice")
    pay = load("fact_invoice_payment")
    last_pay = pay.groupby("invoice_id", as_index=False)["payment_date"].max()
    paid = inv[inv["status"].eq("PAID")].merge(last_pay, on="invoice_id", how="inner")
    paid["days_to_pay_calc"] = (pd.to_datetime(paid["payment_date"]) - pd.to_datetime(paid["invoice_date"])).dt.days
    cl = load("dim_client")[["client_id", "client_name", "payment_terms_days", "payment_behaviour"]]
    out = paid.groupby("client_id", as_index=False).agg(
        paid_invoices=("invoice_id", "count"), avg_days_to_pay=("days_to_pay_calc", "mean"),
        max_days_to_pay=("days_to_pay_calc", "max"), invoiced=("total_amount", "sum"))
    out = out.merge(cl, on="client_id", how="left")
    out["days_over_terms"] = out["avg_days_to_pay"] - out["payment_terms_days"]
    return out.sort_values("avg_days_to_pay", ascending=False)


def cash_in_out() -> pd.DataFrame:
    """Cash in = debits to the bank account (1001); cash out = credits to it. Opening balance excluded."""
    led = load("fact_ledger")
    bank = led[(led["account_code"] == 1001) & (led["source_type"] != "OPENING")]
    out = bank.groupby("posting_period", as_index=False).agg(cash_in=("debit", "sum"), cash_out=("credit", "sum"))
    out["net_cash_flow"] = out["cash_in"] - out["cash_out"]
    receipts = load("fact_invoice_payment")
    rec = receipts.groupby(receipts["payment_date"].astype(str).str[:7])["amount"].sum()
    out["customer_receipts"] = out["posting_period"].map(rec).fillna(0)
    return out.rename(columns={"posting_period": "month"})


def overdue_at(as_of: pd.Timestamp) -> float:
    """M21 at any past date: invoices issued and due before `as_of`, minus payments received by `as_of`
    (DRAFT and CANCELLED excluded). At the cut-off this equals the overdue part of open_invoices()."""
    inv = load("fact_invoice")
    inv = inv[~inv["status"].isin(["DRAFT", "CANCELLED"])].copy()
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"])
    inv["due_date"] = pd.to_datetime(inv["due_date"])
    pay = load("fact_invoice_payment")
    pay["payment_date"] = pd.to_datetime(pay["payment_date"])
    paid = pay[pay["payment_date"] <= as_of].groupby("invoice_id")["amount"].sum()
    due = inv[(inv["invoice_date"] <= as_of) & (inv["due_date"] < as_of)].copy()
    due["open"] = (due["total_amount"] - due["invoice_id"].map(paid).fillna(0)).clip(lower=0)
    return float(due["open"].sum())


def dso(month: str) -> float:
    """M20: closing receivables / revenue incl GST of the last 90 days x 90."""
    end = pd.Period(month, "M").to_timestamp("M")
    inv = load("fact_invoice")
    inv = inv[~inv["status"].isin(["DRAFT", "CANCELLED"])].copy()
    inv["invoice_date"] = pd.to_datetime(inv["invoice_date"])
    pay = load("fact_invoice_payment")
    pay["payment_date"] = pd.to_datetime(pay["payment_date"])
    paid_to_date = pay[pay["payment_date"] <= end].groupby("invoice_id")["amount"].sum()
    issued = inv[inv["invoice_date"] <= end].copy()
    issued["open"] = issued["total_amount"] - issued["invoice_id"].map(paid_to_date).fillna(0)
    closing = issued["open"].clip(lower=0).sum()
    sales_90 = inv[(inv["invoice_date"] > end - pd.Timedelta(days=90)) & (inv["invoice_date"] <= end)]["total_amount"].sum()
    return float(closing / sales_90 * 90) if sales_90 else float("nan")


# --------------------------------------------------------------------------- Task 13: department x month
def dept_month_impact() -> pd.DataFrame:
    """One row per department and month. Each source is aggregated to this grain first, then joined."""
    hc = load("fact_headcount_monthly")
    hc["month"] = hc["month_start_date"].astype(str).str[:7]
    hc = hc.groupby(["department_id", "month"], as_index=False).agg(
        headcount_start=("headcount_start", "sum"), headcount_end=("headcount_end", "sum"),
        hires=("hires", "sum"), exits=("exits", "sum"), voluntary_exits=("voluntary_exits", "sum"))

    pay = clean_payroll()
    pay = pay.groupby(["department_id", "month"], as_index=False).agg(
        paid_employees=("employee_id", "nunique"), gross_pay=("gross_pay", "sum"),
        overtime_pay=("overtime_pay", "sum"), employer_cost=("employer_cost", "sum"), lop_days=("lop_days", "sum"))

    att = load("fact_attendance_monthly")
    att["month"] = att["period_end_date"].astype(str).str[:7]
    att = att.groupby(["department_id", "month"], as_index=False).agg(
        scheduled_days=("scheduled_days", "sum"), present_days=("present_days", "sum"),
        half_days_unpaid=("half_days_unpaid", "sum"), overtime_hours=("overtime_hours", "sum"),
        late_arrivals=("late_arrivals", "sum"))

    lv = load("fact_leave")
    lv = lv[lv["status"].eq("Approved")]
    emp = load("dim_employee")[["employee_key", "department_id"]]
    lv = lv.merge(emp, on="employee_key", how="left")
    lv["month"] = lv["start_date"].astype(str).str[:7]
    lv = lv.groupby(["department_id", "month"], as_index=False).agg(leave_days=("days", "sum"))

    months = sorted(pay["month"].unique())
    base = hc[hc["month"].isin(months)]
    out = base.merge(pay, on=["department_id", "month"], how="left") \
              .merge(att, on=["department_id", "month"], how="left") \
              .merge(lv, on=["department_id", "month"], how="left")
    num = out.select_dtypes("number").columns
    out[num] = out[num].fillna(0)
    out["attendance_rate"] = np.where(out["scheduled_days"] > 0,
                                      (out["present_days"] + 0.5 * out["half_days_unpaid"]) / out["scheduled_days"], np.nan)
    out["overtime_share_pct"] = np.where(out["employer_cost"] > 0, out["overtime_pay"] / out["employer_cost"] * 100, np.nan)
    out["attrition_rate_pct"] = np.where(out["headcount_start"] > 0, out["exits"] / out["headcount_start"] * 100, np.nan)
    out["leave_days_per_head"] = np.where(out["headcount_end"] > 0, out["leave_days"] / out["headcount_end"], np.nan)
    out["cost_per_head"] = np.where(out["paid_employees"] > 0, out["employer_cost"] / out["paid_employees"], np.nan)
    return add_dept_name(out).sort_values(["month", "department_id"])


def reference_comparison() -> tuple[pd.DataFrame, list[str]]:
    """Compare dept_month_impact with reference_summary_dept_month from 04_Validation_Vault, if present."""
    path = VAULT / "reference_summary_dept_month.csv"
    if not path.exists():
        return pd.DataFrame(), []
    ref = pd.read_csv(path, low_memory=False)
    ref.columns = [c.strip().lower() for c in ref.columns]
    mine = dept_month_impact()
    month_col = next((c for c in ref.columns if c in ("month", "month_start_date", "period", "month_start")), None)
    if month_col is None or "department_id" not in ref.columns:
        return pd.DataFrame(), list(ref.columns)
    ref["month"] = ref[month_col].astype(str).str[:7]
    common = [c for c in ref.columns if c in mine.columns and c not in ("department_id", "month", "department_name")]
    m = mine.merge(ref[["department_id", "month"] + common], on=["department_id", "month"],
                   how="outer", suffixes=("_mine", "_ref"), indicator=True)
    for c in common:
        m[f"{c}_diff"] = (m[f"{c}_mine"] - m[f"{c}_ref"]).round(2)
    return m, common


# --------------------------------------------------------------------------- Task 14: AI signals
def anomalies_by_type() -> pd.DataFrame:
    a = load("fact_anomaly")
    a["money_at_risk"] = pd.to_numeric(a["money_at_risk"], errors="coerce")
    out = a.groupby(["source_dataset", "reason_code"], as_index=False).agg(
        flags=("result_id", "count"), money_at_risk=("money_at_risk", "sum"),
        rows_with_money=("money_at_risk", "count"))
    return out.sort_values(["money_at_risk", "flags"], ascending=False)


def anomaly_flag_rate_by_month() -> pd.DataFrame:
    a = load("fact_anomaly")
    a["month"] = a["period"].astype(str).str[:7]
    return a.groupby(["month", "source_dataset"], as_index=False).agg(flags=("result_id", "count"))


def headcount_actuals() -> pd.DataFrame:
    hc = load("fact_headcount_monthly")
    hc["month"] = pd.to_datetime(hc["month_start_date"])
    return hc.groupby("month", as_index=False)["headcount_end"].sum()


def forecast_vs_actual(department_id: str = "ALL") -> pd.DataFrame:
    f = load("fact_forecast")
    f = f[(f["metric"] == "headcount_end") & (f["department_id"] == department_id)].copy()
    f["month"] = pd.to_datetime(f["forecast_month"])
    hc = load("fact_headcount_monthly")
    hc["month"] = pd.to_datetime(hc["month_start_date"])
    if department_id != "ALL":
        hc = hc[hc["department_id"] == department_id]
    act = hc.groupby("month", as_index=False)["headcount_end"].sum().rename(columns={"headcount_end": "actual"})
    out = act.merge(f[["month", "forecast_value", "lower_80", "upper_80"]], on="month", how="outer").sort_values("month")
    return out


def forecast_error_known_months() -> pd.DataFrame:
    """Error for forecast months that already have actuals. With a 30 Sep 2026 cut-off the supplied
    forecasts start in Oct 2026, so this table is empty until new actuals arrive."""
    out = forecast_vs_actual("ALL").dropna(subset=["actual", "forecast_value"])
    out["abs_pct_error"] = (out["actual"] - out["forecast_value"]).abs() / out["actual"] * 100
    return out


def backtest_headcount(train_through: str = "2026-03", horizon: int = 6) -> pd.DataFrame:
    """A transparent back-test so forecast error CAN be measured: fit a straight-line trend on the
    36 months up to `train_through`, forecast the next `horizon` months, compare with actuals."""
    act = headcount_actuals()
    train_end = pd.Period(train_through, "M").to_timestamp()
    train = act[act["month"] <= train_end].tail(36)
    x = np.arange(len(train))
    slope, intercept = np.polyfit(x, train["headcount_end"].to_numpy(dtype=float), 1)
    resid_sd = float(np.std(train["headcount_end"] - (slope * x + intercept), ddof=1))
    future = act[act["month"] > train_end].head(horizon).copy()
    steps = np.arange(len(train), len(train) + len(future))
    future["forecast_value"] = slope * steps + intercept
    future["lower_80"] = future["forecast_value"] - 1.2816 * resid_sd
    future["upper_80"] = future["forecast_value"] + 1.2816 * resid_sd
    future["abs_pct_error"] = (future["headcount_end"] - future["forecast_value"]).abs() / future["headcount_end"] * 100
    future["inside_band"] = future["headcount_end"].between(future["lower_80"], future["upper_80"])
    return future.rename(columns={"headcount_end": "actual"})


def attrition_risk_by_department(min_group: int = 10) -> pd.DataFrame:
    r = load("fact_attrition_risk")
    r = r[r["risk_band"].isin(["Low", "Medium", "High"])]
    out = r.groupby("department_id").agg(employees=("employee_id", "nunique"),
                                         high=("risk_band", lambda s: (s == "High").sum())).reset_index()
    out["high_risk_share_pct"] = out["high"] / out["employees"] * 100
    out.loc[out["employees"] < min_group, ["high", "high_risk_share_pct"]] = np.nan
    return add_dept_name(out)


# --------------------------------------------------------------------------- Task 15: scorecard
def company_people_month() -> pd.DataFrame:
    d = dept_month_impact()
    g = d.groupby("month", as_index=False)[["headcount_start", "headcount_end", "exits", "employer_cost",
                                              "overtime_pay", "scheduled_days", "present_days", "half_days_unpaid"]].sum()
    g["attendance_rate"] = (g["present_days"] + 0.5 * g["half_days_unpaid"]) / g["scheduled_days"]
    g["overtime_share_pct"] = g["overtime_pay"] / g["employer_cost"] * 100
    g["attrition_rate_pct"] = g["exits"] / g["headcount_start"] * 100
    return g


def task_completion_month() -> pd.DataFrame:
    t = load("fact_task")
    s = load("dim_sprint")
    t = t.merge(s[["sprint_id", "end_date"]] if "end_date" in s.columns else s, on="sprint_id", how="left")
    date_col = "end_date" if "end_date" in t.columns else "due_date"
    t["month"] = t[date_col].astype(str).str[:7]
    t = t[t["status"] != "Cancelled"]
    g = t.groupby("month").agg(done=("status", lambda s: (s == "Done").sum()), planned=("task_id", "count")).reset_index()
    g["task_completion_pct"] = g["done"] / g["planned"] * 100
    return g


def company_targets(month: str) -> dict:
    """Company-level targets from kpi_targets (headcount-weighted where it matters)."""
    k = load("kpi_targets")
    k["m"] = k["month"].astype(str).str[:7]
    k = k[k["m"] == month]
    budget = load("budget_payroll_dept_month")
    budget = budget[budget["month"].astype(str).str[:7] == month]["budget_payroll_cost"].sum()
    if k.empty:
        return {"budget_payroll_cost": float(budget)}
    hc = dept_month_impact()
    w = hc[hc["month"] == month].set_index("department_id")["headcount_end"]
    k["w"] = k["department_id"].map(w).fillna(0)
    def wavg(col):
        sub = k.dropna(subset=[col])
        return float(np.average(sub[col], weights=sub["w"])) if sub["w"].sum() > 0 else float(sub[col].mean())
    return {"attendance_rate": wavg("attendance_rate_target"),
            "overtime_share_pct": wavg("overtime_share_target_pct"),
            "attrition_rate_pct": wavg("attrition_monthly_target_pct"),
            "task_completion_pct": float(k["task_completion_target_pct"].dropna().mean()),
            "budget_payroll_cost": float(budget)}


SCORECARD_KPIS = [
    # id, label, metric_id, unit, good_direction, detail page
    ("headcount", "Headcount (month end)", "M01", "count", "context", "People & payroll"),
    ("attrition_rate_pct", "Attrition rate (monthly)", "M04", "pct", "lower", "Department view"),
    ("attendance_rate", "Attendance rate", "M13", "ratio", "higher", "People & payroll"),
    ("overtime_share_pct", "Overtime share of payroll", "M11", "pct", "lower", "Department view"),
    ("payroll_cost", "Payroll cost vs budget", "M09", "inr", "lower", "Department view"),
    ("revenue", "Revenue", "M16", "inr", "higher", "Profit & loss"),
    ("operating_margin_pct", "Operating margin", "M18", "pct", "higher", "Profit & loss"),
    ("task_completion_pct", "Task completion rate", "M22", "pct", "higher", "People & payroll"),
]


def _status(value, target, direction, tolerance=0.05):
    if target is None or pd.isna(target) or pd.isna(value):
        return "No target"
    if direction == "higher":
        if value >= target:
            return "Green"
        return "Amber" if value >= target * (1 - tolerance) else "Red"
    if direction == "lower":
        if value <= target:
            return "Green"
        return "Amber" if value <= target * (1 + tolerance) else "Red"
    return "No target"


def scorecard(month: str) -> pd.DataFrame:
    prev = (pd.Period(month, "M") - 1).strftime("%Y-%m")
    people = company_people_month().set_index("month")
    pnl = pnl_monthly().set_index("month")
    tasks = task_completion_month().set_index("month")
    tg = company_targets(month)

    def val(key, m):
        if key == "headcount":
            return people["headcount_end"].get(m, np.nan)
        if key in ("attrition_rate_pct", "attendance_rate", "overtime_share_pct"):
            return people[key].get(m, np.nan)
        if key == "payroll_cost":
            return people["employer_cost"].get(m, np.nan)
        if key in ("revenue", "operating_margin_pct"):
            return pnl[key].get(m, np.nan)
        if key == "task_completion_pct":
            return tasks["task_completion_pct"].get(m, np.nan)
        return np.nan

    target_for = {"attrition_rate_pct": tg.get("attrition_rate_pct"), "attendance_rate": tg.get("attendance_rate"),
                  "overtime_share_pct": tg.get("overtime_share_pct"), "payroll_cost": tg.get("budget_payroll_cost") or None,
                  "task_completion_pct": tg.get("task_completion_pct")}
    rows = []
    for key, label, mid, unit, direction, page in SCORECARD_KPIS:
        v, p = val(key, month), val(key, prev)
        t = target_for.get(key)
        rows.append({"kpi": label, "metric_id": mid, "unit": unit, "value": v, "previous": p,
                     "change": v - p if pd.notna(v) and pd.notna(p) else np.nan,
                     "target": t, "status": _status(v, t, direction), "good_direction": direction,
                     "detail_page": page})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- Task 18: self-service explorer
ROLE_RULES = {
    # role: (allowed metric ids, may see team level, restricted to own department)
    "ADMIN": ({"M01", "M04", "M09", "M10", "M11", "M13", "M22"}, True, False),
    "HR": ({"M01", "M04", "M09", "M10", "M11", "M13"}, True, False),
    "MANAGER": ({"M01", "M13", "M22"}, True, True),
    "EXECUTIVE": ({"M01", "M04", "M09", "M11", "M13", "M22"}, False, False),
}
EXPLORER_METRICS = {
    "M01": "Headcount", "M04": "Attrition rate (monthly)", "M09": "Payroll cost (employer cost)",
    "M10": "Cost per head", "M11": "Overtime share", "M13": "Attendance rate", "M22": "Task completion rate",
}


def min_group_size(metric_id: str) -> int:
    md = load("metric_dictionary").set_index("metric_id")
    raw = str(md["minimum_group_size"].get(metric_id, "5"))
    digits = "".join(ch for ch in raw if ch.isdigit())
    return int(digits) if digits else 5


def demo_users() -> pd.DataFrame:
    path = STARTER / "demo_users.csv"
    if path.exists():
        u = pd.read_csv(path)
        u.columns = [c.strip().lower() for c in u.columns]
        return u
    return pd.DataFrame([
        {"user_id": "U-ADMIN", "name": "Demo Admin", "role": "ADMIN", "department_id": ""},
        {"user_id": "U-HR", "name": "Demo HR", "role": "HR", "department_id": ""},
        {"user_id": "U-MGR-D01", "name": "Demo Manager D01", "role": "MANAGER", "department_id": "D01"},
        {"user_id": "U-EXEC", "name": "Demo Executive", "role": "EXECUTIVE", "department_id": ""},
    ])


def employee_team_map() -> pd.Series:
    """Team for each employee = the team they were most often assigned to on the task board."""
    t = load("fact_task").dropna(subset=["assignee_employee_id"])
    return t.groupby("assignee_employee_id")["team_id"].agg(lambda s: s.value_counts().index[0])


def explorer_base(month: str) -> pd.DataFrame:
    """Employee-month rows for the explorer (never shown directly; only aggregated + suppressed)."""
    pay = clean_payroll()
    pay = pay[pay["month"] == month][["employee_id", "department_id", "employer_cost", "overtime_pay"]]
    att = load("fact_attendance_monthly")
    att = att[att["period_end_date"].astype(str).str[:7] == month][
        ["employee_id", "scheduled_days", "present_days", "half_days_unpaid"]]
    base = pay.merge(att, on="employee_id", how="left")
    base["team_id"] = base["employee_id"].map(employee_team_map()).fillna("No team")
    return base


def explore(metric_id: str, level: str, month: str, role: str, user_department: str = "",
            department_filter: str | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Return (table, messages). level is 'company', 'department' or 'team'."""
    allowed, team_ok, own_dept_only = ROLE_RULES[role]
    msgs: list[str] = []
    if metric_id not in allowed:
        return pd.DataFrame(), [f"Role {role} is not allowed to see {EXPLORER_METRICS.get(metric_id, metric_id)}."]
    if level == "team" and not team_ok:
        return pd.DataFrame(), [f"Role {role} can see company and department level only."]
    n_min = min_group_size(metric_id)

    if metric_id in ("M04",):  # attrition comes from department-level headcount facts only
        d = dept_month_impact()
        d = d[d["month"] == month]
        if level == "team":
            return pd.DataFrame(), ["Attrition is only recorded per department, so there is no team view."]
        if own_dept_only:
            d = d[d["department_id"] == user_department]
        if level == "company":
            g = pd.DataFrame([{"group": "Company", "group_size": d["headcount_start"].sum(),
                               "value": d["exits"].sum() / max(d["headcount_start"].sum(), 1) * 100}])
        else:
            g = d.assign(group=d["department_name"], group_size=d["headcount_start"],
                         value=d["attrition_rate_pct"])[["group", "group_size", "value"]]
        return _suppress(g, n_min, msgs), msgs

    if metric_id == "M22":
        t = load("fact_task")
        s = load("dim_sprint")
        date_col = "end_date" if "end_date" in s.columns else None
        if date_col:
            t = t.merge(s[["sprint_id", date_col]], on="sprint_id", how="left")
            t = t[t[date_col].astype(str).str[:7] == month]
        t = t[t["status"] != "Cancelled"].merge(load("dim_team")[["team_id", "team_name", "department_id"]],
                                                 on="team_id", how="left")
        if own_dept_only:
            t = t[t["department_id"] == user_department]
        if department_filter:
            t = t[t["department_id"] == department_filter]
        key = {"company": None, "department": "department_id", "team": "team_name"}[level]
        if key is None:
            t = t.assign(group="Company")
            key = "group"
        g = t.groupby(key).agg(group_size=("task_id", "count"),
                               value=("status", lambda s: (s == "Done").mean() * 100)).reset_index()
        g = g.rename(columns={key: "group"})
        if level == "department":
            g = add_dept_name(g.rename(columns={"group": "department_id"})).rename(
                columns={"department_name": "group"}).drop(columns="department_id")
        return _suppress(g[["group", "group_size", "value"]], n_min, msgs), msgs

    base = explorer_base(month)
    if own_dept_only:
        base = base[base["department_id"] == user_department]
    if department_filter:
        base = base[base["department_id"] == department_filter]
    if level == "company":
        base["group"] = "Company"
    elif level == "department":
        base = add_dept_name(base)
        base["group"] = base["department_name"]
    else:
        teams = load("dim_team").set_index("team_id")["team_name"]
        base["group"] = base["team_id"].map(teams).fillna(base["team_id"])
    agg = base.groupby("group").agg(group_size=("employee_id", "nunique"), employer_cost=("employer_cost", "sum"),
                                    overtime_pay=("overtime_pay", "sum"), scheduled=("scheduled_days", "sum"),
                                    present=("present_days", "sum"), half=("half_days_unpaid", "sum")).reset_index()
    agg["value"] = {
        "M01": agg["group_size"],
        "M09": agg["employer_cost"],
        "M10": agg["employer_cost"] / agg["group_size"],
        "M11": agg["overtime_pay"] / agg["employer_cost"].replace(0, np.nan) * 100,
        "M13": (agg["present"] + 0.5 * agg["half"]) / agg["scheduled"].replace(0, np.nan),
    }[metric_id]
    return _suppress(agg[["group", "group_size", "value"]], n_min, msgs), msgs


def _suppress(g: pd.DataFrame, n_min: int, msgs: list[str]) -> pd.DataFrame:
    """Hide groups smaller than n_min. If exactly one group is hidden, also hide the next smallest
    (complementary suppression) so it cannot be worked out from the total."""
    g = g.copy()
    small = g["group_size"] < n_min
    if small.sum() == 1 and len(g) > 2:
        nxt = g.loc[~small, "group_size"].idxmin()
        small.loc[nxt] = True
        msgs.append("One extra group was also hidden so the small group cannot be calculated from the total.")
    if small.any():
        msgs.append(f"{int(small.sum())} group(s) have fewer than {n_min} people/records and are hidden.")
    g["value"] = g["value"].astype(float)
    g.loc[small, "value"] = np.nan
    g.loc[small, "group_size"] = np.nan
    g["shown"] = np.where(small, f"Hidden (< {n_min})", "Shown")
    return g.sort_values("group")


# --------------------------------------------------------------------------- Task 19: API metrics + lineage
LINEAGE = {
    "revenue": {"metric_id": "M16", "raw": "PulseIQ_Dataset.xlsx › fact_ledger",
                "etl": "src/etl_pipeline.py (export + normalise)", "warehouse": "fact_ledger ⋈ dim_account (detail accounts only)",
                "view": "src/views.py › pnl_monthly()", "dashboard": "pages/2_Profit_and_loss.py, Scorecard"},
    "operating_margin_pct": {"metric_id": "M18", "raw": "PulseIQ_Dataset.xlsx › fact_ledger",
                             "etl": "src/etl_pipeline.py", "warehouse": "fact_ledger ⋈ dim_account",
                             "view": "src/views.py › pnl_monthly()", "dashboard": "pages/2_Profit_and_loss.py, Scorecard"},
    "payroll_cost": {"metric_id": "M09", "raw": "PulseIQ_Dataset.xlsx › fact_payroll",
                     "etl": "src/etl_pipeline.py + clean_payroll() removes PI-X rows",
                     "warehouse": "fact_payroll ⋈ dim_department", "view": "src/views.py › dept_month_impact()",
                     "dashboard": "pages/4_Department_view.py, Scorecard"},
    "headcount": {"metric_id": "M01", "raw": "PulseIQ_Dataset.xlsx › fact_headcount_monthly",
                  "etl": "src/etl_pipeline.py", "warehouse": "fact_headcount_monthly ⋈ dim_department",
                  "view": "src/views.py › dept_month_impact()", "dashboard": "pages/1_People_and_payroll.py, Scorecard"},
    "overdue_receivables": {"metric_id": "M21", "raw": "PulseIQ_Dataset.xlsx › fact_invoice",
                            "etl": "src/etl_pipeline.py", "warehouse": "fact_invoice ⋈ dim_client",
                            "view": "src/views.py › open_invoices()", "dashboard": "pages/3_Receivables_and_cash.py"},
}


def api_metric(name: str, month: str) -> dict:
    md = load("metric_dictionary").set_index("metric_id")
    lin = LINEAGE[name]
    mid = lin["metric_id"]
    if name in ("revenue", "operating_margin_pct"):
        value = pnl_monthly().set_index("month")[name].get(month, np.nan)
    elif name == "payroll_cost":
        value = company_people_month().set_index("month")["employer_cost"].get(month, np.nan)
    elif name == "headcount":
        value = company_people_month().set_index("month")["headcount_end"].get(month, np.nan)
    else:
        value = overdue_at(min(pd.Period(month, "M").to_timestamp("M"), CUTOFF))
    return {
        "metric": name, "metric_id": mid, "month": month,
        "value": None if pd.isna(value) else round(float(value), 2),
        "unit": md["unit"].get(mid), "definition": md["business_definition"].get(mid),
        "formula": md["formula"].get(mid), "source": md["source_table"].get(mid),
        "lineage": lin, "data_cutoff": CUTOFF_LABEL, "last_refresh": freshness()["last_refresh"],
    }


def freshness() -> dict:
    files = list(Path(os.environ.get("PULSEIQ_TABLES", TABLES)).glob("*.csv"))
    newest = max((f.stat().st_mtime for f in files), default=0)
    return {"data_cutoff": CUTOFF_LABEL,
            "last_refresh": pd.Timestamp(newest, unit="s").strftime("%Y-%m-%d %H:%M UTC") if newest else "unknown",
            "statement": f"Numbers cover Apr 2025 to Sep 2026. Source data is cut off at {CUTOFF_LABEL}."}


# ---------------------------------------------------------------- Final challenge · collections priority
BEHAVIOUR_WEIGHT = {"risky": 1.5, "slow": 1.2}


def collections_priority(top: int | None = None) -> pd.DataFrame:
    """Rank open invoices by expected money at risk.

    score = balance_due x age factor x client behaviour factor
      age factor       = 1 + days_past_due / 90   (an invoice 90 days late counts double)
      behaviour factor = 1.5 risky, 1.2 slow, 1.0 otherwise (from paid-invoice history)
    Invoices not yet due get score 0 and go to the bottom.
    """
    o = open_invoices().copy()
    beh = days_to_pay_by_client()[["client_id", "payment_behaviour", "days_over_terms"]]
    o = o.merge(beh, on="client_id", how="left")
    o["payment_behaviour"] = o["payment_behaviour"].fillna("no history")
    late = o["days_past_due"].clip(lower=0)
    o["age_factor"] = 1 + late / 90
    o["behaviour_factor"] = o["payment_behaviour"].map(BEHAVIOUR_WEIGHT).fillna(1.0)
    o["priority_score"] = (o["balance_due"] * o["age_factor"] * o["behaviour_factor"]).where(late > 0, 0.0)
    o["action"] = pd.cut(late, [-1, 0, 30, 90, 10_000],
                         labels=["Not due — no action", "Friendly reminder", "Call the client",
                                 "Escalate + credit hold"]).astype(str)
    cols = ["invoice_number", "client_name", "due_date", "days_past_due", "balance_due",
            "payment_behaviour", "priority_score", "action"]
    out = o.sort_values("priority_score", ascending=False)[cols].reset_index(drop=True)
    out.index += 1
    return out.head(top) if top else out


def collections_coverage(n: int = 10) -> float:
    """Share of overdue money covered by the top-n invoices on the priority list."""
    p = collections_priority()
    overdue = p.loc[p["days_past_due"] > 0, "balance_due"].sum()
    return float(p.head(n)["balance_due"].sum() / overdue) if overdue else 0.0
