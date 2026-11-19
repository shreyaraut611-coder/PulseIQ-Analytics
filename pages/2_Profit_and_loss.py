"""Task 11 · Profit and loss, and expense analytics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from ui import header, inr, month_selector, note  # noqa: E402
import views as v  # noqa: E402

header("Profit & loss", "Task 11 · Revenue, expenses, margin, categories and vendors")

pnl = v.pnl_monthly()
month = month_selector("pnl_month")
row = pnl.set_index("month").loc[month]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue (4001-4004)", inr(row["revenue"]))
c2.metric("Expenses (5xxx)", inr(row["expenses"]))
c3.metric("Net profit", inr(row["net_profit"]))
c4.metric("Operating margin", f"{row['operating_margin_pct']:.1f}%")

fig = go.Figure()
fig.add_bar(x=pnl["month"], y=pnl["revenue"], name="Revenue")
fig.add_bar(x=pnl["month"], y=pnl["expenses"], name="Expenses")
fig.add_scatter(x=pnl["month"], y=pnl["operating_margin_pct"], name="Margin %", yaxis="y2", mode="lines+markers")
fig.update_layout(title="Revenue, expenses and margin by month", barmode="group",
                  yaxis2=dict(overlaying="y", side="right", title="Margin %"), legend=dict(orientation="h"))
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader(f"P&L for {month}")
    t = v.pnl_table(month)
    t["amount"] = t["amount"].map(lambda x: f"{x:,.0f}")
    st.dataframe(t, hide_index=True, use_container_width=True, height=420)
with right:
    scope = st.radio("Expense charts cover", ["Selected month", "All 18 months"], horizontal=True)
    m = month if scope == "Selected month" else None
    cat = v.expense_by_category(m)
    st.plotly_chart(px.bar(cat, x="amount_excl_gst", y="category", orientation="h",
                           title="Expenses by category (excl. GST)"), use_container_width=True)
    ven = v.top_vendors(10, m)
    st.plotly_chart(px.bar(ven, x="amount_excl_gst", y="vendor_name", orientation="h",
                           title="Top 10 vendors (excl. GST)"), use_container_width=True)

st.subheader("Tie-out to the books")
note("Only DETAIL accounts (is_group = N) are summed, so a heading such as 5000 Expenses is never added to its "
     "children. The README sheet of this dataset lists row counts, not profit totals, so the P&L is tied to the "
     "ledger itself (debits = credits) and to the payroll and expense facts.")
tie = v.pnl_tieout()
st.dataframe(tie, hide_index=True, use_container_width=True)
bad = tie[(tie["payroll_diff"].abs() > 1) | (tie["expense_diff"].abs() > 1) | (tie["trial_balance_diff"].abs() > 1)]
if bad.empty:
    st.success("Every month ties: trial balance, payroll and expenses.")
else:
    st.warning(f"{len(bad)} month(s) do not fully tie: " + ", ".join(bad["month"]) +
               ". See the findings below for the explanation.")

with st.expander("Account hierarchy (groups vs detail)"):
    st.dataframe(v.account_hierarchy()[["account_code", "account_name", "account_type", "parent_code", "level"]],
                 hide_index=True, use_container_width=True)
with st.expander("Manual journals (year-end accrual and reversal)"):
    st.dataframe(v.manual_journals(), hide_index=True, use_container_width=True)

st.subheader("Findings")
st.markdown("""
1. **Margin is volatile even when revenue grows.** Revenue rose from ₹7.1 Cr (Apr 2025) to ₹8.0 Cr (Sep 2026), but
   margin swings between 8% and 27%. The weakest months (Apr 2025 9%, Jul 2025 8%, Jul 2026 13%) are months with
   high payroll (April bonus and quarter-end incentives).
2. **Payroll is the biggest cost.** Payroll accounts 5001-5005 take 61% to 75% of revenue every month, so a small
   change in pay or headcount moves margin more than any vendor.
3. **Vendor spend is concentrated.** The top 4 vendors (office rent and cloud hosting) take about a third of all
   bills. A ₹18 lakh manual accrual for professional fees was booked in March 2026 and reversed in April 2026, which
   moves profit between those two months.
""")
st.markdown("""
**Think for yourself: revenue grew but margin fell. Three possible causes and the data that would prove each:**
- *Pay rose faster than revenue* → compare payroll cost per head (fact_payroll) with revenue per head month by month.
- *A one-off cost landed in that month* (bonus, accrual, rent deposit) → look at the ledger lines by account and source_type for that month.
- *Revenue mix shifted to lower-margin work* (consulting vs SaaS) → split revenue by account 4001-4004 and compare with effort from fact_task.
""")
