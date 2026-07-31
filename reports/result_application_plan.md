# Result Application Plan

This report turns current external-result state into concrete next actions. It does not edit ledgers or submit to Kaggle.

## Overall

- Status: `ACTION_READY`
- Reason: Branch actions can proceed according to the plan.

## Status Counts

| status | count |
| --- | --- |
| ACTION_READY | 3 |
| PASS | 1 |
| WAIT | 1 |

## Action Plan

| area | branch_id | status | blocks_release | action | evidence | next_command |
| --- | --- | --- | --- | --- | --- | --- |
| ledger_updates | NO_UNAPPLIED_UPDATES | PASS | False | No dry-run ledger updates were detected in the latest poll. | submission_updates=0; kernel_updates=0 | python3 scripts/poll_and_refresh_state.py |
| baseline_anchor | B01_baseline_anchor_valid | ACTION_READY | False | Promote the active-account baseline anchor and allow dependent candidate review. | status=complete; public_score=7.182 | python3 scripts/poll_and_refresh_state.py --apply-submission-updates |
| fleongg_calibration | B04_fleongg_weak | ACTION_READY | False | Downweight Fleongg blend slots and rerank toward SP45/plateau alternatives. | baseline=7.182; fleongg=7.787; margin=0.10 | rerun next_submission_batch_plan after marking Fleongg as weak calibration |
| degnonguidi_reference | B06_degnonguidi_error_or_defer | ACTION_READY | False | Record Degnonguidi terminal status or deferral, then rerun plan without waiting on it. | status=ERROR; version=6 | update kernel ledger, record deferral reason, rerun poll_and_refresh_state.py |
| release_sequence | RELEASE_BLOCKED | WAIT | True | Do not prepare or submit official slots until external blockers and validation errors clear. | pending=0; running=0; release_gates=['BLOCKED_STRATEGY_PIVOT']; validation_errors=0 | python3 scripts/poll_and_refresh_state.py |

## Outputs

- `experiments/result_application_plan.csv`
- `reports/result_application_plan.md`
