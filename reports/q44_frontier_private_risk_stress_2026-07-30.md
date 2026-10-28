# Q44 — private risk stress: best-of-2 is a call option on variance, and the slot-1 argument is smaller than the noise

Date: 2026-07-29 21:05 UTC
Task: `q44_frontier_private_risk_stress` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q44_private_risk_stress.py` · Log: `reports/logs/q44_private_stress_2026-07-30.log`
Outcome: **complete. No submission, no Kaggle run, quota 0/5.**

This round was executed after its own runner turn ended on an API-529 with no work done; the queue row had
been left marked `blocked` with that infrastructure detail. Recorded so the gap in the sequence is explicit.

## 1. What this adds over Q18 and Q53, and why it was needed

Q53 already swept the two axes that decide slot 1 (`retrieval_delta × sigma_transfers`) and produced a point
estimate per cell. **A point estimate is the wrong shape for a best-of-2 decision.** Kaggle scores the
*better* of the two selected submissions on the private rows, so the pair's value is `E[min(p₁, p₂)]` and its
risk is the upper tail of that minimum — both properties of the joint *distribution*, which a point model
cannot express. Q44 models the draw.

Three uncertainties were being conflated. They are different objects and attach in different places:

| # | quantity | size | where it applies |
|---|---|---|---|
| 1 | **public measurement noise** | **sd ≈ 0.03** (Q45, external: 14 unchanged resubmissions of 5 kernels) | ranking two *variants* by public score. **Not** to a banked private score — the submitted file is fixed and the private rows are scored from that same file |
| 2 | **draw non-representativeness** | **sd of the difference ≈ 2.40 ft** | inferring private quality from a 3-well public score. **The dominant term, ~22× the largest stage effect** |
| 3 | **verification / obligation risk** | not a score at all | winner's obligations. Modelled as a selectability constraint, never added to an RMSE |

**Calibration of the 2.40, and an independent corroboration.** Q18 measured that the honest line beats the
frontier line on **~29%** of random 3-well draws at a public gap of 1.328 ft. Inverting,
`σ_diff = 1.328 / |Φ⁻¹(0.29)| = 1.328 / 0.553 = 2.40`. Separately and by a completely different route, the
ledger records the measured *output disagreement* between `54968060` and `54844628` as **rmse 2.54 ft**. Two
independent quantities landing on 2.4–2.5 is the strongest evidence in this round that the draw term is real
and this size. The noise is decomposed as a family shock plus an idiosyncratic term so the correlation
structure is explicit:

```
s_F = 1.6937   s_I = 0.1061   ->  within-family difference sd 0.150   cross-family 2.400
```

**Degeneracy control:** at draw scale 0 the two focus pairs value at **6.6425 vs 6.6430**, a 0.0005 gap,
reproducing Q53's +0.0005 exactly. The stochastic model contains the deterministic one.

## 2. The scale problem, stated once

```
deterministic stage terms separating the slot-1 options
  GR sigma ×1.3            -0.1105
  overlap / retrieval      -0.0310   (measured, Q39 — OFF slightly helps)
  bimodal hedge            +0.0520   (Q45 re-read: ~1.7 sd of the public floor -> unresolved)
uncertainties
  public measurement sd     0.0300   -> two variants are unrankable below ~0.09
  private draw sd (diff)    2.4000   -> 22x the largest stage term
```

**Every quantity the slot-1 debate has turned on is between 0.03 and 0.11 ft. The uncertainty in projecting
any of them onto the private wells is 2.4 ft.** That ratio, not any individual stage, is the finding.

## 3. Scenario grid — 24 cells

Axes: `hyp ∈ {H-visible, H-hidden, mixed}` × `retrieval_delta ∈ {−0.031 measured, 0.0 inert, +0.080 old
model, +0.200 spurious-match stress}` × `sigma_transfers ∈ {True, False}`. The `+0.200` arm is **not
measured** — it stresses the case where the overlap lookup fires on a near-duplicate that is not the same
well and actively injects error; it is included because "retrieval fails" was previously modelled only as
"goes inert", which is the benign failure.

Price of choosing pair **B** (`54968060` + `54844628`, ownership-first) over pair **A** (`54922806` +
`54844628`, score-first), positive = B costs more:

```
                       mean cost   p95 cost          |                        mean cost   p95 cost
