# Full-Data Router Matrix Report

This is the first full-train candidate-path matrix and learned-prior router CV.
It is not a submission package.

## Run Config

- data_dir: `data/rogii`
- splits: native prefix plus `0.50`
- folds: `5` stable well-hash folds
- max_wells: `all`

## Method Summary

| method | splits | eval_rows | weighted_rmse | mean_delta_rmse_vs_baseline | median_delta_rmse_vs_baseline | win_rate_vs_baseline | catastrophic_rate_plus5 | hidden_compatible | router_eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gr_shift__fault_step_recent_level | 1546 | 6330100 | 14.5985 | 0.039709 | 0 | 0.401035 | 0.0194049 | True | False |
| fault_step_recent_level | 1546 | 6330100 | 14.6074 | -0.00553682 | 0 | 0.113195 | 0 | True | False |
| gr_shift__last_value | 1546 | 6330100 | 14.6543 | 0.0779546 | 0 | 0.3674 | 0.0122898 | True | False |
| last_value | 1546 | 6330100 | 14.6844 | 0 | 0 | 0 | 0 | True | True |
| ncc_shift__last_value | 1546 | 6330100 | 14.6844 | 0 | 0 | 0 | 0 | True | False |
| typewell_particle_filter | 1546 | 6330100 | 14.7336 | 0.0778259 | 0.0659087 | 0.46119 | 0.0084088 | True | True |
| gr_shift__typewell_particle_filter | 1546 | 6330100 | 14.7747 | 0.117797 | 0.0839059 | 0.467012 | 0.0194049 | True | False |
| piecewise_tail_slope_Z | 1546 | 6330100 | 14.7846 | 0.204276 | 0.29205 | 0.445666 | 0 | True | False |
| piecewise_tail_slope_md | 1546 | 6330100 | 14.8023 | 0.219348 | 0.321479 | 0.441785 | 0 | True | False |
| gr_shift__self_corr_prefix_shape | 1546 | 6330100 | 14.8155 | 0.247563 | 0 | 0.371928 | 0.042044 | True | False |
| gr_shift__piecewise_tail_slope_Z | 1546 | 6330100 | 14.8503 | 0.355989 | 0.293722 | 0.44696 | 0.0737387 | True | False |
| gr_shift__piecewise_tail_slope_md | 1546 | 6330100 | 14.8626 | 0.336568 | 0.305966 | 0.443726 | 0.0633894 | True | False |
| self_corr_prefix_shape | 1546 | 6330100 | 14.9035 | 0.240603 | 0 | 0.0627426 | 0.0310479 | True | True |
| ncc_shift__recent_plateau_quantile | 1546 | 6330100 | 15.3467 | 0.470542 | 0.0853821 | 0.426261 | 0.0323415 | True | False |
| recent_plateau_quantile | 1546 | 6330100 | 15.3467 | 0.470542 | 0.0853821 | 0.426261 | 0.0323415 | True | True |
| gr_shift__recent_plateau_quantile | 1546 | 6330100 | 15.371 | 0.530933 | 0.184359 | 0.443079 | 0.076326 | True | False |
| damped_tail_linear_Z | 1546 | 6330100 | 15.8175 | 1.11761 | 0.63555 | 0.398448 | 0.198577 | True | True |
| gr_shift__damped_tail_linear_Z | 1546 | 6330100 | 15.8187 | 1.14812 | 0.904469 | 0.39586 | 0.189521 | True | False |
| gr_shift__damped_tail_linear_ASTNL | 1546 | 6330100 | 15.9688 | 1.21943 | 0.955243 | 0.394567 | 0.199871 | False | False |
| gr_shift__damped_tail_linear_BUDA | 1546 | 6330100 | 15.9718 | 1.2223 | 0.9553 | 0.394567 | 0.200517 | False | False |

## Router Summary

| router | splits | eval_rows | weighted_rmse | baseline_weighted_rmse | mean_delta_rmse_vs_baseline | median_delta_rmse_vs_baseline | win_rate_vs_baseline | catastrophic_rate_plus5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| learned_prior_router | 1546 | 6330100 | 14.6844 | 14.6844 | 0 | 0 | 0 | 0 |

## Router Selection Counts

| selected_method | count |
| --- | --- |
| last_value | 1546 |

## Worst Router Decisions

