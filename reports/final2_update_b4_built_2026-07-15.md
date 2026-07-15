# ROGII — Final-2 update after B4′ built & submitted (2026-07-15)

Supersedes the *recommendation* section of `final2_decision_optimization_2026-07-15.md` (the S-A model
is unchanged and still valid). Adds: B4′ is now built, locally validated (FP=0, visible recon RMSE
0.000), and **submitted (ref 54727655, pending)**; a corrected best-of-2 mechanism; and the Sunny-PF /
54723189 candidates. Neutral technical language; goal = private/final rank.

## 1. Corrected best-of-2 mechanism
Kaggle scores the **better of your 2 selected submissions on the private LB** — i.e.
`pair_private = min(pooled_private(A), pooled_private(B))`, a min over two **pooled** scores (NOT a
per-row/per-well blend). Consequence: **the 2nd slot is a free option** — it changes the pair's score
only when it is *strictly better* than the 1st on private. So slot-2 should be the candidate most
likely to have the **lowest pooled private score in the scenario where slot-1 is not already optimal**.

## 2. B4′ self-floors at DWT (key structural fact)
B4′ = the honest DWT 9.519 pipeline (LAM=1.0, 5-model) with a per-well guarded override appended in a
`try/except`:
- override fires ONLY on wells passing the tight gate (`tvt_rmse<0.02 ft`, z_mad<0.02, gr_mad<0.50, ≥50
  overlap rows); FP=0 on all 773 train wells; exact reconstruction on true duplicates (visible RMSE 0.000);
- on ANY override error → the except branch writes the unmodified DWT submission.

Therefore **B4′ ≥ DWT weakly, by construction** (= DWT on novel wells, ≤ DWT on detected duplicates, =
DWT on any malfunction). B4′ dominates the overlap hedge at every overlap fraction f (S-A §2). So among
the *already-measured* candidates, **B4′ has the lowest pooled private score in every scenario** — it is
the correct slot-1.

## 3. Slot-2 candidates (free-option analysis)
| candidate | ref | public | can it beat B4′ on private? | role |
|---|---|---|---|---|
| DWT honest | 54453597 | 9.519 | No — B4′ ≥ DWT by construction (and B4′ already self-floors at DWT) | redundant insurance |
| Gate-Safe hedge | 54289934 | 7.212 | No — B4′ dominates the hedge at every f (S-A) | dominated |
| **Sunny PF90** | 54710185 | **8.864** | **Maybe** — different (PF/beam) architecture, no overlap-copy trick, better public; novel-well honesty unmeasured | **upside free-option** |
| Sunny PF75 | 54672680 | 8.874 | Maybe (same class as PF90; PF90 slightly better public) | upside alt |
| spatial-surface guarded | 54723189 | pending | Unknown — guarded router on V2-class structural surfaces (achievable-negative direction); await score | monitor |
| B4′ | 54727655 | pending | — (this is slot-1) | slot-1 |

Notes:
- **DWT as slot-2 is redundant**: B4′ already contains the DWT base AND self-floors at DWT via its
  try/except, so `min(B4′, DWT) = B4′`. DWT adds no insurance beyond what is already inside B4′.
- **The only slot-2 that can improve the pair is a genuinely different, potentially-stronger model on
  novel wells.** The best available is **Sunny PF90 (8.864)** — an independent particle-filter/beam
  forward architecture (no `TVT_input`-copy overlap trick; uses a benign global-bias calibration). Under
  best-of-2 it is a pure free option: it counts only if it beats B4′ on private, and cannot hurt.
- **Risk on Sunny:** its 8.864 is a blend (Sunny 80% + a v10 artifact stack 20%) and its novel-well
  (private) behavior is unmeasured — it may carry public-favorable components. Under best-of-2 this is
  harmless (it simply would not be selected), but it is not a *proven* honest floor.

## 4. Recommendation
- **Robust lock (default): {B4′ 54727655, DWT 54453597}.** Maximally defensible: B4′ is the dominant
  honest+overlap single submission; DWT is the proven honest anchor. Cost of DWT's redundancy = 0.
- **Higher-upside upgrade (evidence-gated): {B4′ 54727655, Sunny PF90 54710185}.** Under best-of-2,
  swapping the redundant DWT slot for the diverse Sunny PF is a free option that adds novel-well upside
  if Sunny is honestly ~8.86. **Gate to adopt:** (a) B4′ pending public confirms B4′ behaves ≥ DWT
  (i.e. public ≤ 9.519, showing overlap capture without regression); (b) a light check that Sunny PF's
  8.864 is not dominated by public-only calibration (ideally its honest OOF, the deferred B1′ work).
- **Do NOT pick two overlap/public plays** (e.g. {hedge, Sunny}) — both share private-collapse risk and
  neither floors at a strong honest base.

## 5. Contingencies on the two pending scores
- **B4′ (54727655)** completes: if public is in the overlap-improved band (≈7–9, ≤ DWT 9.519) → confirms
  B4′ captures overlap while keeping the DWT base → lock B4′ as slot-1, consider the Sunny upgrade. If
  public ≈ 9.519 exactly → the public hidden split had ~no duplicates (override rarely fired); B4′ still
  == DWT publicly and dominates on any private overlap → still the correct slot-1. If public > 9.519 →
  investigate an unexpected override interaction before locking (fall back to {DWT, hedge}).
- **54723189 (spatial-surface guarded)** completes: it targets the V2 structural-surface direction
  (achievable-negative). If it scores well on public it is likely another overlap-guarded play (a hedge
  variant, dominated by B4′ for the honest slot); record and compare, but it does not displace B4′+DWT.

## 6. Assumptions / risk points
- Best-of-2 private rule is the linchpin (standard Kaggle 2-final mechanism; worth a one-line manual
  confirmation on the rules page). If only the last submission counted, the free-option argument weakens.
- Sunny PF novel-well honesty is unmeasured; the upgrade is explicitly gated on evidence, and under
  best-of-2 the downside of including it is nil.
