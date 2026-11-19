"""Task 12 · Invoices, receivables and cash flow."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402

from ui import header, inr, note  # noqa: E402
import views as v  # noqa: E402

header("Receivables & cash", "Task 12 · Who owes us money, how fast clients pay, cash in vs cash out")

st.markdown(f"**Open invoice statuses used on this page:** {', '.join(v.OPEN_INVOICE_STATUSES)}. "
            "PAID, CANCELLED and DRAFT invoices are not receivables.")
note("Ageing is measured in days past the due date at the cut-off date (30 Sep 2026). "
     "Invoices not yet due are in the 0-30 bucket.")

age = v.receivables_ageing()
chk = v.ageing_check()
c1, c2, c3 = st.columns(3)
c1.metric("Open receivables", inr(chk["open_receivables"]))
c2.metric("Sum of ageing buckets", inr(chk["bucket_total"]))
c3.metric("DSO (Sep 2026)", f"{v.dso('2026-09'):.0f} days")
if chk["passes"]:
    st.success("Bucket check passed: the four buckets add up exactly to total open receivables.")
else:
    st.error(f"Bucket check failed: difference {chk['difference']:,.2f}")

left, right = st.columns(2)
with left:
    st.plotly_chart(px.bar(age, x="age_bucket", y="balance_due", text="invoices",
                           title="Receivables ageing (balance due, invoice count on bar)"), use_container_width=True)
with right:
    od = v.overdue_by_client(10)
    st.plotly_chart(px.bar(od, x="overdue_balance", y="client_name", orientation="h", color="oldest_days",
                           title="Clients with the most overdue money"), use_container_width=True)

st.subheader("Collections priority list (big and old first)")
st.dataframe(od, hide_index=True, use_container_width=True)

st.subheader("Average days to pay by client")
dtp = v.days_to_pay_by_client()
st.plotly_chart(px.bar(dtp, x="client_name", y=["avg_days_to_pay", "payment_terms_days"], barmode="group",
                       title="Average days to pay vs agreed payment terms"), use_container_width=True)
st.dataframe(dtp.round(1), hide_index=True, use_container_width=True)

st.subheader("Cash in vs cash out")
cash = v.cash_in_out()
fig = go.Figure()
fig.add_bar(x=cash["month"], y=cash["cash_in"], name="Cash in (bank debits)")
fig.add_bar(x=cash["month"], y=-cash["cash_out"], name="Cash out (bank credits)")
fig.add_scatter(x=cash["month"], y=cash["net_cash_flow"], name="Net cash flow", mode="lines+markers")
fig.update_layout(barmode="relative", title="Bank account 1001 movements by month (opening balance excluded)")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Findings")
st.markdown("""
- **Most open money is not late yet:** about ₹13.4 Cr of ₹13.9 Cr open is within 30 days, but **₹30 lakh is more than
  90 days overdue** (Siruvani Agro Tech, an invoice 548 days past due).
- **Several clients pay well beyond their terms:** Triveni Steel and Siruvani Agro Tech average more than 100 days
  against 45-60 day terms.
- **Net cash flow was negative in 5 of 18 months** (May 2025, Jan–Mar 2026 and May 2026) but strongly positive over
  the whole period, so late payers are a working-capital cost, not yet a survival risk.

**Think for yourself: a big client always pays at 75 days. Is that a risk?** Not if it is predictable and priced in,
but it ties up cash. I would ask finance: what are the agreed terms, is the delay in the contract, how much of our
revenue is with this client, and could we offer an early-payment discount or invoice in smaller milestones?
""")
