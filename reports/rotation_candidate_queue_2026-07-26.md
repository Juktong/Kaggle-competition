# Rotation candidate queue — 2026-07-26

Scores are 1–5 (5 = best/cheapest/safest). `quota_cost` is the number of submissions a candidate would
consume if it reached the submit gate.

| id | candidate | state | exp_gain_public | H-hidden robustness | non-homogeneity | impl_cost | provenance risk | quota_cost | smoke_ready | proxy support |
|---|---|---|---|---|---|---|---|---|---|---|
| **G1.2** | frontier OOF-style component validation | **audited** | n/a (no submit) | 5 | n/a | 4 | 5 | 0 | 5 | **5 — done this round** |
| G2.1 | SP45-only variant | **submitted → 6.690** | — | — | — | — | — | 1 used | — | settled: post-SP45 stages earn their place |
| G2.2 | well-level selector across variants | **closed** | — | — | — | — | — | 0 | — | oracle margin +0.0000; proxy inverts within-family |
| G3.4/H | final-selection simulator (3 criteria) | **audited** | n/a (no submit) | 5 | n/a | 5 | 5 | 0 | 5 | 5 — all criteria converge |
| G1.1 | full-fidelity overlap-OFF ownership run | **effectively done** | n/a | 5 | 1 (would duplicate `54968060`) | 5 | 4 | 0 | 5 | 5 |
| G1.3 | dependency/provenance audit | static_audited | n/a | 4 | n/a | 4 | 5 | 0 | 5 | 3 |
| G3.1 | stratigraphic heatmap + top-K path search | **closed** | — | — | — | — | — | 0 | — | DP converges to flat-anchor from above; emission adds no info |
| G3.5 | honest prefix calibration for `54844628` | not_started | 2 | 4 | 3 | 3 | 5 | 0–1 | 3 | 2 (heel explains ~5% of toe bias) |
| G3.2 | learned local alignment scorer + DP | not_started | 1 | 3 | 4 | 2 | 5 | 0–1 | 3 | 1 (NCC baseline 0.52; ~34× scale mismatch) |
| G3.3 | multi-hypothesis trajectory model | not_started | 2 | 4 | 5 | 1 | 5 | 0–1 | 2 | 2 |

## Notes that change the default order

- **G1.1 is effectively already satisfied.** `54968060` *is* a full-fidelity overlap-OFF run executed
  from our account (`joezzzzz/rogii-kaiwalya-overlap-off-full` v1), with the notebook, patch and metadata
  tracked in this repo. Re-running it would produce a homogeneous output and is not scheduled.
- **G1.2 completed without a Kaggle run** — the frontier writes its own masked-split component reports;
  they were read from the completed full run. This is the round's main result.
- **G2.1's intermediates are already mapped** (A3/A4/A5, 2026-07-25): model-package = bounded ~1.1 ft
  top-up; prefix-aggressiveness and bimodal are inert on the visible wells. A new variant matrix has low
  expected information beyond what those diffs already showed, so it drops below G3.4.
- **G3.4 rises**: it costs no quota, needs no GPU, and directly serves the final-2 decision, which is the
  binding question with ~10.9 days left.

## Execution order for round 2

1. **G3.4** robust final-selection simulator (no quota, directly decision-relevant).
2. **G1.3** dependency/provenance audit (closes the one open reservation about `54968060` as slot 2).
3. G2.2 well-level selector — only if G1.2/G3.4 surface a well-level signal worth selecting on.

## Re-prioritisation after round 2 (`54990075` = 6.690)

The SP45-only result removes the main reason to keep exploring frontier stage-truncation variants: the
post-SP45 stages are net-positive on the leaderboard, so removing components is not a productive axis.
Combined with the earlier A3/A4/A5 finding (model-package is a bounded ±2 ft top-up; prefix-aggressiveness
and bimodal are inert on the visible wells), **G (small variant matrix) drops to the bottom** — the
remaining knobs are either inert or already shown to be net-positive as configured.

