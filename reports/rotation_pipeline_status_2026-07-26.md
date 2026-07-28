

## Round 11 — 2026-07-28 11:33 UTC (autopilot `n4_conformal_well_uncertainty`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.

Loaded the banked OOF (`aligned_preds.npz`, column `s_54844628`, toe-only, 760 wells, 3,721,471 rows) and
reproduced the banked pooled RMSE **8.8626** exactly before any analysis. Splits are by well (lag-1
within-well residual autocorrelation +0.9998 makes a row split leak).

**Marginal split conformal is valid and retained**: nominal 0.80/0.90/0.95 -> widths 9.99/13.43/17.53 ft
with held-out coverage 0.853/0.942/0.966.

**Conditional (Mondrian) conformal is a negative result.** Best feature association |spearman| 0.172
(`nnb`); 5-fold CV R^2 on log(per-well RMSE) = **0.0736**; width separation across bins only 1.28-1.61x
against a true 8.56x median-to-max spread. Decisively, at matched coverage the conditional intervals are
**wider**, not narrower (13.76 / 13.97 vs marginal 13.43) — conditioning costs width. **The per-well
confidence-gating axis flagged by the variant-matrix round is therefore closed on these features**, for
the same reason the anti-harm guard closed at AUC 0.53: the covariates carry no per-well signal.

Two by-products carry more decision value than the intervals:

- **The 3-well scoring scale, measured on the error level.** For one FIXED model, a random row-weighted
  3-well draw pools to 5th **3.491** / median **6.708** / 95th **15.138**. Independent corroboration of
  the 3-well gate doctrine, previously derived from per-well *gain* variance and now measured on the
  error *level*.
- **Conformal on OOF does not bound the leaderboard.** OOF on the 3 test wells **4.756** vs public
  **7.891** = ratio **1.659**. The marginal bound is a statement about train-masked OOF only.

The 3 visible test wells sit at fleet percentiles 0.264 / 0.480 / 0.499 — an easier-than-typical draw,
pooling to percentile 0.207 of the 3-well draw distribution.

Report: `reports/n4_conformal_well_uncertainty_2026-07-28.md`. Script:
`scripts/n4_conformal_well_uncertainty.py`. Next queued: `n2_increment_structural_field` (120).
