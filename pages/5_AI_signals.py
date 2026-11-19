"""Task 14 · AI signals dashboard."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from ui import ai_label, header, inr, note  # noqa: E402
import views as v  # noqa: E402

header("AI signals", "Task 14 · Anomalies, forecasts and attrition risk — with their limits")

st.subheader("Anomalies by type, ranked by money at risk")
ai_label()
an = v.anomalies_by_type()
an["label"] = an["reason_code"] + " (" + an["source_dataset"].str.replace("_monthly_features", "") + ")"
st.plotly_chart(px.bar(an, x="money_at_risk", y="label", orientation="h", text="flags",
                       title="Money at risk by anomaly type (number of flags on bar)"), use_container_width=True)
note("Payroll anomalies carry money at risk; attendance anomalies do not (the model gives no amount for them), so "
     "they are ranked by count. A flag is a lead for a person to check, not proof of an error.")
st.dataframe(an.drop(columns="label"), hide_index=True, use_container_width=True)
c1, c2 = st.columns(2)
c1.metric("Total money at risk (payroll flags)", inr(an["money_at_risk"].sum()))
c2.metric("Total flags", f"{an['flags'].sum():,}")

st.subheader("Headcount forecast vs actual, with the 80% band")
ai_label()
fa = v.forecast_vs_actual("ALL")
fig = go.Figure()
fig.add_scatter(x=fa["month"], y=fa["actual"], name="Actual headcount", mode="lines")
band = fa.dropna(subset=["forecast_value"])
fig.add_scatter(x=band["month"], y=band["upper_80"], line=dict(width=0), showlegend=False)
fig.add_scatter(x=band["month"], y=band["lower_80"], fill="tonexty", line=dict(width=0), name="80% band")
fig.add_scatter(x=band["month"], y=band["forecast_value"], name="Forecast", mode="lines+markers",
                line=dict(dash="dash"))
fig.update_layout(title="Company headcount: actuals to Sep 2026, model forecast Oct 2026 – Mar 2027")
st.plotly_chart(fig, use_container_width=True)
note("The supplied forecasts start in October 2026, after the data cut-off, so no forecast month has an actual yet. "
     "To still measure accuracy honestly, the table below back-tests a simple trend model trained to March 2026 "
     "against the real April–September 2026 headcount.")

bt = v.backtest_headcount()
st.subheader("Forecast error for months with known actuals (back-test)")
ai_label()
show = bt[["month", "actual", "forecast_value", "lower_80", "upper_80", "abs_pct_error", "inside_band"]].copy()
show["month"] = show["month"].dt.strftime("%Y-%m")
st.dataframe(show.round(1), hide_index=True, use_container_width=True)
st.metric("Back-test MAPE (M28)", f"{bt['abs_pct_error'].mean():.1f}%",
          help=f"{int(bt['inside_band'].sum())} of {len(bt)} actuals fell inside the 80% band")

st.subheader("Attrition risk by department (groups only, never named people)")
ai_label()
r = v.attrition_risk_by_department()
st.plotly_chart(px.bar(r.dropna(subset=["high_risk_share_pct"]), x="department_name", y="high_risk_share_pct",
                       title="Share of employees in the High risk band"), use_container_width=True)
note("Departments with fewer than 10 scored employees are hidden. The model note says it is a baseline demo model: "
     "a support signal for HR, never a decision about a person.")

st.markdown("""
**Think for yourself: forecast error was 12% last month — is that good?** It depends. For company headcount (≈440
people) 12% means about 50 people, which is too large to plan hiring on; our back-test error is about 2-3%. For a
10-person department 12% is about one person and is normal. I would need to know the metric, the size of the group,
the error of a naive "same as last month" forecast, and what decision the forecast is used for.
""")