Revised order:
1. **G2.2 well-level selector** — the one remaining way to combine existing scored outputs without a new
   pipeline. Local-only first.
2. **G3.1 heatmap + top-K path search** — a genuinely different alignment formulation.
3. **G3.5 honest prefix calibration** — improves the fully-owned hedge, which all three selection
   criteria now place in slot 2.
4. G3.2 / G3.3 — higher cost, weaker prior support.
5. G (variant matrix) — deprioritised per above.

## 2026-07-28 update

- **G3.5 honest prefix calibration — closed on evidence.** Deployment-honest prefix-cut signal explains
  3.5% (CUT 0.70) / 0.5% (CUT 0.50) of toe-bias variance, in-sample upper bound; the apparent 43.4% was a
  same-run confound. Weaker than the raw heel level (~5–17%) already exploited by the deployed anchor.
  0 quota used. Report: `reports/g35_honest_prefix_calibration_2026-07-28.md`.
- Next runnable: **`g13_dependency_provenance_audit`** (priority 20, no GPU, `can_submit=false`) — closes
  the one open reservation about the frontier line's third-party dataset dependencies.

## 2026-07-28 update (G1.3)

- **G1.3 dependency/provenance audit — completed.** Frontier dependency surface narrows from 9 datasets
  to **1 frontier-specific prediction-affecting dataset** (`fleongg/rogii-claude-models-pub`, measured
  public value ≈0.047). Report: `reports/frontier_dependency_provenance_audit_2026-07-28.md`. 0 quota.
- New low-cost follow-ups added to the mitigation queue (both output-neutral, verified by FAST smoke,
  no quota): detach the 5 vestigial datasets; drop the guard-rejected `pilkwang/rogii-model-package`.
- Next runnable: **`g32_learned_alignment_smoke`** (priority 30). Note the prior evidence bounding it:
  the NCC alignment baseline scored AUC 0.52 (chance) on 2026-07-20, a pointwise GR difference explained
  0.0% of TVT-difference variance on 07-21, and G3.1 (07-26) found a DP over a GR misfit matrix converges
  to the flat-anchor baseline from above. A learned scorer must beat those, not merely exist.
## 2026-07-28 update (G3.2)

- **G3.2 learned alignment scorer — signal found, not a standalone candidate.** Learned scorer AUC 0.7242
  vs NCC 0.5010 / level 0.6423; its DP beats the flat-anchor baseline (12.527 vs 13.103, interior optimum
  at lam=60) where G3.1's hand-coded emission never did. Still ~42% worse than the deployed pipeline
  (~8.86), so no Kaggle run, no submission, 0 quota.
- Follow-up worth its own prompt: use the learned scorer as an **extra emission term inside the PF**
  rather than as a standalone DP.
- Next runnable: **`g33_multi_hypothesis_smoke`** (priority 40).

## 2026-07-28 update (G3.3)

- **G3.3 multi-hypothesis trajectory — closed on evidence.** Smoke checks all pass (loss decreases,
  diversity 9.734 ft, sane trajectories) but K=1 regression (18.475) is worse than the flat-anchor
  baseline (15.833) and the best achievable K=5 configuration (16.877) still is. Oracle +5.707 vs
  achievable +1.598. 0 quota. Report: `reports/g33_multi_hypothesis_smoke_2026-07-28.md`.
- Recorded minimal next smoke: condition K hypotheses on the PF's own per-well posterior spread
  (`pf_unc.npz`) and train only on high-spread wells.
- Next runnable: **`frontier_variant_matrix_lite`** (priority 50).

## 2026-07-28 update (frontier variant matrix lite)

- **Static diff completed at zero cost** from the existing full-run intermediates. Corrected a published
  error: the **bimodal hedge is the largest post-SP45 effect** (+2.0 ft on all 4,301 rows of `00e12e8b`),
  not zero as A5 recorded. G1.3's ~0.047 becomes a joint bound over two stages.
- **No variant promoted** — prefix-aggressive would re-confirm G3.5; bimodal fires on 1 of 3 wells so any
  public delta sits under the ~0.115 noise floor. 0 quota.
