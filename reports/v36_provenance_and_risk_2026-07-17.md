# ROGII — v36 provenance + overlap-mechanism findings (2026-07-17)

Continuation of session 16baec36 (relaxed-submission round). Neutral technical language.

## 1. v36 / ref 54753209 — provenance trace (task 1)
- **Submission:** ref **54753209**, public **7.482**, description "Codex v36 zero-contact spatial
  balanced hidden-activation architecture", submitted **2026-07-16 05:42** under Kaggle account
  **joezzzzz** (the shared competition account).
- **Trace performed:** (a) all `joezzzzz` kernels enumerated (pages 1-3) — **no v36 / zero-contact /
  spatial kernel exists**; the newest rogii kernel is `rogii-b4-guarded-codex` (07-15). (b) local repo,
  all Claude job dirs, and the whole `/home` + `/tmp` filesystem grepped for `v36 / zero-contact /
  hidden-activation / spatial-balanced` — **no source**. (c) Codex session rollout logs
  (`~/.codex/sessions`) end at **07-14**; there is no 07-15 or 07-16 local session — so v36 (07-16) and
  the spatial-formation candidate (07-15) were produced by **later Codex sessions that left no local
  trace** (likely remote/cloud), and any kernel was created + submitted + (probably) deleted remotely.
- **Verdict:** v36 source is **NOT locally recoverable**; it cannot be reproduced or variant-built from
  this environment (blocks task 5's "v36 variant"). Classification below is from metadata + score + the
  overlap-mechanism analysis in §2.
- **Classification:** public **7.482** sits in the **overlap/public-plateau band** (Gate-Safe 7.212,
  Hongwei 7.220, HMM-PF 7.231, teammate affine 7.278/7.294; honest manifold is 8-14). "zero-contact"
  = reaches the plateau **without** direct train-TVT copy (the naive exact-copy scored 11551 and was
  rejected); "spatial balanced hidden-activation" = a spatial/transductive architecture keyed on the
  hidden-test batch. → v36 is an **overlap/public play (hedge class), high private-collapse risk on a
  novel-heavy private set**, comparable to but slightly weaker than Gate-Safe (7.482 vs 7.212).

## 2. The overlap mechanism is AFFINE near-duplicates — and affine matching is FP-unsafe (task 4 core)
This is the decisive new finding of the round; it reframes B4′ and the whole overlap question.

- **The hidden overlap is affine near-duplicates, not exact.** B4′ (exact `tvt_rmse<0.02`) captured no
  public overlap (scored 9.864 ≈ base) even though Gate-Safe reaches 7.212 on the same split. Re-examining
  the train near-collisions: the pair I earlier called "different wells" (8b95d6d1/a2e8e7f6) is actually
  the **same well** — its toe recovers to **1.1 ft (exact-copy) / 1.4 ft (affine)** with known-region
  agreement ~2.4 ft. The 0.02 ft gate was ~100× too strict; real near-duplicates agree within ~1-3 ft and
  are often **datum-shifted** (affine `b` up to ~100+ ft; e.g. 511e1db0↔ce8399b7: known gap 50.9 ft, toe
  recovers 2.6 ft). Exact-copy was rejected (11551) precisely because the overlap needs the affine `b`.
- **Train near-duplicate population:** 773 wells → **22 geometric matches** (median |dX|,|dZ| < 0.5 ft over
  ≥50 known rows) = 11 pairs, spanning true-dups (toe recovers <2 ft), partials (2-5 ft), and FPs (>10 ft).
- **Affine matching cannot be made FP-safe — the heel↔toe wall.** Gating on the known-region affine-fit
  residual does NOT separate true-dups from FPs: the **lowest-residual** match (efde6ac3↔d085e611,
  aff_res 0.74 ft) is an **FP** whose toe diverges to **18 ft**; a true-dup (8b95d6d1) has aff_res 2.36 ft.
  A cap on |affine − DWT| also fails (the FP's median deviation 3.27 ft is *smaller* than a true-dup's
  3.69 ft — its divergence is concentrated in rows the median hides). **No test-available signal separates
  a true affine-dup from a well whose heel matches but toe diverges** — the same information ceiling as the
  whole project, in affine form.
- **Net effect (honest, novel-heavy proxy = train self-match):** a DWT+affine override is **net-negative**:
  conservative NET **−2.9M** sq-error (fires on 2 FPs, 0 true-dups); balanced NET **−2.9M** (4 true-dups
  reduce error by 63k, but 2 FPs over ~4500 rows each *increase* it by 2.95M). The FP damage dwarfs the
  true-dup gain because FPs are undetectable and hit many rows.

## 3. Consequence for the final-2
- **Overlap plays (Gate-Safe 7.212, v36 7.482, any DWT+affine) are HEDGES, not honest upgrades.** They
  help only when the scored set is overlap-dominated (public split → 7.2), and are net-negative on a
  novel-heavy set (FPs dominate). This is exactly why the plateau "reverts on private."
- **No DWT+overlap single submission can safely dominate DWT** (the affine override is FP-unsafe;
  the exact override (B4′) captures nothing). So the honest slot must be a genuine forward model
  (DWT, or Sunny if durable), and the overlap slot is a bounded hedge (Gate-Safe is the proven, refined
  one at 7.212 — a DWT-base affine hedge is cruder and, on evidence, dominated).
- Full risk matrix + recommendation: `reports/final2_decision_update_2026-07-17.md`.
