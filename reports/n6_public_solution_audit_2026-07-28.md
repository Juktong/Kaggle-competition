# N6 — audit of a second public solution, 2026-07-28

Autopilot task `n6_public_solution_audit` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`).
No submission; quota untouched at 0/5.

## 0. Blocker on the named target, and what was audited instead

The task names `aaryan2203/rogii-wellbore-geology-prediction-argon`. **That repository does not exist.**

```
gh api repos/aaryan2203/rogii-wellbore-geology-prediction-argon  ->  404 Not Found
gh api users/aaryan2203/repos  ->  CyForixx, Devii, Leet-Code, PixieBunnies, reminder-  (none ROGII-related)
gh search repos "rogii argon"  ->  []
```

The name entered our queue from a web-search snippet in the `new_direction_search` round; the snippet was
stale or fabricated by the search engine. **Recorded as a blocker on the literal target.** Rather than
stop, the task's stated intent — *survey a second public solution for formulations not in our ledger* —
was executed against the highest-signal real candidate found by repository search:

**`mycarta/rogii-geosteering-toolkit`** — "Domain-aware toolkit and methodology for the ROGII Wellbore
Geology Prediction Kaggle competition", MIT licence, 6 stars, last updated 2026-07-26. It is the only
public ROGII repository carrying written methodology notes rather than just a notebook dump. (Runner-up
`tom99763/rogii-viewer`, 22 stars, is a PySide6 results viewer — a tool, not a method. The remaining ~13
hits are unannotated student repos.)

### Rule basis for the constraint

The task carries "methods and code only; no external training data or public dataset before the rules are
confirmed". **Complied with as follows:** only the README, two methodology markdown files, and source
headers were read, all via the GitHub API. **No data was imported and no code from the repository was
executed** — the required-execution item 4 is satisfied literally. Reading a public solution's method is
the same class of action already accepted for the public Kaiwalya notebook that our `54896975`/`54968060`
family derives from. The repository is MIT-licensed, so reuse of its code would be permitted with
attribution; nonetheless the queued follow-ups below specify implementing from the **cited paper** rather
than copying, to keep provenance clean.

## 1. Where this pipeline sits relative to ours

Their own note records the state of their line: *"the super-baseline architecture + GroupKFold + delta
target hits OOF 10.5 and the public LB has clones around 12."* No final leaderboard score is published in
the repository.

```
their reported stage : OOF ~10.5, public LB clones ~12
our honest line      : OOF  8.8626, public 7.891   (54844628)
our frontier slot    :                public 6.563 (54922806)
```

**The repository is a source of formulations and independent cross-checks, not of a stronger pipeline.**
That framing governs everything below.

## 2. Component-by-component against our evidence ledger

| Their component | Our status |
|---|---|
| **G1** Multi-scale NCC vs typewell GR (12 feats) — called their "primary signal" | **Tension with our evidence.** N3 (today) measured NCC at chance (0.490–0.517) across 9 wavelet bands × 6 window widths on held-out wells; the closed local-window scorer line had NCC 0.524 = chance. Reconciliation: theirs is a *sliding-profile peak* feature (peak value, location, sharpness) fed to LightGBM, not a scalar similarity. The peak-location content was, however, effectively exercised by G3.1's DP over an NCC-style cost matrix, which "converged to flat-anchor from ABOVE and never crossed". **Substantially covered; not queued.** |
| **G2** Multi-scale NCC vs the lateral's **own** known zone (self-correlation) | **Not yet tried.** Distinct from the closed G3.5, which used the prefix to calibrate *bias*; this uses prefix GR as a higher-resolution matching *template*. Synergises with N3's finding that the **level** cue dominates — self-correlation shares one instrument and one baseline, so it removes the cross-instrument level offset entirely. **Queued (N9).** |
| **G3** Anchor + position | **Deployed** — our heel anchor. |
| **G4** Trajectory + structural elevation, **lateral-only** fit with R² fallback | **Consistent with ours, and explains two of our negatives** — see §3. |
| **G5** Local GR statistical features | **Deployed** — our DWT feature stack. |
| **G6** Q-3D tortuosity, Jing et al. (2022), 7 feats — **their largest single-group gain, −0.107 RMSE** | **Not yet tried anywhere in our ledger.** Computable from MD/X/Y/Z alone, so fully test-available. **Queued (N7).** |
| **G7** Per-formation GR classifier from typewell `Geology` — **they DROPPED it** | **Independently consistent with our M1**: `Geology` is absent from the *test* typewell schema (`TVT,GR` only). Our related facies-marker / structural-surface-label line is already closed. No action. |
| **G8** Catch22 well-level features (AEON, 46 feats) — **DROPPED, made it +0.476 RMSE worse** | **Independent confirmation of our closed SSL/ROCKET line.** Their stated cause — well-level features under GroupKFold-by-well overfit incidental cross-well correlations — matches our own experience. No action. |
| **G9** ClaSPSegmenter typewell segmentation — DROPPED | Overlaps the segmentation idea folded into N1. No action. |
| **G10** dcor scalar — DROPPED | No action. |
| **G11** Segment-well decomposition (three-thirds TVT-vs-MD fit) | **Not yet tried in that form**, but closely related to M4, which closed the whole-well dip fit (oracle 7.65 vs honest prefix-fit 80.29 against a flat anchor of 15.91). Low expected value. Not queued. |
| **G12** Offset-well prior from spatially-close, **azimuth-matched** neighbours | **Deployed and validated in part** — our structural field is the only cross-well component with a confirmed honest gain (+0.436 OOF). But our neighbour selection uses typewell-group + XY distance and **ignores azimuth**. Azimuth matching is a genuine missing ingredient. **Queued (N8).** |
| **G13** Landing-zone state (last 50–100 ft before prediction start) | **Partially deployed** — our anchor averages the last 100 known rows, but we expose no landing-state *features*. Low marginal value on top of the anchor. Not queued. |
| **G14** Well-length / heel-to-TD geometry | Trivially available; our N4 already measured these as carrying almost no per-well information (CV R² 0.074). Not queued. |
| **G15** Vintage features conditional on `seq_id` ordering | **Not queued on principle.** Ordering-derived features are leakage-adjacent and would need a rules check before use. |
| **CV**: StratifiedGroupKFold(5) by well, strata = signed-azimuth quadrant × median-TVT bin × 2×2 XY grid | Different from our plain well-level nested OOF. A reasonable refinement, but our binding constraint is the **3-well gate**, not the CV scheme — N4 measured a fixed model's 3-well draw spanning 3.49→15.14, which dominates any CV-stratification refinement. Noted, not adopted. |
| **Spatial CV (Verde BlockKFold) considered and rejected** because validation wells are spatially *interleaved* with training wells — interpolation, not extrapolation | **Directly relevant to our H-visible / H-hidden fork.** An independent reader of the same data concluded the evaluation regime is interpolation among known wells. That leans toward the H-visible branch of our final-slot framing. Recorded as evidence; it does not change the slot recommendation, which is already robust across both hypotheses. |

## 3. The finding that pays for this audit: within-well TVT–Z decoupling

Their headline geological note measures the TVT-vs-Z relationship at two different scales:

- Global, across all 773 wells: **r = −0.96** — but this is a *between-well* structural-elevation signal,
  dominated by the build section's thousands of feet of Z drop.
- Within a single well's **lateral only**: essentially zero, **mean per-well slope +0.057** (their
  methodology note quotes ~−0.14 on a different subset). ΔZ across the eval zone is ~70–125 ft while
  ΔTVT is ~5–13 ft — largely independent causes.

**This independently explains two of our own negative results from today:**

1. **`new_direction_search` M4.** Our geometry-only arm imposed `TVT = −Z + const`, i.e. a within-lateral
   slope of exactly −1, and scored **107.49** against a flat anchor of **15.91**. If the true
   within-lateral slope is ≈0, a slope of −1 is close to the worst possible choice — which is exactly the
   magnitude of failure observed.
2. **N1's centring arm.** N1 centred the DP transition on `c = −dZ/STEP`, which presumes the formation is
   flat so that TVT moves one-for-one against Z. On 40 wells that centring *hurt* (15.636 vs the
   unbounded control's 12.518). With the true within-lateral slope near zero, centring on the full `−dZ`
   systematically overcorrects — a mechanism N1 recorded empirically but did not explain.

Both of our measurements stand as recorded; this supplies the *why*. The general lesson they state is
worth adopting verbatim: **when a global correlation motivates a per-unit feature, first decompose whether
the correlation is global because of cross-unit structure or within-unit structure.**

## 4. Items queued

Only items that are (a) absent from our ledger and (b) cheap were queued.

| pri | id | why | smallest smoke |
|---|---|---|---|
| 170 | `n8_azimuth_matched_neighbours` | One-factor change to the **only** cross-well component with a confirmed honest gain (+0.436 OOF). The N2 round left a **byte-exact reimplementation** of that builder, so the change is a few lines. | Add an azimuth-similarity filter to neighbour selection, hold gate/W/IDW/anchor fixed, nested OOF on the 760-well split, then `scripts/eval_three_well_gate.py`. |
| 180 | `n7_q3d_tortuosity_features` | Their largest single-group ablation gain (−0.107 RMSE) and absent from our ledger. Computed from MD/X/Y/Z only → fully test-available. | Implement `TQG_Q3D` from Jing et al. (2022) on ~40 wells, correlate against per-well honest OOF residual, and only then consider adding it to the DWT feature stack. |
| 190 | `n9_self_correlation_prefix_template` | Not tried; synergises with N3's result that the **level** cue dominates, and self-correlation removes the cross-instrument level offset by construction. | Score toe rows against the well's own known-zone GR at matching TVT; report held-out-**well** AUC against N3's `TWH=1` baseline of 0.7655. |

Not queued, with reasons, in the table of §2: G1 (covered by G3.1/G3.2/N1), G7/G8/G9/G10 (they dropped
them and our ledger agrees), G11 (covered by M4), G13/G14 (marginal; N4 measured these features at CV
R² 0.074), G15 (leakage-adjacent, needs a rules check), CV scheme (dominated by the 3-well gate).

## 5. Verdict

- The named repository does not exist; the blocker is recorded and the task's intent was executed against
  a real, higher-quality target.
- No component of the audited pipeline beats ours — their reported stage is OOF ~10.5 / LB ~12 against our
  8.8626 / 7.891 / 6.563.
- The audit's value is three-fold: **three independent confirmations** of our closed lines (Catch22
  ≈ SSL/ROCKET, `Geology` unusable at test time, spatial-CV interpolation regime), **one mechanistic
  explanation** for two of our own negatives (within-well TVT–Z decoupling), and **three queued
  formulations** absent from our ledger.
- No submission, no data import, no code execution from the repository.
