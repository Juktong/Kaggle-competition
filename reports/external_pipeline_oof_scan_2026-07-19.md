# ROGII — external/industry honest pipeline scan + group-anchored structural field (Direction F/G, 2026-07-19)

Sprint session `3f11942e`→`4d6cd351`. Goal: find an honest pipeline whose errors decorrelate from BOTH DWT
(GBM) and PF (GR-matching particle filter), to strengthen the honest slot **54804893 (blend OOF 9.2969)**.
Script `scripts/struct_field_gate.py`. Neutral technical language.

## 1. Repo scan — nothing net-new (confirms the prior scan)
Targeted greps found these families **absent from the repo**: matrix profile / shapelets / SAX, HMM / Kalman,
`ruptures` / `tslearn` / `stumpy` / `fastdtw`, kriging / variogram / Gaussian process / dip-azimuth. `viterbi`
appears only in the (already-tested) Lucifer stack; `dtw`/spectral only in the (already-tested)
`spectral_soft_alignment_probe.py`. All typewell access in the repo uses the well's **own** typewell only.

## 2. Data-structure discovery — the 773 typewells are ~54 distinct master logs
Grouping typewells by `round(max(TVT),1)` yields **54 groups** (sizes 71, 53, 41, 38, 31, 31, …; 13
singletons). Group members are the *same master log clipped at different tops* (two members interpolated onto
a common TVT grid: max|ΔGR| = 0.0000, corr = 1.00000). **97.2 % of wells sit in a group of ≥6.** The group key
is computable at inference from the test well's **own typewell file** (test-available).

Two consequences:
- **(a) "Ensemble-of-typewell-references" is void.** For ~97 % of wells the other wells' typewells *are the
  same curve* — pooling them adds no GR information. (Also: 0/71 wells in the largest group have horizontal
  TVT outside their own typewell's span, so reference *extension* adds nothing either.)
- **(b) The group is a structural correlation unit.** Group-mates share a TVT datum, so their `r = TVT + Z`
  fields are mutually comparable — a **cross-well, GR-free, label-driven** channel, structurally different
  from DWT (per-row GBM) and PF (intra-well GR matching).

This also diagnoses the old spatial failure: `scratchpad_probes/tvt_spatial_probe.py` built an `r = TVT+Z` KNN
field but pooled **all** wells (mixed datums) and never heel-anchored → RMSE 178. Restricting to the group and
anchoring on the target's own heel is a different method, not a retry.

## 3. Method (honest by construction)
`structural_field_forward(hw, tw, group_wells, k=12, anchor_rows=100, min_sep)`:
group key from the target's own typewell → pool group-mates' `(X, Y, r=TVT+Z)` → cKDTree IDW (k=12) along the
target trajectory → **anchor the level on the target's OWN last 100 known heel rows**
(`anchor = mean(r_true − r_pred)`) → `TVT = r_pred + anchor − Z`.
Inputs: target `X,Y,Z,TVT_input` + its typewell (all test-available); other **train** wells' `(X,Y,TVT)` =
ordinary supervised use of training labels (the same labels DWT learns from, in a spatial rather than
per-row form). No structural surfaces, no Geology, no `wid in train_wells` gating.

## 4. HONESTY GATE — min_sep A/B (165 wells, 3 densest groups, 808,909 toe rows)
The one real leakage path is a **duplicate twin** in the neighbour pool (it would return the target's own
truth at its own coordinates). Nested weight (5 well-splits), never in-sample:

| min_sep | struct RMSE | mean neighbours | nested gain over blend 8.7060 |
|---|---|---|---|
| 0 ft | 16.147 | 56.8 | **+0.5264** |
| **150 ft** | 16.343 | 56.8 | **+0.4938** |
| 500 ft | 24.609 | 55.5 | −0.0909 |
| 1500 ft | 52.548 | 52.0 | −0.0142 |

corr(struct, DWT) = **+0.073**, corr(struct, PF) = **−0.048** → near-orthogonal to both; fitted weights
**positive** (0.09–0.27 per fold), unlike the previously-rejected geometry family (corr 0.68–0.73, negative
weights). Mate separation: closest mate min 58 ft, p05 192, median 352; only **2/165** targets have a mate
<150 ft.

**The gain rides on the 1–2 mates within ~500 ft** (going 150→500 ft removes barely any neighbours, 56.8→55.5,
yet the signal dies). That pattern would also appear if those close mates were the affine near-duplicates known
to exist in train — so it was tested directly.

### Duplicate-vs-offset test (52 targets with a mate <500 ft) — PASSES
| test | result |
|---|---|
| TVT difference at matched XY | median **64.4 ft** (p10 28.9, min 12.7) |
| mates with TVT-diff < 1 ft (duplicate signature) | **0 / 52** |
| mates with TVT-diff < 3 ft | **0 / 52** |
| GR correlation with closest mate | median **0.102** (same log would be > 0.95) |

The close mates are **genuinely different wells** (tens of feet of structural difference, uncorrelated GR),
not duplicates. The mechanism is standard offset-well practice: neighbours supply the structural **gradient**
of `r`, the target's own heel supplies the **level** — which is why large absolute TVT offsets are irrelevant.

**Verdict: the +0.49 nested gain is honest offset-well structural correlation, not duplicate reconstruction.**
This is the first genuinely new honest signal since the PF.

## 5. Status
- **Full 773-well / 54-group OOF is RUNNING** (detached; `min_sep=150`, k=12, anchor=100) → the decisive
  number against the 9.2969 baseline. Expect a **smaller** gain than +0.49: the 3 densest groups have the most
  close neighbours, while sparse/singleton groups (13 groups are singletons) will contribute little or nothing.
- Wells with no surviving neighbour must fall back to weight 0 (degrades to the current blend) — that fallback
  is already the script's behaviour and must be preserved in any deployable version.
- **No submission yet**: gate requires the full-set nested OOF < 9.2969 with stable bootstrap plus a stress
  check, then a format/leakage audit.

## 6. Deployment considerations (before any submission)
1. **Apply the `min_sep` guard at inference too**, so the honest slot never reconstructs a duplicate twin.
2. Hidden-rerun coverage is the open risk: the gain requires a train well within ~500 ft of the test
   trajectory. Novel wells drilled in the same fields plausibly have that; wells in new areas will not, and
   will fall back to the blend. This bounds the downside but also the upside.
3. Weight must be fixed from nested train OOF (never fitted at test time).
