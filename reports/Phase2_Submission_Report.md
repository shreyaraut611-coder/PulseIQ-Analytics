# PulseIQ Analytics — Phase 2 Report

**Participant:** Shreya Raut  
**Track:** Data Analytics  
**Phase:** Phase 2 — People, Teams and Cost  
**Repository:** Add the final GitHub repository URL before submission  
**Git tag:** `phase-2` (create locally and push after reviewing the files)

## Task status and evidence

| Task | Status | Evidence in this package |
|---|---|---|
| Day 6 — Attendance and leave trends | Implemented; local app execution still needs verification | Attendance/leave page in `app.py`; `outputs/phase2/attendance_monthly_summary.csv` |
| Day 7 — Attrition analytics | Implemented with privacy controls | Actual exits and group-level predicted-risk page in `app.py`; findings below |
| Day 8 — Team productivity | Implemented with documented metric rules | Team/sprint selectors, velocity, cycle time, on-time, blocked/reopened metrics in `app.py` |
| Day 9 — Payroll cost and reconciliation | Cost page and arithmetic checks implemented; official answer-key reconciliation pending | Payroll summaries and arithmetic check results; official `unlock_PQ-09` answer key was not present in the supplied package |
| Day 10 — Budget versus actual and KPI targets | Implemented | Variance chart, ranking, sign rule, and KPI target traffic lights in `app.py`; `outputs/phase2/budget_variance_summary.csv` |

## Numeric findings from the supplied dataset

1. **Attendance:** The lowest monthly attendance rate was **92.64% in May 2026** (7,551 present days / 8,151 scheduled days). January 2026 was **93.11%** and June 2026 was **93.16%**. These are points to investigate; they do not by themselves prove that holidays caused the dips.
2. **Department attendance:** Finance & Accounts had an overall attendance rate of **90.60%** across its records, compared with **94.84%** for Data & AI. Compare working-day mix and department context before drawing conclusions.
3. **Leave:** Approved Earned (Privilege) Leave was the largest category at **2,336 days**, followed by Casual Leave at **1,995 days** and Sick Leave at **1,769 days**.
4. **Attrition:** October 2025 had the most recorded exits (**10**, including **9 voluntary**) among monthly totals. March 2025 had **9** exits and December 2023 had **8**. These counts should be interpreted alongside headcount and department context.
5. **Team productivity:** Support Tooling recorded **10,288 story points** across Done tasks, with **177 blocked tasks** and **142 reopened counts**. Sales Enablement recorded **8,424 story points**, **131 blocked tasks**, and **150 reopened counts**. Velocity alone is not a complete measure of team health.
6. **Payroll / budget:** Across matched department-months, employer cost was **₹861,997,360** against **₹862,030,000** budget, a net variance of about **−₹32,640**. This near-zero overall variance masks department-level differences: Data & AI was about **₹992,768 over budget**, Product & Design about **₹763,164 over**, and Customer Support about **₹482,051 over**.

## Validation and limitations

- Automated test suite: **7 passed** (`python -m pytest -q`).
- Payroll arithmetic checks passed within ₹0.05 tolerance for all 7,344 rows: gross pay = earned fixed pay + overtime pay + variable pay; net pay = gross pay − total deductions; employer cost = gross pay + employer PF + employer ESI.
- Two employee-month duplicate pairs were detected and are shown for review; they were **not silently removed**.
- The provided ZIP did not include the official `04_Validation_Vault/unlock_PQ-09` answer key, so the required official reconciliation cannot honestly be marked complete. Add that answer key, reconcile totals, and document any excluded rows before final submission if the programme requires it.
- This environment did not have Streamlit installed, so the app source was syntax-checked and its data calculations tested, but a live browser screenshot was not captured. Install `requirements.txt`, run `streamlit run app.py`, verify filters/charts, and capture genuine screenshots for the programme portal.
- Predictions are labelled “Predicted, not certain” and shown by department only where at least five predictions exist. They must not be used as individual employment decisions.

## What I learned

I built dashboard views to compare attendance, approved leave, actual exits, predicted risk groups, team delivery and payroll costs. I used explicit metric definitions and checked payroll arithmetic rather than assuming the totals were correct. I learned that aggregate results can hide differences between departments and that predictions must be clearly separated from actual outcomes. I also identified the missing official validation answer key as a blocker for final payroll reconciliation.

## Problems and resolutions

- **Missing official payroll validation key:** Added arithmetic checks and duplicate-row review; did not claim official reconciliation.
- **Sensitive attrition risk data:** Dashboard does not display employee names or IDs in the risk section and suppresses groups with fewer than five predictions.
- **Cancelled task handling:** Cancelled tasks are excluded from delivery-rate denominators and are shown separately; velocity counts story points only for Done tasks.
- **Local runtime dependency:** Streamlit must be installed from `requirements.txt` before a live UI check and screenshot capture.

## Plan for next phase

Run the dashboard locally, review all charts and filters, complete the official payroll answer-key reconciliation, capture genuine screenshots, add the actual GitHub URL, tag the repository as `phase-2`, push the tag, and submit this PDF through the programme site.
