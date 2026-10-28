# Planned Candidate Well Impact

This report analyzes planned submission candidates per well against the active-account baseline output. It is local validation only and does not submit to Kaggle.

## Impact Buckets

| impact_bucket | count |
| --- | --- |
| SPARSE_INFORMATION | 2 |
| BROAD | 2 |
| SINGLE_WELL_DOMINATED | 1 |

## Candidate Summary

| planned_slot | candidate_id | family | impact_bucket | changed_well_count | changed_row_frac | rmse_to_baseline | top_well | top_well_contribution_frac | top_well_rmse_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plateau_recent_quantile_v1_submission | plateau_signal | SINGLE_WELL_DOMINATED | 1 | 0.303936 | 4.72239 | 00e12e8b | 1 | 8.56585 |
| 2 | gr_typewell_light_alpha030_relaxed_v1_submission | gr_typewell_light | SPARSE_INFORMATION | 2 | 0.574871 | 1.0486 | 00e12e8b | 0.528577 | 1.38284 |
| 3 | gr_typewell_light_alpha040_v1_submission | gr_typewell_light | SPARSE_INFORMATION | 2 | 0.574871 | 1.39813 | 00e12e8b | 0.528577 | 1.84379 |
| 4 | rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission | projection_branch | BROAD | 3 | 1 | 1.45864 | 00bbac68 | 0.338564 | 1.3019 |
| 5 | sp45_projection_slot1_codex_v1_fleongg_pretrained_submission | projection_branch | BROAD | 3 | 1 | 3.96196 | 00bbac68 | 0.442046 | 4.04069 |

## Top Impacted Wells

| planned_slot | candidate_id | well | contribution_frac | rmse_diff | changed_frac | p95_abs_diff | max_abs_diff | mean_signed_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plateau_recent_quantile_v1_submission | 00e12e8b | 1 | 8.56585 | 1 | 15.5186 | 15.9286 | -3.33841 |
| 1 | plateau_recent_quantile_v1_submission | 000d7d20 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | plateau_recent_quantile_v1_submission | 00bbac68 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | gr_typewell_light_alpha030_relaxed_v1_submission | 00e12e8b | 0.528577 | 1.38284 | 0.999767 | 1.49989 | 1.49993 | 1.34983 |
| 2 | gr_typewell_light_alpha030_relaxed_v1_submission | 000d7d20 | 0.471423 | 1.38283 | 0.999739 | 1.49989 | 1.49993 | 1.34981 |
| 2 | gr_typewell_light_alpha030_relaxed_v1_submission | 00bbac68 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | gr_typewell_light_alpha040_v1_submission | 00e12e8b | 0.528577 | 1.84379 | 0.999767 | 1.99985 | 1.99991 | 1.79978 |
| 3 | gr_typewell_light_alpha040_v1_submission | 000d7d20 | 0.471423 | 1.84378 | 0.999739 | 1.99985 | 1.99991 | 1.79975 |
| 3 | gr_typewell_light_alpha040_v1_submission | 00bbac68 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission | 00bbac68 | 0.338564 | 1.3019 | 1 | 2.59667 | 4.76804 | 0.323119 |
| 4 | rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission | 000d7d20 | 0.33566 | 1.62312 | 1 | 3.29489 | 7.81309 | 0.6049 |
| 4 | rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission | 00e12e8b | 0.325775 | 1.51013 | 1 | 3.06144 | 4.0465 | -0.507775 |
| 5 | sp45_projection_slot1_codex_v1_fleongg_pretrained_submission | 00bbac68 | 0.442046 | 4.04069 | 1 | 9.62939 | 10.4731 | 1.30514 |
| 5 | sp45_projection_slot1_codex_v1_fleongg_pretrained_submission | 00e12e8b | 0.437509 | 4.75348 | 1 | 9.07289 | 10.9255 | 1.27225 |
| 5 | sp45_projection_slot1_codex_v1_fleongg_pretrained_submission | 000d7d20 | 0.120445 | 2.64094 | 1 | 5.2926 | 6.96841 | 1.79523 |

## Interpretation

- `SINGLE_WELL_DOMINATED` or `SPARSE_INFORMATION` candidates can still be useful information slots, but they should not be treated as broad model improvements without stronger evidence.
- `CONCENTRATED` candidates need per-well review before release because leaderboard movement may depend on a small number of wells.
- `BROAD` candidates change many wells and should be checked for hidden-format and physical-shape risk before any official submission.

## Outputs

- `experiments/planned_candidate_well_impact.csv`
- `experiments/planned_candidate_well_impact_summary.csv`
- `reports/planned_candidate_well_impact_report.md`
