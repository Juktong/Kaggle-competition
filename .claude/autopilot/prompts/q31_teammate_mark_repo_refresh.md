---
id: q31_teammate_mark_repo_refresh
priority: 410
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q31 Teammate / Mark Repo Refresh

Refresh Mark/Marc repo and any teammate-visible updates that could change our queue.

Goal:

- Avoid missing a new strong notebook or patch.
- Integrate only targeted, non-destructive updates.

Required execution:

1. Fetch `origin` and `juktong`.
2. Inspect `origin/main` and relevant branches since last audit.
3. Identify new notebooks, reports, submissions, or artifacts.
4. If a new candidate appears:
   - audit provenance;
   - smoke before full;
   - submit only if it passes the gate and is not a duplicate.
5. If no change, record that fact.

Write `reports/q31_teammate_mark_repo_refresh_2026-07-29.md`.
