# Candidate Decision Report

This report converts local surrogate rows into a lightweight pre-submission decision table.

Decision meanings:

- `BLOCK`: do not submit without a specific override reason.
- `HOLD_DUPLICATE`: too close to the active baseline to spend a slot.
- `HOLD_LOW_UPSIDE`: likely safe but low information value.
- `SUBMIT_CANDIDATE`: eligible for official submission if source and format audits pass.
- `HOLD_NEEDS_REVIEW`: inspect manually before any official submission.

## Focus Candidates

| path | decision | risk_grade | estimated_public_band | rmse_to_current_best_7p235 | anchor_first_abs_p90 | jump_rate_abs_slope_gt3 | typewell_range_violation_frac |
| --- | --- | --- | --- | --- | --- | --- | --- |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv | HOLD_DUPLICATE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission_gold_prefix_aggressive.csv | HOLD_DUPLICATE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission_gold_prefix_balanced.csv | HOLD_DUPLICATE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission_gold_prefix_conservative.csv | HOLD_DUPLICATE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission_pre_gold.csv | HOLD_DUPLICATE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/submission_public_self_verified.csv | HOLD_DUPLICATE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/gr_typewell_light_alpha010_v1/submission.csv | HOLD_LOW_UPSIDE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0.349534 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/gr_typewell_light_alpha020_v1/submission.csv | HOLD_LOW_UPSIDE | near_duplicate_low_upside | likely_around_7p235_low_upside | 0.699067 | 0.0360878 | 7.06814e-05 | 0 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 1.45864 | 6.39778 | 0 | 0 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_sp45_fleongg_w0.60.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 2.15794 | 3.85775 | 0 | 0 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_sp45_fleongg_w0.58.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 2.20956 | 3.73075 | 0 | 0 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_sp45_fleongg_w0.55.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 2.28867 | 3.54025 | 0 | 0 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_sp45_fleongg_w0.52.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 2.36963 | 3.34974 | 0 | 0 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/submission_sp45_fleongg_w0.50.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 2.42452 | 3.22274 | 0 | 0 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/fleongg_pretrained_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 3.68124 | 0.125039 | 0 | 0 |
| artifacts/fleongg_branch_calibration_joezzzzz_v2/fleongg_pretrained_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 3.92105 | 0.124812 | 0 | 0 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/fleongg_pretrained_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 3.92669 | 0.123879 | 0 | 0 |
| artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/fleongg_pretrained_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | plausible_7p2_to_7p8_band | 3.93987 | 0.124027 | 0 | 0 |
| artifacts/plateau_recent_quantile_v1/submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | unknown_possible_but_risky | 4.72239 | 3.28521 | 7.06814e-05 | 0 |
| artifacts/fleongg_branch_calibration_joezzzzz_v1/sp45_projection_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | unknown_possible_but_risky | 5.79449 | 2.65079 | 0 | 0 |
| artifacts/fleongg_branch_calibration_joezzzzz_v2/sp45_projection_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | unknown_possible_but_risky | 5.79449 | 2.65079 | 0 | 0 |
| artifacts/lucifer_baseline_repro_joezzzzz_v1/sp45_projection_submission.csv | SUBMIT_CANDIDATE | plausible_submit_candidate | unknown_possible_but_risky | 5.79449 | 2.65079 | 0 | 0 |

## Recommendation

14 focused candidate(s) are eligible for official submission after audit review.
