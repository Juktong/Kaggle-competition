---
id: q55_dp_decoder_averaging
priority: 626
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q55 DP Decoder Averaging (beam average + soft-min Bellman)

Two cheap changes to the DECODER, leaving emission and transition untouched. Both are Rule #1's averaging
class, and both are untested on the DP.

1. **Beam average.** `run_dp` keeps K=6 beams and returns `beams[0]` only. Average the beam instead,
   weighted by `exp(-cost/T)`, sweeping T.
2. **Soft-min Bellman.** Replace the DP's hard `min` with a soft-min at temperature gamma (soft-DTW /
   differentiable-DP), which is a closed-form average over near-optimal paths.

PRECEDENT THAT THIS IS NOT IDLE: Q21 discovered the deployed PF ensemble IS ALREADY a softmax over paths at
scale T=5, and that T=5 sits at a nested optimum of a 27-member family. The same operator has never been
applied to the DP.

Required execution:

1. Reuse the Q40/Q10 harness, same split seed, >= 40 eval wells.
2. Sweep T (beam average) and gamma (soft-min) jointly with lambda, chosen NESTED by well.
3. Include the T -> 0 / gamma -> 0 limits, which must reproduce the current hard-argmin decoder EXACTLY —
   report that degeneracy check as a correctness control (Q40 used the same device).
4. Validate on DP OUTPUT only.
5. GATE: nested gain over `l1 lam=60` (12.170) > 0 AND helps > 50% of wells AND 3-well 5th > 0.
6. Do not submit.

Same honesty note as q54: this line is ~12.2 vs the deployed 8.8626; passing does not make it submittable.

Expected cost: ~10 min, same harness.

Write `reports/q55_dp_decoder_averaging_<date>.md`.
