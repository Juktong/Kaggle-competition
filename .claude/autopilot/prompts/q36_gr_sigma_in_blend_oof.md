---
id: q36_gr_sigma_in_blend_oof
priority: 460
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q23 GR-sigma widening inside the DWT+PF blend OOF

Q19 found that the public 6.213 kernel differs from our pristine base by exactly one token: `* 1.3` on the
PF likelihood's GR noise sigma. Measured on our own STANDALONE conservative PF (60 wells, splits by well,
nested), the multiplier gave **+2.3513** with **1.5 a confirmed interior optimum** — but the win is
**tail-driven** (helps only 41.7% of wells) and the **3-well bootstrap 5th is -4.1145**, so it failed the
gate.

The standalone PF is only a **0.5-weight component** of the honest line, and Rule #1 records that
averaging and shrinkage transfer while tails get damped. This task tests whether the blend damps the tail
failure.

Required execution:

1. Use `_GS_MULT` (already added to `scripts/pf_honest_forward.py`, default 1.0 = prior behaviour).
2. Evaluate `_GS_MULT` in {1.0, 1.3, 1.5} **inside the DWT+PF blend**, not the standalone PF.
3. Full **760-well** nested OOF; splits BY WELL; multiplier chosen nested (never a bare sweep).
4. Report per-well win rate and the **3-well bootstrap**, not only pooled RMSE.
5. GATE: promote only if the nested gain is positive AND the 3-well bootstrap 5th percentile > 0 AND it
   helps a majority of wells. A tail-driven pooled gain does NOT pass.
6. Do not submit. This is a validation task; `q37` handles any kernel work.

Write `reports/q23_gr_sigma_in_blend_oof_<date>.md`.
