# Clean-machine test

Goal: prove a fresh copy of the repo works with only the README steps.

## Test 1 — fresh clone in a new folder (done while building v1.0.0)
Environment: Linux, Python 3.13, fresh `git clone` into an empty folder, no files copied by hand.

| Step | Command | Result |
|---|---|---|
| Tests | `pytest -q` | 36 passed |
| Monthly PDF | `python build_report.py --month 2026-09` | PDF written |
| Board deck | `python scripts/build_board_deck.py` | 10 slides written |
| Published tables | `python scripts/export_published.py` | 8 tables, 57 KB |
| Dashboard | `streamlit run app.py` | not run in this environment — see Test 2 |
| API | `uvicorn api.main:app` | not run in this environment — see Test 2 |

## Test 2 — my own laptop (fill in)
| Step | Result | Screenshot |
|---|---|---|
| `pip install -r requirements.txt` in a new venv | `<pass / fail>` | `<file>` |
| `pytest -q` | `<n passed>` | `<file>` |
| `streamlit run app.py` — all 7 pages open | `<pass / fail>` | `<file>` |
| `uvicorn api.main:app` — `/docs` opens, `/metrics/revenue` answers | `<pass / fail>` | `<file>` |
| Live Streamlit link opens in a private window | `<pass / fail>` | `<file>` |
| Live API link `/health` answers | `<pass / fail>` | `<file>` |

## Problems found and fixed
- Page files moved into `pages/`, so the data path changed to `parents[1]`. Fixed before release.
- `overdue_receivables` for past months used today's invoice statuses. Added `overdue_at(month)` so history is correct.
