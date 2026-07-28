# New direction search — 2026-07-28

Autopilot task `new_direction_search` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`).
All queued implementation tasks (G3.5, G1.3, G3.2, G3.3, variant matrix) are complete, so the search
space is expanded here.

This round is **not** a literature list. Five cheap measurements were run first, because three of them
changed the ranking of the directions they bear on. Every number below is honest (prefix-only inputs,
hidden-toe scoring on the 760+ well train split) and reproducible from the two scripts committed with
this report.

---

## Part 1 — Measurements taken this round

### M1. Test-available field inventory (direct column check, first time done exhaustively)

```
train/<w>__horizontal_well.csv : MD,X,Y,Z,ANCC,ASTNU,ASTNL,EGFDU,EGFDL,BUDA,TVT,GR,TVT_input
test /<w>__horizontal_well.csv : MD,X,Y,Z,GR,TVT_input
train/<w>__typewell.csv        : TVT,GR,Geology
test /<w>__typewell.csv        : TVT,GR                 <-- no Geology column at all
```

Confirms the six structural-surface columns are train-only, and establishes for the first time by direct
check that **`Geology` is absent from the test typewell schema** — it is a train-only supervision source,
not a test input. Test-available inputs are exactly `MD, X, Y, Z, GR, TVT_input` on the well plus
`TVT, GR` on the typewell.

### M2. The 773 train PNGs carry no information beyond the CSVs

`train/` holds 773 `<well>.png` and `test/` holds **none**. Reading one shows a rendered figure: GR log,
well-path projection with the six structural surfaces, and two TVT panels — all reconstructible from the
CSVs. The only content *not* in the CSVs is the figure title:

```
Well: Well10784 | Typewell: Typewell20030 | Azimuth = 86.50°
```

Azimuth is derivable from X/Y and the prediction-start MD from `TVT_input`. That leaves the
**well/typewell names** as the sole novel field — and no test well has a PNG, so it is unavailable at
prediction time. **Images are ruled out as an input modality** (see N-x1 below).

### M3. Typewell sharing is too sparse to serve as a grouping key

Hashing all 773 train and 3 test typewell files:

```
773 train wells -> 752 distinct typewell files
group sizes: {1: 739 wells, 2: 12 wells, 10: 1 group}
test 000d7d20 / 00bbac68 / 00e12e8b -> 0 train wells share the typewell byte-identically
```

96% of wells have a private typewell, and **none of the three test wells matches any train typewell
exactly**. Exact-identity grouping is therefore not usable; the near-match variant survives but its
value is capped by this distribution (see N5).

### M4. Geometric reparametrization — the oracle/achievable gap appears again

TVT is a stratigraphic thickness, so along a *known* well path it satisfies
`dTVT = -dZ + tan(δ)·dH`, where `dZ` and `dH` are known exactly at every row (X/Y/Z are test-available)
and `δ` is the local apparent dip. If `δ` were near-constant per well, TVT would collapse to a
2-parameter object. Measured apparent dip across 120 wells: **−3.15° to +3.69°**, and removing one
constant dip per well leaves a residual of median **7.11 ft** std. So the geometry does carry most of
the structure. Honest test (`scripts/nds_geometry_reparam_probe.py`, 773 wells, hidden-toe rows,
row-weighted RMSE):

```
flat anchor (carry last known TVT)                 15.9099
geometry only, zero dip                           107.4948
geometry + prefix-fit constant dip     [HONEST]    80.2886
geometry + dip fit on last 30% of prefix [HONEST]   39.5725
geometry + ORACLE whole-well dip   [upper bound]    7.6546
```

The oracle beats the flat anchor by more than 2× (7.65 vs 15.91), and every honest estimator of the same
single parameter is 2.5–5× **worse** than the flat anchor (prefix-fit beats flat on only 14.1% of wells,
recency-fit on 25.7%). **The whole-well apparent dip is not prefix-observable.** This is the fifth
independent instance of the project's recorded pattern — a large oracle margin with no achievable margin
— and it is consistent with the banked finding that the dominant residual component is drift along the
toe (slope std 13.28 ft), which truth-stops-at-the-heel makes unobservable. Direction closed on
evidence in its single-dip form.

### M5. Naive neighbour dip-field — fails; the refined form is what remains open

The banked evidence says the dominant remaining error is **drift** (slope std 13.28 ft), not initial
**level** (std 4.72 ft), yet the only cross-well component that ever produced a confirmed honest gain —
the deployed structural field in `54844628` (+0.436 OOF) — interpolates *level*. The obvious
reformulation is to interpolate the *increment* from the heel anchor instead. Probed with a plain
neighbour plane fit (`scripts/nds_dipfield_probe.py`, K=12 neighbours, 150 ft duplicate guard, 759
wells):

```
flat anchor (carry last known TVT)     15.9793
neighbour LEVEL field, standalone     189.0324
neighbour DIP field (anchor + drift)   64.5711
flat + 0.15*LEVEL                      31.6072
flat + 0.15*DIP                        18.2291
flat + 0.50*DIP                        34.8150

