# ROGII — final-2 risk audit (Direction A, 2026-07-19)

Session `1a07ce3e`. Verify both final-2 slots are selectable, refs/scores/source consistent, and check for a
better same-class version. Neutral technical language.

## Slot selectability + consistency (Kaggle-verified)
| slot | ref | public | status | source / commit | consistent? |
|---|---|---|---|---|---|
| honest | 54804893 | 8.080 | COMPLETE (selectable) | `joezzzzz/rogii-dwt-pf-blend-codex` v1, commit 8544143 | YES — OOF 9.2969, leak-audit clean, public-verified |
| overlap hedge | 54289934 | 7.212 | COMPLETE (selectable) | Plane Top2 "Gate-Safe" (banked) | YES — bounded/guarded affine overlay |

Both are COMPLETE and selectable in the final-selection UI. No wrong/duplicate version of the honest slot
(the DWT+PF blend is the only submission of its kind; det-base DWT 54775625/9.487 is its superseded base).

## Better same-class version found — overlap slot
Sorted board (best public first) shows an overlap cluster **better than Gate-Safe (7.212)**:
`54174151` **7.182** (active-account baseline = base+overlap stack, the team's trusted anchor, audit-pass),
`54331645` 7.220, `54387277` 7.231, `54070198` 7.235. All are overlap/public plays.
- **`54174151` (7.182) captures marginally more overlap than Gate-Safe (7.212)** on the hidden public split
  (public LB uses hidden wells → 7.182 is a real hidden-overlap-generalization number, not visible-overfit).
- Under best-of-2 {honest, overlap-hedge}: the overlap slot only matters in the overlap-heavy scenario, and
  there `54174151` (7.182) < Gate-Safe (7.212) → {blend, 54174151} weakly dominates {blend, Gate-Safe}
  (equal ~9.3 on novel where both overlap plays are floored by the blend; 0.03 better on overlap).
- **Caveat:** Gate-Safe is the team's controlled/bounded/audited mechanism; `54174151` is a public baseline
  reproduction whose internal composition is less controlled. The difference is marginal (0.03).

## Final-2 checklist / recommendation
- [x] Honest slot = **DWT+PF blend 54804893** (8.080 / OOF 9.30) — firm, best honest, robust (Direction B).
- [x] Overlap slot = **Gate-Safe 54289934 (7.212)** by default (controlled), OR **`54174151` (7.182)** if
  maximizing overlap capture is prioritized (marginally better public/hidden-overlap; less controlled).
- [x] Both selectable. No new submission required for A (both refs already banked).
- **Recommended pair: {54804893 DWT+PF blend, 54289934 Gate-Safe}**; note `54174151` as a marginal
  overlap-slot upgrade the user may prefer for pure best-of-2 overlap optimization.
