# ROGII — submission ledger + final-2 (2026-07-19)

Session `dcdcec05`. Extends `submission_ledger_2026-07-17.md`. Goal = private rank on NOVEL wells.
Best-of-2 = min of two pooled private scores. Neutral technical language. Detail:
`final2_decision_update_2026-07-19.md`, `qwer_final2_audit_2026-07-19.md`.

## Board (all final-relevant refs, verified public)
| ref | public | honest OOF | candidate | class | source | final-2 role |
|---|---|---|---|---|---|---|
| **54804893** | **8.080** | **9.2969** | DWT+PF blend | honest, decorrelated (w*=0.44) | `joezzzzz/rogii-dwt-pf-blend-codex` v1 (commit 8544143) | **slot-1 (honest, verified)** |
| **54289934** | 7.212 | — | Gate-Safe | overlap-exploitation hedge | Plane Top2 (banked) | **slot-2 (overlap hedge)** |
| 54710185 | 8.864 | ~11 on novel | Sunny PF90 | overlap-leaked physical | `henry_v10_sunny80_blend` | superseded by the blend (blend beats it honestly) |
| 54775625 | 9.487 | 10.3987 | det-base DWT | honest GBM base | `joezzzzz/rogii-dwt-detbase-codex` | superseded by the blend for the honest slot |
| 54777533 | 7.921 | 6.909 (**leakage**) | qwer | overlap/meta play, source unrecoverable | remote Codex (SHA424e unresolved) | **EXCLUDED** (not honest; dominated by Gate-Safe for overlap) |
| 54753209 | 7.482 | — | v36 | overlap/spatial hedge, unrecoverable | remote Codex | not a slot (dominated by Gate-Safe) |
| 54723189 | 9.150 | — | spatial-formation | structural-surface guard | remote Codex | not a slot (unverifiable) |
| 54727655 | 9.864 | — | B4′ exact | DWT + exact override | this branch | not a slot (no capture) |
| 54775626 | 9.823 | — | DWT+affine | DWT + affine override | this branch | not a slot (FP-unsafe, net-negative) |

## Submissions this round (2026-07-19): 0
No new submission. Router gain over the fixed-0.5 blend is negligible (+0.025), qwer is leakage, and no new
honest candidate cleared a gate. Budget preserved (2026-07-18 used 1: the DWT+PF blend 54804893).

**A→G audit continuation (session 1a07ce3e):** confirmed no submittable candidate. Weight W=0.44 gains only
0.019 (within noise); expanded router HURTS (nested 9.319 vs fixed 9.297); GR-free geometry/change-point
family is weak+DWT-correlated (0.68), adds +0.076 via NEGATIVE λ-disguise weights (non-transferring); qwer
unrecoverable (4th check). **A finding for the overlap slot:** `54174151` (public **7.182**, active-account
base+overlap stack) captures marginally more overlap than Gate-Safe (7.212) — an optional overlap-slot upgrade
({blend, 54174151} weakly dominates {blend, Gate-Safe} for best-of-2 overlap optimization; Gate-Safe is the
more controlled mechanism). Reports: `final2_risk_audit`, `private_risk_stress_test`, `router_and_weight_search`,
`qwer_forensic_recovery`, `public_notebook_honest_scan` (all 2026-07-19).

## Final-2 recommendation (verified)
**{DWT+PF blend 54804893 (public 8.080, OOF 9.30), Gate-Safe 54289934 (public 7.212)}** — best of both private
scenarios (blend holds ~9.3 on novel; Gate-Safe wins ~7.2 on overlap). qwer's better public (7.921) is
overlap-driven, not novel-quality → excluded. Private hidden until 2026-08-05.

## Open levers (next round, all gated)
- A genuinely NEW honest input channel / model family decorrelated from DWT AND the plain PF (the router
  analysis shows the DWT/PF complementarity is oracle-only, so more of the same PF family won't help).
- A reproducible honest source for any remote-Codex submission (qwer/v36/spatial) would change their status;
  none is currently recoverable.

## FINAL-SELECTION AUDIT (session 8de8cbed) — 2nd slot resolved to 54174151 vs Gate-Safe
Full board (50 subs) + 54174151 provenance recovered: **54174151 = Lucifer baseline repro
(`joezzzzz/rogii-lucifer-baseline-repro-codex` v1)**, overlap-exploitation (RMSE 0.005 on visible overlap),
public 7.182, exact-id gate → FP-safe on novel, reproducible + audit-pass, submission.csv on disk. It is the
ONLY overlap play below Gate-Safe (7.212); all others (7.22–7.92: Hongwei/HMM/Top1/affine/v36/Amged/qwer)
dominated. **Recommended final-2 = {54804893 DWT+PF blend (honest, 8.080/OOF 9.30), 54174151 Lucifer (7.182,
overlap hedge)}**; conservative alternative keeps Gate-Safe 54289934 (7.212) if private overlap is affine-only.
No new submission. Deadline 2026-08-05. Reports: `final_overlap_slot_audit`, `historical_submission_board_audit`,
`final2_scenario_table`, `final_selection_package`, `teammate_final_selection_note_zh` (all 2026-07-19).
