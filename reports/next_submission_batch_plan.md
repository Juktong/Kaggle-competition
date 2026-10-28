# Next Submission Batch Plan

This is a conditional 4-5 slot plan built from audited candidates. It does not submit anything.

## Current Status

- Batch status: `NEEDS_NEW_ARCHITECTURE_CANDIDATES`
- Pending official submissions: `0`
- Running kernels: `0`
- Eligible audited candidates: `17`
- Planned slots: `5`
- Pending IDs: ``
- Running kernels: ``
- Baseline/Fleongg/SP45 official scores: `7.182` / `7.787` / `7.753`
- Weak-branch flags: Fleongg `True`, SP45 `True`

## Planned Slots

| planned_slot | slot_role | family | batch_status | current_action | priority_score | estimated_public_band | novelty_bucket | rmse_to_current_best_7p235 | path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | flexible_information_slot | plateau_signal | NEEDS_NEW_ARCHITECTURE_CANDIDATES | build_new_architecture_first | 65 | unknown_possible_but_risky | high | 4.72239 | artifacts/plateau_recent_quantile_v1/submission.csv |
| 2 | low_upside_backup | gr_typewell_light | NEEDS_NEW_ARCHITECTURE_CANDIDATES | build_new_architecture_first | -25 | plausible_7p2_to_7p8_band | moderate | 1.0486 | artifacts/gr_typewell_light_alpha030_relaxed_v1/submission.csv |
| 3 | low_upside_backup | gr_typewell_light | NEEDS_NEW_ARCHITECTURE_CANDIDATES | build_new_architecture_first | -25 | plausible_7p2_to_7p8_band | moderate | 1.39813 | artifacts/gr_typewell_light_alpha040_v1/submission.csv |
| 4 | structural_candidate | projection_branch | NEEDS_NEW_ARCHITECTURE_CANDIDATES | build_new_architecture_first | -26 | plausible_7p2_to_7p8_band | moderate | 1.45864 | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv |
| 5 | backup_structural_comparison | projection_branch | NEEDS_NEW_ARCHITECTURE_CANDIDATES | build_new_architecture_first | -28 | plausible_7p2_to_7p8_band | high | 3.96196 | artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv |

## Release Rules

| result | next_action |
| --- | --- |
| 54174151 baseline scores near expected reference | Use it as the active-account anchor and allow SP45 projection review. |
| 54174151 blank or catastrophic | Block dependent submissions; repair active-account baseline before spending more slots. |
| 54174876 Fleongg improves or ties baseline | Prioritize SP45+Fleongg blend sweep slots after final review. |
| 54174876 Fleongg worsens materially | Prefer pure SP45 projection or plateau information slot; downweight Fleongg blends. |
| Degnonguidi v6 completes and audits cleanly | Insert its best distinct output ahead of lower-priority blend or plateau slots. |

## Outputs

- `experiments/next_submission_batch_plan.csv`
- `reports/next_submission_batch_plan.md`
