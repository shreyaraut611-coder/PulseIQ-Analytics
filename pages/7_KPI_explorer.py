"""Task 18 · Self-service KPI explorer with privacy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from ui import header, month_selector  # noqa: E402
import views as v  # noqa: E402

header("KPI explorer", "Task 18 · Choose a metric and a level; small groups are always hidden")

users = v.demo_users()
labels = [f"{r['name']} ({r['role']}{', ' + str(r['department_id']) if str(r.get('department_id', '')) not in ('', 'nan') else ''})"
          for _, r in users.iterrows()]
who = st.selectbox("Signed in as (demo user)", range(len(users)), format_func=lambda i: labels[i])
user = users.iloc[who]
role = str(user["role"]).upper()
user_dept = "" if str(user.get("department_id", "")) == "nan" else str(user.get("department_id", ""))

allowed, team_ok, own_only = v.ROLE_RULES[role]
metric = st.selectbox("Metric", sorted(allowed), format_func=lambda m: f"{m} · {v.EXPLORER_METRICS[m]}")
levels = ["company", "department"] + (["team"] if team_ok else [])
c1, c2 = st.columns(2)
level = c1.radio("Drill level", levels, horizontal=True)
month = month_selector("exp_month")
dept_filter = None
if level == "team" and not own_only:
    depts = v.departments()
    pick = c2.selectbox("Department (optional)", ["All"] + depts["department_id"].tolist(),
                        format_func=lambda d: d if d == "All" else depts.set_index("department_id").loc[d, "department_name"])
    dept_filter = None if pick == "All" else pick

table, msgs = v.explore(metric, level, month, role, user_dept, dept_filter)
for m in msgs:
    st.info(m)
if own_only:
    st.caption(f"Managers only see their own department ({user_dept}).")
if not table.empty:
    shown = table.dropna(subset=["value"])
    if not shown.empty:
        st.plotly_chart(px.bar(shown, x="group", y="value", title=f"{v.EXPLORER_METRICS[metric]} — {level} — {month}"),
                        use_container_width=True)
    st.dataframe(table, hide_index=True, use_container_width=True)
st.caption(f"Minimum group size for this metric: {v.min_group_size(metric)} (from metric_dictionary).")

with st.expander("Who can see what"):
    st.markdown("""
| Role | Metrics | Levels |
|---|---|---|
| ADMIN | all explorer metrics incl. payroll | company, department, team |
| HR | people + payroll metrics | company, department, team |
| MANAGER | headcount, attendance, task completion — **own department only**, no pay | company, department, team |
| EXECUTIVE | people, payroll and delivery totals | company and department only |

**A manager with a team of 3: should they see attrition for that team?** No. With 3 people one leaver is 33% and
everyone knows who it was; the metric dictionary sets a minimum group of 10 for attrition. The manager sees the
department rate instead, and HR discusses individual cases privately.
""")