-0.031 sigmaF H-hidden   +0.0013    +0.0021          | 0.080 sigmaF H-hidden   -0.0762    -0.0637
-0.031 sigmaF mixed      +0.0285    +0.0285          | 0.080 sigmaF mixed      -0.0099    -0.0076
-0.031 sigmaT H-hidden   +0.0773    +0.0653  <- max  | 0.200 sigmaF H-hidden   -0.1570    -0.1359  <- best
-0.031 sigmaT H-visible  +0.0559    +0.0448          | 0.200 sigmaT H-hidden   -0.0833    -0.0757
 0.000 sigmaF H-hidden   -0.0205    -0.0169          | 0.200 sigmaF mixed      -0.0513    -0.0478
```

- **Worst case over all 24 cells: ownership-first costs +0.0773 mean / +0.0653 p95.**
- In the **measured + evidence-supported** cell (retrieval −0.031, `sigma_transfers=False` — the arm Q36's
  760-well measurement supports, since the multiplier helps only 42.1% of wells with a negative median):
  **+0.0013**, i.e. free to three decimal places.
- **Ownership-first is strictly better in 8 of 24 cells** — every cell where retrieval is at least inert
  *and* the GR-sigma edge does not transfer, and every spurious-match cell.
- `P(B < A)` ranges 0.16–0.65 and sits at **0.35** in the measured cell. The two pairs are close to a coin
  flip once the draw is modelled.

## 4. THE HEADLINE — the second slot is worth ~0.46 ft, an order of magnitude more than the slot-1 argument

H-hidden, measured cell, value of the pair versus its slot-1 candidate alone:

```
pair                                        mean     p95      p5   | gain over slot-1 alone
A  54922806 + 54844628  (diverse)         6.1818  8.5017  3.7270   |  mean -0.4561   p95 -0.9389
B  54968060 + 54844628  (diverse, ours)   6.1829  8.5022  3.7327   |  mean -0.4560   p95 -0.9302
C  54922806 + 54968060  (frontier only)   6.5783  9.3671  3.7850   |  mean -0.0595   p95 -0.0735
D  55064411 + 54844628  (diverse, ours)   6.2178  8.5310  3.7690   |  mean -0.4721   p95 -0.9455
```

**A diverse pair is worth ~0.456 ft in the mean and ~0.94 ft in the bad tail. A second frontier member is
worth 0.060 / 0.074 — about 8× and 13× less.** For comparison, the entire slot-1 dispute is worth at most
0.077.

The mechanism is worth naming because it inverts how the second slot has been described:

> **Best-of-2 is a call option on variance.** You keep the better of two realisations, so the *more*
> uncertain the private draw is and the *less* correlated the two candidates are, the more the second slot is
> worth. Q18 called the honest slot-2 "free insurance at zero modelled worst-case cost" — under a point
> model that was the most it could say. Under the draw, the second slot is not a hedge that costs nothing,
> it is the **largest single positive term in the whole decision**.

This also reverses the usual reading of the draw noise. §5 shows the pair's *mean* improving as the draw gets
noisier (6.6425 → 6.1820 → 5.7493 at scale 0 / 1 / 1.5), which is not an error: with two decorrelated
candidates and best-of-2 scoring, variance is an asset.

## 5. Draw representativeness

Measured cell, H-hidden:

```
draw noise scale          A mean / p95        B mean / p95      P(B<A)
representative (0×)      6.6425 / 6.6425    6.6430 / 6.6430     0.000
mild (0.25×)             6.6389 / 7.3216    6.6394 / 7.3208     0.484
as measured (1×)         6.1820 / 8.5033    6.1826 / 8.4988     0.353
non-representative 1.5×  5.7493 / 9.1599    5.7488 / 9.1732     0.323
```

**The choice between A and B is insensitive to this axis** (the gap stays ≤0.001 in the mean at every
scale), while the *value of holding a diverse pair* rises steeply with it. So the axis that was expected to
discriminate between the two pairs instead discriminates between "diverse pair" and "single line".

## 6. Teammate provenance — available vs unavailable

Modelled as a hard selectability constraint, not a score penalty:

```
teammate selectable = True   -> pool 7, best by mean: 54844628 + 54896975  (6.1871 / 8.4941)
                                best OURS-ONLY pair:  54844628 + 54968060  (6.1872 / 8.4801)
