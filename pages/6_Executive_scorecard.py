"""Task 15 · The executive company-health scorecard (one A4 page)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from ui import header, inr, month_selector  # noqa: E402
import views as v  # noqa: E402

header("Executive scorecard", "Task 15 · 8 headline KPIs: value, target, trend, status")

st.markdown("<style>@media print {section[data-testid='stSidebar'], header {display:none;} "
            ".block-container {padding:0.5cm !important;}}</style>", unsafe_allow_html=True)

month = month_selector("score_month")
sc = v.scorecard(month)

PAGES = {"People & payroll": "pages/1_People_and_payroll.py", "Profit & loss": "pages/2_Profit_and_loss.py",
         "Department view": "pages/4_Department_view.py"}
ICON = {"Green": "🟢", "Amber": "🟠", "Red": "🔴", "No target": "⚪"}


def fmt(unit, x):
    if pd.isna(x):
        return "–"
    if unit == "inr":
        return inr(x)
    if unit == "pct":
        return f"{x:.1f}%"
    if unit == "ratio":
        return f"{x:.1%}"
    return f"{x:,.0f}"


cols = st.columns(4)
for i, r in sc.iterrows():
    with cols[i % 4]:
        arrow = "▲" if r["change"] > 0 else ("▼" if r["change"] < 0 else "■")
        st.markdown(f"**{ICON[r['status']]} {r['kpi']}**")
        st.markdown(f"<span style='font-size:1.6em'>{fmt(r['unit'], r['value'])}</span>", unsafe_allow_html=True)
        st.caption(f"Target: {fmt(r['unit'], r['target'])} · {arrow} vs last month: {fmt(r['unit'], r['previous'])} "
                   f"· {r['metric_id']}")
        st.page_link(PAGES[r["detail_page"]], label=f"Details → {r['detail_page']}")

st.divider()
st.caption("Statuses follow kpi_targets (attendance, overtime, attrition, task completion) and the payroll budget. "
           "Green = on target, Amber = within 5%, Red = worse. Revenue, margin and headcount have no target in "
           "kpi_targets, so they show the trend only. Every number comes from a metric view in src/views.py.")

with st.expander("Why these 8 KPIs"):
    st.markdown("""
- **Headcount** — the size of the company; every cost and capacity number depends on it.
- **Attrition rate** — losing people is expensive and slows delivery.
- **Attendance rate** — the simplest health signal for engagement and capacity.
- **Overtime share** — early warning of overload and burnout.
- **Payroll cost vs budget** — the biggest cost line, compared with what was planned.
- **Revenue** — is the business growing?
- **Operating margin** — is growth profitable?
- **Task completion rate** — are teams delivering what they planned?

**If I could show only 5:** I would remove headcount (it is context, not health), attendance (it rarely moves and is
already behind attrition and overtime) and task completion (it is a team-level measure). Revenue, margin, payroll vs
budget, attrition and overtime tell a founder about money and people risk in under two minutes.
""")
