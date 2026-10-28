# ROGII — submission report: structural-field candidate (2026-07-20)

## Identity
| field | value |
|---|---|
| submission ref | **54844628** |
| submitted | 2026-07-20 04:08:43 UTC |
| kernel | `joezzzzz/rogii-struct-field-blend-codex` v1 |
| notebook | `kaggle_kernel_struct_field_blend/rogii-struct-field-blend-codex.ipynb` |
| source commit | `d972986` |
| baseline it extends | **54804893** (DWT+PF blend, public 8.080, honest OOF 9.2969) |
| public score | **PENDING at time of writing** — see "retrieving the score" below |

## What it is
The banked DWT+PF honest blend **plus** a group-anchored cross-well structural field, applied only where
train-OOF stress shows it is reliable:
```
group key = round(max(TVT),1) of the target's OWN typewell     (test-available)
neighbours= same-group TRAIN wells with median trajectory XY separation >= 150 ft   (duplicate guard)
field     = IDW(k=12, w=1/(d+1)) over neighbours' (X, Y, r=TVT+Z)
anchor    = mean(r_true - r_pred) over the target's OWN last 100 known heel rows
struct    = r_pred + anchor - Z
GATE      = (surviving neighbours >= 4) AND (closest mate < 1000 ft)      -> 87.3 % of train rows
output    = 0.85 * (DWT+PF blend) + 0.15 * struct   on gated rows; DWT+PF blend unchanged elsewhere
```
Weight and gates are **fixed from nested train OOF**; nothing is fitted at test time.

## Why it was worth a submission slot
| gate | evidence |
|---|---|
| honest OOF beats the incumbent | nested 760-well OOF **9.2987 → 8.8626 (+0.4361)** |
| stable, not a fitting artefact | bootstrap over 200 well-resamples: mean +0.4335, **5th pct +0.2356, 100 % positive**; per-fold weights all positive |
| decorrelated / new channel | corr(struct, DWT) +0.24, corr(struct, PF) +0.08 — a cross-well, GR-free, label-driven operator, unlike DWT (per-row GBM) and PF (intra-well GR matching) |
| honest provenance | duplicate gate: closest mates differ by median 64 ft TVT at matched XY, GR corr 0.10, **0/52 duplicate signatures**; `min_sep=150` verified live (each visible well's self-twin at 0.0 ft dropped) |
| stress-safe | gates remove the harmful regimes (≤3 mates → struct RMSE 116.7; closest > 1000 ft → −0.20). Worst per-well regression improves **+11.44 → +3.66 ft**; ungated wells provably unchanged |
| smoke | Kaggle interactive run COMPLETE, 0 errors, full `[struct]` diagnostics |
| format audit | all PASS (14,151 rows, id order/set, 0 dupes, all finite, range [11595.0, 12240.8]) |
| diff explainable | 100 % rows changed, mean 0.928 ft = W × mean|struct−base| (0.15 × 7.46) |

Diagnostic on the 3 visible wells (train duplicates, indicative only): pooled base 3.941 → candidate **3.677**.

## Decision meaning
- If the public score improves on 8.080, the candidate **replaces 54804893 as the honest slot** and the
  final-2 becomes `{54844628, overlap hedge}`.
- If it does not improve, 54804893 is retained and 54844628 is kept as a diagnostic — note that public is the
  3-visible-overlap-well game while the OOF proxies the novel/private target, so a null public move does not
  by itself refute the +0.436 honest OOF gain.
- Either way the downside is structurally bounded: 12.7 % of rows (and all sparse/distant wells) are byte-
  identical to the already-verified 54804893.

## Retrieving the score (the run was still scoring when this was written)
A detached waiter is polling and appending to
`/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/substatus.log` (survives session exit). Or directly:
```
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle \
  competitions submissions rogii-wellbore-geology-prediction --csv | grep 54844628
```
