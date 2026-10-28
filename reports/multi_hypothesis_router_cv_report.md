# Multi-Hypothesis Router CV Report

This report evaluates a first candidate-path matrix and prefix-holdout router on train pseudo-hidden splits.
It is a diagnostic harness, not an official submission package.

Baseline comparator: `last_value`

## Method Summary

| method | splits | eval_rows | weighted_rmse | mean_rmse | median_rmse | mean_delta_rmse_vs_baseline | median_delta_rmse_vs_baseline | win_rate_vs_baseline | fallback_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| router_confidence_guarded | 15 | 57397 | 14.5068 | 12.6767 | 12.9591 | -0.400249 | 0 | 0.133333 | 0 |
| router_guarded_prefix_holdout | 15 | 57397 | 14.5517 | 12.9377 | 12.9591 | -0.13924 | 0 | 0.0666667 | 0 |
| piecewise_tail_slope_md | 15 | 57397 | 14.6828 | 12.9933 | 11.0843 | -0.0836368 | -0.536917 | 0.533333 | 0 |
| self_corr_prefix_shape | 15 | 57397 | 14.7197 | 12.8159 | 12.9591 | -0.261009 | 0 | 0.0666667 | 0.933333 |
| last_value | 15 | 57397 | 14.764 | 13.0769 | 12.9591 | 0 | 0 | 0 | 0 |
| ncc_shift__last_value | 15 | 57397 | 14.764 | 13.0769 | 12.9591 | 0 | 0 | 0 | 1 |
| fault_step_recent_level | 15 | 57397 | 14.8487 | 13.2588 | 12.8674 | 0.18185 | 0 | 0.0666667 | 0.8 |
| ncc_shift__recent_plateau_quantile | 15 | 57397 | 14.8981 | 13.0208 | 9.46256 | -0.0560993 | 0.00460859 | 0.466667 | 1 |
| recent_plateau_quantile | 15 | 57397 | 14.8981 | 13.0208 | 9.46256 | -0.0560993 | 0.00460859 | 0.466667 | 0 |
| piecewise_tail_slope_Z | 15 | 57397 | 15.1159 | 13.2941 | 12.7844 | 0.217172 | -0.077762 | 0.533333 | 0 |
| gr_shift__recent_plateau_quantile | 15 | 57397 | 15.3034 | 12.9699 | 9.46256 | -0.107022 | -0.00865228 | 0.533333 | 0.4 |
| router_prefix_holdout_best | 15 | 57397 | 15.3522 | 13.6994 | 10.5901 | 0.622512 | 0 | 0.266667 | 0 |
| gr_shift__self_corr_prefix_shape | 15 | 57397 | 15.669 | 13.3521 | 12.3943 | 0.275191 | 0 | 0.266667 | 0.4 |
| gr_shift__piecewise_tail_slope_md | 15 | 57397 | 15.7743 | 13.9835 | 13.2779 | 0.906524 | 0.361031 | 0.466667 | 0.133333 |
| gr_shift__last_value | 15 | 57397 | 15.8209 | 13.9814 | 12.5933 | 0.904459 | 0 | 0.2 | 0.4 |
| gr_shift__fault_step_recent_level | 15 | 57397 | 15.8871 | 14.2294 | 12.9627 | 1.15249 | 0 | 0.2 | 0.4 |

## Router Summary

| method | splits | eval_rows | weighted_rmse | mean_rmse | median_rmse | mean_delta_rmse_vs_baseline | median_delta_rmse_vs_baseline | win_rate_vs_baseline | fallback_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| router_confidence_guarded | 15 | 57397 | 14.5068 | 12.6767 | 12.9591 | -0.400249 | 0 | 0.133333 | 0 |
| router_guarded_prefix_holdout | 15 | 57397 | 14.5517 | 12.9377 | 12.9591 | -0.13924 | 0 | 0.0666667 | 0 |
| router_prefix_holdout_best | 15 | 57397 | 15.3522 | 13.6994 | 10.5901 | 0.622512 | 0 | 0.266667 | 0 |

