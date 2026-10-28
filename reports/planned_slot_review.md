# Planned Slot Review

This report combines release gates, audit readiness, final-package state, per-well impact, and pairwise diversity into one slot-level review. It does not submit to Kaggle.

## Review Counts

| slot_review | count |
| --- | --- |
| BUILD_NEW_ARCHITECTURE_FIRST | 5 |

## Slot Review

| planned_slot | slot_role | family | slot_review | slot_action | evidence_review | evidence_action | release_gate | impact_bucket | diversity_flag | min_pair_rmse | top_well | slot_review_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | flexible_information_slot | plateau_signal | BUILD_NEW_ARCHITECTURE_FIRST | BLOCK | SPARSE_INFO_SLOT_REVIEW | REVIEW | BLOCKED_STRATEGY_PIVOT | SINGLE_WELL_DOMINATED | OK | 4.29244 | 00e12e8b | Official calibration rejected the planned branch family; build new structural candidates before submitting. |
| 2 | low_upside_backup | gr_typewell_light | BUILD_NEW_ARCHITECTURE_FIRST | BLOCK | REVIEW_REDUNDANT | REVIEW | BLOCKED_STRATEGY_PIVOT | SPARSE_INFORMATION | REDUNDANT_REVIEW | 0.349534 | 00e12e8b | Official calibration rejected the planned branch family; build new structural candidates before submitting. |
| 3 | low_upside_backup | gr_typewell_light | BUILD_NEW_ARCHITECTURE_FIRST | BLOCK | REVIEW_REDUNDANT | REVIEW | BLOCKED_STRATEGY_PIVOT | SPARSE_INFORMATION | REDUNDANT_REVIEW | 0.349534 | 00e12e8b | Official calibration rejected the planned branch family; build new structural candidates before submitting. |
| 4 | structural_candidate | projection_branch | BUILD_NEW_ARCHITECTURE_FIRST | BLOCK | KEEP_FOR_FINAL_REVIEW | KEEP | BLOCKED_STRATEGY_PIVOT | BROAD | OK | 1.80381 | 00bbac68 | Official calibration rejected the planned branch family; build new structural candidates before submitting. |
| 5 | backup_structural_comparison | projection_branch | BUILD_NEW_ARCHITECTURE_FIRST | BLOCK | KEEP_FOR_FINAL_REVIEW | KEEP | BLOCKED_STRATEGY_PIVOT | BROAD | OK | 3.46813 | 00bbac68 | Official calibration rejected the planned branch family; build new structural candidates before submitting. |

## Release Interpretation

- `HOLD_EXTERNAL_CONTEXT`: keep blocked until scores/kernel outcomes resolve.
- `BUILD_NEW_ARCHITECTURE_FIRST`: do not spend official slots on the current planned family; create new structural candidates first.
- `evidence_review` shows the latent quality/diversity decision even while the release gate is blocked.
- `KEEP_ONLY_IF_CALIBRATION_SWEEP`: the slot is redundant, but may be kept if the explicit experiment is to map a blend curve.
- `SPARSE_INFO_SLOT_REVIEW`: use only as an information slot, not as broad model promotion.
- `KEEP_FOR_FINAL_REVIEW`: candidate has enough non-redundant evidence for final review once gates clear.

## Outputs

- `experiments/planned_slot_review.csv`
- `reports/planned_slot_review.md`
