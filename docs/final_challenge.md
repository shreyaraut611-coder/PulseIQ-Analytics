# Final challenge — collections priority list

**Branch:** `final-challenge` (kept separate so the v1.0.0 release stays unchanged).

## Problem
₹2.71 Cr was overdue at the 30 Sep 2026 cut-off, spread over many invoices. The finance team needs to know which invoices to chase first each week, and how.

## What I built
- `src/views.py → collections_priority()` ranks every open invoice by a money-at-risk score.
- `pages/8_Collections_priority.py` shows this week's list, the share of overdue money it covers, a CSV download, and money by recommended action.
- `tests/test_final_challenge.py` checks the list adds up to the overdue total and that invoices not yet due are never chased.

## Method
score = balance due × (1 + days past due ÷ 90) × client factor

| Part | Why |
|---|---|
| Balance due | Bigger invoices matter more |
| Age factor | An invoice 90 days late counts double; 180 days, triple |
| Client factor | 1.5 for clients who historically pay very late, 1.2 for slow payers |

Recommended action: 1–30 days late = friendly reminder; 31–90 = call the client; 90+ = escalate and put the client on credit hold.

## Result
- The top 10 invoices cover about 89% of overdue money.
- The two oldest invoices (548 and 438 days) come first.
- The list adds up exactly to the ₹27,110,866 overdue total on the Receivables page.

## Limits
The weights are chosen, not learned. With real recovery data (which reminders led to payment) they could be fitted.
