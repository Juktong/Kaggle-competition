---
id: q45_external_leaderboard_gap_refresh
priority: 640
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q45 External Leaderboard Gap Refresh

Q19 found the public published pool does not explain the top-200 gap. Refresh this once, cheaply.

Required execution:

1. Refresh public leaderboard rank and top scores.
2. Refresh public kernels/notebooks since Q19 by recency.
3. Identify only genuinely new methods or kernels that advertise <=6.5 or materially different architecture.
4. For each candidate:
   - compare code lineage;
   - identify exact changed tokens/stages;
   - classify as adoptable, information-only, or not useful.
5. Create follow-up queue items only if smoke-testable and non-duplicate.
6. Do not submit in this task.

Write `reports/q45_external_leaderboard_gap_refresh_2026-07-30.md`.
