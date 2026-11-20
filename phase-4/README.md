# Phase 4 — Release: Reporting, Automation, Self-service, API and Board Pack (Days 16–20)

PulseIQ is one application that grows phase by phase, so the code stays at the repository root. This folder is the index for Phase 4. Git tags: [`phase-4`](https://github.com/shreyaraut611-coder/PulseIQ-Analytics/releases/tag/phase-4) · [`v1.0.0`](https://github.com/shreyaraut611-coder/PulseIQ-Analytics/releases/tag/v1.0.0)

**Live dashboard:** https://pulseiq-shreya.streamlit.app

## What was built
| Task | What | Files |
|---|---|---|
| 16 | One-command monthly PDF for any month | [`build_report.py`](../build_report.py) |
| 17 | GitHub Actions (tests, monthly PDF, weekly refresh) and live deployment on Streamlit Community Cloud | [`.github/workflows/`](../.github/workflows), [`.streamlit/`](../.streamlit), [`docs/hosting.md`](../docs/hosting.md), [`scripts/export_published.py`](../scripts/export_published.py) |
| 18 | Self-service KPI explorer with roles and small-group suppression | [`pages/7_KPI_explorer.py`](../pages/7_KPI_explorer.py), [`docs/privacy_tests.md`](../docs/privacy_tests.md) |
| 19 | Metrics API with definitions, lineage and freshness | [`api/main.py`](../api/main.py), [`docs/API.md`](../docs/API.md), [`docs/lineage.md`](../docs/lineage.md), [`render.yaml`](../render.yaml) |
| 20 | Release notes, clean-machine test, board deck | [`RELEASE_NOTES.md`](../RELEASE_NOTES.md), [`docs/clean_machine_test.md`](../docs/clean_machine_test.md), [`scripts/build_board_deck.py`](../scripts/build_board_deck.py) |
| Final challenge | Collections priority list | branch [`final-challenge`](https://github.com/shreyaraut611-coder/PulseIQ-Analytics/tree/final-challenge) |

Tests: [`tests/test_phase4.py`](../tests/test_phase4.py). All 36 tests run on every push ([Actions](https://github.com/shreyaraut611-coder/PulseIQ-Analytics/actions)).

## Report
- [Phase 4 report](../reports/Phase4_Submission_Report.md) · [Release notes](../RELEASE_NOTES.md)

## Run
```bash
python build_report.py --month 2026-09
python scripts/build_board_deck.py
uvicorn api.main:app --reload
pytest -q
```
