---
id: q15_frontier_dependency_replacement
priority: 250
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q15 Frontier Prediction-Affecting Dependency Replacement

G1.3 narrowed the frontier dependency surface from 9 public datasets to 1 prediction-affecting
third-party dataset worth about 0.047 public. Test whether that dependency can be replaced or bounded
without losing the frontier line.

Goal:

- Reduce final-slot provenance risk while preserving frontier score.
- Produce an our-repo-controlled replacement or ablation if feasible.

Required execution:

1. Read `reports/frontier_dependency_provenance_audit_2026-07-28.md`.
2. Identify the single prediction-affecting dependency and its exact effect.
3. Try replacement strategies in this order:
   - vendored/reproduced artifact if rules and repo constraints allow;
   - bounded substitute from existing repo artifacts;
   - ablation with calibrated correction.
4. Validate by output diff and public-family proxy; do not use public 3 wells as the only criterion.
5. If a replacement is non-homogeneous and materially reduces provenance risk, Kaggle smoke/full is allowed.
6. Submit only if it passes the gate and the description states the provenance purpose.

Write `reports/q15_frontier_dependency_replacement_2026-07-29.md`.