## Router Selection Counts

| selected_eval_method | count |
| --- | --- |
| fault_step_recent_level | 4 |
| gr_shift__fault_step_recent_level | 2 |
| gr_shift__piecewise_tail_slope_md | 2 |
| last_value | 1 |
| piecewise_tail_slope_Z | 1 |
| gr_shift__piecewise_tail_slope_Z | 1 |
| damped_tail_linear_Z | 1 |
| gr_shift__recent_plateau_quantile | 1 |
| gr_shift__damped_tail_linear_BUDA | 1 |
| damped_tail_linear_md | 1 |

## Guarded Router Selection Counts

| guarded_eval_method | count |
| --- | --- |
| last_value | 12 |
| self_corr_prefix_shape | 2 |
| damped_tail_linear_Z | 1 |

## Confidence Router Selection Counts

| confidence_eval_method | count |
| --- | --- |
| last_value | 11 |
| self_corr_prefix_shape | 3 |
| damped_tail_linear_Z | 1 |

## Worst Router Splits

| well | split | cut_idx | prefix_rows | eval_rows | rmse | baseline_rmse | delta_rmse_vs_baseline | detail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00bbac68 | frac_0.50 | 3780 | 3780 | 3779 | 26.709 | 26.709 | 0 | selected=last_value;default_last_value_after_confidence_gate |
| 00bbac68 | frac_0.65 | 4913 | 4913 | 2646 | 24.0711 | 24.0711 | 0 | selected=last_value;default_last_value_after_confidence_gate |
| 00bbac68 | frac_0.35 | 2646 | 2646 | 4913 | 18.8997 | 18.8997 | 0 | selected=last_value;default_last_value_after_confidence_gate |
| 00bbac68 | frac_0.25 | 1890 | 1890 | 5669 | 17.37 | 17.37 | 0 | selected=last_value;default_last_value_after_confidence_gate |
| 00e12e8b | frac_0.25 | 1596 | 1596 | 4788 | 13.8535 | 13.8535 | 0 | selected=last_value;default_last_value_after_confidence_gate |
| 00bbac68 | native_prefix | 1545 | 1545 | 6014 | 13.1744 | 15.2631 | -2.0886 | selected=damped_tail_linear_Z;kept_prefix_holdout_guard |
| 00e12e8b | frac_0.65 | 4150 | 4150 | 2234 | 13.1458 | 13.1458 | 0 | selected=self_corr_prefix_shape;kept_prefix_holdout_guard |
| 00e12e8b | frac_0.50 | 3192 | 3192 | 3192 | 12.9591 | 12.9591 | 0 | selected=last_value;default_last_value_after_confidence_gate |
| 00e12e8b | frac_0.35 | 2234 | 2234 | 4150 | 10.2291 | 10.2291 | 0 | selected=self_corr_prefix_shape;kept_prefix_holdout_guard |
| 000d7d20 | frac_0.35 | 1847 | 1847 | 3431 | 9.47122 | 9.47122 | 0 | selected=last_value;default_last_value_after_confidence_gate |

## Interpretation

- `router_prefix_holdout_best` chooses a candidate family using only a holdout from the known prefix.
- `router_guarded_prefix_holdout` falls back to `last_value` unless holdout improvement, margin, and family safety gates pass.
- `router_confidence_guarded` starts from the guarded router, then allows high-confidence self-correlation evidence visible in the evaluation GR.
- Piecewise slope and recent fault-step candidates are lightweight dynamic-dip probes; they are diagnostic unless the guarded router selects them without worsening worst-split risk.
- A useful router should improve weighted RMSE or at least reduce worst-split risk versus `last_value`.
- If the router underperforms, inspect `experiments/multi_hypothesis_router_cv_decisions.csv` to see which candidate families the prefix holdout over-selected.

## Outputs

- `experiments/multi_hypothesis_router_cv_scores.csv`
- `experiments/multi_hypothesis_router_cv_summary.csv`
- `experiments/multi_hypothesis_router_cv_decisions.csv`
