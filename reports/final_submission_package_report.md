# Final Submission Package Report

This report inspects local final-submission package readiness. It never submits to Kaggle.

## Package Gate Counts

| package_gate | count |
| --- | --- |
| BLOCKED_RELEASE_GATE | 5 |

## Planned Slot Package State

| planned_slot | candidate_id | family | release_gate | manifest_gate | package_gate | package_submission_exists | source_path | package_submission_path | package_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plateau_recent_quantile_v1_submission | plateau_signal | BLOCKED_STRATEGY_PIVOT | PASS_SOURCE_POINTER | BLOCKED_RELEASE_GATE | False | artifacts/plateau_recent_quantile_v1/submission.csv | artifacts/plateau_recent_quantile_v1_submission/submission.csv | Release gate is BLOCKED_STRATEGY_PIVOT. |
| 2 | gr_typewell_light_alpha030_relaxed_v1_submission | gr_typewell_light | BLOCKED_STRATEGY_PIVOT | PASS_SOURCE_POINTER | BLOCKED_RELEASE_GATE | False | artifacts/gr_typewell_light_alpha030_relaxed_v1/submission.csv | artifacts/gr_typewell_light_alpha030_relaxed_v1_submission/submission.csv | Release gate is BLOCKED_STRATEGY_PIVOT. |
| 3 | gr_typewell_light_alpha040_v1_submission | gr_typewell_light | BLOCKED_STRATEGY_PIVOT | PASS_SOURCE_POINTER | BLOCKED_RELEASE_GATE | False | artifacts/gr_typewell_light_alpha040_v1/submission.csv | artifacts/gr_typewell_light_alpha040_v1_submission/submission.csv | Release gate is BLOCKED_STRATEGY_PIVOT. |
| 4 | rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission | projection_branch | BLOCKED_STRATEGY_PIVOT | PASS_SOURCE_POINTER | BLOCKED_RELEASE_GATE | True | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv | artifacts/rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission/submission.csv | Release gate is BLOCKED_STRATEGY_PIVOT. |
| 5 | sp45_projection_slot1_codex_v1_fleongg_pretrained_submission | projection_branch | BLOCKED_STRATEGY_PIVOT | PASS_SOURCE_POINTER | BLOCKED_RELEASE_GATE | False | artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv | artifacts/sp45_projection_slot1_codex_v1_fleongg_pretrained_submission/submission.csv | Release gate is BLOCKED_STRATEGY_PIVOT. |

## Outputs

- `experiments/final_submission_package_summary.csv`
- `reports/final_submission_package_report.md`
