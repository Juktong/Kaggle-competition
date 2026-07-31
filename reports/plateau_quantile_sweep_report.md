# Plateau Quantile Sweep Report

This report checks whether the plateau recent-quantile rule is stable across nearby local-validation parameters.
It uses pseudo-test splits only and does not consume official Kaggle submissions.

## Stability Summary

- Parameter combos tested: `36`
- Combos beating `last_value` weighted RMSE: `10`
- Beat rate: `0.278`
- Default combo rank: `1`

## Top Combos

| combo_id | window | quantile | min_move | blend | weighted_rmse | delta_weighted_rmse_vs_last_value | win_rate_vs_last_value | fallback_rate | ok_splits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | 256 | 0.5 | 4 | 1 | 14.5636 | -0.200451 | 0.133333 | 0.8 | 3 |
| 36 | 512 | 0.65 | 8 | 1 | 14.5643 | -0.199662 | 0.0666667 | 0.933333 | 1 |
| 23 | 256 | 0.65 | 6 | 1 | 14.5832 | -0.180792 | 0.0666667 | 0.933333 | 1 |
| 24 | 256 | 0.65 | 8 | 1 | 14.5832 | -0.180792 | 0.0666667 | 0.933333 | 1 |
| 35 | 512 | 0.65 | 6 | 1 | 14.5999 | -0.164121 | 0.133333 | 0.8 | 3 |
| 15 | 256 | 0.35 | 6 | 1 | 14.6641 | -0.0999102 | 0.0666667 | 0.933333 | 1 |
| 14 | 256 | 0.35 | 4 | 1 | 14.704 | -0.0600555 | 0.0666667 | 0.866667 | 2 |
| 1 | 128 | 0.35 | 2 | 1 | 14.7081 | -0.0558995 | 0.0666667 | 0.866667 | 2 |
| 21 | 256 | 0.65 | 2 | 1 | 14.733 | -0.0310485 | 0.133333 | 0.733333 | 4 |
| 17 | 256 | 0.5 | 2 | 1 | 14.7508 | -0.0132164 | 0.133333 | 0.733333 | 4 |
| 2 | 128 | 0.35 | 4 | 1 | 14.764 | 0 | 0 | 1 | 0 |
| 3 | 128 | 0.35 | 6 | 1 | 14.764 | 0 | 0 | 1 | 0 |

## By Window

| window | combos | best_weighted_rmse | mean_delta | beat_rate |
| --- | --- | --- | --- | --- |
| 256 | 12 | 14.5636 | -0.041644 | 0.583333 |
| 512 | 12 | 14.5643 | 0.707327 | 0.166667 |
| 128 | 12 | 14.7081 | 0.00572291 | 0.0833333 |

## By Quantile

| quantile | combos | best_weighted_rmse | mean_delta | beat_rate |
| --- | --- | --- | --- | --- |
| 0.5 | 12 | 14.5636 | 0.320513 | 0.166667 |
| 0.65 | 12 | 14.5643 | -0.00126964 | 0.416667 |
| 0.35 | 12 | 14.6641 | 0.352163 | 0.25 |

## By Min Move

| min_move | combos | best_weighted_rmse | mean_delta | beat_rate |
| --- | --- | --- | --- | --- |
| 4 | 9 | 14.5636 | 0.212816 | 0.222222 |
| 8 | 9 | 14.5643 | 0.176176 | 0.222222 |
| 6 | 9 | 14.5832 | 0.179185 | 0.333333 |
| 2 | 9 | 14.7081 | 0.327031 | 0.333333 |

## Best Combo Split Detail

| combo_id | well | split | status | rmse | baseline_rmse | delta_rmse_vs_baseline | detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | 00e12e8b | frac_0.65 | ok | 8.40927 | 13.1458 | -4.73658 | window=256;quantile=0.500;target=11592.5800;move=5.3100 |
| 18 | 00e12e8b | frac_0.35 | ok | 8.20539 | 10.2291 | -2.02372 | window=256;quantile=0.500;target=11605.7800;move=-4.5300 |
| 18 | 000d7d20 | native_prefix | fallback | 7.45444 | 7.45444 | 0 | target=11746.6400;move=-0.7300;min_move=4.000 |
| 18 | 000d7d20 | frac_0.25 | fallback | 7.12635 | 7.12635 | 0 | target=11746.5200;move=-0.5500;min_move=4.000 |
| 18 | 000d7d20 | frac_0.35 | fallback | 9.47122 | 9.47122 | 0 | target=11749.2900;move=-0.0100;min_move=4.000 |
| 18 | 000d7d20 | frac_0.50 | fallback | 4.53304 | 4.53304 | 0 | target=11742.7300;move=0.7700;min_move=4.000 |
| 18 | 000d7d20 | frac_0.65 | fallback | 7.14371 | 7.14371 | 0 | target=11745.2700;move=1.1400;min_move=4.000 |
| 18 | 00bbac68 | native_prefix | fallback | 15.2631 | 15.2631 | 0 | target=12223.2750;move=-0.2650;min_move=4.000 |
| 18 | 00bbac68 | frac_0.25 | fallback | 17.37 | 17.37 | 0 | target=12228.6500;move=0.0100;min_move=4.000 |
| 18 | 00bbac68 | frac_0.35 | fallback | 18.8997 | 18.8997 | 0 | target=12229.1300;move=0.0100;min_move=4.000 |
| 18 | 00bbac68 | frac_0.50 | fallback | 26.709 | 26.709 | 0 | target=12237.7300;move=1.2300;min_move=4.000 |
| 18 | 00bbac68 | frac_0.65 | fallback | 24.0711 | 24.0711 | 0 | target=12226.2500;move=-1.4400;min_move=4.000 |
| 18 | 00e12e8b | frac_0.25 | fallback | 13.8535 | 13.8535 | 0 | target=11590.2500;move=-1.7300;min_move=4.000 |
| 18 | 00e12e8b | frac_0.50 | fallback | 12.9591 | 12.9591 | 0 | target=11615.8350;move=3.6650;min_move=4.000 |
| 18 | 00e12e8b | native_prefix | ok | 8.56588 | 7.92459 | 0.641291 | window=256;quantile=0.500;target=11600.7200;move=-4.1000 |

## Interpretation

- A high beat rate across nearby parameters supports a structural rule.
- A single narrow winner suggests local overfit and should stay on hold.
- Use this report to decide whether plateau candidates deserve an official information slot after pending scores resolve.

## Outputs

- `experiments/plateau_quantile_sweep.csv`
- `experiments/plateau_quantile_sweep_split_scores.csv`