teammate selectable = False   -> pool 4, best by mean: 54844628 + 54968060  (6.1827 / 8.4863)
```

**Losing access to every teammate submission costs about 0.004 ft in the mean and nothing in the tail.** The
ours-only optimum is the same pair B that ownership-first already recommends.

Q38 has since made this axis largely counterfactual: `54922806`'s kernel slug, `scriptVersionId 337355891`,
version count and full source were all recovered and archived, which closed Q30's actionable provenance
caveat. **One residual remains and it is not closed:** the kernel has 7 versions, we hold the latest, and
Q38's question to the teammate — *were any of these kernels edited or re-run after the submission?* — is
unanswered. That is a live, non-hypothetical instance of "provenance unavailable", and §6 prices removing it
at ~0.004.

## 7. Frontier public-derived dependency risk — the axis that does not discriminate

Two distinctions matter and were not separated before:

- **A banked private score cannot be changed by a dependency.** The submission file is already scored on all
  test rows; the private figure is computed and hidden, not recomputed at the deadline. Deleting
  `fleongg/rogii-claude-models-pub` tomorrow would not move any recorded private score.
- **Where dependencies bite is verification and disclosure.** Per Q30/G1.3: the frontier carries **two**
  prediction-affecting third-party artifacts (`ravaghi/wellbore-geology-prediction-artifacts` and
  `fleongg/rogii-claude-models-pub`, learned-trajectory weight 0.40) plus derivation from a public notebook;
  the honest line carries **one** (`ravaghi/...`).

**Both recommended pairs contain `54844628` and exactly one frontier member, so their dependency sets are
identical.** This axis therefore does **not** discriminate between A and B — and it should stop being cited
as though it favours either. It does discriminate between *any* recommended pair and a frontier-only pair,
which §4 already rejects on far larger grounds.

Also worth keeping visible: **neither slot is dependency-free.** `ravaghi/...artifacts` is required by the
honest line, and Q30 recorded the one unverified provenance link — that dataset ships a `data/train.csv`
described in our own kernel as a cache — as still unverified. It is **common to both pairs**, so it is a
team-level disclosure item, not a slot-selection input.

## 8. Board-level reshuffle at our position

Local board density from the Q45 refresh plus the external snapshot (~570 teams inside ±0.037 ft of 6.473;
ranks 190–200 spanning 0.007 ft): **≈7700 teams per ft** near 6.47–6.57.

```
a private shift of 0.030 ft (public measurement sd) ~   231 ranks
a private shift of 0.500 ft                         ~ 3851 ranks
a private shift of 2.400 ft (the draw sd)           > the entire board
our rank 1339 / 5914 | bronze 6.470 | our public 6.563 -> gap 0.093 ft ~ 716 ranks
```

Two readings, and the second is the one that matters:

1. **In score units the slot-1 dispute is negligible; in rank units it is not.** A 0.077 ft price is ~590
   ranks at this density. That is the honest counterweight to §3 and it is why ownership-first is argued
   below on *evidence and risk*, not on "0.077 is small".
2. **The draw dominates anyway.** One sd of draw noise exceeds the whole board's width at this density, so
   the naive extrapolation breaks — which is itself the finding: at rank 1339 in a band this dense, the
   private ordering is set by the draw, not by a stage term.

**The caveat that must accompany this, and it cuts in our favour:** all teams shift together, so rank
movement depends on our shift *relative* to the crowd. The top-200 board is dominated by the same public
family our frontier line belongs to, so most rivals' shifts are strongly correlated with our frontier slot —
inside that family, relative movement is small. **`54844628` is the one submission whose error is
decorrelated from the crowd** (2.54 ft output disagreement, Q18's 29% independent-reversal rate). Under
best-of-2 we keep its upside without wearing its downside. The diverse pair is therefore not only the
best-valued pair for our own score (§4) — it is the only source of *relative* rank movement we hold.

## 9. Deliverable (task step 4) — when ownership-first should override score-first

**Override — the conditions, in decreasing strength of evidence:**

1. **When score-first's discriminator is not a measurement.** Its entire case is the 0.080 public gap between
   `54922806` (6.563) and `54968060` (6.643). Q45's measured floor puts a same-code rerun sd at 0.03, so
   0.080 is **2.7 sd — below the 3 sd (~0.09) needed to rank two variants at all.** Q39 decomposes the gap
   into GR-sigma (−0.1105, 3.7 sd, resolvable on public) and overlap (+0.031, ~1 sd, noise). So the *only*
   resolvable component is the GR-sigma term — and **Q36 measured that exact multiplier on 760 wells with
   truth: it helps 42.1% of wells with a negative median per-well gain.** Under the private objective (novel
   wells) score-first's advantage rests on the one mechanism our own held-out evidence says does not
   transfer. **This is the primary condition and it currently holds.**
2. **When the teammate kernel's post-submission state cannot be confirmed.** Q38's question is unanswered;
   §6 prices removing that exposure at ~0.004 ft. **Currently holds.**
3. **When any non-trivial weight is placed on winner-obligation friction from a teammate-run kernel.** The
   price is bounded at +0.077 mean / +0.065 p95 worst-case across all 24 cells and +0.0013 in the
   evidence-supported cell. There is no cell where it exceeds 0.078.
4. **When retrieval might fail non-benignly.** In all four `+0.200` spurious-match cells and all
   `retrieval ≥ 0` + `sigma_transfers=False` cells, ownership-first is **strictly better** (up to −0.157).

**Do not override on these grounds:**

5. **Not on dependency risk** — §7: both pairs carry identical dependency sets.
6. **Not on draw representativeness** — §5: the A-vs-B gap is ≤0.001 at every draw scale.
7. **Not by dropping the honest slot to make room** — §4: that costs ~0.46 ft in the mean and ~0.94 in the
   tail, 6× the entire slot-1 argument. **Whatever happens in slot 1, `54844628` holds slot 2.**

**Net recommendation, and it is a change in framing rather than in the pair:** score-first and
ownership-first are **not** separate criteria that must be traded off — score-first's discriminator is at
2.7 sd and its only resolvable component is measured not to transfer. They are therefore **tied on
measurement**, and a tie should be broken by the axis that is not noise-limited: ownership and verifiability.
On that reading `54968060` + `54844628` is at least as good as `54922806` + `54844628` on private, and
strictly better in 8 of 24 modelled cells.

**This remains the owner's decision** and is presented as such: the two pairs differ by ≤0.077 ft in every
modelled cell, which is inside the resolution of every instrument available. What Q44 changes is that
"score-first" can no longer be cited as the *stronger* criterion, because its input is below the measured
resolution.

## 10. Negative results

- **No axis was found that separates the two candidate pairs by more than 0.077 ft** in any of 24 cells. The
  slot-1 question is not resolvable by any modelling this project can do; it is a judgement.
- **The dependency-risk axis, which the task asked to stress, turns out not to discriminate at all** (§7).
- **The draw-representativeness axis also does not discriminate** between the pairs (§5), contrary to the
  expectation behind including it.
- **The provenance-availability axis is nearly free** (~0.004), so it cannot carry an argument by itself —
  its force in §9 comes from evidence about the GR-sigma mechanism, not from the constraint's price.

## 11. Limits

- Everything is arithmetic and Monte Carlo over **already-recorded public scores**. No new measurement was
  made, and no private information exists.
- `σ_diff = 2.40` is calibrated from Q18's single measured statement (29% reversal at a 1.328 gap) and is
  corroborated by one independent quantity (2.54 ft output disagreement). It is **one** calibration, and the
  Gaussian shape is an assumption — real 3-well draws are heavy-tailed, which would *increase* the value of
  the diverse pair in §4, not decrease it.
- **Family shocks are modelled as independent.** Frontier and honest predictions correlate ~1.0 trivially
  (both track well depth); what matters is *error* decorrelation, for which Q18's 29% is the anchor. If the
  two lines' errors are more correlated than that implies, §4's 0.456 shrinks.
- The `+0.200` spurious-retrieval arm is a stress, not a measurement, and is labelled as such throughout.
- `54853492` is excluded from every view by standing instruction.
- Board density is a local linearisation from two snapshots; §8 states explicitly where it breaks.

## 12. Next

`q46_submission_asset_inventory` (priority 650) is next in the queue; `q57_dip_state_augmented_dp` (628) and
`q56_pf_backward_smoothing` (627) sit ahead of it by priority. `q29_final_slot_candidate_packager`
reactivates **2026-08-03**; the final selection action is due by **2026-08-04**, costs no quota, and per §9
should record which of the two tie-broken pairs the owner chooses and on which of the four override
conditions.
