# ROGII — final overlap-slot audit: 54174151 vs Gate-Safe (Directions A & C, 2026-07-19)

Session `8de8cbed`. Decide the 2nd (overlap-hedge) slot. The honest slot 54804893 (DWT+PF blend, 8.080/OOF
9.30) is firm. Neutral technical language.

## 1. 54174151 provenance (RECOVERED — full source + predictions on disk)
- Submission **54174151**, public **7.182**, COMPLETE, 2026-06-29, file `submission.csv`.
- **Source: kernel `joezzzzz/rogii-lucifer-baseline-repro-codex` v1** = the **Lucifer physics-PF-stack baseline
  reproduction** (NOT an abstract baseline). Local artifact `artifacts/lucifer_baseline_repro_joezzzzz_v1/`
  (submission.csv + submission_audit.json + run_summary.json + log). Format audit **PASS** (14151 rows, id
  order matches sample, tvt range [11587,12240], sha256 recorded). Audit doc `baseline_repro_audit_2026-06-29.md`.
- **Mechanism = the analyzed Lucifer stack:** honest PF/beam + GBM forward, with an **overlap override
  `guarded_contact_override`** gated `if wid not in train_wells: continue` — i.e. it reconstructs the toe
  ONLY on exact-id train-duplicate wells (via the train well's contacts/EGFDU), and uses the honest forward
  on everything else.

## 2. Data-based classification (predictions on the 3 visible exact-twin overlap wells, truth known)
| model | 000d7d20 | 00bbac68 | 00e12e8b | pooled |
|---|---|---|---|---|
| 54174151 (Lucifer) | 0.01 | 0.01 | 0.01 | **0.005** |
| DWT+PF blend 54804893 | 3.03 | 4.22 | 4.24 | 3.94 |

- **54174151 = near-perfect (RMSE 0.005) on overlap wells → confirmed overlap-EXPLOITATION play** (exact toe
  reconstruction via the override). It is NOT an honest/novel model; on novel wells it reverts to the honest
  Lucifer forward (~11–15, weaker than the blend 9.30).

## 3. 54174151 vs Gate-Safe (54289934) — the overlap-slot comparison
| axis | 54174151 (Lucifer repro) | Gate-Safe (Plane Top2) |
|---|---|---|
| public (hidden-overlap capture) | **7.182 (lower = more capture)** | 7.212 |
| mechanism | exact-id toe reconstruction (Lucifer override) | bounded **affine** overlay |
| FP risk on novel | **none** — gated on exact-id, doesn't fire on novel | affine can fire on coincidental FPs (heel↔toe wall) |
| reproducible | YES (local kernel + submission.csv + audit) | banked ref (mechanism ≈ david_v12 `_fast_exact_recovery`) |
| novel-private behavior | honest Lucifer forward (~11–15), floored by the blend | collapses, floored by the blend |
| captures AFFINE-only overlap? | NO (exact-id gate misses different-id affine dups) | YES (affine matching) |

- **On the hidden PUBLIC split, 54174151 (exact-id, 7.182) beat Gate-Safe (affine, 7.212)** → the hidden
  public overlap is dominated by exact-id train duplicates that 54174151 reconstructs, and its aggressive
  exact reconstruction net-outperforms the bounded affine overlay. It is also FP-safe on novel (exact-id gate).
- **The one scenario favoring Gate-Safe:** if the PRIVATE overlap is AFFINE-only (different ids), 54174151's
  exact-id gate misses it while Gate-Safe's affine overlay catches it. No evidence the private differs from the
  public overlap distribution, but this is the residual risk that keeps Gate-Safe a defensible conservative pick.

## 4. Recommendation (2nd slot)
- **Marginally-optimal: 54174151 (7.182)** — lower public (more hidden-overlap capture), FP-safe on novel
  (exact-id gate), fully understood + reproducible. Under best-of-2 {blend, 54174151} weakly dominates
  {blend, Gate-Safe} (0.03 better on an exact-id-overlap private; equal ~9.3 on novel where the blend floors both).
- **Conservative alternative: Gate-Safe 54289934 (7.212)** — bounded affine overlay; safer ONLY if the private
  overlap is affine-only (exact-id would miss it). 
- **The difference is marginal (0.03) and matters only in the overlap-heavy scenario** (which contradicts the
  novel goal). The honest slot (54804893) is the primary and floors both on novel. **No new submission** — both
  are banked/selectable; this is a final-selection choice, not a modeling task.
