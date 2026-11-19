"""PulseIQ Analytics — landing page.

Run locally:  streamlit run app.py
The other pages are in the pages/ folder and appear in the sidebar.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

from ui import header, inr  # noqa: E402
import views as v  # noqa: E402

header("PulseIQ Analytics", "Company health for Zenith Nova Technologies")

st.markdown(
    """
**PulseIQ** turns raw HR, payroll, finance and AI feeds into one trusted view of the company:
people, cost, cash and risk. Every number on these pages comes from one governed metric layer
(`src/views.py`) and is checked against the books.

Use the **sidebar** to move between pages:

| Page | Question it answers |
|---|---|
| 1 · People & payroll | How many people, how present, how productive, what do they cost? |
| 2 · Profit & loss | Where is money earned and where does it leak? |
| 3 · Receivables & cash | Who owes us money and is cash coming in? |
| 4 · Department view | Which departments combine high cost, overtime and attrition? |
| 5 · AI signals | What do the anomaly, forecast and attrition models say (with their limits)? |
| 6 · Executive scorecard | Is the company healthy this month? (one A4 page) |
| 7 · KPI explorer | Build your own view safely (role-based, small groups hidden) |
"""
)

month = v.months_available()[-1]
pnl = v.pnl_monthly().set_index("month")
people = v.company_people_month().set_index("month")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Headcount (Sep 2026)", f"{people['headcount_end'].get(month, 0):,.0f}")
c2.metric("Revenue (Sep 2026)", inr(pnl["revenue"].get(month)))
c3.metric("Operating margin", f"{pnl['operating_margin_pct'].get(month):.1f}%")
c4.metric("Open receivables", inr(v.ageing_check()["open_receivables"]))

st.caption(v.freshness()["statement"] + " Small groups are hidden to protect privacy.")
