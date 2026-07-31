---
id: q32_score_watcher_and_recovery
priority: 420
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q32 Score Watcher And Recovery

Handle long-pending Kaggle submissions and update queue/final decisions once scores land.

Goal:

- Do not block research on pending scores.
- Do not resubmit near-duplicates.
- Keep final-slot docs current.

Required execution:

1. Check all pending submissions, especially `55064411`.
2. If scored, update:
   - submission ledger;
   - final-slot package;
   - rotation queue;
   - any score-response report.
3. If still pending, record latency and next poll cadence.
4. If Kaggle submission appears stuck beyond normal but kernel is complete, do not resubmit unless there is a non-duplicate reason.

Write `reports/q32_score_watcher_and_recovery_2026-07-29.md`.
