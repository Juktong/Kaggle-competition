# ROGII — final-2 scenario table (Direction D, 2026-07-19)

Session `8de8cbed`. Best-of-2 = min of two pooled private scores. Honest slot fixed = 54804893 (DWT+PF blend,
public 8.080 / OOF 9.30). Rows = 2nd-slot options; columns = private-composition scenarios. Lower is better.
Values are directional (public/OOF-anchored; private hidden until 2026-08-05). Neutral technical language.

## Pair × scenario (each cell = expected pooled-private of the BETTER slot)
| 2nd slot | novel-heavy (goal) | overlap-heavy (exact-id) | overlap-heavy (affine-only) | mixed | public-like | if 2nd slot collapses |
|---|---|---|---|---|---|---|
| **54289934 Gate-Safe (7.212)** | ~9.3 (blend) | ~7.2 (Gate-Safe) | **~7.2 (Gate-Safe, affine)** | blend or 7.2 | ~7.2 | blend floors ~9.3 |
| **54174151 Lucifer (7.182)** | ~9.3 (blend) | **~7.18 (54174151)** | ~9.3 (blend; exact-id misses affine) | blend or 7.18 | ~7.18 | blend floors ~9.3 |
| qwer 54777533 (7.921) | ~9.3 (blend) | ~7.9 (worse capture) | ~9.3 (blend) | blend | ~7.9 | blend floors ~9.3 |
| v36 54753209 (7.482) | ~9.3 (blend) | ~7.5 | ~7.5 | blend | ~7.5 | blend floors ~9.3 |
| Amged/HMM (7.23–7.73) | ~9.3 (blend) | 7.23–7.73 | mixed | blend | 7.23–7.73 | blend floors ~9.3 |
| 54775625 DWT (9.487) | ~9.5 (≈blend or DWT) | ~9.5 (no capture) | ~9.5 (no capture) | ~9.5 | ~9.5 | blend floors ~9.3 |

## Reading
- **Every pair is floored at ~9.3 on novel-heavy private** (the DWT+PF blend holds; all overlap 2nd-slots
  collapse and are floored by the blend). So on the STATED goal (novel), the 2nd-slot choice barely matters.
- **The 2nd slot only differentiates on overlap-heavy private:** there the LOWEST-public overlap play wins.
  **54174151 (7.182) wins if the private overlap is exact-id; Gate-Safe (7.212) wins if it is affine-only.**
- qwer/v36/Amged/HMM 2nd slots are dominated (higher public overlap capture, same collapse). DWT as 2nd slot
  adds nothing (no overlap capture; blend already ≥ DWT).
- **Worst-case robustness:** in every scenario the blend floors the pair at ~9.3 — there is no pair where a
  2nd-slot failure drops below the blend. So the downside is bounded regardless of the 2nd-slot pick.

## Verdict
- **{54804893, 54174151}** — best expected (wins the exact-id-overlap scenario by 0.03, ties elsewhere).
- **{54804893, 54289934 Gate-Safe}** — best if the private overlap is believed affine-only (Gate-Safe's affine
  overlay catches what exact-id misses).
- Both are floored at ~9.3 on the novel goal. The choice is a marginal overlap-scenario hedge; the honest slot
  is the decision that matters and it is firm.
