"""PulseIQ Phase 2 workforce, team and cost analytics dashboard.
Run from this directory with: streamlit run app.py
"""
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "data" / "tables"
st.set_page_config(page_title="PulseIQ | Phase 2", page_icon="📊", layout="wide")
st.title("PulseIQ Analytics — Phase 2")
st.caption("Workforce, team productivity and payroll analytics | Data cut-off: 30 Sep 2026")

@st.cache_data
def load(stem):
    p = TABLES / f"{stem}.csv"
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, low_memory=False)
    except Exception as exc:
        st.warning(f"Could not load {stem}: {exc}")
        return pd.DataFrame()

def dept_names(df, key="department_id"):
    departments = load("dim_department")
    if df.empty or key not in df.columns or departments.empty:
        return df
    return df.merge(departments[["department_id", "department_name"]].drop_duplicates(), on="department_id", how="left")

def month_col(df, candidates):
    for col in candidates:
        if col in df.columns:
            return col
    return None

def money(v):
    return f"₹{v:,.0f}"

def empty_note():
    st.info("Required source table is not available in data/tables.")

# Shared filters / source tables
attendance = load("fact_attendance_monthly")
leave = load("fact_leave")
calendar = load("dim_date")
headcount = load("fact_headcount_monthly")
risk = load("fact_attrition_risk")
tasks = load("fact_task")
teams = load("dim_team")
sprints = load("dim_sprint")
payroll = load("fact_payroll")
budget = load("budget_payroll_dept_month")
targets = load("kpi_targets")

pages = st.tabs(["Day 6 · Attendance & leave", "Day 7 · Attrition", "Day 8 · Team productivity", "Day 9 · Payroll", "Day 10 · Budget vs actual", "Source explorer"])

with pages[0]:
    st.header("Attendance and leave trends")
    if attendance.empty:
        empty_note()
    else:
        a = dept_names(attendance.copy())
        a["month"] = pd.to_datetime(a["period_end_date"], errors="coerce").dt.to_period("M").astype(str)
        departments = ["All departments"] + sorted(a["department_name"].dropna().unique().tolist())
        selected = st.selectbox("Department", departments, key="att_dept")
        if selected != "All departments": a = a[a.department_name == selected]
        monthly = a.groupby("month", as_index=False).agg(
            scheduled_days=("scheduled_days", "sum"), present_days=("present_days", "sum"),
            late_arrivals=("late_arrivals", "sum"), overtime_hours=("overtime_hours", "sum"),
            paid_leave_days=("paid_leave_days", "sum"), unpaid_absence_days=("unpaid_absence_days", "sum"))
        monthly["attendance_rate"] = monthly.present_days / monthly.scheduled_days.replace(0, pd.NA)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Attendance rate", f"{monthly.present_days.sum()/max(monthly.scheduled_days.sum(),1):.1%}")
        c2.metric("Late arrivals", f"{monthly.late_arrivals.sum():,.0f}")
        c3.metric("Overtime hours", f"{monthly.overtime_hours.sum():,.1f}")
        c4.metric("Leave + absence days", f"{(monthly.paid_leave_days.sum()+monthly.unpaid_absence_days.sum()):,.0f}")
        st.plotly_chart(px.line(monthly, x="month", y="attendance_rate", markers=True, title="Attendance rate by month"), use_container_width=True)
        c1,c2 = st.columns(2)
        with c1: st.plotly_chart(px.bar(monthly, x="month", y="late_arrivals", title="Late arrivals by month"), use_container_width=True)
        with c2: st.plotly_chart(px.bar(monthly, x="month", y="overtime_hours", title="Overtime hours by month"), use_container_width=True)
        if not leave.empty:
            approved = leave[leave.status.astype(str).str.lower().eq("approved")].copy()
            approved["days"] = pd.to_numeric(approved["days"], errors="coerce").fillna(0)
            lt = load("dim_leave_type")
            if not lt.empty: approved = approved.merge(lt[["leave_type_code","leave_type_name"]].drop_duplicates(), on="leave_type_code", how="left")
            if "leave_type_name" not in approved: approved["leave_type_name"] = approved["leave_type_code"]
            leave_plot = approved.groupby("leave_type_name", as_index=False)["days"].sum().sort_values("days", ascending=False)
            st.plotly_chart(px.bar(leave_plot, x="leave_type_name", y="days", title="Approved leave days by type"), use_container_width=True)
        # Holiday context: count holidays in the month; these are context, not assumed causes.
        if not calendar.empty and {"date","is_holiday"}.issubset(calendar.columns):
            cal = calendar.copy(); cal["month"] = pd.to_datetime(cal["date"], errors="coerce").dt.to_period("M").astype(str)
            holiday_months = cal[cal.is_holiday.astype(str).str.upper().isin(["Y","YES","TRUE","1"])].groupby("month").size().rename("holiday_days").reset_index()
            monthly = monthly.merge(holiday_months, on="month", how="left").fillna({"holiday_days":0})
            st.caption("Calendar context: holiday counts are shown to help interpret dips; correlation alone does not prove causation.")
            st.dataframe(monthly[["month","attendance_rate","late_arrivals","overtime_hours","paid_leave_days","unpaid_absence_days","holiday_days"]], use_container_width=True)
        else: st.dataframe(monthly, use_container_width=True)
        st.download_button("Download attendance summary CSV", monthly.to_csv(index=False).encode("utf-8"), "attendance_monthly_summary.csv", "text/csv")

