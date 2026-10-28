# Poll And Refresh Report

This report summarizes the latest safe polling pass. It does not submit to Kaggle.

## Summary

| metric | value |
| --- | --- |
| kernel_updates_detected | 0 |
| kernel_errors | 0 |
| kernel_apply | False |
| submission_updates_detected | 0 |
| submission_appended_detected | 0 |
| submission_missing_not_appended | 0 |
| submission_dry_run | False |
| pending_official_submissions | 0 |
| running_kernels | 0 |
| readiness_status_counts | READY_AFTER_AUDIT_REVIEW=26; HOLD_DUPLICATE=11; HOLD_PENDING_ANCHOR=5; HOLD_LOW_UPSIDE=2; HOLD_INFORMATION_SLOT=1 |
| audit_gate_counts | AUDIT_PASS_WARN_REVIEW=42; AUDIT_PASS=3 |
| submission_gate_counts | READY_REVIEW_WARNINGS=26; HOLD_DUPLICATE=11; HOLD_PENDING_ANCHOR=5; HOLD_LOW_UPSIDE=2; HOLD_INFORMATION_SLOT=1 |
| batch_status | NEEDS_NEW_ARCHITECTURE_CANDIDATES |
| planned_slots | 5 |
| current_action_counts | build_new_architecture_first=5 |
| well_impact_bucket_counts | SPARSE_INFORMATION=2; BROAD=2; SINGLE_WELL_DOMINATED=1 |
| diversity_flag_counts | OK=3; REDUNDANT_REVIEW=2 |
| slot_review_counts | BUILD_NEW_ARCHITECTURE_FIRST=5 |
| slot_evidence_review_counts | REVIEW_REDUNDANT=2; KEEP_FOR_FINAL_REVIEW=2; SPARSE_INFO_SLOT_REVIEW=1 |
| slot_contingency_action_counts | WAIT_NO_SUBMIT=1; FINAL_REVIEW_BLEND_SWEEP=1; PARTIAL_RELEASE_NEEDS_REPLACEMENTS=1; BLOCK_ALL_DEPENDENT_SLOTS=1; INSERT_DEGNONGUIDI_AND_RERANK=1; FOLLOW_SCORE_BRANCH_WITHOUT_DEGNONGUIDI=1; KEEP_ONE_BLEND_FIND_REPLACEMENTS=1 |
| slot_contingency_new_candidate_needed_counts | 0=4; 2=2; 4=1 |
| replacement_pool_role_counts | manual_review=22; do_not_use_duplicate=11; pending_equivalent_not_replacement=5; already_planned=5; conservative_low_upside_backup=2 |
| replacement_queue_status_counts | ARTIFACT_AND_AUDIT_EXIST=2; ACTIVE=1; NO_CANDIDATE=1; TODO_BUILD=1; DESIGN_REQUIRED=1; WAIT_KERNEL=1 |
| replacement_queue_ready_now_counts | False=5; True=2 |
| artifact_manifest_gate_counts | PASS_SOURCE_POINTER=5 |
| release_gate_counts | BLOCKED_STRATEGY_PIVOT=5 |
| final_package_gate_counts | BLOCKED_RELEASE_GATE=5 |
| result_branch_rules | 7 |
| result_application_status_counts | ACTION_READY=3; PASS=1; WAIT=1 |
| planning_validation_status_counts | PASS=40 |
| planning_validation_error_failures | 0 |

## Interpretation

- If `kernel_updates_detected` or `submission_updates_detected` is nonzero while the corresponding apply flag is false, rerun with explicit apply after reviewing the dry-run output.
- If `batch_status` is `WAIT_EXTERNAL_CONTEXT`, keep preparing candidates but do not spend official submission slots.
- Before any official submission, rerun this script after applying external state changes so readiness, audit summary, and batch plan agree.

## Outputs Refreshed

- `reports/next_batch_readiness_report.md`
- `reports/candidate_audit_summary_report.md`
- `reports/next_submission_batch_plan.md`
- `reports/planned_candidate_well_impact_report.md`
- `reports/planned_candidate_diversity_report.md`
- `reports/planned_slot_review.md`
- `reports/planned_slot_contingency.md`
- `reports/replacement_candidate_queue.md`
- `reports/candidate_artifact_manifest_report.md`
- `reports/submission_release_gate_report.md`
- `reports/final_submission_package_report.md`
- `reports/planning_state_validation_report.md`
- `reports/result_branch_matrix.md`
- `reports/result_application_plan.md`
- `experiments/poll_refresh_summary.csv`
- `reports/poll_refresh_report.md`
