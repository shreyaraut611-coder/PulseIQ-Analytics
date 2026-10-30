-- PulseIQ PostgreSQL warehouse foundation
CREATE SCHEMA IF NOT EXISTS pulseiq;
CREATE SCHEMA IF NOT EXISTS staging;

-- Load CSV exports into staging tables using your preferred loader (COPY / pgAdmin).
-- Example:
-- CREATE TABLE staging.dim_employee AS SELECT * FROM ...;  -- create columns to match CSV first.

CREATE TABLE IF NOT EXISTS pulseiq.dim_employee (
    employee_id TEXT PRIMARY KEY,
    employee_name TEXT,
    department_id TEXT,
    role_id TEXT,
    location_id TEXT,
    hire_date DATE,
    exit_date DATE,
    employment_status TEXT
);

CREATE TABLE IF NOT EXISTS pulseiq.dim_department (
    department_id TEXT PRIMARY KEY,
    department_name TEXT
);

CREATE TABLE IF NOT EXISTS pulseiq.dim_date (
    date_key INTEGER PRIMARY KEY,
    calendar_date DATE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name TEXT
);

CREATE TABLE IF NOT EXISTS pulseiq.fact_payroll (
    payroll_id TEXT,
    employee_id TEXT,
    date_key INTEGER,
    gross_pay NUMERIC(14,2),
    net_pay NUMERIC(14,2),
    department_id TEXT
);

CREATE TABLE IF NOT EXISTS pulseiq.fact_attendance_monthly (
    employee_id TEXT,
    date_key INTEGER,
    days_present NUMERIC(8,2),
    days_absent NUMERIC(8,2),
    department_id TEXT
);

CREATE TABLE IF NOT EXISTS pulseiq.fact_headcount_monthly (
    date_key INTEGER,
    department_id TEXT,
    headcount INTEGER
);

CREATE INDEX IF NOT EXISTS ix_payroll_employee ON pulseiq.fact_payroll(employee_id);
CREATE INDEX IF NOT EXISTS ix_payroll_date ON pulseiq.fact_payroll(date_key);
CREATE INDEX IF NOT EXISTS ix_attendance_employee ON pulseiq.fact_attendance_monthly(employee_id);

CREATE OR REPLACE VIEW pulseiq.vw_payroll_monthly AS
SELECT date_key, department_id,
       COUNT(*) AS payroll_rows,
       SUM(gross_pay) AS gross_pay_total,
       SUM(net_pay) AS net_pay_total
FROM pulseiq.fact_payroll
GROUP BY date_key, department_id;

CREATE OR REPLACE VIEW pulseiq.vw_headcount_by_department_month AS
SELECT date_key, department_id, SUM(headcount) AS headcount
FROM pulseiq.fact_headcount_monthly
GROUP BY date_key, department_id;

-- Note: CSV column names can differ from these illustrative canonical columns.
-- Map the actual supplied CSV headers before loading; do not use this script as a blind COPY script.