- Concrete next variant if revisited: lower `skip_separation` so the bimodal hedge also fires on
  `00bbac68` (separation 3.594 ft) — a multi-well effect would be resolvable.
- Next runnable: **`new_direction_search`** (priority 90).

## 2026-07-28 update (new direction search)

Implementation round complete. Six new directions queued at 110–160, each with a CPU-only smoke and no
quota cost:

| pri | id | submission path | smallest smoke |
|---|---|---|---|
| 110 | `n4_conformal_well_uncertainty` | none (decision support) | split conformal on the banked 760-well OOF; check coverage per feature bin |
| 120 | `n2_increment_structural_field` | **yes** (gate required) | swap the deployed field's target level -> heel-referenced increment, gate/W fixed |
| 130 | `n1_geometry_bounded_alignment` | none | per-row admissible band on the G3.2 DP from `dZ`/`dH`, sweep the dip bound |
| 140 | `n3_multiscale_gr_matching` | none | 4-level DWT, scorer AUC per level vs G3.2's 0.7242 |
| 150 | `n6_public_solution_audit` | none | method diff of a second public solution vs our ledger (methods only, no external data) |
| 160 | `n5_typewell_fingerprint_families` | none | 30-min time-box: GR-vs-TVT curve match, does it beat the deployed spatial gate |

Closed this round: **single-dip geometric reparametrization** (oracle 7.65 vs honest 80.29 vs flat 15.91),
**train-only PNG images as an input modality** (no test PNGs), **exact typewell grouping** (0/3 test wells
match). Not queued with reasons: RL geosteering (no action space), azimuthal-GR dip inversion (single
scalar GR only).

## 2026-07-28 update (N4 conformal per-well uncertainty)

- **Closed: per-well confidence gating on test-available features.** CV R^2 0.074 on log(per-well OOF
  RMSE); conditional conformal intervals are wider than the unconditional one at matched coverage
  (13.76/13.97 vs 13.43). A gate built on `nnb` / closest-mate / prefix-fraction / GR-std / geometry would
  be close to random. Do not re-attempt without a materially different feature source.
- **Retained:** marginal conformal bound for the honest line — 90% of wells <= 13.43 ft, 95% <= 17.53 ft,
  coverage verified out-of-sample. Table at `rogii_sprint_shared/tmp/n4_well_uncertainty.csv`.
- **New constraint on all future validation:** for one fixed model, a random 3-well draw pools to
  5th 3.491 / median 6.708 / 95th 15.138. Quote this whenever a small margin is proposed.
- **New measured transfer gap:** OOF 4.756 on the 3 test wells vs public 7.891 = 1.659x. OOF-based bounds
  are not leaderboard bounds.
- Next runnable: **`n2_increment_structural_field`** (priority 120) — the only queued item with a
  submission path.

## 2026-07-28 update (N2 increment structural field)

- **Closed: re-referencing the structural field's increment.** The deployed field is already heel-anchored
  and level-invariant, so the intended level->increment swap is a no-op; the two constructions that DO
  differ both fail the 3-well gate on the full 760-well split (`iso` -0.1003 pooled, 5th -1.7148;
  `increment` -1.6840 pooled, 5th -5.5224).
- **Corrected:** `new_direction_search` described the deployed field as interpolating the TVT level. It
  interpolates the increment and takes the level from the target's own known heel.
- **New anchor fact:** the deployed neighbourhood is effectively single-well — 99.38% of the k=12
  contributing points come from the same well as the nearest point, and the nearest well essentially never
  changes along a lateral. Any future cross-well idea should assume a single dominant neighbour.
- **Retained:** a byte-exact reimplementation of the deployed structural field
  (`scripts/n2_increment_structural_field.py`), reproducing the banked 8.8626 to -0.0000 on the full split.
  Reusable for any future variant of this component.
- Next runnable: **`n1_geometry_bounded_alignment`** (priority 130).

