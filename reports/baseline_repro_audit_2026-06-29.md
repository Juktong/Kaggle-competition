# Baseline Reproduction Audit - 2026-06-29

Candidate:

- `lucifer_baseline_repro_joezzzzz`

Kernel:

- `joezzzzz/rogii-lucifer-baseline-repro-codex`
- version: `1`
- Kaggle worker status: `COMPLETE`

Official submission:

- submission id: `54174151`
- status at recording time: `PENDING`
- message: `Codex active-account 7.235 baseline reproduction audit pass`

## Output Download

Downloaded to ignored local artifact folder:

```text
artifacts/lucifer_baseline_repro_joezzzzz_v1/
```

Important files:

- `submission.csv`
- `submission_audit.json`
- `gold_prefix_submission_audit.json`
- `run_summary.json`
- `rogii-lucifer-baseline-repro-codex.log`

## Format Audit

Local command:

```text
python3 scripts/pre_submit_audit.py artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv --sample data/sample/sample_submission.csv --json-out artifacts/lucifer_baseline_repro_joezzzzz_v1/local_pre_submit_audit.json
```

Result:

| field | value |
| --- | --- |
| status | `PASS` |
| rows | `14151` |
| columns | `id,tvt` |
| sample rows | `14151` |
| id order matches sample | `true` |
| duplicate ids | `0` |
| tvt min | `11587.038593358397` |
| tvt max | `12240.016065617148` |
| tvt mean | `11903.630072938824` |
| tvt std | `278.02477266709434` |
| sha256 | `fdf4a8175b6ec6a70c9b78fd6916ac3c317e43f7e9c08bbca87cd02314801ca9` |

Notebook `submission_audit.json` reports the same sha256 and sample ID-order match.

## Hidden-Compatibility Source Review

Source review outcome: `PASS`.

Local command:

```text
python3 scripts/notebook_source_audit.py working/kaggle_kernel_lucifer_baseline_joezzzzz/wellbore-wizard-physics-pf-stack.ipynb --json-out artifacts/lucifer_baseline_repro_joezzzzz_v1/source_audit.json
```

Result:

| field | value |
| --- | --- |
| status | `PASS` |
| code cells | `19` |
| failures | `0` |
| warnings | `0` |
| sample_submission signal | `true` |
| dynamic horizontal well discovery | `true` |
| test split reference | `true` |
| submission write | `true` |

Reasons:

- data path resolution searches standard Kaggle competition mounts and verifies `train/`, `test/`, and `sample_submission.csv`;
- test wells are discovered dynamically from `test/*__horizontal_well.csv`;
- IDs are generated from `sample_submission.csv` and parsed with `rsplit("_", 1)`;
- output is reindexed to the sample order before writing `submission.csv`;
- strict audit checks exact columns, row count, ID order, duplicate IDs, and finite predictions;
- no static visible-test `submission.csv` replay was used.

Known caveat:

- current visible example has 3 wells and 14,151 rows, so the output row count alone is not evidence of hidden compatibility. The source scan is the stronger evidence.

## Decision

Decision: `SUBMITTED_CALIBRATION`.

Why:

- the output passed format audit;
- the source is designed for hidden rerun rather than static replay;
- the submission answers Q20260629-B01 by calibrating an active-account reproduction of the current `7.235` project baseline.

Next:

- poll submission `54174151`;
- if the public score reproduces the expected baseline region, close Q20260629-B01 and use this output as the active-account comparison anchor;
- if score is blank or poor, inspect Kaggle logs/output mismatch before submitting further baseline-adjacent candidates.