with pages[1]:
    st.header("Attrition analytics")
    if headcount.empty:
        empty_note()
    else:
        h = dept_names(headcount.copy())
        h["month"] = pd.to_datetime(h["month_start_date"], errors="coerce").dt.to_period("M").astype(str)
        departments = ["All departments"] + sorted(h["department_name"].dropna().unique().tolist())
        selected = st.selectbox("Department", departments, key="attr_dept")
        if selected != "All departments": h = h[h.department_name == selected]
        hm = h.groupby("month", as_index=False).agg(exits=("exits","sum"), voluntary_exits=("voluntary_exits","sum"), headcount_start=("headcount_start","sum"))
        hm["exit_rate_pct"] = hm.exits / hm.headcount_start.replace(0, pd.NA) * 100
        c1,c2,c3 = st.columns(3)
        c1.metric("Recorded exits", f"{hm.exits.sum():,.0f}")
        c2.metric("Voluntary exits", f"{hm.voluntary_exits.sum():,.0f}")
        c3.metric("Overall monthly exit rate", f"{hm.exits.sum()/max(hm.headcount_start.sum(),1)*100:.2f}%")
        st.plotly_chart(px.line(hm, x="month", y="exits", markers=True, title="Actual exits by month"), use_container_width=True)
        st.plotly_chart(px.bar(hm, x="month", y="voluntary_exits", title="Voluntary exits by month"), use_container_width=True)
        st.dataframe(hm, use_container_width=True)
        if not risk.empty:
            r = dept_names(risk.copy())
            r["risk_score_12m"] = pd.to_numeric(r["risk_score_12m"], errors="coerce")
            st.subheader("Predicted, not certain")
            st.warning("This is a baseline model signal, not a fact or a decision about any person. This dashboard only shows group-level summaries; individual names and IDs are not displayed.")
            # Suppress small groups: minimum 5 predictions.
            group = r.groupby("department_name", dropna=False).agg(predictions=("prediction_id","count"), mean_risk=("risk_score_12m","mean"), high_risk_count=("risk_band",lambda s:(s.astype(str).str.lower()=="high").sum())).reset_index()
            group = group[group.predictions >= 5]
            if not group.empty:
                group["mean_risk_pct"] = group.mean_risk * 100
                st.plotly_chart(px.bar(group, x="department_name", y="mean_risk_pct", title="Average predicted 12-month risk by department (%)"), use_container_width=True)
                st.dataframe(group[["department_name","predictions","mean_risk_pct","high_risk_count"]], use_container_width=True)
            else: st.info("No department meets the minimum group size of 5 predictions.")

