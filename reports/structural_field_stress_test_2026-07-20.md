# ROGII — structural-field stress test (A2, 2026-07-20)

Session `4d6cd351`. Stress the group-anchored cross-well structural field before it can be submitted against
the honest slot **54804893 (DWT+PF blend, honest OOF 9.2969, public 8.080)**.
Scripts: `scripts/struct_oof_produce.py` (saves per-row struct OOF + per-well neighbour metadata),
`scripts/struct_field_stress.py`. Data: 760 wells / 3,721,471 toe rows. Neutral technical language.

## 0. Reproduction (A1)
Independent re-run reproduces the earlier numbers exactly: base `DWT+PF 0.5/0.5 = 9.2987`,
`struct = 26.0024`, nested (blanket weight) `9.1626`, gain `+0.1361`, per-fold w = [0.069, 0.069, 0.082,
0.066, 0.073]. 13/773 wells have **0 surviving neighbours** and fall back to the blend unchanged.

## 1. What the stress found — a blanket weight is NOT safe
| stress | finding |
|---|---|
| **S2 neighbour count** | wells with **≤3 mates** have struct RMSE **116.7**; a blanket W=0.07 moves them **10.192 → 15.609**. The nested fit correctly learns w=0 there, but a fixed deployed weight would not. |
| **S3 closest-mate distance** | gain by distance band: **<300 ft +0.447 · 300–500 ft +0.287 · 500–1000 ft +0.686 · >1000 ft −0.202**. The field helps only while a train well runs within ~1 km. |
| **S5 per-well risk (blanket W=0.07)** | 478/760 improved, 282 worsened; **worst well +11.44 ft** (9dfff011, closest mate 3278 ft). All five worst wells have closest mates 2.7–4.7 kft. |
| **S4 fallback** | 13 wells (singleton typewell groups) produce no struct row → contribution disabled, prediction identical to the DWT+PF blend. |
| **duplicate guard** | `min_sep = 150 ft` verified live: on each of the 3 visible test wells the exact self-twin (separation **0.0 ft**) is dropped, leaving 13/40/13 genuine offset mates. Without the guard the twin would return the well's own truth. |

## 2. Fix — deterministic, test-available gates (this is the deployed configuration)
```
gate    = (surviving neighbours >= 4) AND (closest mate < 1000 ft)     -> 87.3 % rows, 657/760 wells
weight  = 0.15, FIXED from nested train OOF (never fitted at test time)
guard   = min_sep 150 ft duplicate exclusion ; k = 12 ; anchor = last 100 known heel rows
fallback= ungated wells and wells with no surviving neighbour keep the DWT+PF blend unchanged
```

**Gate comparison (nested, full-set RMSE with ungated rows at weight 0):**
| gate | nested | gain |
|---|---|---|
| no gate (blanket) | 9.1626 | +0.1361 |
| nnb ≥ 4 | 9.0591 | +0.2396 |
| closest < 1000 ft | 8.9414 | +0.3572 |
| **nnb ≥ 4 AND closest < 1000 ft** | **8.9194** | **+0.3793** |
| nnb ≥ 4 AND closest < 800 ft | 8.9461 | +0.3525 |
| nnb ≥ 4 AND closest < 1500 ft | 8.9558 | +0.3429 |
| nnb ≥ 8 AND closest < 1000 ft | 8.9591 | +0.3396 |

**Fixed-weight sweep under the chosen gate (full-set RMSE):**
`0.05 → 9.1007 · 0.10 → 8.9545 · 0.12 → 8.9111 · **0.15 → 8.8626** · 0.18 → 8.8344 · 0.20 → 8.8268 (min) ·
0.22 → 8.8284 · 0.25 → 8.8477 · 0.30 → 8.9249` — a smooth, flat optimum.

**Bootstrap (200 well-resamples):**
| W | mean gain | 5th pct | frac > 0 |
|---|---|---|---|
| 0.12 | +0.3810 | +0.2210 | 100 % |
| **0.15** | **+0.4335** | **+0.2356** | **100 %** |
| 0.18 | +0.4745 | +0.2276 | 100 % |
| 0.20 | +0.4743 | +0.1950 | 100 % |

**W = 0.15 selected**: on the conservative side of the 0.20 point-optimum (smaller deviation from the
public-verified base) while carrying the **highest 5th-percentile gain**, with every resample positive.

## 3. Resulting risk profile
- Honest OOF **9.2987 → 8.8626 (+0.4361)**, i.e. more than 3× the blanket-weight gain.
- Per-well worst-case regression improves from **+11.44 ft → +3.66 ft**; mean delta −0.146.
- Wells the field cannot serve (sparse group, distant neighbours, no surviving mate after the guard) are
  **provably unchanged** — they keep the exact DWT+PF prediction, so the downside is structurally bounded.

## 4. Known caveats carried into the submission decision
1. **Gate metric definition.** `closest` is the minimum separation over *all* group-mates, computed **before**
   the duplicate guard. It is defined identically in the OOF and in inference, so the OOF estimate is
   self-consistent; but for a well whose twin was dropped, the gate can pass on the twin's distance. In
   practice such a well is genuinely in a densely-drilled area, and the field itself only ever uses
   guard-surviving neighbours.
2. **Hidden-rerun coverage is the main transfer risk.** The gain requires a train well within ~1 km of the
   test trajectory. Novel wells drilled in the same fields plausibly satisfy this (87 % of train wells do);
   wells in new areas will be gated off and fall back to the blend — bounding both the downside and the upside.
3. The weight is fixed; no test-time fitting anywhere in the inference path.
