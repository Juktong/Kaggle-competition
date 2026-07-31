# SP45 Fleongg W060 Slot 2 Preflight - 2026-06-30

## Decision

- Candidate: `sp45_fleongg_w060_slot2_conditional`
- Kernel slug prepared: `joezzzzz/rogii-sp45-fleongg-w060-slot2-codex`
- Local working folder: `working/kaggle_kernel_sp45_fleongg_w060_slot2_joezzzzz/`
- Planned role: one conditional blend calibration slot after SP45 slot 1 scores
- Current action: hold; do not push, run, or submit until `54198676` has a public score

## Why This Candidate

The first 2026-06-30 official slot is the broad SP45 projection information test. The next best dependent question is whether a low-dimensional SP45 plus Fleongg blend can recover useful signal if SP45 itself is competitive with the `7.182` active-account baseline.

Among the prepared blend sweep, `w0.60` is the preferred first calibration point because standalone Fleongg scored worse (`7.787`) while SP45 is the current unknown. A heavier SP45 weight is therefore the safer first blend than lower SP45 weights.

## Local Preflight Evidence

| check | value |
| --- | --- |
| source audit status | `PASS` |
| source audit code cells | `40` |
| source audit failures | `0` |
| source audit warnings | `0` |
| dynamic horizontal well discovery signal | `true` |
| sample submission signal | `true` |
| submission write signal | `true` |
| test split reference signal | `true` |
| final CSV audit status | `PASS` |
| final CSV risk status | `WARN` |
| rows | `14151` |
| columns | `id,tvt` |
| id order matches sample | `true` |
| submission sha256 | `3e9f4c8e81ffb241acb7ebe3c1b71563510bc3915f73a0a19a69dad1955b0cfa` |
| notebook sha256 | `f8f2c17f00431924b6055aab5781b3b6e859d585e932e4d6bd67005410810d6c` |
| metadata sha256 | `4412c488ce69d5cf5c8e5b20f3d27fe8b4d319ff6a77158f38419fa2b1264a63` |

The `WARN` state is from missing optional historical local reference files. Available active-account references passed.

## Distance Review

| comparison | rmse | mae | p95 abs diff | max abs diff |
| --- | ---: | ---: | ---: | ---: |
| w0.60 vs active-account baseline | `2.15794` | `1.61377` | `4.63309` | `5.83684` |
| w0.60 vs Fleongg standalone output | `2.09107` | `1.54904` | `4.56644` | `6.03164` |

## Release Rule

- If SP45 slot 1 is competitive with the `7.182` baseline, push/run this kernel as the next calibration candidate, download output, rerun output audit, then submit only if the dynamic Kaggle output still passes.
- If SP45 slot 1 is weak, do not submit this dependent blend next. Downweight the SP45/blend branch and promote a replacement candidate instead.
- If SP45 slot 1 is blank or anomalous, inspect the slot 1 kernel/output mismatch before pushing this slot 2 notebook.

## Not Submitted

No Kaggle kernel push, kernel run, or official submission has been made for this slot 2 candidate as of this preflight record.
