"""Task 16 · Build the monthly management report pack with ONE command.

Usage (from the repository root):
    python build_report.py                 # latest month in the data
    python build_report.py --month 2026-08 # any month
    python build_report.py --month 2026-08 --out reports/monthly

Creates reports/monthly/PulseIQ_Monthly_Report_<month>.pdf with 5 sections:
  1. Executive scorecard (8 KPIs vs target)
  2. Profit & loss trend (last 12 months) and the month's P&L summary
  3. Department table (headcount, cost, overtime, attendance, attrition)
  4. Receivables ageing and the slowest payers
  5. AI signals: top anomaly types by money at risk (labelled as AI output)
Every page is stamped with the date range, the data cut-off and the build time.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

import views as v  # noqa: E402


def inr(x) -> str:
    if pd.isna(x):
        return "-"
    x = float(x)
    if abs(x) >= 1e7:
        return f"Rs {x / 1e7:,.2f} Cr"
    if abs(x) >= 1e5:
        return f"Rs {x / 1e5:,.2f} L"
    return f"Rs {x:,.0f}"


def fmt(unit, x) -> str:
    if pd.isna(x):
        return "-"
    return {"inr": inr, "pct": lambda y: f"{y:.1f}%", "ratio": lambda y: f"{y:.1%}"}.get(unit, lambda y: f"{y:,.0f}")(x)


def table(data, widths=None, header_bg="#1f3b5c"):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def chart(fig, path: Path, width=17 * cm):
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    img = Image(str(path))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth, img.drawHeight = width, width * ratio
    return img


def build(month: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "_charts"
    tmp.mkdir(exist_ok=True)
    months = v.months_available()
    if month not in months:
        raise SystemExit(f"Month {month} is not in the data. Available: {months[0]} to {months[-1]}")
    period_start = pd.Period(month, "M").to_timestamp().strftime("%d %b %Y")
    period_end = pd.Period(month, "M").to_timestamp("M").strftime("%d %b %Y")
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stamp = f"Reporting period: {period_start} to {period_end}  |  Data cut-off: {v.CUTOFF_LABEL}  |  Built: {built}"

    styles = getSampleStyleSheet()
    h1, h2, body = styles["Title"], styles["Heading2"], styles["BodyText"]
    small = styles["Italic"]
    story = [Paragraph(f"PulseIQ monthly management report — {pd.Period(month, 'M').strftime('%B %Y')}", h1),
             Paragraph("Zenith Nova Technologies (fictional training data)", small), Spacer(1, 6)]

    # 1. Scorecard
    sc = v.scorecard(month)
    story += [Paragraph("1. Executive scorecard", h2)]
    rows = [["KPI", "Value", "Previous month", "Target", "Status"]]
    for _, r in sc.iterrows():
        rows.append([r["kpi"], fmt(r["unit"], r["value"]), fmt(r["unit"], r["previous"]),
                     fmt(r["unit"], r["target"]), r["status"]])
    t = table(rows, [6 * cm, 3 * cm, 3 * cm, 3 * cm, 2.2 * cm])
    status_colours = {"Green": "#c8e6c9", "Amber": "#ffe0b2", "Red": "#ffcdd2"}
    for i, r in enumerate(sc.itertuples(), start=1):
        if r.status in status_colours:
            t.setStyle(TableStyle([("BACKGROUND", (4, i), (4, i), colors.HexColor(status_colours[r.status]))]))
    story += [t, Spacer(1, 10)]

    # 2. P&L
    pnl = v.pnl_monthly()
    upto = pnl[pnl["month"] <= month].tail(12)
    fig, ax = plt.subplots(figsize=(9, 3.4))
    x = range(len(upto))
    ax.bar([i - 0.2 for i in x], upto["revenue"] / 1e7, width=0.4, label="Revenue (Cr)")
    ax.bar([i + 0.2 for i in x], upto["expenses"] / 1e7, width=0.4, label="Expenses (Cr)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(upto["month"], rotation=45, fontsize=7)
    ax2 = ax.twinx()
    ax2.plot(list(x), upto["operating_margin_pct"], color="black", marker="o", label="Margin %")
    ax.set_title("Revenue, expenses and operating margin (last 12 months)")
    ax.legend(loc="upper left", fontsize=7)
    ax2.legend(loc="upper right", fontsize=7)
    row = pnl.set_index("month").loc[month]
    story += [Paragraph("2. Profit and loss", h2), chart(fig, tmp / "pnl.png"),
              table([["Revenue", "Other income", "Expenses", "Net profit", "Margin", "Payroll % of revenue"],
                     [inr(row["revenue"]), inr(row["other_income"]), inr(row["expenses"]), inr(row["net_profit"]),
                      f"{row['operating_margin_pct']:.1f}%", f"{row['payroll_pct_of_revenue']:.1f}%"]]),
              PageBreak()]

    # 3. Departments (no hard-coded department list, so a new department simply appears)
    d = v.dept_month_impact()
    d = d[d["month"] == month]
    rows = [["Department", "Headcount", "Payroll cost", "Cost/head", "Overtime %", "Attendance", "Attrition %"]]
    for r in d.itertuples():
        small_group = r.headcount_end < 5
        rows.append([r.department_name, f"{r.headcount_end:,.0f}",
                     "hidden (<5)" if small_group else inr(r.employer_cost),
                     "hidden (<5)" if small_group else inr(r.cost_per_head),
                     f"{r.overtime_share_pct:.2f}" if pd.notna(r.overtime_share_pct) else "-",
                     f"{r.attendance_rate:.1%}" if pd.notna(r.attendance_rate) else "-",
                     f"{r.attrition_rate_pct:.1f}" if (pd.notna(r.attrition_rate_pct) and r.headcount_start >= 10) else "hidden"])
    story += [Paragraph("3. Departments", h2), table(rows), Spacer(1, 4),
              Paragraph("Pay is hidden for groups under 5 people and attrition for groups under 10 "
                        "(minimum group sizes from the metric dictionary).", small), Spacer(1, 10)]

    # 4. Receivables
    as_of = min(pd.Period(month, "M").to_timestamp("M"), v.CUTOFF)
    age = v.receivables_ageing(as_of)
    chk = v.ageing_check(as_of)
    fig, ax = plt.subplots(figsize=(6, 2.6))
    ax.bar(age["age_bucket"], age["balance_due"] / 1e5)
    ax.set_ylabel("Rs lakh")
    ax.set_title(f"Receivables ageing at {as_of:%d %b %Y} (days past due)")
    od = v.overdue_by_client(5, as_of)
    rows = [["Client", "Overdue balance", "Invoices", "Oldest (days)"]] + \
           [[r.client_name, inr(r.overdue_balance), r.invoices, int(r.oldest_days)] for r in od.itertuples()]
    story += [Paragraph("4. Receivables and collections", h2), chart(fig, tmp / "ageing.png", 12 * cm),
              Paragraph(f"Open receivables {inr(chk['open_receivables'])}; buckets total {inr(chk['bucket_total'])} "
                        f"(check {'passed' if chk['passes'] else 'FAILED'}). Open = SENT, OVERDUE, PARTIALLY_PAID.", body),
              table(rows), PageBreak()]

    # 5. AI signals
    an = v.anomalies_by_type().head(6)
    rows = [["Source", "Anomaly type", "Flags", "Money at risk"]] + \
           [[r.source_dataset.replace("_monthly_features", ""), r.reason_code, r.flags, inr(r.money_at_risk)]
            for r in an.itertuples()]
    bt = v.backtest_headcount()
    story += [Paragraph("5. AI signals", h2),
              Paragraph(f"<b>{v.AI_LABEL}.</b> Flags are leads for a person to check, not proof.", body),
              table(rows), Spacer(1, 6),
              Paragraph(f"Headcount forecast back-test (trained to Mar 2026): mean absolute error "
                        f"{bt['abs_pct_error'].mean():.1f}%; {int(bt['inside_band'].sum())} of {len(bt)} months inside "
                        "the 80% band.", body)]

    out = out_dir / f"PulseIQ_Monthly_Report_{month}.pdf"

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.drawString(1.5 * cm, 1 * cm, stamp)
        canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"Page {doc.page}")
        canvas.restoreState()

    SimpleDocTemplate(str(out), pagesize=A4, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm,
                      bottomMargin=1.8 * cm, title=f"PulseIQ report {month}").build(story, onFirstPage=on_page,
                                                                                   onLaterPages=on_page)
    for f in tmp.glob("*.png"):
        f.unlink()
    tmp.rmdir()
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="Build the PulseIQ monthly report pack (PDF).")
    p.add_argument("--month", default="latest", help="YYYY-MM, or 'latest' (default)")
    p.add_argument("--out", default=str(ROOT / "reports" / "monthly"), help="output folder")
    a = p.parse_args(argv)
    month = v.months_available()[-1] if a.month == "latest" else a.month
    path = build(month, Path(a.out))
    print(f"Report written: {path}")
    return path


if __name__ == "__main__":
    main()
