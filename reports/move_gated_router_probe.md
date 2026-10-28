# Move-Gated Router Probe

Method: `typewell_particle_filter` | move feature: `pred_move_abs_p90` | splits: 1546

Out-of-fold: the move threshold is chosen on the training folds (by pooled
RMSE) and applied to the held-out validation fold. No PF rerun; reads the
existing candidate matrix.

| router | pooled_rmse | delta_vs_baseline | pf_selected_splits | catastrophic_rate_plus5 |
| --- | --- | --- | --- | --- |
| baseline_last_value | 14.6844 | 0.0 | 0 | 0.0 |
| always_on_pf | 14.7336 | 0.0492 | 1546 | 0.0084 |
| oof_move_gated_pf | 14.6782 | -0.0062 | 384 | 0.0084 |

## Per-fold learned thresholds

| fold | val_splits | best_train_quantile | threshold | pf_selected |
| --- | --- | --- | --- | --- |
| 0.0 | 302.0 | 0.8 | 7.477 | 53.0 |
| 1.0 | 334.0 | 0.8 | 7.36 | 74.0 |
| 2.0 | 324.0 | 0.8 | 7.459 | 61.0 |
| 3.0 | 262.0 | 0.8 | 7.365 | 58.0 |
| 4.0 | 324.0 | 0.6 | 5.37 | 138.0 |

## Interpretation

- Always-on PF is slightly worse than last_value on full data, which is why
  the unconditional-prior router rejects it and returns the baseline exactly.
- Gating PF by its own move magnitude recovers a small out-of-fold gain by
  keeping PF only on the high-move splits (its concentrated high-drift rescues)
  and last_value elsewhere.
- Next step: promote move-gated (or a small learned move/uncertainty) router
  into the framework, and plumb PF diagnostics into the matrix.