with pages[2]:
    st.header("Team productivity")
    if tasks.empty:
        empty_note()
    else:
        t = tasks.copy()
        if not teams.empty: t = t.merge(teams[["team_id","team_name","active_members"]].drop_duplicates(), on="team_id", how="left")
        if not sprints.empty: t = t.merge(sprints[["sprint_id","sprint_name","working_days"]].drop_duplicates(), on="sprint_id", how="left")
        t["story_points"] = pd.to_numeric(t.story_points, errors="coerce").fillna(0)
        t["cycle_time_days"] = pd.to_numeric(t.cycle_time_days, errors="coerce")
        t["reopened_count"] = pd.to_numeric(t.reopened_count, errors="coerce").fillna(0)
        t["is_done"] = t.status.astype(str).str.lower().eq("done")
        t["is_cancelled"] = t.status.astype(str).str.lower().eq("cancelled")
        # Explicit rule: cancelled work is excluded from throughput/on-time denominator; all other tasks are in scope.
        st.info("Metric rules: velocity = story points on Done tasks; cycle time = median cycle time for Done tasks with a recorded value; on-time rate = completed-on-time among Done tasks with a known on-time flag. Cancelled tasks are excluded from delivery-rate denominators but shown separately.")
        team_names = sorted(t.get("team_name", t["team_id"]).dropna().unique().tolist())
        selected_team = st.selectbox("Team", ["All teams"] + team_names, key="team_sel")
        if selected_team != "All teams": t = t[t.get("team_name", t["team_id"]) == selected_team]
        sprint_names = sorted(t.get("sprint_name", t["sprint_id"]).dropna().unique().tolist())
        selected_sprint = st.selectbox("Sprint", ["All sprints"] + sprint_names, key="sprint_sel")
        if selected_sprint != "All sprints": t = t[t.get("sprint_name", t["sprint_id"]) == selected_sprint]
        done = t[t.is_done]
        ontime = done[done.completed_on_time.astype(str).str.upper().isin(["Y","YES","TRUE","1","N","NO","FALSE","0"])]
        ontime_rate = ontime.completed_on_time.astype(str).str.upper().isin(["Y","YES","TRUE","1"]).mean() if len(ontime) else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Done tasks", f"{len(done):,}")
        c2.metric("Velocity (story points)", f"{done.story_points.sum():,.0f}")
        c3.metric("Median cycle time", f"{done.cycle_time_days.median():.1f} days" if done.cycle_time_days.notna().any() else "N/A")
        c4.metric("On-time rate", f"{ontime_rate:.1%}")
        t["team_label"] = t.get("team_name", t["team_id"])
        byteam = t.groupby("team_label", as_index=False).agg(total_tasks=("task_id","count"), done_tasks=("is_done","sum"), cancelled=("is_cancelled","sum"), story_points=("story_points",lambda s:s[t.loc[s.index,"is_done"]].sum()), reopened=("reopened_count","sum"), blocked=("status",lambda s:s.astype(str).str.lower().eq("blocked").sum()), median_cycle_time=("cycle_time_days","median"))
        st.plotly_chart(px.bar(byteam, x="team_label", y="story_points", title="Velocity by team (Done tasks only)"), use_container_width=True)
        st.plotly_chart(px.bar(byteam, x="team_label", y="blocked", title="Blocked tasks by team"), use_container_width=True)
        st.dataframe(byteam, use_container_width=True)
        st.download_button("Download team summary CSV", byteam.to_csv(index=False).encode("utf-8"), "team_productivity_summary.csv", "text/csv")

with pages[3]:
    st.header("Payroll cost and reconciliation")
    if payroll.empty:
        empty_note()
    else:
        p = dept_names(payroll.copy())
        p["month"] = pd.to_datetime(p["period_end_date"], errors="coerce").dt.to_period("M").astype(str)
        p["gross_pay"] = pd.to_numeric(p["gross_pay"], errors="coerce")
        p["net_pay"] = pd.to_numeric(p["net_pay"], errors="coerce")
        p["employer_cost"] = pd.to_numeric(p["employer_cost"], errors="coerce")
        departments = ["All departments"] + sorted(p["department_name"].dropna().unique().tolist())
        selected = st.selectbox("Department", departments, key="pay_dept")
        if selected != "All departments": p = p[p.department_name == selected]
        pm = p.groupby(["month","department_name"], as_index=False).agg(gross_pay=("gross_pay","sum"), net_pay=("net_pay","sum"), employer_cost=("employer_cost","sum"), payroll_rows=("payroll_item_id","count"), employees=("employee_id","nunique"))
        pm["employer_cost_per_employee"] = pm.employer_cost / pm.employees.replace(0, pd.NA)
        c1,c2,c3 = st.columns(3)
        c1.metric("Gross payroll", money(p.gross_pay.sum()))
        c2.metric("Net payroll", money(p.net_pay.sum()))
        c3.metric("Employer cost", money(p.employer_cost.sum()))
        st.plotly_chart(px.line(pm, x="month", y="employer_cost", color="department_name", markers=True, title="Employer cost by month and department"), use_container_width=True)
        st.dataframe(pm, use_container_width=True)
        # Arithmetic reconciliation checks from the available payroll fields.
        q = load("fact_payroll")
        for c in ["earned_fixed_pay","overtime_pay","variable_pay","gross_pay","total_deductions","net_pay","pf_employer","esi_employer","employer_cost"]:
            q[c] = pd.to_numeric(q[c], errors="coerce")
        checks = pd.DataFrame([
            {"check":"Gross = earned fixed + overtime + variable", "rows_checked":len(q), "exceptions":int(((q.earned_fixed_pay+q.overtime_pay+q.variable_pay-q.gross_pay).abs()>0.05).sum())},
            {"check":"Net = gross - total deductions", "rows_checked":len(q), "exceptions":int(((q.gross_pay-q.total_deductions-q.net_pay).abs()>0.05).sum())},
            {"check":"Employer cost = gross + employer PF + employer ESI", "rows_checked":len(q), "exceptions":int(((q.gross_pay+q.pf_employer+q.esi_employer-q.employer_cost).abs()>0.05).sum())},
        ])
        st.subheader("Arithmetic validation")
        st.dataframe(checks, use_container_width=True)
        st.warning("The supplied package does not contain the official unlock_PQ-09 validation answer key. These arithmetic checks do not replace that answer-key reconciliation. Potential duplicate employee-month rows are flagged for review rather than silently deleted.")
        dup = q[q.duplicated(["employee_id","period_end_date"], keep=False)][["payroll_item_id","employee_id","period_end_date","department_id","gross_pay","net_pay","employer_cost"]]
        st.write(f"Employee-month duplicate rows for review: {len(dup)}")
        if not dup.empty: st.dataframe(dup, use_container_width=True)
        st.download_button("Download payroll summary CSV", pm.to_csv(index=False).encode("utf-8"), "payroll_cost_summary.csv", "text/csv")

