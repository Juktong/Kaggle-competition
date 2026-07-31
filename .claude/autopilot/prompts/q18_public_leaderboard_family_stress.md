---
id: q18_public_leaderboard_family_stress
priority: 280
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q18 Public Leaderboard Family Stress Test

Update the final-slot simulator with all 2026-07-28/29 queue findings and the observed family-level
failures. This is a decision task, not a submission task.

Goal:

- Separate score-first, diversity-first, provenance-first, and our-account-first views.
- Stress how much `54922806` would need to degrade for `54968060` or `54844628` to become slot 1.
- Evaluate whether any new Q10-Q17 candidate changes the final pair.

Required execution:

1. Read current final-slot package and all Q/N reports.
2. Update simulator assumptions:
   - family correlation;
   - provenance risk;
   - OOF support;
   - public-to-private transfer from N4;
   - no new private score visibility.
3. Output a concise table of final-pair recommendations.
4. Do not submit.

Write `reports/q18_public_leaderboard_family_stress_2026-07-29.md`.
