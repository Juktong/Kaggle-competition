---
id: n7_q3d_tortuosity_features
priority: 180
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# N7 Q-3D wellbore tortuosity as a residual predictor

Test whether quasi-3D wellbore tortuosity carries information about our honest line's per-well error.

Context (do not re-derive):

- `reports/n6_public_solution_audit_2026-07-28.md`: a public methodology repo reports Q-3D tortuosity
  (Jing et al. 2022) as its **largest single feature-group ablation gain, -0.107 RMSE**. The stated
  mechanism is that high tortuosity marks active steering, which signals the formation deviating from
  plan.
- The quantity is computed from MD/X/Y/Z alone, so it is **fully test-available**.
- Absent from our evidence ledger entirely.
- **Implement from the cited paper, not by copying the repo's code**, to keep provenance clean:
  Jing, J., Ye, W., Cao, C., Ran, X. (2022). "Actual wellbore tortuosity evaluation using a new
  quasi-three-dimensional approach." Petroleum, 8, 118-127.

Required execution:

1. Derive inclination and azimuth from successive XYZ deltas; compute per-portion `T_incline`,
   `Gamma_incline`, `T_azimuth`, `Gamma_azimuth` and the combined `TQG_Q3D`.
2. Compute on ~40 wells first as a smoke; confirm the values are finite, scale-sane and stable.
3. **Before** touching the model: correlate per-well tortuosity against the banked per-well honest OOF
   RMSE (`rogii_sprint_shared/tmp/n4_well_uncertainty.csv`). N4 measured that every test-available
   feature tried so far reaches only CV R^2 0.074 on log per-well RMSE — report whether tortuosity beats
   that bar.
4. If and only if it does, extend to all 760 wells and consider it as a feature; otherwise close the
   direction and record the measured correlation.

Write:

- `reports/n7_q3d_tortuosity_features_2026-07-28.md`
- Reusable script under `scripts/`.

No submission.
