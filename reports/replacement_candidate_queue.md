# Replacement Candidate Queue

This report turns planned-slot contingency needs into concrete candidate build, audit, and design tasks. It does not submit to Kaggle.

## Status Counts

| status | count |
| --- | --- |
| ARTIFACT_AND_AUDIT_EXIST | 2 |
| ACTIVE | 1 |
| NO_CANDIDATE | 1 |
| TODO_BUILD | 1 |
| DESIGN_REQUIRED | 1 |
| WAIT_KERNEL | 1 |

## Task Type Counts

| task_type | count |
| --- | --- |
| build_new_candidate | 3 |
| process_gate | 1 |
| existing_candidate_review | 1 |
| design_new_candidate | 1 |
| kernel_output_audit | 1 |

## Queue

| task_id | priority | task_type | status | source_question_id | trigger_scenario | family | target_artifact | decision_gate | expected_value | risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RCQ01_replacement_need_guard | 110 | process_gate | ACTIVE | Q20260629-40 | S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved | planning |  | Need at least two non-duplicate replacement candidates before using 4-5 slots if the blend sweep is weak or unjustified. | Prevents the daily submission target from forcing duplicate blend submissions. | none |
| RCQ02_dedupe_backup_sp45_projection | 100 | existing_candidate_review | NO_CANDIDATE | Q20260629-B02, Q20260629-B06, Q20260629-B12, Q20260629-B13 | S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved | projection_branch |  | Promote at most one representative if audit passes and it is not a duplicate of an already planned SP45 output. | Uses existing audited projection signal without adding another nearby blend weight. | unknown_possible_but_risky; backup projection paths appear duplicate with each other |
| RCQ03_build_gr_typewell_alpha040 | 92 | build_new_candidate | ARTIFACT_AND_AUDIT_EXIST | Q20260629-B02, Q20260629-B06, Q20260629-B12, Q20260629-B13 | S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved | gr_typewell_light | artifacts/gr_typewell_light_alpha040_v1/submission.csv | Keep only if audit passes and distance from baseline is high enough to add information without high shape risk. | Tests whether a stronger GR/typewell correction can escape low-upside alpha 0.10/0.20 behavior. | may still be low-upside or overcorrect a small visible sample |
| RCQ04_build_gr_typewell_relaxed_alpha030 | 84 | build_new_candidate | ARTIFACT_AND_AUDIT_EXIST | Q20260629-B02, Q20260629-B06, Q20260629-B12, Q20260629-B13 | S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved | gr_typewell_light | artifacts/gr_typewell_light_alpha030_relaxed_v1/submission.csv | Use only if it changes more than alpha 0.20 while retaining clean anchor/jump/typewell audit metrics. | Tests a slightly broader GR gate without committing to a full GR path-search rewrite. | relaxed gate can introduce visible-sample overfit |
| RCQ05_build_plateau_nondefault_variant | 72 | build_new_candidate | TODO_BUILD | Q20260629-B12 | S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved | plateau_signal | artifacts/plateau_recent_quantile_w512_q0p65_m8p0_b1p0_v1/submission.csv | Use only as sparse information unless a broader validation source appears. | Adds a second plateau diagnostic from the best non-default stability-sweep combo. | high fallback/sparse well coverage; not a broad model promotion |
| RCQ06_design_sp45_plateau_gate | 64 | design_new_candidate | DESIGN_REQUIRED | Q20260629-B03 | S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved | ensemble_gating |  | Implement only if per-well impact shows the plateau change is localized and SP45 projection remains broad. | Could replace redundant blend slots with a per-well route rather than another global weight. | needs a new builder and may overfit the three visible wells |
| RCQ07_audit_degnonguidi_if_complete | 60 | kernel_output_audit | WAIT_KERNEL | Q20260629-B07 | S05_degnonguidi_complete_clean | reference_reproduction |  | If COMPLETE and audit passes, insert ahead of sparse or redundant planned slots. | Could add the strongest independent 7.159-family reference if the patched kernel succeeds. | kernel still running and may fail another object-contract issue |

## Commands

| task_id | build_command | audit_command |
| --- | --- | --- |
| RCQ01_replacement_need_guard |  |  |
| RCQ02_dedupe_backup_sp45_projection |  |  |
| RCQ03_build_gr_typewell_alpha040 | python3 scripts/build_gr_typewell_light_candidate.py --baseline artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv --data-dir data/sample --output-dir artifacts/gr_typewell_light_alpha040_v1 --alpha 0.40 --max-move 12.0 | python3 scripts/pre_submit_audit.py artifacts/gr_typewell_light_alpha040_v1/submission.csv --data-dir data/sample --reference-registry experiments/reference_submission_registry.csv --json-out artifacts/gr_typewell_light_alpha040_v1/local_pre_submit_audit.json |
| RCQ04_build_gr_typewell_relaxed_alpha030 | python3 scripts/build_gr_typewell_light_candidate.py --baseline artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv --data-dir data/sample --output-dir artifacts/gr_typewell_light_alpha030_relaxed_v1 --alpha 0.30 --max-move 10.0 --min-eval-improvement 0.02 | python3 scripts/pre_submit_audit.py artifacts/gr_typewell_light_alpha030_relaxed_v1/submission.csv --data-dir data/sample --reference-registry experiments/reference_submission_registry.csv --json-out artifacts/gr_typewell_light_alpha030_relaxed_v1/local_pre_submit_audit.json |
| RCQ05_build_plateau_nondefault_variant | python3 scripts/build_plateau_recent_quantile_candidate.py --baseline artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv --data-dir data/sample --output-dir artifacts/plateau_recent_quantile_w512_q0p65_m8p0_b1p0_v1 --window 512 --quantile 0.65 --min-move 8 --blend 1 | python3 scripts/pre_submit_audit.py artifacts/plateau_recent_quantile_w512_q0p65_m8p0_b1p0_v1/submission.csv --data-dir data/sample --reference-registry experiments/reference_submission_registry.csv --json-out artifacts/plateau_recent_quantile_w512_q0p65_m8p0_b1p0_v1/local_pre_submit_audit.json |
| RCQ06_design_sp45_plateau_gate |  |  |
| RCQ07_audit_degnonguidi_if_complete |  | python3 scripts/audit_kernel_output.py --kernel joezzzzz/rogii-degnonguidi-7159-preflight-codex --output-dir artifacts/kernel_outputs/rogii-degnonguidi-7159-preflight-codex_v6 --kaggle-bin /home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle --force-download |

## Interpretation

- Build or audit replacement candidates only while official slots remain blocked by external context.
- A replacement candidate is not submission-ready until it appears in candidate audit/readiness reports and passes release gates.
- Existing backup SP45 projections should be deduped before promotion; do not spend multiple slots on the same hash.
- GR/typewell and plateau tasks are replacement sources, not permission to submit before pending public scores resolve.

## Outputs

- `experiments/replacement_candidate_queue.csv`
- `reports/replacement_candidate_queue.md`
