# Candidate Artifact Convention

Generated candidate files stay local under ignored `artifacts/`. The tracked repository records only the convention, reports, and lightweight CSV summaries.

## Standard Folder

Each future promoted candidate should use:

```text
artifacts/<candidate_id>/
├── candidate_manifest.json
├── submission.csv
├── deep_pre_submit_audit.json
├── candidate_audit.json
└── run_notes.md
```

Only `submission.csv` and `deep_pre_submit_audit.json` are required before official submission. `candidate_audit.json` and `run_notes.md` are optional but useful when the candidate was built by a local script.

Downloaded multi-output kernel folders may remain under `artifacts/kernel_outputs/`. When one file from such a folder becomes an official-submission candidate, create a manifest folder for the selected candidate and point `source_path` to the raw kernel output.

## Initialize A Candidate

Dry-run a manifest:

```bash
python3 scripts/init_candidate_artifact.py --candidate-id baidalin_sp45_projection_v1 --family projection_branch --source-path artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv --dry-run
```

Write the local manifest:

```bash
python3 scripts/init_candidate_artifact.py --candidate-id baidalin_sp45_projection_v1 --family projection_branch --source-path artifacts/kernel_outputs/rogii-baidalin-7-201-preflight-codex_v1/sp45_projection_submission.csv
```

Validate manifests for the current planned official-submission slots:

```bash
python3 scripts/candidate_artifact_manifest_summary.py
```

The routine polling command also refreshes this report:

```bash
python3 scripts/poll_and_refresh_state.py
```

Inspect final package readiness:

```bash
python3 scripts/final_submission_package.py
```

After release gates clear and the selected slot passes final review, prepare the local package:

```bash
python3 scripts/final_submission_package.py --prepare --planned-slot 1
```

This copies the exact selected source output into the ignored candidate artifact folder and reruns the deep pre-submit audit. It does not submit to Kaggle.

## Required Release Evidence

Before an official Kaggle submission:

1. `submission.csv` is the exact selected output.
2. Deep audit passes:

```bash
python3 scripts/pre_submit_audit.py artifacts/<candidate_id>/submission.csv --data-dir data/sample --reference-registry experiments/reference_submission_registry.csv --json-out artifacts/<candidate_id>/deep_pre_submit_audit.json
```

3. `experiments/candidate_audit_summary.csv` includes the candidate with a non-failing audit gate.
4. `python3 scripts/poll_and_refresh_state.py` has been rerun after the latest Kaggle status check.
5. `reports/candidate_artifact_manifest_report.md` has no `FAIL_*` manifest gate for the selected slot.
6. `reports/submission_release_gate_report.md` has no `BLOCKED_*` or `REVIEW_LEDGER_UPDATES` result for the selected slot.
7. `reports/final_submission_package_report.md` shows the selected slot can be packaged, or has been prepared after final review.
8. `reports/planning_state_validation_report.md` reports zero error failures.
9. `experiments/submission_ledger.csv` is updated after the official submission.

## Current Decision

This convention avoids committing generated submissions while making every candidate traceable from question, to output, to audit, to release gate. It also gives future batches one standard place to look before spending any of the daily official submission slots.
