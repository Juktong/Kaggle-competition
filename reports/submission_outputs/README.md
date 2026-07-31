# Archived submission outputs — provenance of each file

Retrieved 2026-07-29 23:47 UTC by `api.kernels_output(<slug>)` (Q46). Every file was verified against
`data/rogii/sample_submission.csv`: **14,151 rows, id set equal, id order equal, all values finite**.

`kernels_output` returns the kernel's **latest** output bundle, which is not necessarily the version that was
submitted. Each file below therefore carries the evidence that it is (or is not) the submitted artifact.

| file | ref | public | account | scriptVersionId | sha256 (12) | verified as the submitted artifact by |
|---|---|---|---|---|---|---|
| `54844628_submission.csv` | 54844628 | 7.891 | joezzzzz | 336599680 | `4b74b5dddadb` | pairwise RMSE 2.537 vs `54968060`, matching the "rmse 2.54" recorded in `54968060`'s description |
| `54896975_submission.csv` | 54896975 | 6.669 | leemarc223 | 337097140 | `b192d3f348ae` | its own description records "SHA b192d3" — exact prefix match |
| `54968060_submission.csv` | 54968060 | 6.643 | joezzzzz | 337787958 | `e955180038f0` | reference for the two RMSE checks above and below |
| `54990075_submission.csv` | 54990075 | 6.690 | joezzzzz | 337982098 | `98d157778772` | pairwise RMSE **1.640** vs `54968060`, exactly the figure in its own description |
| `55064411_submission.csv` | 55064411 | 6.695 | joezzzzz | 338650633 | `4eec813b1213` | pairwise RMSE **1.756** vs `54968060`, exactly the figure in its own description |

## Two files were deliberately NOT kept

`54922806` (6.563) and `54923144` (6.678) were retrieved and their outputs came back **byte-identical to
`54896975`'s** (`b192d3f348ae`). Three submissions that scored 6.563 / 6.669 / 6.678 cannot share one
prediction file, so at most one of the three retrieved copies is a submitted artifact — and the SHA match
identifies that one as `54896975`'s. Keeping files named `54922806_submission.csv` / `54923144_submission.csv`
would have planted a mislabelled artifact in the repo, so they were removed rather than archived.

**Consequence, and it is not cosmetic:** the submitted output of `54922806` — the score-first slot-1
candidate — is **not currently archived anywhere in this repo**, and the API's default retrieval does not
return it. See the owner actions in `reports/q46_submission_asset_inventory_2026-07-30.md`.

## Reproducing this archive

```
python3 - <<'PY'
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi(); api.authenticate()
api.kernels_output('joezzzzz/rogii-struct-field-blend-codex', path='<dir>')   # etc.
PY
```

`api.kernels_output` takes no version argument, so a specific `scriptVersionId` must be fetched from the
Kaggle UI (kernel → Version history → the version → Output).
