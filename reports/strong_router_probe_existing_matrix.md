# Strong Router Probe

Method: `typewell_particle_filter`
Matrix: `experiments/full_data_router_candidate_matrix.csv`

This OOF probe learns simple diagnostic gates on training folds and applies
the selected gate to the held-out fold. It is a lightweight precursor to a
larger learned geosteering router.

## Summary

| router | pooled_rmse | delta_vs_baseline | selected_splits | catastrophic_rate_plus5 |
| --- | --- | --- | --- | --- |
| baseline_last_value | 14.6844 | 0.0 | 0 | 0.0 |
| always_on_typewell_particle_filter | 14.7336 | 0.0492 | 1546 | 0.0084 |
| oof_diag_gated_typewell_particle_filter | 14.6952 | 0.0108 | 483 | 0.0058 |

## Fold Rules

| fold | rule | train_rmse | val_rmse | selected | val_splits |
| --- | --- | --- | --- | --- | --- |
| 0 | pred_move_abs_p90>q0.80 | 14.3526 | 15.8433 | 53 | 302 |
| 1 | pred_move_abs_p90>q0.80 | 15.0276 | 13.2291 | 74 | 334 |
| 2 | pred_range<q0.40 | 14.6841 | 14.5373 | 112 | 324 |
| 3 | pred_range<q0.40 | 14.6781 | 14.5344 | 117 | 262 |
| 4 | pred_range<q0.40 | 14.4836 | 15.2584 | 127 | 324 |

## Interpretation

- A useful result must improve the baseline on held-out folds, not merely on
  the training folds used to pick a gate.
- If this probe beats the existing move-only gate, promote the selected
  diagnostics into the full router feature set.
- If it fails, the next candidate generator should be constrained alignment
  rather than more PF threshold search.
