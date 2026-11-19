"""Final challenge · Collections priority list — which invoices to chase first, and how."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from ui import header, inr, note  # noqa: E402
import views as v  # noqa: E402

header("Collections priority", "Final challenge · Which overdue invoices to chase first")

note("Score = balance due × (1 + days past due ÷ 90) × client factor (1.5 risky payer, 1.2 slow payer, 1.0 otherwise). "
     "Client behaviour comes from how late each client paid its past invoices. Invoices not yet due score 0.")

top_n = st.slider("Invoices on this week's list", 5, 30, 10)
p = v.collections_priority()
overdue_total = p.loc[p["days_past_due"] > 0, "balance_due"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Overdue money (30 Sep 2026)", inr(overdue_total))
c2.metric(f"Covered by top {top_n}", f"{v.collections_coverage(top_n):.0%}")
c3.metric("Invoices to escalate (90+ days)", int((p["days_past_due"] > 90).sum()))

show = p.head(top_n).copy()
show["balance_due"] = show["balance_due"].map(inr)
show["priority_score"] = show["priority_score"].round(0).map("{:,.0f}".format)
show["due_date"] = show["due_date"].dt.date
st.dataframe(show, use_container_width=True)
st.download_button("Download this week's list (CSV)", p.head(top_n).to_csv(index=True), "collections_list.csv")

by_action = p[p["days_past_due"] > 0].groupby("action", as_index=False)["balance_due"].sum()
st.plotly_chart(px.bar(by_action, x="action", y="balance_due", title="Overdue money by recommended action",
                       labels={"balance_due": "₹", "action": ""}), use_container_width=True)

st.subheader("Findings")
st.markdown(
    f"- The top 10 invoices cover **{v.collections_coverage(10):.0%}** of all overdue money, so a short weekly list is enough.\n"
    "- Two old invoices (Siruvani Agro Tech, 548 days; Triveni Steel Industries, 438 days) rank first even though "
    "bigger invoices exist — age and payment history push them up.\n"
    "- Siruvani Agro Tech appears three times in the top 5: one call can cover several invoices."
)
st.subheader("Think for yourself")
st.markdown(
    "- **Why not just sort by amount?** A large invoice that is 5 days late usually gets paid anyway; "
    "a smaller one that is 18 months late may never be paid without action.\n"
    "- **What would change the weights?** Real recovery data: if we learn which reminders worked, "
    "the 1.5 / 1.2 factors and the 90-day scale can be fitted instead of chosen."
)
