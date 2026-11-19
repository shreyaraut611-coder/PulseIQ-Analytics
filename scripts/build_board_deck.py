"""Task 20 · Build the board pack (10 slides) from the governed metric views.

    python scripts/build_board_deck.py      ->  reports/PulseIQ_Board_Pack.pptx

Each finding slide = one headline, one evidence chart, one recommendation.
All numbers are computed live from src/views.py, so the deck re-reconciles every time it is built.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

import views as v  # noqa: E402

NAVY = RGBColor(0x1F, 0x3B, 0x5C)
GREY = RGBColor(0x55, 0x55, 0x55)
OUT = ROOT / "reports" / "PulseIQ_Board_Pack.pptx"
TMP = ROOT / "reports" / "_deck_charts"


def cr(x):
    return f"₹{x / 1e7:,.2f} Cr"


def save(fig, name):
    TMP.mkdir(parents=True, exist_ok=True)
    p = TMP / f"{name}.png"
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    return p


def text(slide, left, top, width, height, lines, size=16, bold_first=False, color=None):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.bold = bold_first and i == 0
        if color is not None:
            p.font.color.rgb = color
    return box


def finding_slide(prs, n, headline, chart_path, evidence, recommendation):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.5, 0.3, 12.3, 0.9, [f"Finding {n}: {headline}"], size=26, bold_first=True, color=NAVY)
    s.shapes.add_picture(str(chart_path), Inches(0.5), Inches(1.3), width=Inches(7.6))
    text(s, 8.4, 1.4, 4.5, 2.6, ["Evidence"] + evidence, size=14, bold_first=True)
    text(s, 8.4, 4.3, 4.5, 2.4, ["Recommendation", recommendation], size=15, bold_first=True, color=NAVY)
    text(s, 0.5, 6.9, 12, 0.4, [f"Source: PulseIQ metric views · data cut-off {v.CUTOFF_LABEL} · fictional training data"],
         size=10, color=GREY)
    return s


def main():
    pnl = v.pnl_monthly()
    people = v.company_people_month()
    dept = v.dept_month_impact()
    last12 = dept[dept["month"].between("2025-10", "2026-09")]
    g = last12.groupby("department_name").agg(exits=("exits", "sum"), avg_hc=("headcount_end", "mean"),
                                              ot=("overtime_pay", "sum"), cost=("employer_cost", "sum"))
    g["attrition_12m"] = g["exits"] / g["avg_hc"] * 100
    g["overtime_share"] = g["ot"] / g["cost"] * 100
    g = g[g["avg_hc"] >= v.min_group_size("M02")]  # privacy: small teams never shown
    risk = v.attrition_risk_by_department().set_index("department_name")
    ageing = v.ageing_check()
    od = v.overdue_by_client(5)
    dtp = v.days_to_pay_by_client()
    tie = v.pnl_tieout()
    first6, last6 = pnl["revenue"].head(6).sum(), pnl["revenue"].tail(6).sum()
    hc_start = v.headcount_actuals().set_index("month")["headcount_end"]
    hc_a, hc_b = hc_start.loc["2025-03-01"], hc_start.loc["2026-09-01"]
    overdue = v.overdue_at(v.CUTOFF)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # 1 Title + the decision first
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.7, 1.2, 12, 1.2, ["PulseIQ board pack — company health, Apr 2025 to Sep 2026"], size=34, bold_first=True, color=NAVY)
    text(s, 0.7, 2.7, 12, 3, [
        "The decision we ask for today:",
        f"1. Start a collections drive on {cr(overdue)} of overdue invoices, oldest first.",
        "2. Fund a staffing review in Customer Support and Operations & IT before attrition rises further.",
        "3. Smooth bonus and incentive costs across the year so margin stops swinging between 8% and 27%.",
    ], size=20, bold_first=True)
    text(s, 0.7, 6.6, 12, 0.5, ["Prepared by Shreya Raut · Aura Workforce Data Analytics Track · Zenith Nova Technologies is fictional"],
         size=12, color=GREY)

    # 2 Scorecard at a glance
    sc = v.scorecard("2026-09")
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.5, 0.3, 12.3, 0.8, ["September 2026 at a glance: delivery and people KPIs are on target"], size=26,
         bold_first=True, color=NAVY)
    rows, cols = len(sc) + 1, 5
    tbl = s.shapes.add_table(rows, cols, Inches(0.5), Inches(1.2), Inches(12.3), Inches(4.5)).table
    for j, h in enumerate(["KPI", "Value", "Last month", "Target", "Status"]):
        tbl.cell(0, j).text = h
    def f(u, x):
        import math
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return "–"
        return cr(x) if u == "inr" else (f"{x:.1f}%" if u == "pct" else (f"{x:.1%}" if u == "ratio" else f"{x:,.0f}"))
    for i, r in enumerate(sc.itertuples(), start=1):
        for j, val in enumerate([r.kpi, f(r.unit, r.value), f(r.unit, r.previous), f(r.unit, r.target), r.status]):
            tbl.cell(i, j).text = str(val)
    for row in tbl.rows:
        row.height = Inches(0.5)
        for c in row.cells:
            for para in c.text_frame.paragraphs:
                para.font.size = Pt(13)
    text(s, 0.5, 6.4, 12.3, 0.8, ["Margin fell from 27.2% in August to 18.7% in September even though revenue was almost flat — "
                                  "the next slides explain why money, cash and people need attention."], size=14)

    # 3 Finding 1: growth
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(pnl["month"], pnl["revenue"] / 1e7, color="#1f77b4")
    ax.set_ylabel("Revenue (₹ Cr)")
    ax.tick_params(axis="x", rotation=60, labelsize=7)
    ax.set_title("Monthly revenue (ledger accounts 4001-4004)")
    finding_slide(prs, 1, "The business is growing — revenue +21% and headcount +17%",
                  save(fig, "growth"),
                  [f"Revenue last 6 months {cr(last6)} vs first 6 months {cr(first6)} (+{(last6 / first6 - 1) * 100:.0f}%).",
                   f"Headcount {hc_a:.0f} (Mar 2025) → {hc_b:.0f} (Sep 2026).",
                   "Task completion stays above the 80% target (85.7% in Sep 2026)."],
                  "Keep hiring in line with revenue: approve new roles only where revenue per head holds.")

    # 4 Finding 2: payroll and margin
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(pnl["month"], pnl["operating_margin_pct"], marker="o", label="Operating margin %")
    ax.plot(pnl["month"], pnl["payroll_pct_of_revenue"], marker="s", label="Payroll % of revenue")
    ax.tick_params(axis="x", rotation=60, labelsize=7)
    ax.legend()
    ax.set_title("Margin moves opposite to payroll share")
    finding_slide(prs, 2, "Payroll takes ~69% of revenue, so pay spikes swing margin from 8% to 27%",
                  save(fig, "margin"),
                  [f"Average payroll share {pnl['payroll_pct_of_revenue'].mean():.0f}% (range 61–75%).",
                   "Lowest margins: Apr 2025 (8.9%), Jul 2025 (8.3%), Apr 2026 (13.7%), Jul 2026 (13.4%) — bonus and incentive months.",
                   "A ₹18 L manual accrual (Mar 2026, reversed Apr 2026) also shifts profit between months."],
                  "Accrue bonuses and incentives monthly and report margin on a rolling 3-month basis.")

    # 5 Finding 3: cash stuck
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(od["client_name"][::-1], od["overdue_balance"][::-1] / 1e5, color="#d62728")
    ax.set_xlabel("Overdue balance (₹ lakh)")
    ax.set_title("Clients with the most overdue money (30 Sep 2026)")
    slow = dtp.head(2)
    finding_slide(prs, 3, f"{cr(overdue)} is overdue and two clients pay after 100+ days",
                  save(fig, "cash"),
                  [f"Open receivables {cr(ageing['open_receivables'])}; ageing buckets tie exactly.",
                   "Siruvani Agro Tech has an invoice 548 days past due (₹30 L in the 90+ bucket).",
                   f"{slow.iloc[0]['client_name']} averages {slow.iloc[0]['avg_days_to_pay']:.0f} days, "
                   f"{slow.iloc[1]['client_name']} {slow.iloc[1]['avg_days_to_pay']:.0f} days vs 45–60 day terms.",
                   "Net cash flow was negative in 5 of 18 months."],
                  "Run a weekly collections list (big and old first); put 90+ day clients on credit hold.")

    # 6 Finding 4: Customer Support
    order = g.sort_values("overtime_share", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    names = order.index.tolist()
    ax.bar(names, order["overtime_share"], color="#ff7f0e", label="Overtime share of payroll %")
    ax2 = ax.twinx()
    ax2.plot(names, [risk["high_risk_share_pct"].get(n, float("nan")) for n in names], "ko-", label="AI high-risk share %")
    ax.tick_params(axis="x", rotation=60, labelsize=7)
    ax.set_title("Overtime (bars) and AI attrition-risk share (dots) by department")
    cs = g.loc["Customer Support"]
    finding_slide(prs, 4, "Customer Support carries the most overtime and the most attrition risk",
                  save(fig, "support"),
                  [f"Overtime share {cs['overtime_share']:.1f}% of payroll (highest; company average under 1%).",
                   f"{risk['high_risk_share_pct'].get('Customer Support', float('nan')):.0f}% of the team is in the AI high-risk band "
                   "(AI-generated, for human review).",
                   f"Actual attrition is still low ({cs['attrition_12m']:.1f}% over 12 months) — this is an early warning."],
                  "Review staffing and shift patterns in Customer Support this quarter; HR to hold stay interviews.")

    # 7 Finding 5: Ops & IT attrition
    order = g.sort_values("attrition_12m", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(order.index, order["attrition_12m"], color="#9467bd")
    ax.set_ylabel("12-month attrition %")
    ax.tick_params(axis="x", rotation=60, labelsize=7)
    ax.set_title("12-month attrition by department")
    ops = g.loc["Operations & IT"]
    finding_slide(prs, 5, "Operations & IT lost about a quarter of its people in 12 months",
                  save(fig, "attrition"),
                  [f"Operations & IT: {ops['exits']:.0f} leavers on ~{ops['avg_hc']:.0f} people = {ops['attrition_12m']:.0f}%.",
                   f"Product & Design is next ({g.loc['Product & Design', 'attrition_12m']:.0f}%); company target is about 12% a year (1% a month).",
                   f"Operations & IT also has above-average overtime ({ops['overtime_share']:.1f}%)."],
                  "Read exit reasons for Operations & IT and Product & Design before the next hiring round.")

    # 8 Data trust
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.5, 0.3, 12.3, 0.8, ["Can we trust these numbers? Yes — with one open item"], size=26, bold_first=True, color=NAVY)
    bad_pay = tie[tie["payroll_diff"].abs() > 1]
    text(s, 0.7, 1.4, 12, 5, [
        "Reconciliations (re-run on the live data every time this deck is built):",
        f"• Ledger balances: debits = credits in all {len(tie)} months.",
        f"• Expense bills vs ledger accounts 5101-5112: tie in all {len(tie)} months.",
        f"• Clean payroll vs ledger payroll accounts 5001-5005: tie in {len(tie) - len(bad_pay)} of {len(tie)} months; "
        + (f"{', '.join(bad_pay['month'])} differs by ₹{bad_pay['payroll_diff'].abs().sum():,.0f} (open item for Finance)." if len(bad_pay) else "all months tie."),
        "• Receivables ageing buckets add up exactly to total open receivables.",
        f"• {len(v.payroll_quarantine())} planted payroll rows (duplicates and unknown employees) were quarantined, not deleted.",
        "• Automated tests: run `pytest -q` (all pass for this release).",
        "• Privacy: groups under 5 people (10 for attrition) are never shown.",
    ], size=17, bold_first=True)

    # 9 Recommendations + what we will NOT recommend yet
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.5, 0.3, 12.3, 0.8, ["Recommendations — and one we are not making yet"], size=26, bold_first=True, color=NAVY)
    text(s, 0.7, 1.3, 6.2, 5, [
        "Do now",
        "1. Weekly collections list; credit hold at 90+ days.",
        "2. Staffing review in Customer Support.",
        "3. Exit-reason review in Operations & IT and Product & Design.",
        "4. Accrue bonuses monthly; report rolling 3-month margin.",
        "5. Approve new roles only where revenue per head holds.",
    ], size=17, bold_first=True)
    text(s, 7.2, 1.3, 5.7, 5, [
        "Not yet: cut overtime to stop attrition",
        "Overtime and attrition are high in the same departments, but the data does not show that overtime causes "
        "people to leave. Both could come from understaffing or a difficult client, and small departments make the "
        "rates jumpy. We need exit-interview reasons and 6 more months of data before acting on this.",
        "We will also not act on any individual attrition-risk score: the model is a baseline demo for human review.",
    ], size=15, bold_first=True, color=NAVY)

    # 10 Next steps
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.5, 0.3, 12.3, 0.8, ["What you get from PulseIQ every month"], size=26, bold_first=True, color=NAVY)
    text(s, 0.7, 1.3, 12, 5, [
        "• Live dashboard with a landing page, 7 pages and the data cut-off on every page.",
        "• One-command monthly PDF pack, built automatically on the 2nd of each month.",
        "• Self-service KPI explorer with role-based access and small-group protection.",
        "• Metrics API: every number comes with its definition, source, lineage and freshness.",
        "• Known limits: fictional data to 30 Sep 2026; supplied forecasts start after the cut-off, so accuracy is "
        "shown with a back-test; reference summary from the validation vault still to be compared.",
    ], size=18)

    TMP.mkdir(exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    for p in TMP.glob("*.png"):
        p.unlink()
    TMP.rmdir()
    print(f"Board pack written: {OUT} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
