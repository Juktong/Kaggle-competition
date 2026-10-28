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

## 4. The DWT+affine override — built, submitted, EMPIRICALLY CONFIRMED net-negative
Task 4 (DWT + affine override) was built, validated, and submitted with a deterministic-base control:
- **det-base (54775625) = public 9.487** — deterministic DWT base (`optuna n_jobs=1`); reproduces ≈ banked
  DWT 9.519. Resolves B4′'s post-proc variance (use `n_jobs=1`).
- **DWT+affine (54775626) = public 9.823** — **+0.336 WORSE than the base**. The affine override HURT the
  hidden public split: it fired on coincidental affine FPs (heel-match, toe-diverge) rather than the true
  overlap that Gate-Safe captures (7.212). This **empirically confirms** the train analysis (affine is
  FP-unsafe / net-negative; §2 of the provenance report, NET −2.9M).
**Conclusion:** a naive DWT-base affine hedge is **not viable** and does not compete with the proven
Gate-Safe for the overlap slot. The last "can we safely put overlap capture on a strong honest base?"
question is answered **no** (the heel↔toe wall). For a novel-private goal an overlap hedge is low-value
anyway; the remaining pivot is the **Sunny OOF verification** (a diagnostic run — the highest-value
next step). No further overlap variant is warranted.

---

## ROUND 2 (2026-07-17b) — full candidate matrix + three final-2 recommendations

### Candidate pool attributes
| ref | public | class | reproducible? | source? | OOF / honesty support | compliant? | public/private risk |
|---|---|---|---|---|---|---|---|
| **54775625** det-base DWT | **9.487** | honest GBM ensemble | **YES** (`n_jobs=1`, this branch) | YES | DWT OOF (combo_state); honest | YES | low — safe on novel |
| 54453597 old DWT | 9.519 | honest GBM ensemble | no (`n_jobs=-1`) | (banked) | honest, CV 10.40 | YES | low — equivalent to det-base on private |
| **54710185** Sunny PF90 | **8.864** | PF/beam/DTW + GBM meta | via henry fork | YES (`henry_v10_sunny80_blend`) | **leakage audit PASSED**; CV (fork errored; leakage-audit-confirmed honest) | YES (no ext-data leak) | **honest upside** — if durable, beats DWT on novel |
| 54289934 Gate-Safe | 7.212 | affine-overlay hedge | no source | no | overlap (proven) | YES (within-comp) | collapses on novel; wins overlap |
| 54753209 v36 | 7.482 | zero-contact spatial | no | no (remote) | none (unverifiable) | unknown | overlap/spatial; dominated by Gate-Safe |
| 54777533 qwer | 7.921 | overlap OOF-meta | no | no (remote, SHA424e) | **leakage-inflated OOF 6.909** (not honest) | unknown | weakest overlap play; excluded |
| 54723189 spatial-formation | 9.150 | structural-surface guard | no | no (remote) | partial/unclear | unknown | partial overlap; reverts on novel |
| 54727655 B4′ | 9.864 | DWT + exact override | yes (this branch) | YES | override no-op | YES | dominated by det-base DWT |
| 54775626 DWT+affine | 9.823 | DWT + affine override | yes (this branch) | YES | **FP-unsafe, +0.336 worse** | YES | net-negative; not a slot |

### Three final-2 recommendations
Best-of-2 = min of two pooled **private** scores. Honest slot = **det-base DWT 54775625** (reproducible,
9.487; old DWT 54453597 equivalent fallback). qwer/v36/spatial/B4′/affine are excluded (unverifiable or
dominated). The 2nd slot depends on the private-composition scenario:

1. **NOVEL-heavy private (the stated competition goal): `{det-base DWT 54775625, Sunny PF90 54710185}`.**
   Overlap hedges are worthless on novel wells; Sunny is a diverse *honest* model (leakage-audit-clean,
   8.864 in the honest manifold) that may beat DWT on novel. DWT floors the pair if Sunny does not hold.
   Sunny is leakage-audit-confirmed honest (CV fork errored — whack-a-mole; not decision-critical under best-of-2).
2. **OVERLAP-heavy private: `{det-base DWT 54775625, Gate-Safe 54289934}`.** DWT honest floor + the proven
   affine-overlay hedge (7.212, the only overlap play with a real edge; v36/qwer are dominated).
3. **MIXED / uncertain private: `{det-base DWT 54775625, Sunny PF90 54710185}`** (default), because the
   competition goal frames the private as novel (low overlap fraction f). Quantitatively the crossover is
   ~f≈0.4: for f<0.4 the Sunny honest edge (min→~8.9) beats the Gate-Safe overlap capture; only for f>0.4
   does {DWT, Gate-Safe} win. Given the novel framing (f likely low), the mixed default is {DWT, Sunny},
   with {DWT, Gate-Safe} as the explicit hedge if a high private-overlap fraction is suspected.

### Task 4 (备线 A) — honest meta / selector: CLOSED (gate not met)
Mandatory this round; evaluated and **not submitted**, with reasons:
1. **Best-of-2 IS the honest selector.** Kaggle scores the better of the 2 selected submissions on private
   → selecting `{det-base DWT, Sunny}` already realizes a submission-level honest selector (pick DWT or
   Sunny per private scenario). A *within-submission* blend/selector would REPLACE one slot and must beat
   BOTH DWT and Sunny individually on private to help — a strictly higher bar than the free best-of-2.
2. **Within-submission blends are blend-neutral** (20 rounds of evidence: every honest OOF blend with DWT
   lands on ρ≈σ_D/σ_M with weight ≈0; V3 pooled OOS gain −0.0024). Per-well selectors are non-identifiable
   (§8/§14 synthetic-selector 16.32 > best-cost). So a DWT+Sunny blend/selector is very unlikely to beat
   selection.
3. **The one untested hope** (Sunny is *strong-AND-decorrelated* → a positive blend) is **not affordably
   testable**: it needs a full 773-well Sunny OOF aligned with DWT, but the partial 120-well OOF fork
   already runs >30 min → a full OOF is impractical (hours), and qwer (the other candidate) is unverifiable.
**Decision:** no separate honest-meta submission (gate not met, per the stop condition "don't submit
without evidence"). The honest meta/selector is delivered as the **final-2 selection `{det-base DWT,
Sunny}`** (best-of-2). If a future session obtains a full Sunny OOF, the DWT+Sunny blend weight is the
single check that would reopen this.

## 5. Open risk points
- **Sunny durability** (the pivot): architecturally honest but OOF-unverified; prior sessions framed it as
  a "hedge". Resolve via a Kaggle OOF diagnostic.
- **Private overlap presence** (the scenario pivot): unprobeable from submissions; prior belief = novel
  (plateau reverts on private). If wrong, the robust fallback applies.
- v36 source unrecoverable → no v36 variant possible (task 5 blocked).