## 2026-07-28 update (N1 geometry-bounded alignment)

- **Closed: the geometry-derived admissible band.** It binds 83-91% of transitions (not inert), but on 40
  eval wells every geometry-aware arm is worse than the unbounded control, and nested selection never
  picks one. Pooled held-out DP 13.644 vs flat-anchor 12.722.
- **Amended: G3.2's "DP beats the flat anchor".** That comparison selected lam on the wells it reported;
  with nesting on 40 wells it does not beat flat. The scorer's AUC 0.7242 vs NCC 0.5010 stands.
- **New standing caution:** the 12-well eval set used by G3.1/G3.2/N1 is small enough that a 20-config
  sweep produced an apparent 25% gain (9.412) that vanished on 40 wells. Any future alignment result must
  be nested and reported on >=40 wells.
- **Retained:** the geometric bound gives stability at weak regularisation (unbounded diverges to 42.359
  at lam=1; bounded stays 14-16). Useful if a future formulation needs a weak regulariser.
- Next runnable: **`n3_multiscale_gr_matching`** (priority 140).

## 2026-07-28 update (N3 multi-scale GR matching)

- **Closed: coarse-to-fine wavelet decomposition as the fix for the GR-scorer line.** No level exceeds
  G3.2's 0.7242; the raw band is best (0.7160) and AUC falls monotonically with coarser approximation
  (0.6573 at 16 ft). NCC is at chance in all 9 bands, so shape matching is not a scale problem.
- **Banked positive: typewell window TWH=1 (3 ft).** Held-out-WELL AUC 0.7655 +/- 0.0030 (5 seeds) vs
  0.7300 +/- 0.0028 at G3.2's TWH=8 — +0.0355, 8.7x seed noise. A **no-training** level score reaches
  0.7352, above G3.2's trained 0.7242. Available to any future alignment work.
- **New standing protocol rule:** scorer comparisons must split by WELL, not by pair. G3.2's pair split
  ranked the windows wrongly (chose TWH=32; the well split chooses TWH=1) and understated absolute AUC.
- Next runnable: **`n6_public_solution_audit`** (priority 150), then `n5` (160).

## 2026-07-28 update (N6 public-solution audit)

- **Blocker:** the queued target `aaryan2203/rogii-wellbore-geology-prediction-argon` does not exist (404;
  the name came from a stale web-search snippet). Audited `mycarta/rogii-geosteering-toolkit` (MIT)
  instead — same intent, real target.
- **Newly queued from the audit:**
  - `n8_azimuth_matched_neighbours` (170) — azimuth-similarity filter on the structural field's neighbour
    selection; the only cross-well component with a confirmed honest gain, and N2 left a byte-exact
    reimplementation to modify. **The one queued item with a submission path.**
  - `n7_q3d_tortuosity_features` (180) — Q-3D tortuosity (Jing et al. 2022) was their largest single-group
    ablation gain (-0.107 RMSE) and is fully test-available from MD/X/Y/Z. Gate it against N4's CV R^2
    0.074 bar before touching the model.
  - `n9_self_correlation_prefix_template` (190) — the lateral's own known zone as the matching template;
    removes the cross-instrument level offset, which is the cue N3 showed dominates.
- **Confirmed closed by an independent party:** Catch22/AEON well-level features (+0.476 worse for them),
  typewell-`Geology` classifier (they dropped it; we measured `Geology` absent from the test schema).
- **Do not re-attempt** from their stack: G11 three-thirds TVT-vs-MD fit (covered by M4), G13/G14
  landing-state and well-length features (N4 measured CV R^2 0.074 for this feature class), G15 vintage
  `seq_id` features (leakage-adjacent, needs a rules check first).
- Next runnable: **`n5_typewell_fingerprint_families`** (priority 160, time-boxed 30 min).

## 2026-07-28 update (N5 typewell fingerprint)

- **Closed: typewell-fingerprint well families.** The near-identical set and the deployed group-key set
  are identical in both directions on all three test wells (13/13, 40/40, 13/13). 5/5 of the fingerprint
  top-5 are already in the deployed surviving-neighbour set. Nothing is added over production.