with pages[4]:
    st.header("Budget vs actual and KPI targets")
    if payroll.empty or budget.empty:
        empty_note()
    else:
        p = payroll.copy(); p["month"] = pd.to_datetime(p["period_end_date"], errors="coerce").dt.to_period("M").astype(str)
        p["employer_cost"] = pd.to_numeric(p["employer_cost"], errors="coerce")
        actual = p.groupby(["department_id","month"], as_index=False).agg(actual_employer_cost=("employer_cost","sum"))
        b = budget.copy(); b["month"] = pd.to_datetime(b["month"], errors="coerce").dt.to_period("M").astype(str); b["budget_payroll_cost"] = pd.to_numeric(b["budget_payroll_cost"], errors="coerce")
        v = actual.merge(b, on=["department_id","month"], how="outer")
        v["variance"] = v.actual_employer_cost - v.budget_payroll_cost
        v["variance_pct"] = v.variance / v.budget_payroll_cost.replace(0, pd.NA) * 100
        v = dept_names(v)
        # Positive variance means overspend.
        st.caption("Sign convention: variance = actual employer cost − budget. Positive means overspend; negative means underspend.")
        departments = ["All departments"] + sorted(v["department_name"].dropna().unique().tolist())
        selected = st.selectbox("Department", departments, key="budget_dept")
        if selected != "All departments": v = v[v.department_name == selected]
        c1,c2,c3 = st.columns(3)
        c1.metric("Actual cost", money(v.actual_employer_cost.sum()))
        c2.metric("Budget", money(v.budget_payroll_cost.sum()))
        c3.metric("Variance", money(v.variance.sum()), delta=f"{v.variance.sum()/max(v.budget_payroll_cost.sum(),1)*100:.2f}% vs budget")
        st.plotly_chart(px.bar(v, x="month", y="variance", color="department_name", title="Budget variance by month (positive = overspend)"), use_container_width=True)
        rank = v.groupby("department_name", as_index=False).agg(actual=("actual_employer_cost","sum"), budget=("budget_payroll_cost","sum"), variance=("variance","sum"))
        rank["variance_pct"] = rank.variance / rank.budget.replace(0, pd.NA) * 100
        st.subheader("Departments ranked by overspend")
        st.dataframe(rank.sort_values("variance", ascending=False), use_container_width=True)
        if not targets.empty:
            st.subheader("KPI target traffic lights")
            st.caption("Attendance and task completion are green when at/above target; attrition and overtime share are green when at/below target. Overtime share is calculated as overtime hours divided by scheduled hours (scheduled days × 8), expressed as a percentage.")
            kt = targets.copy()
            kt["month"] = pd.to_datetime(kt["month"], errors="coerce").dt.to_period("M").astype(str)
            parts = []
            if not attendance.empty:
                aa = attendance.copy(); aa["month"] = pd.to_datetime(aa["period_end_date"], errors="coerce").dt.to_period("M").astype(str)
                aa["scheduled_days"] = pd.to_numeric(aa["scheduled_days"], errors="coerce").fillna(0)
                aa["present_days"] = pd.to_numeric(aa["present_days"], errors="coerce").fillna(0)
                aa["overtime_hours"] = pd.to_numeric(aa["overtime_hours"], errors="coerce").fillna(0)
                aa = aa.groupby(["department_id","month"], as_index=False).agg(scheduled_days=("scheduled_days","sum"), present_days=("present_days","sum"), overtime_hours=("overtime_hours","sum"))
                aa["attendance_actual"] = aa.present_days / aa.scheduled_days.replace(0, pd.NA)
                aa["overtime_share_actual_pct"] = aa.overtime_hours / (aa.scheduled_days * 8).replace(0, pd.NA) * 100
                parts.append(aa[["department_id","month","attendance_actual","overtime_share_actual_pct"]])
            if not headcount.empty:
                hh = headcount.copy(); hh["month"] = pd.to_datetime(hh["month_start_date"], errors="coerce").dt.to_period("M").astype(str)
                hh["attrition_monthly_pct"] = pd.to_numeric(hh["attrition_rate_monthly_pct"], errors="coerce")
                hh = hh.groupby(["department_id","month"], as_index=False).agg(attrition_actual_pct=("attrition_monthly_pct","mean"))
                parts.append(hh)
            if not tasks.empty and not teams.empty:
                tt = tasks.merge(teams[["team_id","department_id"]].drop_duplicates(), on="team_id", how="left")
                tt["month"] = pd.to_datetime(tt["completed_date"], errors="coerce").dt.to_period("M").astype(str)
                tt = tt[tt["month"].notna() & ~tt["status"].astype(str).str.lower().eq("cancelled")]
                tt["done_flag"] = tt["status"].astype(str).str.lower().eq("done").astype(int)
                tt = tt.groupby(["department_id","month"], as_index=False).agg(tasks_completed=("done_flag","sum"), tasks_in_scope=("task_id","count"))
                tt["task_completion_actual_pct"] = tt.tasks_completed / tt.tasks_in_scope.replace(0, pd.NA) * 100
                parts.append(tt[["department_id","month","task_completion_actual_pct"]])
            kpi = kt
            for part in parts: kpi = kpi.merge(part, on=["department_id","month"], how="left")
            if "attendance_actual" in kpi:
                kpi["attendance_status"] = kpi.apply(lambda r: "Green" if pd.notna(r.get("attendance_actual")) and r.attendance_actual >= r.attendance_rate_target else ("Red" if pd.notna(r.get("attendance_actual")) else "N/A"), axis=1)
            if "overtime_share_actual_pct" in kpi:
                kpi["overtime_status"] = kpi.apply(lambda r: "Green" if pd.notna(r.get("overtime_share_actual_pct")) and r.overtime_share_actual_pct <= r.overtime_share_target_pct else ("Red" if pd.notna(r.get("overtime_share_actual_pct")) else "N/A"), axis=1)
            if "attrition_actual_pct" in kpi:
                kpi["attrition_status"] = kpi.apply(lambda r: "Green" if pd.notna(r.get("attrition_actual_pct")) and r.attrition_actual_pct <= r.attrition_monthly_target_pct else ("Red" if pd.notna(r.get("attrition_actual_pct")) else "N/A"), axis=1)
            if "task_completion_actual_pct" in kpi:
                kpi["task_status"] = kpi.apply(lambda r: "Green" if pd.notna(r.get("task_completion_actual_pct")) and r.task_completion_actual_pct >= r.task_completion_target_pct else ("Red" if pd.notna(r.get("task_completion_actual_pct")) else "N/A"), axis=1)
            display_cols = [c for c in ["month","department_id","attendance_actual","attendance_rate_target","attendance_status","overtime_share_actual_pct","overtime_share_target_pct","overtime_status","attrition_actual_pct","attrition_monthly_target_pct","attrition_status","task_completion_actual_pct","task_completion_target_pct","task_status"] if c in kpi.columns]
            st.dataframe(kpi[display_cols], use_container_width=True, height=350)
            st.download_button("Download KPI traffic-light CSV", kpi[display_cols].to_csv(index=False).encode("utf-8"), "kpi_traffic_lights.csv", "text/csv")
        st.download_button("Download budget variance CSV", v.to_csv(index=False).encode("utf-8"), "budget_variance_summary.csv", "text/csv")

with pages[5]:
    st.header("Source explorer")
    options = sorted(p.stem for p in TABLES.glob("*.csv"))
    chosen = st.selectbox("Select source table", options, index=options.index("fact_headcount_monthly") if "fact_headcount_monthly" in options else 0)
    df = load(chosen)
    st.write(f"**{chosen}** · {len(df):,} rows · {len(df.columns):,} columns")
    st.dataframe(df.head(1000), use_container_width=True)
    st.download_button("Download selected source CSV", df.to_csv(index=False).encode("utf-8"), f"{chosen}.csv", "text/csv")

st.divider()
st.caption("Privacy: predicted attrition is displayed only in groups meeting the minimum group size of five. Do not use predictions as individual employment decisions.")
