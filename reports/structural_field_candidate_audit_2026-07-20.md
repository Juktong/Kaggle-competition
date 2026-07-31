# ROGII — structural-field candidate pre-submit audit (A5, 2026-07-20)

Candidate: `kaggle_kernel_struct_field_blend/rogii-struct-field-blend-codex.ipynb` v1, kernel
`joezzzzz/rogii-struct-field-blend-codex`, source commit `d972986`. Baseline: the submitted honest slot
**54804893** (DWT+PF blend, public 8.080). Neutral technical language.

## 1. Smoke (A4) — Kaggle interactive run, status COMPLETE, 0 errors
Log evidence (verbatim):
```
[struct] train reference pool: 773 wells in 54 typewell groups
[struct] per-well: 000d7d20:nb=13,closest=0ft,ok(dropped=1) | 00bbac68:nb=40,closest=0ft,ok(dropped=1)
                 | 00e12e8b:nb=13,closest=0ft,ok(dropped=1)
[struct] applied W=0.15 to 14151/14151 rows (100.0%); mean|diff|=1.119ft max|diff|=4.051ft;
         mean|struct-base|=7.46ft
[PF-blend] PF rows=14151 finite=True range=[11598.6,12241.2]
[PF-blend] coverage 14151/14151 rows blended (W=0.5)
```
`dropped=1` on every well is the **duplicate guard removing that well's exact self-twin (separation 0.0 ft)**
from the reference pool — the duplicate-reconstruction path is blocked in the live inference run, not just in
the local test. 13/40/13 genuine offset mates survive.

## 2. Format audit — ALL PASS
| check | result |
|---|---|
| row count == sample_submission | PASS (14,151 vs 14,151) |
| columns == [id, tvt] | PASS |
| id ORDER identical to sample | PASS |
| id SET identical to sample | PASS |
| duplicate ids | PASS (0) |
| all finite (no NaN/inf) | PASS (NaN = 0) |
| TVT range sane | PASS [11595.0, 12240.8] |
| mean / std | 11904.25 / 278.39 |
| sha256 (first 16) | `4b74b5dddadb9be3` |

## 3. Diff vs the submitted base 54804893 — explainable
| scope | rows changed | mean abs diff | max abs diff |
|---|---|---|---|
| all | 14,151 / 14,151 (100 %) | **0.928 ft** | 4.064 ft |
| 000d7d20 | 3,836 | 0.567 | 1.345 |
| 00bbac68 | 6,014 | 1.348 | 4.064 |
| 00e12e8b | 4,301 | 0.661 | 1.553 |

All three visible wells pass the gate (nb = 13/40/13 ≥ 4; closest < 1000 ft), so 100 % of rows are adjusted.
The magnitude is exactly what the fixed weight implies: `W × mean|struct − base| = 0.15 × 7.46 ≈ 1.1 ft`.

## 4. Leakage audit — no new leakage vs the already-submitted base
- **The structural cell reads only**: target `TVT_input, X, Y, Z` (all test-available) and train mates'
  `TVT, X, Y, Z` (ordinary supervised use of training labels). Verified by AST/string extraction of the cell.
- Term-by-term comparison against the submitted 54804893 notebook:
  | term | 54804893 (submitted) | candidate | verdict |
  |---|---|---|---|
  | ANCC / ASTNU / BUDA / EGFDU | cell 7 | cell 7 (identical) | inherited DWT base, unchanged |
  | tvt_from_contacts | cell 25 (comment only: "NO tvt_from_contacts leakage") | same | comment, not a call |
  | Geology | — | cell 27 **comment only** ("No structural surfaces, no Geology…") | comment, not a usage |
- **The candidate introduces no new leakage term as an actual usage.** Its honest status is identical to the
  base plus a cell that is independently clean.
- `min_sep = 150 ft` duplicate guard is applied **in inference**, evidenced by `dropped=1` per well above.
- No hidden truth, no private labels, no external data.

## 5. Honest-gate evidence (A1/A2)
- Nested train OOF (760 wells / 3.72 M rows): **9.2987 → 8.8626, gain +0.4361**.
- Bootstrap over 200 well-resamples at W = 0.15: mean +0.4335, **5th pct +0.2356, 100 % positive**.
- Stress: gates remove the harmful regimes (≤3 mates, closest > 1000 ft); worst per-well regression improves
  **+11.44 → +3.66 ft**; ungated / no-neighbour wells keep the DWT+PF prediction exactly.
- Diagnostic on the 3 visible wells (train duplicates, so indicative only): pooled base 3.941 →
  candidate **3.677**, same direction as the OOF gain.

**Audit result: PASS on every gate → submission authorized.**
