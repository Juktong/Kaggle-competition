---
id: n1_geometry_bounded_alignment
priority: 130
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# N1 Geometry-bounded monotonic alignment (slope-constrained DP)

Add a physically derived, test-available admissible band to the G3.2 alignment DP.

Context (do not re-derive):

- G3.2 result (`reports/g32_learned_alignment_smoke_2026-07-28.md`): learned scorer AUC **0.7242** vs NCC
  0.5010, and its DP beats the flat anchor (**12.527 vs 13.103**, interior optimum at lam=60). It is still
  ~42% above the deployed ~8.86, so the formulation needs a constraint, not more capacity.
- The depth-matching literature requires strict monotonicity **and slope constraints** on the warping
  path for geological plausibility and to avoid singularity artifacts. G3.2's DP had only the flat-anchor
  regulariser.
- The new ingredient is that the bound is not a hyper-parameter. TVT satisfies
  `dTVT = -dZ + tan(delta)*dH` with `dZ` and `dH` known exactly per row at test time, and
  `reports/new_direction_search_2026-07-28.md` M4 measured the admissible apparent dip at roughly
  **+/-3.7 degrees** across wells. Each row therefore gets a hard admissible band on the warping slope.

Required execution:

1. Extend `scripts/g32_learned_alignment_smoke.py` with a per-row admissible band on the DP transition,
   derived from that row's `dZ`, `dH` and a dip bound parameter.
2. Sweep the dip bound (e.g. 1, 2, 4, 8 degrees, plus unbounded as the control).
3. Compare on the SAME wells against the recorded 12.527 (DP) and 13.103 (flat anchor). Reuse the same
   scorer weights so the band is the only change.
4. Report whether the band is binding (fraction of rows where it clips the unconstrained optimum). If it
   never binds, the constraint is inert and the result is negative — record that.
5. Do not scale up unless the band produces a clear improvement over 12.527.

Write:

- `reports/n1_geometry_bounded_alignment_2026-07-28.md`

No submission.
