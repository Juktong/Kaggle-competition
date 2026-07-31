# Q42 — honest-line error taxonomy: most of the apparent structure is well-level sampling noise

Date: 2026-07-29 17:55 UTC
Task: `q42_honest_line_error_taxonomy` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q42_error_taxonomy.py` · Log: `reports/logs/q42_taxonomy_2026-07-30.log`
Outcome: **line closed. No group-level intervention proposed. No submission. Quota 0/5.**

## 1. The taxonomy, in-sample

Deployed line `54844628`: pooled RMSE 8.8626, mean signed residual **−0.3832**, median −0.1533. Mean
signed residual by quintile of each test-available segment (760 wells, 3.72M rows):

```
feature                    q1        q2        q3        q4        q5     spread
struct_contrib         -0.016    +0.033    -0.288    +0.016    -1.662     1.694
well_md                +0.419    -1.175    -0.223    -0.526    -0.419     1.594
prefix_frac            -0.420    -0.471    -0.402    +0.296    -0.916     1.212
mean_incl              -0.627    +0.393    -0.557    -0.399    -0.728     1.120
nnb                    -0.281    +0.002    -0.623    -0.838    -0.175     0.840
dwt_pf_disagree        -0.196    -0.133    -0.090    -0.573    -0.924     0.833
tortuosity             -0.073    -0.365    -0.294    -0.283    -0.905     0.832
closest_surv           -0.295    -0.267    -0.138    -0.769    -0.445     0.631
gr_std_toe             -0.463    -0.531    -0.088    -0.152    -0.682     0.594
gr_std                 -0.261    -0.516    -0.480    -0.051    -0.609     0.559
closest_all            -0.208    -0.590    -0.118    -0.433    -0.567     0.471
rows_from_anchor       -0.167    -0.402    -0.440    -0.514    -0.394     0.347
row_frac               -0.282    -0.388    -0.466    -0.395    -0.386     0.184
```

Spreads of 0.5–1.7 ft look like real structure. **Most of it is not.**

## 2. Split-half test — which segments actually reproduce

The taxonomy was recomputed on two **disjoint halves of 380 wells each**:

```
feature             corr(A,B)   max|diff|
dwt_pf_disagree        +0.815       0.373   <- reproduces
struct_contrib         +0.802       1.213   <- reproduces (pattern), magnitude varies 2x
tortuosity             -0.162       1.084
prefix_frac            -0.270       1.573
well_md                -0.290       2.235
nnb                    -0.566       1.226
mean_incl              -0.648       1.874
closest_all            -0.751       1.615
```

**Only 2 of 8 reproduce, and they are exactly the two ROW-level features.** Every **well-level** feature
*anti*-correlates across disjoint well halves — their quintile patterns flip sign, which is what noise
does, not what structure does.

### The arithmetic that explains it

```
per-well mean residual: std across wells = 6.673
wells per quintile     ~ 152
=> standard error of a group mean ~ 6.673 / sqrt(152) ~ 0.54
```

The observed spreads for the well-level features (0.47–1.59) are **the size of their own standard error**.
Rows within a well are strongly correlated, so binning by a well-level feature gives an effective sample
size of **152 wells, not 744,000 rows**. The apparent taxonomy is well-level sampling noise dressed as
segment structure.

**Proposed standing rule:** *when segmenting residuals by a WELL-level feature, the effective n is the
number of wells in the bin, not the number of rows. Compare any observed spread against σ_well/√n_wells
before treating it as structure.*

## 3. Out-of-fold group-constant corrections — 2 of 13 positive, none actionable

Estimate each group's mean signed residual on train wells, subtract it on held-out wells,
`GroupKFold(5)` by well:

```
feature              OOF RMSE    vs base    helps%  3-well 5th
struct_contrib         8.8562    +0.0065     46.3%     -0.5101   <- best
row_frac               8.8624    +0.0003     48.6%     -0.2614
rows_from_anchor       8.8639    -0.0013     49.1%     -0.2718
well_md                8.8660    -0.0034     48.8%     -0.4320
dwt_pf_disagree        8.8695    -0.0069     48.8%     -0.3625
...
mean_incl              8.9044    -0.0418     47.5%     -0.4231
```

| gate condition | required | observed (best) | verdict |
|---|---|---|---|
| OOF gain | > 0 | **+0.0065** | PASS (negligibly) |
| helps a majority of wells | > 50% | **46.3%** | FAIL |
| 3-well bootstrap 5th | > 0 | **−0.5101** | FAIL |

**Segments with a positive OOF gain: 2 of 13. Segments clearing the 3-well 5th: 0 of 13.** Not one segment
helps a majority of wells — the maximum across all thirteen is 49.1%.

Note that even the two *reproducible* segments do not deliver: `struct_contrib` gives +0.0065 and
`dwt_pf_disagree` gives **−0.0069**. The pattern reproduces; its magnitude is too small and too unstable
(A: −2.18 vs B: −0.97 in q5) for a constant correction to pay.

## 4. The question the task asked: does coarsening rescue Q16?

Q16 found the **row-level** signed residual unpredictable: CV R² = **−0.0802**, i.e. the fitted structure
*anti-transfers*. Group-level constants are a far lower-variance estimator, so this was a real hypothesis.

```
struct_contrib     OOF R^2 = -0.00042
row_frac           OOF R^2 = -0.00181
rows_from_anchor   OOF R^2 = -0.00217
well_md            OOF R^2 = -0.00263
dwt_pf_disagree    OOF R^2 = -0.00342
closest_all        OOF R^2 = -0.00640
Q16 reference (row-level GBM, same protocol): -0.0802
```

**Coarsening changes the failure mode but not the conclusion.** R² moves from −0.0802 to ≈ **−0.001**, so
the coarse estimator has essentially eliminated the over-fitting that made the GBM anti-transfer — but it
converges to **zero**, not to a positive value. There is no usable signed-residual signal at group level
either; the earlier result was not merely an artefact of an over-flexible model.

That is a sharper statement than Q16 alone could make: the row-level failure was *both* over-fitting *and*
absence of signal, and removing the over-fitting exposes the absence.

## 5. Deliverable — the line is closed, with no interventions proposed

Step 4 asks for 3–5 candidate group-level interventions **or** closure. **Closure**, for reasons that are
structural rather than marginal:

1. **11 of 13 segments have a negative OOF gain**; the best is +0.0065 on an 8.86 RMSE — 0.07%.
2. **No segment helps a majority of wells** (max 49.1%), so any correction is a coin flip per well.
3. **0 of 13 clear the 3-well 5th percentile**, consistent with Q41's finding that the 3-well 5th is
   maximised by leaving the deployed line unchanged.
4. **The segments that look most promising are the least real** — every well-level feature anti-correlates
   across disjoint well halves (§2).
5. Step 3's precondition — *"do not build a correction unless the sign is predictable out-of-fold"* — is
   **not met at group level either** (§4).

The honest line remains valuable as **slot-2 diversity**, which is what the task's preamble asserts and
what Q18 quantified (it beats the frontier line on ~29% of random 3-well draws). Nothing here changes
that; what is closed is the idea of *improving* it by group-level residual correction.

## 6. Limits

- Quintile binning only; a different binning or a 2-D interaction of two reproducible row-level features
  was not tested. Given the best single-segment OOF gain is +0.0065, an interaction would have to be an
  order of magnitude stronger to matter.
- Corrections are **additive constants per group**. A multiplicative or shrinkage-toward-zero form was not
  tested, though Q41 showed the 3-well condition is unreachable for any change of this magnitude.
- The split-half uses one random partition of the 760 wells; the anti-correlations are large enough
  (−0.16 to −0.75) that a different partition would not change the reading, but it is one draw.
- All of this is on train wells against toe truth, and the 3-well bootstrap is the standing scale proxy.

## 7. Next

`q43_public_research_transition_priors`. `q29_final_slot_candidate_packager` reactivates **2026-08-03**;
the final selection action is due by **2026-08-04** and costs no quota.
