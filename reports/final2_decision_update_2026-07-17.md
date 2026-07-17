# ROGII — final-2 risk matrix + recommendation (2026-07-17)

Relaxed-submission round, session 16baec36. Supersedes the recommendation in
`final2_update_b4_built_2026-07-15.md`. Goal = **private/final ranking on NOVEL wells** (per CLAUDE.md).
Best-of-2 rule confirmed (min of two pooled private scores). Neutral technical language.

## 1. Candidate inventory + risk classification

| ref | public | class | honest? | risk type on NOVEL private | risk on OVERLAP private |
|---|---|---|---|---|---|
| **DWT** 54453597 | 9.519 | GBM ensemble, honest forward | **YES** (proven, CV 10.40) | safe ~9.5 | ~9.5 (no overlap capture) |
| **Sunny PF90** 54710185 | **8.864** | PF/beam/DTW + GBM, Caruana blend | **architecturally yes** (147 OOF/GroupKFold refs, no overlap-copy); OOF-unverified | if durable ~8.9 (**beats DWT**); if PF is public-favorable → ~DWT | ~8.9 (no overlap capture) |
| spatial-formation 54723189 | 9.150 | structural-surface guarded LOO | partial (V2 surfaces are achievable-negative → gain likely from the guard) | ~9.2 if honest; mild collapse if guard=overlap | mild overlap capture |
| **Gate-Safe** 54289934 | 7.212 | affine-overlay, bounded/guarded | **NO** (overlap hedge) | **collapses** (weak base + affine FP) → worse than DWT | wins ~7.2 |
| v36 54753209 | 7.482 | zero-contact spatial | **NO** (overlap/spatial hedge; source unrecoverable) | collapses (spatial fit uninformative on novel, per B3′) | wins ~7.5 |
| B4′ 54727655 | 9.864 | DWT + exact override | ~honest (base post-proc variance) | ~9.9 (dominated by banked DWT) | exact override captured nothing |

Key facts driving the classification (see `v36_provenance_and_risk_2026-07-17.md`): the hidden overlap
is **affine near-duplicates**, and affine matching is **FP-unsafe** (the heel↔toe wall: lowest-residual
match is an 18-ft-toe FP). So every overlap play is a **hedge that is net-negative on novel wells** (FPs
dominate) and only wins on an overlap-dominated set.

## 2. Best-of-2 pair analysis (lower is better)

`pair = min(pooled_private(A), pooled_private(B))`. Two private scenarios:

| pair | NOVEL-heavy private (the stated goal) | OVERLAP-heavy private |
|---|---|---|
| {DWT, Gate-Safe} | **9.5** (Gate-Safe collapses → DWT floors) | ~7.2 (Gate-Safe wins) |
| **{DWT, Sunny}** | **8.9 if Sunny durable, else 9.5** (DWT floors) | ~8.9 (no overlap capture) |
| {Sunny, Gate-Safe} | 8.9 if Sunny durable, else ~weak (no DWT floor — risky) | ~7.2 |
| {DWT, v36} | 9.5 (v36 collapses) | ~7.5 |
| {DWT, B4′} | 9.5 (B4′ base ≥ DWT, no capture) | ~9.5 (exact captured nothing) |

**The decisive observation:** on a **NOVEL** private set, every overlap hedge collapses and is never
selected → {DWT, Gate-Safe} = {DWT, v36} = {DWT, B4′} = **DWT alone (9.5)**. Only **{DWT, Sunny}** can
do better than DWT on novel wells, because Sunny is a *diverse honest model* that may beat DWT there —
and under best-of-2 the DWT slot floors it if Sunny does not hold. **So for the stated goal (novel
private), {DWT, Sunny} weakly dominates {DWT, Gate-Safe}: the overlap hedge is worthless on novel wells,
so the 2nd slot is better spent on honest upside.**

The ONLY scenario in which {DWT, Gate-Safe} beats {DWT, Sunny} is if the **private set actually contains
train-duplicate (overlap) wells** — which contradicts the "novel wells" goal and the prior evidence that
"the overlap-chasers shake down on private" (lessons §1).

## 3. Recommendation

- **Primary (recommended): {DWT 9.519 (54453597), Sunny PF90 8.864 (54710185)}.**
  Rationale: the private goal is novel wells; on novel wells the overlap hedges provide no value, so the
  best 2nd slot is a diverse honest model. Sunny is architecturally honest (extensive OOF/GroupKFold, no
  overlap-copy) and 8.864 sits in the honest manifold (8-14), so it is a credible honest model that may
  beat DWT on novel wells. Best-of-2 makes it a **downside-free option relative to DWT** (DWT floors the
  pair at 9.5 if Sunny does not hold).
  - **Verification gate (recommended before final lock):** run Sunny's honest OOF (Kaggle diagnostic) to
    confirm its CV is materially below DWT's 10.40. If its OOF ≈ DWT or worse, Sunny's 8.864 is
    public-favorable → fall back to the robust pair below. (Even unverified, {DWT, Sunny} carries no
    novel-private downside vs {DWT} — the risk is only opportunity cost vs an overlap hedge.)
- **Robust fallback: {DWT 9.519, Gate-Safe 7.212 (54289934)}.**
  Choose this iff there is reason to believe the private set contains overlap wells (i.e. the public/private
  split is random over a test set that includes train-duplicates, rather than a deliberately-novel private).
  It hedges the overlap scenario at the cost of the Sunny upside on novel wells.
- **Not recommended for a slot:** v36 (overlap/spatial hedge, weaker than Gate-Safe, source unrecoverable),
  B4′ (base variance, no overlap capture), spatial-formation (structural-guard, partial/unclear),
  two-overlap pairs (no honest floor).

## 4. Why no new overlap submission this round
Task 4 (DWT + affine override) was built and validated: it is **FP-unsafe and net-negative on the honest
(novel) proxy** (NET −2.9M sq-error; §2 of the provenance report). For a novel-private goal an overlap
hedge is low-value by construction, and a DWT-base affine hedge is additionally cruder than and dominated
by the proven Gate-Safe. Submitting it would not inform the recommendation (it would at best confirm
"Gate-Safe is the better hedge"), so a leaderboard slot is not spent on it. The relaxed budget is better
directed at the **Sunny OOF verification** (a diagnostic run), which resolves the actual pivot (slot-1/2).

## 5. Open risk points
- **Sunny durability** (the pivot): architecturally honest but OOF-unverified; prior sessions framed it as
  a "hedge". Resolve via a Kaggle OOF diagnostic.
- **Private overlap presence** (the scenario pivot): unprobeable from submissions; prior belief = novel
  (plateau reverts on private). If wrong, the robust fallback applies.
- v36 source unrecoverable → no v36 variant possible (task 5 blocked).
