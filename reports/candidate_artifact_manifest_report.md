# Candidate Artifact Manifest Report

This report checks local ignored `candidate_manifest.json` files for the planned official-submission slots.

## Summary

| manifest_gate | count |
| --- | --- |
| PASS_SOURCE_POINTER | 5 |

## Planned Slot Manifests

| planned_slot | candidate_id | manifest_gate | manifest_found_by | source_path_exists | audit_json_exists | audit_gate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | plateau_recent_quantile_v1_submission | PASS_SOURCE_POINTER | candidate_id | True | True | AUDIT_PASS_WARN_REVIEW | planned_slot_5_conditional_batch |
| 2 | gr_typewell_light_alpha030_relaxed_v1_submission | PASS_SOURCE_POINTER | candidate_id | True | True | AUDIT_PASS_WARN_REVIEW | replacement placeholder after weak SP45/Fleongg calibration; low-upside backup only |
| 3 | gr_typewell_light_alpha040_v1_submission | PASS_SOURCE_POINTER | candidate_id | True | True | AUDIT_PASS_WARN_REVIEW | replacement placeholder after weak SP45/Fleongg calibration; low-upside backup only |
| 4 | rogii_baidalin_7_201_preflight_codex_v1_sp45_projection_submission | PASS_SOURCE_POINTER | candidate_id | True | True | AUDIT_PASS_WARN_REVIEW | planned_slot_1_conditional_batch |
| 5 | sp45_projection_slot1_codex_v1_fleongg_pretrained_submission | PASS_SOURCE_POINTER | candidate_id | True | True | AUDIT_PASS_WARN_REVIEW | tracked only for comparison after weak official calibration; not a preferred release candidate |

## Gate Meaning

- `PASS_SOURCE_POINTER`: the manifest exists, points to the exact planned output path, the selected output exists locally, and candidate audit evidence exists.
- `FAIL_*`: an official submission should not proceed until the missing or mismatched evidence is fixed.

## Outputs

- artifact root: `artifacts`
- `experiments/candidate_artifact_manifest_summary.csv`
- `reports/candidate_artifact_manifest_report.md`
