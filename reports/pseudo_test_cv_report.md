# Pseudo-Test CV Report

This report hides suffixes of training wells and scores simple hidden-zone inference strategies against known `TVT` labels.
It is not a substitute for Kaggle Public LB, but it gives pre-submission evidence about method families before spending daily slots.

Baseline comparator: `last_value`

## Method Summary

| method | splits | eval_rows | weighted_rmse | mean_delta_rmse_vs_baseline | win_rate_vs_baseline | fallback_rate |
| --- | --- | --- | --- | --- | --- | --- |
| plateau_recent_quantile | 15 | 57397 | 14.5636 | -0.407934 | 0.133333 | 0.8 |
| last_value | 15 | 57397 | 14.764 | 0 | 0 | 0 |
| gr_shift_plateau_quantile | 15 | 57397 | 15.3786 | 0.16478 | 0.266667 | 0.466667 |
| plateau_gated_tail_linear | 15 | 57397 | 16.6411 | 2.18918 | 0 | 0.666667 |
| gr_shift_plateau_gated | 15 | 57397 | 17.3177 | 3.06636 | 0.0666667 | 0.333333 |
| gr_shift_tail_linear | 15 | 57397 | 50.0381 | 24.1649 | 0.266667 | 0.0666667 |
| tail_linear_md | 15 | 57397 | 51.699 | 24.1515 | 0.266667 | 0 |
| best_strat_linear | 15 | 57397 | 100.783 | 81.9628 | 0 | 0 |
| gr_shift_best_strat | 15 | 57397 | 101.008 | 81.1449 | 0 | 0 |
| full_linear_md | 15 | 57397 | 1175.2 | 852.49 | 0 | 0 |

Interpretation:

- Negative `mean_delta_rmse_vs_baseline` means the method beat the baseline comparator on average.
- High `fallback_rate` means a method's safety gate often refused to modify the baseline.
- Treat this as directional evidence; full public/private hidden wells can differ.

## Worst Split Rows

| well | split | method | status | rmse | baseline_rmse | delta_rmse_vs_baseline | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 00bbac68 | native_prefix | full_linear_md | ok | 2010.78 | 15.2631 | 1995.51 |  |
| 00e12e8b | frac_0.25 | full_linear_md | ok | 1853.27 | 13.8535 | 1839.42 |  |
| 00bbac68 | frac_0.25 | full_linear_md | ok | 1500.26 | 17.37 | 1482.89 |  |
| 00e12e8b | native_prefix | full_linear_md | ok | 1302.31 | 7.92459 | 1294.38 |  |
| 00e12e8b | frac_0.35 | full_linear_md | ok | 1172.1 | 10.2291 | 1161.87 |  |
| 000d7d20 | frac_0.25 | full_linear_md | ok | 909.029 | 7.12635 | 901.902 |  |
| 00bbac68 | frac_0.35 | full_linear_md | ok | 849.645 | 18.8997 | 830.745 |  |
| 000d7d20 | native_prefix | full_linear_md | ok | 781.003 | 7.45444 | 773.548 |  |
| 00e12e8b | frac_0.50 | full_linear_md | ok | 642.501 | 12.9591 | 629.542 |  |
| 000d7d20 | frac_0.35 | full_linear_md | ok | 501.45 | 9.47122 | 491.979 |  |
| 00bbac68 | frac_0.50 | full_linear_md | ok | 438.886 | 26.709 | 412.177 |  |
| 00e12e8b | frac_0.65 | full_linear_md | ok | 371.18 | 13.1458 | 358.034 |  |

## Outputs

- `experiments/pseudo_test_cv_scores.csv`
- `experiments/pseudo_test_cv_summary.csv`