| validation_fold | well | split | selected_method | router_rmse | baseline_rmse | delta_rmse_vs_baseline | selected_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 000d7d20 | native_prefix | last_value | 7.45444 | 7.45444 | 0 | fallback_last_value |
| 3 | 7acda2df | native_prefix | last_value | 13.8412 | 13.8412 | 0 | fallback_last_value |
| 3 | 5d7198fd | native_prefix | last_value | 13.3665 | 13.3665 | 0 | fallback_last_value |
| 3 | 5cb483ac | frac_0.50 | last_value | 10.854 | 10.854 | 0 | fallback_last_value |
| 3 | 5cb483ac | native_prefix | last_value | 6.11408 | 6.11408 | 0 | fallback_last_value |
| 3 | 5aa03df7 | frac_0.50 | last_value | 12.422 | 12.422 | 0 | fallback_last_value |
| 3 | 5aa03df7 | native_prefix | last_value | 6.58601 | 6.58601 | 0 | fallback_last_value |
| 3 | 5a1a8fd8 | frac_0.50 | last_value | 11.6054 | 11.6054 | 0 | fallback_last_value |
| 3 | 5a1a8fd8 | native_prefix | last_value | 13.1653 | 13.1653 | 0 | fallback_last_value |
| 3 | 577eec7c | frac_0.50 | last_value | 18.4736 | 18.4736 | 0 | fallback_last_value |
| 3 | 577eec7c | native_prefix | last_value | 18.8753 | 18.8753 | 0 | fallback_last_value |
| 3 | 5567d551 | frac_0.50 | last_value | 6.13954 | 6.13954 | 0 | fallback_last_value |
| 3 | 5567d551 | native_prefix | last_value | 10.2895 | 10.2895 | 0 | fallback_last_value |
| 3 | 54753541 | frac_0.50 | last_value | 27.8908 | 27.8908 | 0 | fallback_last_value |
| 3 | 54753541 | native_prefix | last_value | 16.2228 | 16.2228 | 0 | fallback_last_value |
| 3 | 5305524b | frac_0.50 | last_value | 5.79663 | 5.79663 | 0 | fallback_last_value |

## Learned Method Priors

| method | prior_mean_delta | prior_median_delta | prior_win_rate | prior_catastrophic_rate_plus5 | prior_splits | prior_allowed | validation_fold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| last_value | 0 | 0 | 0 | 0 | 1244 | True | 0 |
| typewell_particle_filter | 0.0542648 | 0.0679715 | 0.456592 | 0.00643087 | 1244 | False | 0 |
| self_corr_prefix_shape | 0.200147 | 0 | 0.0643087 | 0.0321543 | 1244 | False | 0 |
| recent_plateau_quantile | 0.463336 | 0.0824749 | 0.422026 | 0.0337621 | 1244 | False | 0 |
| damped_tail_linear_Z | 1.05997 | 0.557531 | 0.404341 | 0.19373 | 1244 | False | 0 |
| last_value | 0 | 0 | 0 | 0 | 1212 | True | 1 |
| typewell_particle_filter | 0.0865252 | 0.0705823 | 0.457921 | 0.00742574 | 1212 | False | 1 |
| self_corr_prefix_shape | 0.295609 | 0 | 0.0635314 | 0.0371287 | 1212 | False | 1 |
| recent_plateau_quantile | 0.485713 | 0.0829561 | 0.433993 | 0.0338284 | 1212 | False | 1 |
| damped_tail_linear_Z | 1.15578 | 0.665244 | 0.403465 | 0.20462 | 1212 | False | 1 |
| last_value | 0 | 0 | 0 | 0 | 1222 | True | 2 |
| typewell_particle_filter | 0.0751587 | 0.0659087 | 0.462357 | 0.00736498 | 1222 | False | 2 |
| self_corr_prefix_shape | 0.177948 | 0 | 0.0597381 | 0.0220949 | 1222 | False | 2 |
| recent_plateau_quantile | 0.425152 | 0.0834899 | 0.42635 | 0.0278232 | 1222 | False | 2 |
| damped_tail_linear_Z | 1.14001 | 0.63555 | 0.392799 | 0.194763 | 1222 | False | 2 |
| last_value | 0 | 0 | 0 | 0 | 1284 | True | 3 |
| typewell_particle_filter | 0.0959244 | 0.0684936 | 0.46028 | 0.0101246 | 1284 | False | 3 |
| self_corr_prefix_shape | 0.256173 | 0 | 0.0654206 | 0.0327103 | 1284 | False | 3 |
| recent_plateau_quantile | 0.47238 | 0.0821736 | 0.42757 | 0.0327103 | 1284 | False | 3 |
| damped_tail_linear_Z | 1.11991 | 0.680303 | 0.392523 | 0.197819 | 1284 | False | 3 |
| last_value | 0 | 0 | 0 | 0 | 1222 | True | 4 |
| typewell_particle_filter | 0.0768335 | 0.0530683 | 0.468903 | 0.0106383 | 1222 | False | 4 |
| self_corr_prefix_shape | 0.273529 | 0 | 0.0605565 | 0.0310966 | 1222 | False | 4 |
| recent_plateau_quantile | 0.506289 | 0.0978227 | 0.42144 | 0.0335516 | 1222 | False | 4 |
| damped_tail_linear_Z | 1.11364 | 0.63555 | 0.399345 | 0.202128 | 1222 | False | 4 |

## Interpretation

- This run uses all available train wells unless `--max-wells` is set.
- The router is intentionally simple: out-of-fold method priors plus prefix-holdout evidence.
- Hidden-incompatible train-only formation columns are allowed as diagnostics in the matrix, but labeled explicitly.
- The learned-prior router is stricter than hidden compatibility: it currently allows only conservative release-eligible methods.
- A useful next router should beat `last_value` on weighted RMSE and keep catastrophic-rate low.

## Outputs

- `experiments/full_data_router_candidate_matrix.csv`
- `experiments/full_data_router_method_summary.csv`
- `experiments/full_data_router_choices.csv`
- `experiments/full_data_router_summary.csv`
- `experiments/full_data_router_method_priors.csv`
