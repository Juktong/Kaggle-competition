---
id: q54_dp_hard_path_constraints
priority: 625
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q54 DP Hard Path Constraints (Sakoe-Chiba corridor + Itakura slope limits)

Q40 tested 45 transition arms and the deployed `lam*|dstate|/BAND` beat all of them — but every arm was a
SOFT PER-STEP PENALTY (L1, L2, Huber, drift, curvature). Q40 also produced the mechanism: **a per-step
directional term is multiplied by the path length**, compounding over ~477 DP steps into tens of feet.

A HARD constraint does the opposite: it bounds accumulated deviation REGARDLESS of path length. That makes
this the structural complement of everything Q40 closed, motivated by Q40's own finding.

The current DP has NO global constraint. `run_dp` uses `lo, hi = max(0, s-BAND), min(S, s+BAND+1)` — a
+-60 window around the PREVIOUS state — so cumulative deviation from the anchor is unbounded, and there is
no minimum or maximum slope.

Required execution:

1. Reuse the Q40/Q10 harness (`scripts/q40_transition_model_search.py`), same split seed, >= 40 eval wells.
2. Add an ADMISSIBILITY MASK to `run_dp`, not a penalty:
   - cumulative corridor: `|state_j - anchor| <= C`, sweep C;
   - slope limits: `slope_min <= dstate/dstep <= slope_max` (Itakura's classic is 0.5-2; generalise).
3. Sweep both jointly, chosen NESTED (select on one half of the eval wells, score on the disjoint half).
4. Validate on DP OUTPUT only — never a pointwise emission metric (Q17's rule).
5. GATE: nested gain over the `l1 lam=60` baseline (12.170 pooled) > 0 AND helps > 50% of wells AND
   3-well bootstrap 5th > 0.
6. Do not submit.

HONESTY NOTE to carry into the report: this line sits at ~12.2 against the deployed honest line's 8.8626.
Passing here makes the transition lever worth pursuing; it does NOT make the artifact submittable. Q41 also
showed the 3-well 5th condition is maximised by changing nothing, so expect that condition to fail — the
informative outputs are the nested gain and the per-well win rate.

Expected cost: ~10 min, reusing the existing harness.

Write `reports/q54_dp_hard_path_constraints_<date>.md`.
