import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import views as v  # noqa: E402


def test_priority_list_covers_all_overdue_money():
    p = v.collections_priority()
    assert abs(p.loc[p["days_past_due"] > 0, "balance_due"].sum() - v.overdue_at(v.CUTOFF)) < 1


def test_not_due_invoices_score_zero_and_sort_last():
    p = v.collections_priority()
    assert (p.loc[p["days_past_due"] <= 0, "priority_score"] == 0).all()
    assert p["priority_score"].is_monotonic_decreasing


def test_coverage_between_zero_and_one():
    assert 0 < v.collections_coverage(10) <= 1
