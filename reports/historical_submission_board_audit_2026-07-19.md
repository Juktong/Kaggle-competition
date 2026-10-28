# ROGII — historical submission board audit (Direction B, 2026-07-19)

Session `8de8cbed`. Full classification of all 50 submissions (`/tmp/rogii_submissions_latest.csv`). Goal =
identify every candidate for the 2nd slot and confirm none beats the current picks. Neutral technical language.

## Board by class (38 scored + 12 blank/failed)
**Honest / novel (public ≥ 8.0):**
| ref | public | class | 2nd-slot fit |
|---|---|---|---|
| **54804893** | **8.080** | **DWT+PF blend — honest, decorrelated, OOF 9.30** | **SLOT-1 (honest, firm)** |
| 54710185 | 8.864 | Sunny PF90 (overlap-leaked physical) | no (blend beats it) |
| 54672680 | 8.874 | Sunny PF75 | no |
| 54723189 | 9.150 | spatial-formation guard | no (unverifiable) |
| 54775625 | 9.487 | DWT det-base (honest GBM) | sanity baseline only (superseded) |
| 54453597 | 9.519 | DWT honest base (non-det) | equiv fallback |

**Overlap / public hedges (7.18–7.31) — all overlap-exploitation, NOT honest:**
| ref | public | mechanism | vs Gate-Safe |
|---|---|---|---|
| **54174151** | **7.182** | Lucifer repro (exact-id toe reconstruction) | **beats Gate-Safe (lower public, FP-safe)** |
| 54289934 | 7.212 | Gate-Safe (bounded affine overlay) | current 2nd slot |
| 54331645 | 7.220 | Hongwei posterior bounded ruler overlay | dominated by both |
| 54387277 | 7.231 | HMM PF prefix-calibrated overlay | dominated |
| 54070198 | 7.235 | Wellbore-wizard physics-PF fork | dominated |
| 54259463 | 7.243 | singlewell 000d7d20 router | dominated (single-well) |
| 54070940 | 7.263 | David v12 fork | dominated |
| 54272932/54331650/54240269/54272931/54239972/54070179/54260126 | 7.27–7.31 | Top1/Hongwei/affine/gold overlays | all dominated by 54174151 & Gate-Safe |

**Mid / weaker hedges + leakage (7.48–7.92):** v36 54753209 (7.482, spatial, unrecoverable), David bimodal
54098152 (7.703), Amged baseline 54447950 (7.732, public reproduction), SP45 54198676 (7.753), fleongg
54174876 (7.787), qwer 54777533 (7.921, leakage-OOF, unrecoverable). None competitive with 54174151/Gate-Safe.

**Dominated / diagnostic (≥9.8):** DWT+affine 54775626 (9.823, FP-unsafe), B4′ 54727655 (9.864, no capture),
post-proc isolations (54561443/54527528/54578305/54528969), neural-aligner 54385308 (12.87), TabICL 54162612
(13.45), mycarta 54415309 (14.09), Nickson 54099603 (20.58), overlap-lookup diagnostics (11551/15357 — broken).

**Blank/failed (no public score — NOT selectable):** 54488090, 54486481/54486472 (high-upside projection),
54386773 (HMM notebook), 54331160/54331164 (Hongwei), 54239504/54239485 (affine), 54162415/54162323
(Kojimar), 54099186 (Aevion), 54069750 (Super6).

## Conclusion
- **Honest slot:** 54804893 (8.080) is unambiguously the best honest/novel candidate. Nothing else honest is
  close (next is Sunny 8.864, which the blend beats).
- **Overlap slot:** only **54174151 (7.182)** is below Gate-Safe (7.212); every other overlap play is
  dominated by both. So the 2nd-slot decision is strictly **54174151 vs Gate-Safe** (see
  `final_overlap_slot_audit_2026-07-19.md`). All lower-public candidates are exact-id/affine overlap plays that
  collapse on novel and are floored by the blend.
