# Result Branch Matrix

This report maps pending public scores and reference-kernel outcomes to concrete next actions.

## Current Planned Slots

| planned_slot | slot_role | family | current_action | release_condition | path |
| --- | --- | --- | --- | --- | --- |
| 1 | flexible_information_slot | plateau_signal | build_new_architecture_first | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. | artifacts/plateau_recent_quantile_v1/submission.csv |
| 2 | low_upside_backup | gr_typewell_light | build_new_architecture_first | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. | artifacts/gr_typewell_light_alpha030_relaxed_v1/submission.csv |
| 3 | low_upside_backup | gr_typewell_light | build_new_architecture_first | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. | artifacts/gr_typewell_light_alpha040_v1/submission.csv |
| 4 | structural_candidate | projection_branch | build_new_architecture_first | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv |
| 5 | backup_structural_comparison | projection_branch | build_new_architecture_first | Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first. | artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv |

## Branch Rules

| branch_id | trigger | evidence_to_check | decision | slot_effect | candidate_effect | next_command |
| --- | --- | --- | --- | --- | --- | --- |
| B01_baseline_anchor_valid | 54174151 completes with plausible active-account baseline score | public_score present, nonblank, and close to expected 7.235/7.263 reference band; no scoring failure | promote_baseline_anchor | Allow SP45 projection final review; keep release gate blocked until Fleongg and Degnonguidi dependency rules are resolved. | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv; artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv | python3 scripts/poll_and_refresh_state.py --apply-submission-updates |
| B02_baseline_anchor_failed | 54174151 completes blank, catastrophic, or far outside expected baseline band | blank score, operational failure, or public_score much worse than trusted references | block_dependent_submissions | Do not release SP45, blend, or plateau slots; repair active-account baseline reproduction first. | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv; artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv; ; artifacts/plateau_recent_quantile_v1/submission.csv | record failure, patch baseline path, rerun source/output audit before any new official submission |
| B03_fleongg_competitive | 54174151 anchor is valid and 54174876 is competitive with baseline | Fleongg public_score is better than, tied with, or close enough to baseline to justify ensemble diversity | prioritize_blend_sweep | Keep SP45+Fleongg calibration sweep slots ; release only after final audit/release-gate review. |  | python3 scripts/poll_and_refresh_state.py --apply-submission-updates |
| B04_fleongg_weak | 54174151 anchor is valid and 54174876 is materially worse | Fleongg public_score is clearly worse than baseline or repeats known weak learned-signal behavior | downweight_blends | Prefer pure SP45 projection; keep at most one blend as an information slot, and only if a planned question remains. |  | rerun next_submission_batch_plan after marking Fleongg as weak calibration |
| B05_degnonguidi_complete_clean | Degnonguidi v6 reaches COMPLETE and output audit passes | kernel status COMPLETE; output downloaded; deep audit PASS; output is distinct from current plan | insert_degnonguidi_candidate | Insert best distinct Degnonguidi output ahead of lower-priority blend or plateau slot. | pending Degnonguidi output artifact | python3 scripts/audit_kernel_output.py --kernel joezzzzz/rogii-degnonguidi-7159-preflight-codex --output-dir artifacts/kernel_outputs/rogii-degnonguidi-7159-preflight-codex_v6 --kaggle-bin /home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle --force-download |
| B06_degnonguidi_error_or_defer | Degnonguidi v6 errors, stalls beyond useful window, or is explicitly deferred | kernel status ERROR/CANCELLED, repeated runtime incompatibility, or deliberate defer decision in log | release_without_degnonguidi_if_scores_allow | If baseline/Fleongg scores are resolved and release gate passes, allow Baidalin-derived slots to proceed without waiting for Degnonguidi. | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv; artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv | update kernel ledger, record deferral reason, rerun poll_and_refresh_state.py |
| B07_no_external_change | No new official score and no terminal kernel status | poll refresh reports submission_updates_detected=0 and kernel_updates_detected=0 | continue_preparation_no_submit | Keep all planned slots blocked; continue local validation, audit coverage, and planning consistency work. | artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv; artifacts/sp45_projection_slot1_codex_v1/fleongg_pretrained_submission.csv; ; artifacts/plateau_recent_quantile_v1/submission.csv | python3 scripts/poll_and_refresh_state.py |

## Outputs

- `experiments/result_branch_matrix.csv`
- `reports/result_branch_matrix.md`
