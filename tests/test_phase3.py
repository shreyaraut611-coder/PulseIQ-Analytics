"""Phase 3 checks: each test matches a line of the completion checklist."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import views as v  # noqa: E402


# Task 11
def test_no_group_account_is_summed():
    lines = v._pl_lines()
    groups = v.load("dim_account").query("is_group == 'Y'")["account_code"]
    assert not lines["account_code"].isin(groups).any()


def test_pnl_ties_to_trial_balance_and_expense_facts():
    tie = v.pnl_tieout()
    assert (tie["trial_balance_diff"].abs() < 1).all()
    assert (tie["expense_diff"].abs() < 1).all()
    # payroll ties in every month except the one known ledger gap (Jun 2026)
    assert (tie["payroll_diff"].abs() > 1).sum() <= 1


def test_pnl_table_net_profit_matches_monthly_view():
    month = "2026-09"
    t = v.pnl_table(month).set_index("account_name")["amount"]
    m = v.pnl_monthly().set_index("month").loc[month]
    assert abs(t["NET PROFIT"] - m["net_profit"]) < 1


def test_top_vendors_are_sorted_and_ten():
    tv = v.top_vendors(10)
    assert len(tv) == 10
    assert tv["amount_excl_gst"].is_monotonic_decreasing


# Task 12
def test_ageing_buckets_add_up_to_open_receivables():
    assert v.ageing_check()["passes"]


def test_only_open_statuses_are_receivables():
    assert set(v.open_invoices()["status"]) <= set(v.OPEN_INVOICE_STATUSES)


def test_cash_view_covers_all_months():
    assert len(v.cash_in_out()) == len(v.months_available())


# Task 13
def test_department_month_grain_is_unique():
    d = v.dept_month_impact()
    assert not d.duplicated(["department_id", "month"]).any()


def test_department_view_payroll_equals_clean_payroll():
    d = v.dept_month_impact()
    assert abs(d["employer_cost"].sum() - v.clean_payroll()["employer_cost"].sum()) < 1


def test_planted_payroll_rows_are_removed():
    assert len(v.payroll_quarantine()) == 4
    assert not v.clean_payroll()["payroll_item_id"].str.startswith("PI-X").any()


# Task 14
def test_anomalies_ranked_by_money():
    a = v.anomalies_by_type()
    assert a["money_at_risk"].is_monotonic_decreasing


def test_backtest_has_error_for_every_known_month():
    bt = v.backtest_headcount()
    assert len(bt) == 6 and bt["abs_pct_error"].notna().all()


def test_attrition_risk_never_shows_small_departments():
    r = v.attrition_risk_by_department(min_group=10)
    assert r.loc[r["employees"] < 10, "high_risk_share_pct"].isna().all()


# Task 15
def test_scorecard_has_8_kpis_with_metric_ids():
    sc = v.scorecard("2026-09")
    assert len(sc) == 8
    md = set(v.load("metric_dictionary")["metric_id"])
    assert set(sc["metric_id"]) <= md


def test_scorecard_status_follows_targets():
    sc = v.scorecard("2026-09").set_index("kpi")
    r = sc.loc["Attendance rate"]
    expected = "Green" if r["value"] >= r["target"] else ("Amber" if r["value"] >= r["target"] * 0.95 else "Red")
    assert r["status"] == expected
    assert np.isnan(sc.loc["Revenue", "target"]) and sc.loc["Revenue", "status"] == "No target"