per-well gain of flat+0.15*DIP vs flat: mean -1.9476, median -0.7336, frac>0 0.404
3-WELL bootstrap (the scored scale): 5th -8.1771  50th -1.3783  95th +3.0101  P(gain>0) 0.314
```

Every form is worse than the flat anchor. **This does not contradict the deployed field's +0.436** — the
deployed field is group-anchored, IDW-weighted and applied at W=0.15 only on gated rows (nnb≥4 AND
closest surviving mate <1000 ft, 87% of rows), whereas this probe is an ungated global plane over an
8000 ft radius. The measurement's actual content is that **the naive plane formulation is not the
carrier of the idea**; the increment target has to be tested inside the deployed machinery, which is
exactly what N2 specifies. Recorded so that the naive form is not re-attempted.

---

## Part 2 — Candidate directions

Six directions queued, four explicitly not queued. Ordered by (value ÷ cost).

### N4 — Calibrated per-well uncertainty via split conformal on the banked OOF
- **Why it applies.** The variant-matrix round found per-well confidence gating to be an axis the
  frontier never exposes, and the final decision is a *pair* choice under two hypotheses (H-visible /
  H-hidden). A calibrated per-well risk estimate is decision-relevant even with zero score change.
- **How it differs from tried methods.** The closed anti-harm guard (AUC 0.53) tried to predict the
  *sign* of a candidate's harm — a hard, poorly-posed target. This estimates the *width* of the honest
  model's own error distribution conditioned on test-available well features, which is a well-posed
  quantity with a distribution-free coverage guarantee.
- **Smallest smoke.** Split-conformal intervals from the banked 760-well OOF residuals, conditioned on
  `nnb`, closest-mate distance, prefix fraction and GR variance; check empirical coverage at 80/90/95%.
- **Expected cost.** Minutes, CPU. The OOF is already banked; no new model fit.
- **Submit relevance.** None — decision support for slot selection and for any future gating axis.
- **Queue.** Yes, priority **110**. Cheapest item with direct decision value.

### N2 — Increment-target refinement of the deployed structural field
- **Why it applies.** Attacks the drift component that holds the dominant share of the residual, using
  the one cross-well construction with a confirmed honest gain.
- **How it differs.** The closed spatial-KNN line and the `54878409` anisotropic attempt both changed
  the *kernel*; the target stayed the TVT level. This changes the *target* to the heel-referenced
  increment while holding the gate, the group anchor, the IDW kernel and W fixed at their deployed
  values — so the comparison isolates one factor.
- **Smallest smoke.** In the existing structural-field builder, swap the interpolated quantity for the
  increment; keep gate and W unchanged; score nested OOF on the same 760-well split, then run
  `scripts/eval_three_well_gate.py`. Report both the 760-well reference and the 3-well gate.
- **Expected cost.** Half a day, CPU, no quota. Prior: M5 shows the naive form fails, so the smoke must
  be read as a genuine test rather than a formality.
- **Submit relevance.** Medium-high — it improves the honest line, which is the provenance-first slot.
  Any submission still requires the 3-well gate plus the submit gate.
- **Queue.** Yes, priority **120**.

### N1 — Geometry-bounded monotonic alignment (slope-constrained DP)
- **Why it applies.** G3.2 produced the alignment line's first positive result: learned scorer AUC
  **0.7242** vs NCC 0.5010, and its DP beat the flat anchor (12.527 vs 13.103, interior optimum at
  lam=60). It remained ~42% above the deployed ~8.86, so the formulation needs a constraint, not more
  capacity.
- **How it differs.** The depth-matching literature is explicit that an admissible warping path needs
  strict monotonicity **and slope constraints** to stay geologically plausible and to avoid singularity
  artifacts. G3.2's DP had only a flat-anchor regulariser. The new ingredient is that the slope bound
  here is not a hyper-parameter — M4 measured the physically admissible apparent-dip range (≈±3.7°),
  and `dZ`/`dH` are known per row at test time, so each row gets a **hard, test-available admissible
  band** on the warping slope. That constraint has never been applied.
- **Smallest smoke.** Re-run `scripts/g32_learned_alignment_smoke.py` with a per-row admissible band on
  the DP transition; sweep the band width; compare on the *same* wells against the recorded 12.527 /
  13.103.
- **Expected cost.** 1–2 h, CPU.
- **Submit relevance.** None until the gap to ~8.86 closes.
- **Queue.** Yes, priority **130**.

### N3 — Coarse-to-fine multi-scale GR matching
- **Why it applies.** The closed local-window learned GR scorer line was closed with a *named* cause: a
  ~34× vertical scale mismatch in the pairing, with an NCC baseline of 0.524 ≈ chance. Multilevel
  wavelet decomposition followed by coarse-to-fine matching is the standard remedy for exactly that
  failure, and it addresses the stated cause rather than working around it.
- **How it differs.** Every previous attempt matched at a single scale. The repo's own base model is a
  DWT fork, so the decomposition machinery already exists.
- **Smallest smoke.** 4-level DWT of target GR and typewell GR; compute the scorer AUC **per level**;
  report whether any level exceeds G3.2's single-scale 0.7242. Purely diagnostic — no model training.
- **Expected cost.** ~1 h, CPU.
- **Submit relevance.** None directly; it would feed N1.
- **Queue.** Yes, priority **140**.

### N6 — Audit of a second public solution (`aaryan2203/rogii-wellbore-geology-prediction-argon`)
- **Why it applies.** We already integrated and audited one public solution (Kaiwalya, `54896975` /
  `54968060` family). A second independent public solution is a cheap source of formulations and an
  independent check on which of our closed lines others also found unproductive.
- **How it differs.** Not a method — a survey with a defined output: a diff of its approach against our
  evidence ledger.
- **Smallest smoke.** Read the repo's method description; produce a table of {its component → our
  evidence status}. No code execution, no data import.
- **Expected cost.** Minutes.
- **Submit relevance.** None directly. **Constraint carried explicitly:** methods and code only — no
  external training data or public dataset is to be used before the competition rules are confirmed and
  the rule basis is written down.
- **Queue.** Yes, priority **150**.

### N5 — Typewell-fingerprint well families (near-match)
- **Why it applies.** The typewell file *is* a test-available input and encodes the stratigraphic column
  the interpreter used. Wells sharing a column are the strongest possible analogue set.
- **How it differs.** The closed spatial-KNN line grouped by distance; this groups by column identity.
- **Bounded by M3.** Exact grouping is unusable (739/773 wells private; 0/3 test wells match). The
  near-match variant survives but its upside is capped by that distribution, so it is queued as a
  time-boxed check rather than a development line.
- **Smallest smoke.** Correlate each test typewell's GR-vs-TVT curve against all 773 train typewells on
  the overlapping TVT range; report the top-5 matches, their correlation, and **whether the matches are
  already spatial neighbours** — i.e. whether it adds anything over the deployed spatial gate. Stop at
  30 minutes.
- **Expected cost.** Minutes.
- **Submit relevance.** None directly; would feed a router or gate.
- **Queue.** Yes, priority **160**, time-boxed.

---

## Part 3 — Considered and not queued, with reasons

### N-x1. Train-only PNG images as an input modality
Not queued. M2: `test/` contains no PNGs, and the image content is a render of the CSVs. The only
non-CSV field is the well/typewell name, unavailable at prediction time. There is no input path.

### N-x2. Sequential-decision / reinforcement-learning geosteering
Not queued. The published RL geosteering formulations optimise a *drilling action* under sequential
feedback. This competition asks for an offline batch prediction of the entire hidden toe at once, with
no action space and no feedback loop. The formulation does not map onto the task.

### N-x3. Azimuthal-GR dip inversion
Not queued. The published dip-from-GR methods rely on azimuthal or multi-detector GR images to resolve
the bed inclination. The dataset provides a single scalar `GR` per MD row (M1). The required measurement
is absent, so the method cannot be instantiated regardless of merit.

### N-x4. Semantic-segmentation stratigraphic correlation as a separate line
Not queued as its own item. Its usable content — a segmentation of the well into constant-dip segments
used as a prior — is the same constraint N1 applies through the admissible band, and its marker labels
would come from the train-only structural surfaces. Folded into N1 rather than duplicated.

---

## Summary

- Five measurements, three of which changed a ranking: images ruled out (M2), typewell grouping capped
  (M3), and the single-dip geometric reparametrization **closed on evidence** (M4: oracle 7.65 vs honest
  80.29 against a flat anchor of 15.91).
- M5 records that the naive plane form of the dip-field idea fails (3-well P(gain>0) = 0.314) while
  isolating the specific refined form that remains open — the content of N2.
- Six directions queued at priorities 110–160, each with a smoke that runs on CPU with no quota.
  N2 is the only one with a plausible path to a submission; the rest are diagnostics or decision support.
- No submission this round (`can_submit=false`, 0/5 quota used). The slot recommendation is untouched:
  `54922806` + `54844628` under all three criteria.

Reusable artifacts: `scripts/nds_geometry_reparam_probe.py`, `scripts/nds_dipfield_probe.py`.
