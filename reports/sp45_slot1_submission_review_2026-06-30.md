# SP45 Slot 1 Submission Review - 2026-06-30

## Decision

- Candidate: `sp45_projection_slot1_dynamic_rerun`
- Kernel: `joezzzzz/rogii-sp45-projection-slot1-codex`
- Kernel version: `1`
- Official submission: `54198676`
- Status at recording time: `PENDING`
- Message: `Codex SP45 projection slot1 dynamic audit pass`

## Why This Slot First

The active-account baseline reproduction scored `7.182`, the standalone Fleongg branch scored `7.787`, and Degnonguidi ended with `ERROR`. Under the staged plan, the first new official slot should test the broad SP45 projection before spending redundant blend-sweep slots.

## Output Review

The final Kaggle output was downloaded to:

```text
artifacts/sp45_projection_slot1_codex_v1/
```

The submitted `submission.csv` equals the kernel's dynamic `sp45_projection_submission.csv`.

| field | value |
| --- | --- |
| rows | `14151` |
| columns | `id,tvt` |
| id order matches sample | `true` |
| sha256 | `6fecb86c8355fa3469215a424542eb1f2e0482e755a663c5686379a00e4e5e58` |
| risk status | `WARN` |
| audit status | `PASS` |

The warning is from missing optional historical local reference files in the audit registry. The available active references passed.

## Hash Difference

The earlier Baidalin preflight SP45 package had sha256:

```text
9143b80439517ef8f3ecc9aba1f16f65275cb06d3331ad97c9909598c2bf55eb
```

The dedicated slot-1 rerun produced:

```text
6fecb86c8355fa3469215a424542eb1f2e0482e755a663c5686379a00e4e5e58
```

The pulled source notebook code cells matched the original Baidalin preflight. The difference appears to come from notebook/runtime nondeterminism rather than the final override cell. Because the final output was still dynamic SP45 projection, passed format/source checks, and remained a broad non-duplicate candidate, it was submitted as an information slot with the distinct hash recorded.

## Distance Review

| comparison | rmse | mae | p95 abs diff | max abs diff |
| --- | ---: | ---: | ---: | ---: |
| dynamic slot1 vs baseline | `2.31466` | `1.60349` | `5.34586` | `8.75127` |
| planned SP45 vs baseline | `1.45864` | `1.08353` | `2.95415` | `7.81309` |
| dynamic slot1 vs planned SP45 | `1.47557` | `0.78250` | `4.03850` | `4.35885` |

## Next Rule

Poll `54198676` before spending additional slots.

- If SP45 is competitive with the `7.182` baseline, submit at most one SP45+Fleongg blend next to calibrate direction.
- If SP45 is weak, downweight the SP45/blend branch and use replacement candidates rather than spending multiple redundant blend submissions.
- Keep plateau as a later sparse information slot only after the SP45 result is known.

## Poll Log

- `2026-06-30 11:29:18 UTC`: `54198676` remained `PENDING`; no additional official slot was spent.
