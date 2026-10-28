---
id: q41_nonhomogeneous_ensemble_search
priority: 600
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q41 Non-Homogeneous Ensemble Search

The final score is best-of-2, but a non-homogeneous ensemble may still be valuable if it becomes a better single slot than an existing member.

Do not average near-duplicate frontier variants just to create another frontier submission.

Required execution:

1. Gather available local/submission predictions for:
   - honest DWT+PF/structural field;
   - frontier family members;
   - qwer/historical public-derived candidates if predictions exist.
2. Search only ensembles that mix different error mechanisms:
   - honest + frontier;
   - structural field + frontier;
   - bounded residual blend with strict gates;
   - rank/median/trimmed ensemble if predictions are on a common row order.
3. Validate by well. Include 3-well bootstrap and family-correlation analysis.
4. Submit only if the candidate is non-homogeneous and expected public effect is >0.115 or changes final-slot logic.
5. If no candidate passes, close with exact reason.

Write `reports/q41_nonhomogeneous_ensemble_search_2026-07-30.md`.