- **M3 corrected:** its byte-hash measured FILE identity, not CURVE identity (files are truncated to
  different TVT ranges). Typewell sharing is common — 13/40/13 near-identical curves per test well — not
  rare as M3 implied.
- **Banked positive:** the deployed `round(max(typewell.TVT), 1)` group key is a lossless proxy for
  typewell identity on the scored wells; its truncation-sensitivity was a real worry and is now measured
  and dismissed. Relevant to `n8`: neighbour membership is correct, so any gain there must come from the
  weighting.
- Next runnable: **`n8_azimuth_matched_neighbours`** (170) — the only queued item with a submission path —
  then `n7` (180), `n9` (190).

## 2026-07-28 update (N8 azimuth-matched neighbours)

- **Closed: azimuth filtering of the structural field's neighbour set.** All four tolerances are worse
  than no filter (-0.0697 to -0.0789 pooled) and all fail the 3-well gate (5th -0.86 to -0.90,
  P(gain>0) ~0.49). The no-filter control is byte-exact against the banked field.
- **Measured context:** the deployed selection is already azimuth-coherent (median neighbour spread
  26.7 deg), so the filter is largely redundant; it does remove the nearest well for 10.9-12.2% of targets,
  and that is what costs the score.
- **Component now probed on three independent axes and unchanged on all three:** membership (N5, group key
  lossless), orientation (N8, already coherent), referencing (N2, anchor already correct). Any further work
  on the structural field should target the WEIGHTING, not these.
- **Not queued:** azimuth as a soft IDW weight instead of a hard gate — plausible but the headroom is small
  (no change for ~58% of wells) against the 3-well gate's demands.
- Next runnable: **`n7_q3d_tortuosity_features`** (180), then `n9_self_correlation_prefix_template` (190).

## 2026-07-28 update (N7 Q-3D tortuosity)

- **Closed: Q-3D wellbore tortuosity as a residual predictor.** Well-level CV R^2 **0.0292** vs the
  0.0736 bar; adding it to N4's features buys +0.0029 (noise). Row-level pooled spearman -0.0416, and the
  within-well relationship flips sign between wells (mean -0.083, std 0.371, |rho|>0.2 in 60.8%).
- **Not a refutation of the source ablation** — theirs measures tortuosity as a TVT-prediction feature in
  their pipeline; ours measures whether it explains our deployed line's error. Different questions.
- **New standing caution (applies to ALL future trajectory features):** any angle derived from this
  dataset's 1 ft XYZ grid must first be resampled to >=30 ft survey-station spacing. At 1 ft the ~0.01 ft
  XY resolution produces ~0.6 deg of spurious swing per step; the unfixed version reported dogleg severity
  of ~49 deg/100ft, which is physically impossible.
- **Retained artifact:** `scripts/n7_q3d_tortuosity.py` + per-well table
  `rogii_sprint_shared/tmp/n7_tortuosity.csv`, reusable for any trajectory-shape descriptor.
- Next runnable: **`n9_self_correlation_prefix_template`** (190) — the last queued item.

## 2026-07-28 update (N9 self-correlation) — QUEUE EXHAUSTED

- **Closed: self-correlation against the lateral's own known zone.** Held-out-well AUC 0.6628 vs the
  typewell control's 0.7706 (~19x seed noise); the combined arm 0.7605 +/- 0.0057 does not beat the
  control either. Prefix coverage is ample (63.5% of toe rows within 0.5 ft of their true TVT), so the
  failure is not for lack of opportunity.
- **Mechanism isolated:** self AUC is 0.7174 on prefix-covered states but 0.4548 (below chance) on
  uncovered ones — it works where the prefix has data and misleads where the profile was interpolated.
  Any future use must be gated on the coverage mask, never interpolated.
- **Banked fallback:** a typewell-independent emission measured at 0.7174 on covered states, available if
  a future line needs to test whether the typewell itself is the limiting factor.

