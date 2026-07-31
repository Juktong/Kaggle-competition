# Planned Candidate Diversity

This report measures pairwise output diversity among planned submission slots. It is local validation only and does not submit to Kaggle.

## Redundancy Buckets

| redundancy_bucket | count |
| --- | --- |
| DIVERSE | 6 |
| DIRECTIONALLY_DIVERSE | 2 |
| HIGHLY_REDUNDANT | 1 |
| MODERATE_INCREMENT | 1 |

## Candidate Summary

| planned_slot | candidate_id | family | min_pair_rmse | max_diff_corr | redundant_pair_count | most_similar_slot | diversity_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plateau_recent_quantile_v1_submission | plateau_signal | 4.29244 | 0.612734 | 0 | 4 | OK |
| 2 | gr_typewell_light_alpha030_relaxed_v1_submission | gr_typewell_light | 0.349534 | 1 | 1 | 3 | REDUNDANT_REVIEW |
| 3 | gr_typewell_light_alpha040_v1_submission | gr_typewell_light | 0.349534 | 1 | 1 | 2 | REDUNDANT_REVIEW |
| 4 | rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission | projection_branch | 1.80381 | 0.501296 | 0 | 2 | OK |
| 5 | sp45_projection_slot1_codex_v1_fleongg_pretrained_submission | projection_branch | 3.46813 | 0.612734 | 0 | 4 | OK |

## Pairwise Distances

| left_slot | right_slot | left_family | right_family | pair_rmse | diff_corr_vs_baseline | same_direction_frac | redundancy_bucket |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4 | plateau_signal | projection_branch | 4.29244 | 0.470765 | 0.263939 | DIRECTIONALLY_DIVERSE |
| 1 | 5 | plateau_signal | projection_branch | 4.47304 | 0.612734 | 0.226768 | DIRECTIONALLY_DIVERSE |
| 2 | 4 | gr_typewell_light | projection_branch | 1.80381 | -0.124459 | 0.259416 | DIVERSE |
| 3 | 4 | gr_typewell_light | projection_branch | 2.02924 | -0.124459 | 0.259416 | DIVERSE |
| 3 | 5 | gr_typewell_light | projection_branch | 3.71008 | 0.134067 | 0.414882 | DIVERSE |
| 2 | 5 | gr_typewell_light | projection_branch | 3.72576 | 0.134067 | 0.414882 | DIVERSE |
| 1 | 2 | plateau_signal | gr_typewell_light | 5.0428 | -0.0698413 | 0.184612 | DIVERSE |
| 1 | 3 | plateau_signal | gr_typewell_light | 5.19244 | -0.0698413 | 0.184612 | DIVERSE |
| 2 | 3 | gr_typewell_light | gr_typewell_light | 0.349534 | 1 | 1 | HIGHLY_REDUNDANT |
| 4 | 5 | projection_branch | projection_branch | 3.46813 | 0.501296 | 0.659105 | MODERATE_INCREMENT |

## Interpretation

- `NEAR_DUPLICATE`, `HIGHLY_REDUNDANT`, and `RELATED_LOW_INCREMENT` pairs should not both be submitted unless they answer a deliberate calibration-sweep question.
- High correlation among blend weights is expected, but it reduces information value if daily slots are scarce.
- Diverse candidates can still be bad; this report only checks redundancy, not hidden-label accuracy.

## Outputs

- `experiments/planned_candidate_diversity.csv`
- `experiments/planned_candidate_diversity_summary.csv`
- `reports/planned_candidate_diversity_report.md`
