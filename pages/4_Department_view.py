"""Task 13 · Cross-department impact view."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from ui import header, month_selector, note  # noqa: E402
import views as v  # noqa: E402

header("Department view", "Task 13 · Headcount, payroll, attendance and leave per department and month")

note("Grain: one row per department and month. Each source (headcount, payroll, attendance, leave) is aggregated "
     "to that grain FIRST and then joined, so no join can multiply rows. Join order: headcount (base) → payroll → "
     "attendance → leave, all LEFT joins on department_id + month.")

d = v.dept_month_impact()
month = month_selector("dept_month")
m = d[d["month"] == month].copy()
# Privacy: pay is hidden for groups under 5 people and attrition for groups under 10 (metric dictionary).
small_pay = m["headcount_end"] < 5
if small_pay.sum() == 1:  # complementary suppression: the company total is shown below, so hide one more group
    small_pay.loc[m.loc[~small_pay, "headcount_end"].idxmin()] = True
m.loc[small_pay, ["employer_cost", "cost_per_head", "overtime_pay", "overtime_share_pct"]] = float("nan")
m.loc[m["headcount_start"] < 10, "attrition_rate_pct"] = float("nan")
if small_pay.any():
    st.caption("Pay is hidden for departments with fewer than 5 people (plus one more, so it cannot be worked out "
               "from the company total), and attrition for fewer than 10: "
               + ", ".join(m.loc[small_pay, "department_name"]) + ".")

fig = px.scatter(m.dropna(subset=["employer_cost", "overtime_share_pct", "attrition_rate_pct"]), x="overtime_share_pct", y="attrition_rate_pct", size="employer_cost", color="department_name",
                 hover_data=["headcount_end", "cost_per_head", "leave_days_per_head", "attendance_rate"],
                 title=f"Cost (bubble size), overtime share and attrition by department — {month}")
st.plotly_chart(fig, use_container_width=True)

cols = ["department_name", "headcount_end", "paid_employees", "employer_cost", "cost_per_head", "overtime_pay",
        "overtime_share_pct", "attendance_rate", "exits", "attrition_rate_pct", "leave_days", "leave_days_per_head"]
st.dataframe(m[cols].round(2), hide_index=True, use_container_width=True)

st.subheader("Reconciliation with the reference summary (04_Validation_Vault)")
comp, common = v.reference_comparison()
if comp.empty:
    st.warning("Put `reference_summary_dept_month.csv` from your kit's 04_Validation_Vault (unlock_PQ-13) into "
               "`data/vault/` to run the comparison. Until then, the page checks its own totals below.")
else:
    diff_cols = [f"{c}_diff" for c in common]
    st.dataframe(comp[["department_id", "month", "_merge"] + diff_cols], hide_index=True, use_container_width=True)
    nonzero = comp[(comp[diff_cols].abs() > 0.5).any(axis=1)]
    st.write(f"{len(nonzero)} department-month rows differ from the reference.")

tot = d.groupby("month")[["employer_cost"]].sum().rename(columns={"employer_cost": "dept_view_payroll"})
tie = v.pnl_tieout().set_index("month")[["payroll_fact_employer_cost", "payroll_ledger_5001_5005"]]
st.dataframe(tot.join(tie).assign(diff_vs_ledger=lambda x: x["dept_view_payroll"] - x["payroll_ledger_5001_5005"]).round(0),
             use_container_width=True)
st.markdown("""
**Differences explained:**
- 4 planted payroll rows (PI-X0001 to PI-X0004: two exact duplicates and two rows for unknown employees with
  employee_key = -1) are removed. That is why this view is lower than the raw payroll fact in those months.
- **June 2026:** the ledger payroll accounts are ₹18,450 higher than the clean payroll fact. The payroll run itself
  ties; the gap sits in the ledger and should be checked against dq_known_issues.
- Leave is counted in the month the leave **starts**, using the employee's department from dim_employee (employee_key).

**Think for yourself: overtime is high where attrition is high — does overtime cause attrition?** Not proven. Both
could be caused by understaffing, a hard client or a bad manager; leavers create overtime for those who stay
(reverse cause); and small departments make rates jumpy. I would look at timing (does overtime rise *before* exits?),
compare teams inside the same department, and read exit-interview reasons.
""")
