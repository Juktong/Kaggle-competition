---
id: q38_teammate_submission_provenance_recovery
priority: 570
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q38 Teammate Submission Provenance Recovery

Purpose: answer the owner's question: "Do we have all teammate solution data?"

Do not infer private-kernel facts. Build an evidence table.

Required execution:

1. Refresh Kaggle submissions and repo remotes.
2. Enumerate every teammate-side submission in the ledger, at minimum:
   - 54922806, 54896975, 54923144, 54853492.
3. For each, record what we actually have:
   - submission description;
   - public score;
   - suspected family;
   - kernel slug if known;
   - exact kernel version if known;
   - dataset_sources if known;
   - whether code is accessible from this account;
   - whether a reproducible package exists in repo.
4. Specifically distinguish:
   - Mark/origin/main public-6.626 repro package;
   - exact 54922806 6.563 private run.
5. If any teammate data is missing, write a concise request message the owner can send to the teammate.
6. Do not submit.

Write `reports/q38_teammate_submission_provenance_recovery_2026-07-30.md`.
