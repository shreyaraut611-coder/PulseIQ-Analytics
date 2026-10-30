from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / 'data' / 'tables'

def load(name):
    return pd.read_csv(TABLES / f'{name}.csv', low_memory=False)

def test_required_phase2_tables_exist_and_nonempty():
    for name in ['fact_attendance_monthly','fact_leave','dim_date','fact_headcount_monthly','fact_attrition_risk','fact_task','dim_team','dim_sprint','fact_payroll','dim_department','budget_payroll_dept_month','kpi_targets']:
        df = load(name)
        assert not df.empty, name

def test_attendance_rate_is_bounded():
    d = load('fact_attendance_monthly')
    rate = pd.to_numeric(d['attendance_rate'], errors='coerce').dropna()
    assert ((rate >= 0) & (rate <= 1)).all()

def test_payroll_arithmetic_reconciles_within_tolerance():
    d = load('fact_payroll')
    cols = ['earned_fixed_pay','overtime_pay','variable_pay','gross_pay','total_deductions','net_pay','pf_employer','esi_employer','employer_cost']
    for c in cols: d[c] = pd.to_numeric(d[c], errors='coerce')
    assert ((d.earned_fixed_pay+d.overtime_pay+d.variable_pay-d.gross_pay).abs() <= .05).all()
    assert ((d.gross_pay-d.total_deductions-d.net_pay).abs() <= .05).all()
    assert ((d.gross_pay+d.pf_employer+d.esi_employer-d.employer_cost).abs() <= .05).all()

def test_task_dataset_has_expected_teams_and_sprints():
    d = load('fact_task')
    assert d.team_id.nunique() == 16
    assert d.sprint_id.nunique() == 38
