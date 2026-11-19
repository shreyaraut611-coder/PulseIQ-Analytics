"""Phase 4 checks: report builder, new-department robustness, privacy, API metrics."""
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
import views as v  # noqa: E402


# ---------- Task 16: report builder
def test_report_builds_for_any_month(tmp_path):
    import build_report
    for month in (v.months_available()[0], v.months_available()[-1]):
        out = build_report.build(month, tmp_path)
        assert out.exists() and out.stat().st_size > 20_000


def test_report_has_date_range_and_cutoff(tmp_path):
    import subprocess
    import build_report
    out = build_report.build("2026-09", tmp_path)
    if shutil.which("pdftotext"):
        text = subprocess.run(["pdftotext", str(out), "-"], capture_output=True, text=True).stdout
        assert "Reporting period: 01 Sep 2026 to 30 Sep 2026" in text
        assert "Data cut-off: 30 Sep 2026" in text


def test_new_department_next_month_does_not_break_anything(tmp_path, monkeypatch):
    """Think-for-yourself test: copy the data, add a brand-new department D11 with people, payroll and
    headcount, and check every view and the report still work and show it."""
    tables = tmp_path / "tables"
    shutil.copytree(ROOT / "data" / "tables", tables)
    dd = pd.read_csv(tables / "dim_department.csv")
    dd.loc[len(dd)] = {"department_id": "D11", "department_name": "Cyber Security", "cost_center": "CC-011",
                       "description": "New in Sep 2026", "is_leadership": "N"}
    dd.to_csv(tables / "dim_department.csv", index=False)
    hc = pd.read_csv(tables / "fact_headcount_monthly.csv")
    hc.loc[len(hc)] = {"date_key": 20260930, "month_start_date": "2026-09-01", "department_id": "D11",
                       "headcount_start": 0, "hires": 6, "exits": 0, "voluntary_exits": 0, "transfers_in": 0,
                       "transfers_out": 0, "headcount_end": 6, "attrition_rate_monthly_pct": 0.0}
    hc.to_csv(tables / "fact_headcount_monthly.csv", index=False)
    pay = pd.read_csv(tables / "fact_payroll.csv")
    new = pay[pay["date_key"] == 20260930].head(6).copy()
    new["department_id"] = "D11"
    new["payroll_item_id"] = [f"PI-NEW{i}" for i in range(6)]
    new["employee_id"] = [f"EMP-N{i}" for i in range(6)]
    pd.concat([pay, new]).to_csv(tables / "fact_payroll.csv", index=False)

    monkeypatch.setenv("PULSEIQ_TABLES", str(tables))
    v.clear_cache()
    try:
        d = v.dept_month_impact()
        row = d[(d["department_id"] == "D11") & (d["month"] == "2026-09")]
        assert len(row) == 1 and row["department_name"].iloc[0] == "Cyber Security"
        assert row["paid_employees"].iloc[0] == 6
        assert len(v.scorecard("2026-09")) == 8
        import build_report
        assert build_report.build("2026-09", tmp_path / "out").exists()
    finally:
        v.clear_cache()


# ---------- Task 18: privacy ("try to break it")
@pytest.mark.parametrize("metric", ["M01", "M09", "M10", "M11", "M13"])
def test_no_visible_group_is_below_minimum(metric):
    n = v.min_group_size(metric)
    for level in ("company", "department", "team"):
        t, _ = v.explore(metric, level, "2026-09", "ADMIN")
        visible = t.dropna(subset=["value"])
        assert (visible["group_size"] >= n).all()


def test_single_hidden_group_triggers_complementary_suppression():
    t, msgs = v.explore("M09", "department", "2026-09", "HR")
    assert t["value"].isna().sum() >= 2   # Executive Office (1 person) + one more
    assert any("extra group" in m for m in msgs)


def test_small_team_filter_cannot_reveal_one_person():
    # Legal & Compliance has ~11 people who are mostly not on the task board
    for dept in v.departments()["department_id"]:
        t, _ = v.explore("M10", "team", "2026-09", "ADMIN", department_filter=dept)
        visible = t.dropna(subset=["value"])
        assert (visible["group_size"] >= 5).all()


def test_roles_see_different_data():
    mgr, msgs = v.explore("M09", "department", "2026-09", "MANAGER", "D01")
    assert mgr.empty and "not allowed" in msgs[0]
    exe, msgs = v.explore("M01", "team", "2026-09", "EXECUTIVE")
    assert exe.empty and "company and department" in msgs[0]
    own, _ = v.explore("M01", "department", "2026-09", "MANAGER", "D01")
    assert set(own["group"]) == {"Engineering"}


def test_attrition_has_no_team_view_and_uses_min_10():
    t, msgs = v.explore("M04", "team", "2026-09", "ADMIN")
    assert t.empty
    t, _ = v.explore("M04", "department", "2026-09", "ADMIN")
    assert (t.dropna(subset=["value"])["group_size"] >= 10).all()


# ---------- Task 19: API metrics
def test_each_api_metric_returns_definition_source_and_freshness():
    for name in v.LINEAGE:
        r = v.api_metric(name, "2026-09")
        assert r["value"] is not None
        assert r["definition"] and r["source"] and r["formula"]
        assert r["data_cutoff"] == "30 Sep 2026" and r["last_refresh"]
        assert set(r["lineage"]) >= {"raw", "etl", "warehouse", "view", "dashboard"}


def test_api_values_match_the_dashboard_views():
    assert v.api_metric("revenue", "2026-09")["value"] == round(v.pnl_monthly().set_index("month").loc["2026-09", "revenue"], 2)
    open_inv = v.open_invoices()
    assert v.api_metric("overdue_receivables", "2026-09")["value"] == round(open_inv.loc[open_inv.days_past_due > 0, "balance_due"].sum(), 2)
