# Fleongg Branch Calibration Audit - 2026-06-29

Candidate:

- `fleongg_pretrained_branch_calibration`

Kernel:

- `joezzzzz/rogii-fleongg-branch-calibration-codex`
- submitted version: `2`

Official submission:

- submission id: `54174876`
- status at recording time: `PENDING`
- message: `Codex fleongg pretrained branch calibration v2 audit pass`

## Why This Candidate

The daily plan targets 4-5 official submissions when enough audited, informative candidates exist. The GR/typewell alpha probes were format-safe but too close to the active baseline:

| candidate | RMSE delta vs baseline | decision |
| --- | ---: | --- |
| `gr_typewell_light_alpha010_v1` | `0.3495` | `HOLD_LOW_UPSIDE` |
| `gr_typewell_light_alpha020_v1` | `0.6991` | `HOLD_LOW_UPSIDE` |
| `fleongg_pretrained_branch` | `3.9211` | `SUBMIT_CANDIDATE` |

The fleongg branch gives a more useful learned-signal calibration point than another near-duplicate baseline tweak.

## Failed Direct Submit Attempt

Attempt:

```text
kaggle competitions submit -c rogii-wellbore-geology-prediction -k joezzzzz/rogii-lucifer-baseline-repro-codex -v 1 -f fleongg_pretrained_submission.csv
```

Result:

- Kaggle API returned `400`.

Interpretation:

- The safe route for this code competition is to create a kernel whose final output file is the desired `submission.csv`.

## Version 1 Branch Kernel

Outcome:

- kernel completed;
- final `submission.csv` still matched the baseline output;
- `fleongg_branch_submission_audit.json` was absent;
- rejected before official submission.

Decision:

- do not submit version 1.

## Version 2 Branch Kernel

Fix:

- corrected the notebook override cell so it executes after the baseline notebook summary;
- final `submission.csv` is rewritten from `fleongg_pretrained_submission.csv`;
- `fleongg_branch_submission_audit.json` is written.

Output directory:

```text
artifacts/fleongg_branch_calibration_joezzzzz_v2/
```

Format audit:

| field | value |
| --- | --- |
| status | `PASS` |
| rows | `14151` |
| columns | `id,tvt` |
| id order matches sample | `true` |
| sha256 | `2f8be645a7e59669871f19d74bb7805b144ac775b9811433dbcd427058d515a7` |
| tvt min | `11597.405124838058` |
| tvt max | `12239.880628416158` |
| tvt mean | `11904.918696229626` |
| tvt std | `277.74869508647424` |

Branch identity check:

| check | result |
| --- | --- |
| final `submission.csv` equals `fleongg_pretrained_submission.csv` | `true` |
| RMSE delta vs active baseline | `3.9210524667990643` |
| MAE delta vs active baseline | `2.836798817563971` |
| p95 abs delta vs active baseline | `9.25584185671778` |
| max abs delta vs active baseline | `11.200761502876048` |

Decision:

- `SUBMITTED_CALIBRATION`

Next:

- poll official submission `54174876`;
- compare against active-account baseline submission `54174151` when both scores appear;
- use the score gap to decide whether learned-signal branches should enter future ensembles or remain diagnostic only.
