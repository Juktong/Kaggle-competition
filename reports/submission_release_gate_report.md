# Submission Release Gate

This report checks whether the planned official submission slots may be released. It does not submit anything.

## Overall Gate

- Status: `BLOCKED_STRATEGY_PIVOT`
- Reason: Official calibration rejected the planned branch family; build new structural candidates before submitting.

## Gate Counts

| release_gate | count |
| --- | --- |
| BLOCKED_STRATEGY_PIVOT | 5 |

## Planned Slot Gates

| planned_slot | slot_role | family | release_gate | current_action | priority_score | path | release_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | flexible_information_slot | plateau_signal | BLOCKED_STRATEGY_PIVOT | build_new_architecture_first | 65 | artifacts/plateau_recent_quantile_v1/submission.csv | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. |
| 2 | low_upside_backup | gr_typewell_light | BLOCKED_STRATEGY_PIVOT | build_new_architecture_first | -25 | artifacts/gr_typewell_light_alpha030_relaxed_v1/submission.csv | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. |
| 3 | low_upside_backup | gr_typewell_light | BLOCKED_STRATEGY_PIVOT | build_new_architecture_first | -25 | artifacts/gr_typewell_light_alpha040_v1/submission.csv | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. |
| 4 | structural_candidate | projection_branch | BLOCKED_STRATEGY_PIVOT | build_new_architecture_first | -26 | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. |
| 5 | backup_structural_comparison | projection_branch | BLOCKED_STRATEGY_PIVOT | build_new_architecture_first | -28 | artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. |

## Outputs

- `experiments/submission_release_gate.csv`
- `reports/submission_release_gate_report.md`
