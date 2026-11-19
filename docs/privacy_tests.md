# KPI explorer: privacy rules and "try to break it" notes (Task 18)

## What is allowed

| Role (demo_users.csv) | Metrics | Levels | Department scope |
|---|---|---|---|
| ADMIN | M01 Headcount, M04 Attrition, M09 Payroll cost, M10 Cost per head, M11 Overtime share, M13 Attendance, M22 Task completion | company → department → team | all |
| HR | M01, M04, M09, M10, M11, M13 | company → department → team | all |
| MANAGER | M01, M13, M22 (no pay, no attrition) | company → department → team | **own department only** |
| EXECUTIVE | M01, M04, M09, M11, M13, M22 | company → department (no team level) | all |

* Minimum group size comes from `metric_dictionary.minimum_group_size` (5 for most metrics, 10 for attrition).
* A group below the minimum is shown as **"Hidden (< n)"**, never as a number.
* If exactly one group is hidden, the next smallest group is also hidden (**complementary suppression**),
  otherwise the hidden value could be worked out as *total − all other groups*.
* Attrition is only recorded per department, so it has no team level.
* Team for an employee = the team they are most often assigned to on the task board (`fact_task`). People not
  on the board appear as "No team".
* Until the kit's `05_Starter/demo_users.csv` is copied to `data/starter/`, the app uses 4 built-in demo users
  (one per role, the manager owns D01).

## Break-it log

| # | What I tried | What happened before the fix | Fix | Result now | Test |
|---|---|---|---|---|---|
| 1 | HR → Payroll cost → department, Sep 2026 | Executive Office (1 person) showed one person's full cost | Hide groups below the minimum size | Executive Office shows "Hidden (< 5)" | `test_no_visible_group_is_below_minimum` |
| 2 | Same view, then subtract all other departments from the company total | The hidden person's pay could be calculated | Complementary suppression: also hide the next smallest group (Legal & Compliance) | Two groups hidden, message explains why | `test_single_hidden_group_triggers_complementary_suppression` |
| 3 | ADMIN → Cost per head → team, filtered to each department one by one | Small teams inside a department could drop to 1–2 people | Suppression applied after the department filter | No visible group under 5 for any department | `test_small_team_filter_cannot_reveal_one_person` |
| 4 | MANAGER (D01) → Payroll cost | – | Payroll metrics not in the manager's allowed list | "Role MANAGER is not allowed to see Payroll cost" | `test_roles_see_different_data` |
| 5 | MANAGER (D01) → Headcount → department | Could see every department | Filter to the manager's own department | Only Engineering is shown | `test_roles_see_different_data` |
| 6 | EXECUTIVE → team level | – | Executives get company and department only | Clear message, no table | `test_roles_see_different_data` |
| 7 | ADMIN → Attrition → team | Attrition does not exist per team | Blocked with a message | No team view | `test_attrition_has_no_team_view_and_uses_min_10` |
| 8 | Attrition → department with a 1-exit month in a 11-person department | 1 exit = 9% points to a person | Minimum 10 for M04 + complementary suppression | Departments under 10 hidden | same test |

After the fixes I redeploy (push to GitHub → Streamlit Cloud redeploys) and repeat tests 1–8 on the **live link**
with screenshots of two role views (HR and MANAGER).

## Decision: a manager with a team of 3 — should they see attrition for their team?

**No.** With 3 people a single leaver is 33% and everyone knows who it was, so the number describes a person,
not a team. The metric dictionary sets a minimum group of 10 for attrition. The manager sees the department
rate, and HR talks about individual cases one to one.