### State of the queue

All 19 rounds are complete and no task remains queued. Every direction opened by
`new_direction_search` (N1-N9) plus the G-series has now been measured and closed, with one exception
worth restating: **no candidate has passed the 3-well gate since `54844628`**, and the slot recommendation
has been unchanged across all 19 rounds at `54922806` + `54844628` under all three criteria.

Directions explicitly left un-queued, with their reasons recorded in the round reports: azimuth as a soft
IDW weight (N8), MiniROCKET-style convolutional emission features (N6), G11 three-thirds TVT-vs-MD fit
(covered by M4), G13/G14 landing-state and well-length features (N4 measured this class at CV R^2 0.074),
G15 vintage `seq_id` features (leakage-adjacent, needs a rules check first).

## 2026-07-29 update (Q10 TWH=1 DP candidate)

- **First nested-validated win over the flat anchor in the alignment line**: TWH=1 emission gives nested
  DP **12.170** vs flat 12.722 (both folds agree), against TWH=8's 13.206 and N1's 13.644. lam=60 verified
  as an interior optimum after extending the grid to 800.
- **Still not submittable**: 12.170 vs deployed ~8.86 (~37% worse); tail-driven (helps 16-17 of 40 wells);
  margin (0.28-0.55) is grid-sensitive. No Kaggle smoke prepared, 0 quota.
- **Revises N1**: the emission was NOT saturated — +0.030 AUC bought -1.04 RMSE. "The gap is in the
  transition model, not the emission" is withdrawn as a generalisation; N1 amended in place.
- **Exchange rate now measured**, and it bounds the line: ~1 RMSE per +0.03 AUC. Closing the remaining
  3.3 RMSE to deployed on that rate needs an implausible AUC, so emission tuning alone cannot get there.
- **Not queued:** a per-typewell-group router over the family structure (n=2-5 per group; hard selection
  is a closed pattern).

## 2026-07-29 update (Q11 PF path ranker)

- **Closed: ranking/selecting among PF candidate paths**, with or without TWH=1 alignment features. All
  three arms lose to the PF mean default on 40 held-out wells (-0.19 to -0.56); 3-well P(gain>0) 0.2696.
- **Closes the PF-path line's second shape.** Generation from a pointwise emission was closed by
  G3.1/G3.2/N1/Q10; selection among proposals is now closed by the prior top-K ranker and Q11.
- **Banked headroom measurement:** ORACLE best-of-96 = 7.1579 vs deployed 8.8626 — the information IS in
  the path set, but it is truth-selected and no test-available selector reaches it.
- **The lever, if this is ever revisited:** a *combiner* (weighting over paths) rather than a *selector*,
  because weighting preserves the averaging that makes the PF mean robust. Not queued now.
- **Methodology reinforced:** an 8-well smoke showed +73.5% headroom conversion that became -12.8% at 40
  wells. Never accept a pooled figure from a small eval set when its own per-well statistics disagree.
- Next runnable: **`q12_coverage_gated_self_template`** (220).

## 2026-07-29 update (Q12 coverage-gated self template)

- **Closed: coverage-gated self-correlation, at the well level.** No coverage band favours `self`
  (deficit -0.005 to -0.149 in all five); `both` is pooled +0.0012 and beats typewell on 51.7% of wells.
- **The decisive number:** corr(coverage, self-typewell) = **0.0867**, corr(coverage, both-typewell) =
  **0.0604**. A gate can only help if the gating variable predicts where the treatment works; this one
  does not.
- **Together with N9 this closes the self-template line** (state-level gate and well-level gate both fail).
- **Carry forward for `q13_twh1_self_hybrid_emission` (230):** Q12 already measured the `both` arm — a
  typewell+self hybrid emission — at +0.0012 pooled over 60 held-out wells with no coverage stratification.
  q13 should treat that as its prior and check first whether it proposes anything materially different
  from the `both` arm before spending a full implementation.
- Next runnable: **`q13_twh1_self_hybrid_emission`** (230).
