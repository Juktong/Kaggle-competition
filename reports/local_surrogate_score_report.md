# ROGII Local Surrogate Score Report

This report scores already-generated submission CSV files without using hidden labels.
It cannot replace Kaggle Public LB, but it helps reject implausible candidates before spending limited submissions.

## Inputs
- Data dir: `data/sample`
- Valid submission files scored: `69`
- Known public-score calibration rows: `0`

## Important Limitation

A submission CSV only contains hidden-row predictions, so true prefix RMSE cannot be computed from a CSV alone.
Instead, the script computes visible-prefix compatibility: first hidden prediction vs last `TVT_input`, slope continuity, jump rate, typewell range checks, and distances to known scored references.

## Best Known Public Scores In This Scan

No known public-score rows were matched.

## Top Unknown Candidates By Surrogate

| path | risk_grade | estimated_public_band | rmse_to_current_best_7p235 | nearest_known_public_score | rmse_to_nearest_known | anchor_first_abs_p90 | jump_rate_abs_slope_gt3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artifacts/baidalin_preflight_redownload_v1/submission.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/baidalin_preflight_redownload_v1/submission_gold_prefix_aggressive.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/baidalin_preflight_redownload_v1/submission_gold_prefix_balanced.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/baidalin_preflight_redownload_v1/submission_gold_prefix_conservative.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/baidalin_preflight_redownload_v1/submission_public_self_verified.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/baidalin_preflight_redownload_v1/submission_version2_refactor_copy.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/submission.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/submission_gold_prefix_aggressive.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/submission_gold_prefix_balanced.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/submission_gold_prefix_conservative.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/submission_pre_gold.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/submission_public_self_verified.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v2/submission_gold_prefix_aggressive.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v2/submission_gold_prefix_balanced.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v2/submission_gold_prefix_conservative.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v2/submission_pre_gold.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/fleongg_branch_calibration_joezzzzz_v2/submission_public_self_verified.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_gold_prefix_aggressive.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_gold_prefix_balanced.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_gold_prefix_conservative.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_public_self_verified.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_version2_refactor_copy.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission_gold_prefix_aggressive.csv | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 |  |  | 0.0360878 | 7.06814e-05 |

## Recommended Use

1. Run this script after every new kernel output is downloaded.
2. Do not submit candidates marked `reject_known_bad`, `reject_far_from_best`, or `high_shape_risk` unless there is a specific reason.
3. Treat `near_duplicate_low_upside` as safe but unlikely to improve public LB.
4. Prioritize `plausible_submit_candidate` candidates that are not too far from the current best and have low jump/anchor risk.

## Output Files

- `experiments/local_surrogate_scores.csv`
- `experiments/local_surrogate_pairwise_distance.csv`