
## 2026-07-28 update (G3.3)

- **G3.3 multi-hypothesis trajectory — closed on evidence.** Smoke checks all pass (loss decreases,
  diversity 9.734 ft, sane trajectories) but K=1 regression (18.475) is worse than the flat-anchor
  baseline (15.833) and the best achievable K=5 configuration (16.877) still is. Oracle +5.707 vs
  achievable +1.598. 0 quota. Report: `reports/g33_multi_hypothesis_smoke_2026-07-28.md`.
- Recorded minimal next smoke: condition K hypotheses on the PF's own per-well posterior spread
  (`pf_unc.npz`) and train only on high-spread wells.
- Next runnable: **`frontier_variant_matrix_lite`** (priority 50).

