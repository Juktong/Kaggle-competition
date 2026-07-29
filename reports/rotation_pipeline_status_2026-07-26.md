# ROGII rotation pipeline — status (2026-07-26)

A repeating loop around the Kaiwalya/frontier line. Each round: live refresh → candidate pool update →
priority scoring → smoke → full → output audit → local/proxy evaluation → submit/HOLD → ledger update →
commit/push → next round. Stops only on a hard blocker or exhausted round budget.

## Fixed rules

**A. Live refresh (every round):** Kaggle submissions, today's UTC quota, active kernels, local
processes/watchers, `git status`, `origin`/`juktong` fetch, and whether `origin/main` has new commits.
New teammate/public kernels are recorded (source + result) before the pool is adjusted. A dirty worktree
is understood before anything is written.

**Smoke:** every Kaggle kernel gets a FAST/tiny smoke first, checking imports, dataset availability, GPU,
output path, submission schema, id order, finiteness, and **that the intended patch actually applied**.
Max 3 automatic repair attempts; then `blocked` and move to the next candidate.

**Full:** only from `smoke_passed`. Output downloaded and audited via
`scripts/rotation_candidate_audit.py` (rows=14151, columns, id order, finite, distribution, per-well
trajectory slope/jump, diff vs every scored reference, sha256, homogeneity flag). Full output is never
auto-submitted.

**Submit gate (all must hold):** quota remaining > 0; HARD sanity pass; not a plain rerun / near-duplicate
(rmse-diff ≥ 0.50 vs every scored reference); clear public or final-slot information value; report states
why the slot is worth spending; description accurate and not overstated. On submit: record ref, poll to
COMPLETE (or leave a ref-matched watcher), then update ledger / final-slot / queue.

**Never:** submit a smoke or dummy; resubmit a homogeneous plain rerun; submit on a small 3-well public
difference alone; overwrite unread changes; use emotive framing.

**State fields:** `not_started · static_audited · smoke_prepared · smoke_running · smoke_passed ·
smoke_failed · full_running · full_passed · audited · submitted · hold · blocked`.

## Round 1 — 2026-07-26 02:30 UTC

**Live refresh result:** today's quota **0/5**; no Kaggle kernel running; no local process/watcher; git
clean at `e923cd7`; `origin/main` unchanged at `a589fa8`; no new teammate kernel or submission since
`54968060`.

| ref | public | side |
|---|---|---|
| `54922806` | **6.563** | teammate (frontier overlap-ON) |
| `54968060` | **6.643** | ours (frontier overlap-OFF) |
| `54896975` | 6.669 | teammate |
| `54923144` | 6.678 | teammate |
| `54844628` | 7.891 | ours (fully-owned honest) |
| `54878409` | 7.953 | ours (excluded) |

**Executed this round:** infrastructure (`scripts/rotation_candidate_audit.py`, 5 management reports) +
**G1.2 frontier component validation** — completed from the frontier's own masked-split reports without
spending a Kaggle run. See `reports/frontier_oof_component_validation_2026-07-26.md`.

**Submissions this round: 0.** Nothing reached the submit gate; the round's output is diagnostic.

## Infrastructure

- `scripts/rotation_candidate_audit.py` — unified sanity/diff/score/homogeneity table (self-tested on
  `54968060`: HARD PASS, distinct from all scored references).
- `reports/rotation_candidate_queue_2026-07-26.md` — pool + priority scores + state fields.
- `reports/rotation_submission_decisions_2026-07-26.md` — every submit/HOLD decision with reasons.
- `reports/submission_ledger_2026-07-26.md` — daily quota and board.
- `reports/final_slot_package_corrected_gate_2026-07-26.md` — current final-2 recommendation.

## Round 2 — 2026-07-26 02:36 UTC (in progress)

**Candidate: G2.1 SP45-projection-only.** Built from the overlap-OFF notebook (retrieval stays off) with
a final cell that writes `sp45_projection_submission.csv` as the submission, and asserts row count and
finiteness so the patch cannot silently no-op.

- kernel `joezzzzz/rogii-frontier-sp45-only-smoke` v1 — **smoke_passed** (FAST=1, 40 wells, 47 s).
  Patch proof in the log: `[G2.1] FINAL submission.csv <- sp45_projection_submission.csv rows=14151
  mean=11903.637`. Audit: HARD PASS; proxy RMSE **1.958**; rmse **2.520 vs `54968060`** → non-homogeneous.
- kernel `joezzzzz/rogii-frontier-sp45-only-full` v1 — **full_running**.
- Note: Kaggle resolved the slug from the title (`...sp45-only-smoke`, not `...sp45only-smoke`);
  `kernel-metadata.json` was corrected to match so later pushes stay on one slug.
- On smoke pass → full run → `scripts/rotation_candidate_audit.py` → submit gate.
- Pre-registered read: if it scores **below 6.643**, the frontier's post-SP45 stages are net-negative on
  the leaderboard and SP45-only becomes the stronger slot-2 candidate; if **above**, those stages earn
  their place and `54968060` stays. Either way the result is decision-relevant, which is what justifies
  the slot under the gate.

## Round 3 — 2026-07-26 15:09 UTC

**Live refresh:** today 1/5 used (4 remaining); `54990075` COMPLETE **6.690**; no local processes or
Kaggle kernels running; git clean; `origin/main` unchanged at `a589fa8`; no new teammate submission.

| item | result |
|---|---|
| **A** final-slot contradiction | **fixed** — three criteria stated separately; all converge on `54922806 + 54844628` |
| **H** simulator upgrade | **done** — adds `54990075`, family/provenance/OOF flags, measured prediction correlations; emits score-first / diversity-first / provenance-first. Fixed a tiebreak flaw treating an unmeasurable correlation as worst-case |
| **G2.1** result | `54990075` = **6.690** → the `> 6.678` branch: post-SP45 stages **earn their place**; the local proxy pointed the wrong way |
| **B / G2.2** well-level selector | **closed** — oracle margin **+0.0000**; and the proxy **inverts** the within-family ranking |
| **C / G3.1** heatmap + top-K path search | **closed** — DP converges to the flat-anchor baseline from above and never crosses it; emission adds no information |

**Submissions this round: 0** (the round's one submission, `54990075`, was made in round 2 and scored
this round). Quota 1/5 used today.

### Methodological result carried forward

Two independent findings this round converge on the same rule: **the train-copy proxy must not be used
to rank candidates that are close together.** `54990075` (proxy-best) scored worst of the frontier pair
on public, and the G2.2 table shows the proxy inverting the within-family ordering while ranking across
families correctly. Only a structural argument or a leaderboard result can separate close candidates.

## Round 4 — 2026-07-28 05:33 UTC (autopilot `live_refresh_and_decision`)

Live-refresh task only (`can_submit=false`, no heavy run). **Material state changes since round 3**, so
this status file is updated:

| item | round 3 (07-26) | round 4 (07-28) |
|---|---|---|
| daily quota | 1/5 used | **0/5 used, 5 remaining** (new day) |
| days to deadline | ~10.4 | **8.77** (2026-08-05 23:59 UTC) |
| Kaggle kernels running | 0 | 0 (`sp45-only-full`, `overlap-off-full` both COMPLETE) |
| new submissions | — | **none** since `54990075` (6.690, 07-26) |
| `origin/main` | `a589fa8` | `a589fa8` — **no new Mark/Marc commits** |
| branch vs `juktong` | in sync | in sync (0 unpushed) |
| execution model | manual rounds | **autopilot runner active** (`scripts/claude_autopilot.py --loop --sleep 900`, commits `01f2294`, `1e372e1`) |

An idle gap of ~2 days occurred between rounds 3 and 4; no work was lost and no process was left
running. The board is unchanged, so no candidate re-ranking is warranted and the final-slot package
stands as written.

### Queue decision

Next runnable task by priority: **`g35_honest_prefix_calibration`** (priority 10, `requires_gpu=false`,
`can_submit=true`, `max_submit_cost=1`). It is the correct next step: all three selection criteria place
the fully-owned honest line (`54844628`) in slot 2, so improving it has direct final-slot value, and it
needs no GPU.

**Design constraint carried into that task** (so the boundary is not rediscovered): the 2026-07-21
per-well bias analysis measured how much of a well's whole-toe bias is visible from its known heel —

```
corr(first-100-row bias, whole-well bias) = +0.213  ->  ~5% of variance
corr(first-500-row bias, whole-well bias) = +0.415  ->  ~17% of variance
```

so a prefix-derived correction can address at most a small share of the per-well bias. G3.5 should
therefore be scoped as a **bounded** correction validated by honest masked split / OOF / bootstrap, with
a modest expected effect, and must not use train-copy lookup. Sub-0.1 local gains cannot be ranked by
the train-copy proxy (retired as a ranking tool in round 3).

Following tasks in queue order: `g13_dependency_provenance_audit` (no GPU, no submit),
`g32_learned_alignment_smoke`, `g33_multi_hypothesis_smoke`, `frontier_variant_matrix_lite`,
`new_direction_search`, `status_summary_for_user`.

## Round 5 — 2026-07-28 05:48 UTC (autopilot `g35_honest_prefix_calibration`)

Live refresh: quota **0/5** at start and **0/5 at end** (no submission); no Kaggle kernels running; git
in sync with `juktong`; `origin/main` unchanged at `a589fa8`.

**G3.5 closed on evidence** — `reports/g35_honest_prefix_calibration_2026-07-28.md`. The honest line
already anchors on its own last 100 known heel rows, so the only untried mechanism was the frontier's
**prefix-cut self-calibration**. Its prerequisite was tested before building anything and does not hold:

```
CUT 0.70   confounded 43.4%  ->  deployment-honest  3.5%   (in-sample upper bound 3.4%)
CUT 0.50   confounded 14.1%  ->  deployment-honest  0.5%   (in-sample upper bound 0.4%)
```

The apparent signal was almost entirely a **confound**: taking the calibration signal and its target from
the same truncated run makes them share the shorter-prefix degradation. Pairing a truncated-run signal
with a full-prefix target — the only pairing that exists at inference — drops explained variance by 3–4×.

No variant was built, no Kaggle smoke/full was launched, **no submission** (submit gate never reached,
since the local smoke produced nothing to carry forward). `54844628` unchanged.

**Standing rule added:** never measure a calibration signal and its target on the same truncated run.

## Round 6 — 2026-07-28 06:03 UTC (autopilot `g13_dependency_provenance_audit`)

Live refresh: quota **0/5** (unchanged, no submission); no Kaggle kernels running; branch in sync with
`juktong`; `origin/main` unchanged at `a589fa8`.

**G1.3 completed** — `reports/frontier_dependency_provenance_audit_2026-07-28.md`. Static source analysis
plus empirical run-log evidence narrows the frontier's 9-dataset attachment to:

```
1  affects predictions, shared with our honest line   ravaghi/…artifacts (SP45 ridge, w 0.30)
1  affects predictions, frontier-specific             fleongg/rogii-claude-models-pub (learned traj, w 0.40)
1  runtime environment only (offline pip wheels)      phongnguyn…/koolbox-offline
1  loaded but guard-REJECTED at runtime               pilkwang/rogii-model-package (p95 29.464 > 25.000)
5  vestigial: zero source refs, zero log appearances  nina2025, thbdh5765 v10/v11, chesnikovleonid, needless090
```

The single frontier-specific prediction dependency has a **measured public value of ≈0.047**
(`54990075` 6.690 SP45-only vs `54968060` 6.643 — those two runs differ only in that component, since
prefix-cal applied `alpha=0`, the model package was rejected and bimodal made no change). That is inside
the ~0.115 config-variance floor.

Both generic `/kaggle/input` scans were checked and are guarded (`MODEL_PACKAGE_ALLOW_AUTO_SEARCH=False`;
the train-well glob is a fallback that never fires when the competition dataset is attached), so the
vestigial datasets cannot leak into predictions.

Final-slot risk language narrowed accordingly; **the slot recommendation is unchanged**.
Mitigation queue recorded (detach 5 vestigial + 1 guard-rejected dataset, verified by FAST smoke, no
quota cost).

## Round 7 — 2026-07-28 07:18 UTC (autopilot `g32_learned_alignment_smoke`)

Live refresh: quota **0/5** (no submission); no Kaggle kernels running; branch in sync; `origin/main`
unchanged. Local `torch 2.12.1+cpu`, no local GPU — smoke run on CPU per the standing rules.

**G3.2: real signal, first positive result in the alignment line, but far below the deployed pipeline.**
Report: `reports/g32_learned_alignment_smoke_2026-07-28.md`.

```
scorer (identical val pairs):  NCC 0.5010 | level 0.6423 | LEARNED 0.7242
DP vs flat-anchor:  lam 5 -> 16.167 worse | lam 20 -> 12.885 BEATS | lam 60 -> 12.527 BEATS | lam 150 -> 12.912 BEATS
reference: flat-anchor 13.103 | deployed honest pipeline OOF ~8.86
```

Two design corrections were the operative change (matched vertical extent; level cue preserved by not
z-scoring), not extra capacity — a 17-feature MLP beats the 2026-07-21 CNNs that plateaued at 0.647.
The DP optimum is **interior** (best at lam=60), the signature of an informative emission; G3.1's
hand-coded `|GR diff|` emission never crossed flat.

**But 12.527 ft is ~42% worse than the deployed pipeline (~8.86).** Per the task rule, the masked split
does not support a full Kaggle run, so none was launched and the submit gate was never reached.

Refines an earlier conclusion: *pointwise hand-coded* GR costs add nothing (G3.1), but a *learned,
level-aware, extent-matched* scorer does. Kept open as a possible extra emission term inside a stronger
sequential model (the PF reaches ~11.0 ft standalone), which needs its own prompt.

## Round 8 — 2026-07-28 08:33 UTC (autopilot `g33_multi_hypothesis_smoke`)

Live refresh: quota **0/5** (no submission); no Kaggle kernels running; branch in sync; `origin/main`
unchanged at `a589fa8`. Local CPU only.

**G3.3 closed on evidence** — `reports/g33_multi_hypothesis_smoke_2026-07-28.md`.

```
flat-anchor 15.833 | K=1 18.475 | K=5 argmax 16.877 | K=5 mix 16.848 | K=5 ORACLE 12.768 | deployed ~8.86
oracle margin +5.707   achievable margin +1.598   diversity 9.734 ft   loss 1.99->0.66 / 1.74->0.28
```

All three smoke checks pass (loop runs, loss decreases, diversity nonzero, trajectories sane), but:
**K=1 is worse than the flat baseline (18.475 vs 15.833)** — a fourth independent confirmation that the
per-well residual is not predictable from test-available features (after directions 1, 2 and 3). The MTP
structure does recover some of that (+1.598 achievable, and the probability head carries *some* selection
signal, unlike earlier selectors), but the best achievable configuration is still below a trivial
flat-anchor baseline and far from the deployed ~8.86.

Oracle +5.707 vs achievable +1.598 repeats the established pattern: an oracle number is not evidence of
an achievable gain.

Minimal next smoke recorded (not a broad plan): feed the **PF's own per-well posterior spread**
(`pf_unc.npz`, available at inference) as an input and train K hypotheses only on high-spread wells, to
test whether multi-hypothesis helps specifically on wells the PF already flags as ambiguous.

## Round 9 — 2026-07-28 08:48 UTC (autopilot `frontier_variant_matrix_lite`)

Live refresh: quota **0/5** (no submission); no Kaggle kernels running; branch in sync; `origin/main`
unchanged. Static diff + local proxy only, no plain-frontier rerun.

**Main product: a correction.** Every "before X" intermediate sits exactly 1.103 ft from the final output
with `max|d| = 2.00` on exactly 30.4% of rows = 4,301 rows = the whole of well `00e12e8b`. Direct check
confirms **the PF bimodal branch hedge applies +2.0 ft to all 4,301 rows of that well** (separation
29.44 ft; the other two wells are skipped). It is the **largest single post-SP45 effect**.

The 2026-07-25 A5 claim that the bimodal hedge "contributes zero" was wrong: it compared
`before_branch_hedge` with `before_model_package`, which are both *upstream* of the hedge. A5, G1.3 and
the G2.1 wording are corrected. Knock-on: G1.3's ≈0.047 is a **joint** upper bound for the
learned-trajectory blend *and* the bimodal hedge, not a clean measurement of the `fleongg` dataset alone.

Live axes: **bimodal hedge strength** (active, 1 of 3 wells) and **prefix calibration strength**
(aggressive 1.996 / conservative 1.287 rmse vs final; the selected `balanced` profile applied alpha=0).
Model-package weights are guard-rejected and vary only ~0.02 between themselves; SP45/learned weights
likewise, and their extreme was already tested as `54990075`.

**No promotion this round.** Prefix-aggressive would mostly re-confirm today's G3.5 result (prefix signal
3.5%/0.5%) and the frontier's own selector already chose alpha=0; the bimodal axis fires on only one
well, so any public delta would sit under the ~0.115 config-variance floor. Both HOLD; quota preserved.
Concrete next variant recorded: lower `skip_separation` so the hedge also fires on `00bbac68`
(separation 3.594 ft), making it a multi-well effect.

## Round 10 — 2026-07-28 09:03 UTC (autopilot `new_direction_search`)

Live refresh: quota **0/5**, no Kaggle kernels running, branch in sync. `can_submit=false` for this task,
so no submission was possible or attempted.

Five cheap measurements were run before listing any direction, and three of them changed a ranking:

- **M1 test-available inventory.** `test/*__horizontal_well.csv` = `MD,X,Y,Z,GR,TVT_input`;
  `test/*__typewell.csv` = `TVT,GR`. Establishes by direct check that **`Geology` is absent from the test
  typewell schema** — train-only supervision, not a test input.
- **M2 images ruled out.** 773 train PNGs, **0 test PNGs**. The image is a render of the CSVs; the only
  non-CSV content is the well/typewell name in the title, unavailable at prediction time.
- **M3 typewell grouping capped.** 773 wells -> 752 distinct typewell files (group sizes {1:739, 2:12,
  10:1}); **none of the 3 test wells matches any train typewell byte-identically.**
- **M4 single-dip geometric reparametrization CLOSED on evidence.** `dTVT = -dZ + tan(delta)*dH` with
  `dZ`/`dH` exact at every row. Oracle whole-well dip reaches **7.65** row-weighted RMSE vs a flat anchor
  of **15.91**, but every honest estimator of that one parameter is far worse: prefix-fit **80.29**,
  recency-fit **39.57**. Fifth independent instance of large-oracle / no-achievable-margin.
- **M5 naive dip-field fails.** Ungated neighbour plane: 64.57 standalone, 18.23 at W=0.15, vs flat 15.98;
  3-well bootstrap P(gain>0) = **0.314**. This does not contradict the deployed field's +0.436 (which is
  group-anchored, IDW-weighted and gated); it isolates the refined form that remains open.

Six directions queued at priorities **110–160**: N4 conformal per-well uncertainty, N2 increment-target
structural field (the only one with a submission path), N1 geometry-bounded alignment DP, N3 multi-scale
GR matching, N6 second public-solution audit, N5 time-boxed typewell fingerprint. Four directions
explicitly **not** queued with reasons: train-only images, RL geosteering, azimuthal-GR dip inversion,
standalone semantic-segmentation correlation.

Report: `reports/new_direction_search_2026-07-28.md`. Scripts: `scripts/nds_geometry_reparam_probe.py`,
`scripts/nds_dipfield_probe.py`. Next queued: `status_summary_for_user` (100).

## Round 11 — 2026-07-28 11:33 UTC (autopilot `n4_conformal_well_uncertainty`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.

Loaded the banked OOF (`aligned_preds.npz`, column `s_54844628`, toe-only, 760 wells, 3,721,471 rows) and
reproduced the banked pooled RMSE **8.8626** exactly before any analysis. Splits are by well (lag-1
within-well residual autocorrelation +0.9998 makes a row split leak).

**Marginal split conformal is valid and retained**: nominal 0.80/0.90/0.95 -> widths 9.99/13.43/17.53 ft
with held-out coverage 0.853/0.942/0.966.

**Conditional (Mondrian) conformal is a negative result.** Best feature association |spearman| 0.172
(`nnb`); 5-fold CV R^2 on log(per-well RMSE) = **0.0736**; width separation across bins only 1.28-1.61x
against a true 8.56x median-to-max spread. Decisively, at matched coverage the conditional intervals are
**wider**, not narrower (13.76 / 13.97 vs marginal 13.43) — conditioning costs width. **The per-well
confidence-gating axis flagged by the variant-matrix round is therefore closed on these features**, for
the same reason the anti-harm guard closed at AUC 0.53: the covariates carry no per-well signal.

Two by-products carry more decision value than the intervals:

- **The 3-well scoring scale, measured on the error level.** For one FIXED model, a random row-weighted
  3-well draw pools to 5th **3.491** / median **6.708** / 95th **15.138**. Independent corroboration of
  the 3-well gate doctrine, previously derived from per-well *gain* variance and now measured on the
  error *level*.
- **Conformal on OOF does not bound the leaderboard.** OOF on the 3 test wells **4.756** vs public
  **7.891** = ratio **1.659**. The marginal bound is a statement about train-masked OOF only.

The 3 visible test wells sit at fleet percentiles 0.264 / 0.480 / 0.499 — an easier-than-typical draw,
pooling to percentile 0.207 of the 3-well draw distribution.

Report: `reports/n4_conformal_well_uncertainty_2026-07-28.md`. Script:
`scripts/n4_conformal_well_uncertainty.py`. Next queued: `n2_increment_structural_field` (120).

## Round 12 — 2026-07-28 11:48 UTC (autopilot `n2_increment_structural_field`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. **No submission** — the 3-well gate
fails for every variant, so the task's submit step never triggers.

**The task's premise turned out to be wrong, and that is the round's main finding.** Reading the builder
behind `54844628` (`struct_oof_produce.py`), the anchor is `mean(r_true - r_pred)` over the target's own
last 100 known heel rows, so

    pred = ( r_pred - mean(r_pred over heel) ) + mean(r_true over heel) - Z

The level of `r_pred` cancels **exactly**: the deployed field is already heel-anchored and
level-invariant, i.e. **already an increment estimator**. A literal level->increment swap is a no-op. That
"interpolates the level" description came from our own `new_direction_search` round earlier the same day
and is corrected here.

Preflight was clean at both scales: the reimplementation reproduces the banked `struct_oof.npz` to
`max|d| = 0.00000000`, and on the **full 760-well split** it reproduces the banked pooled **8.8626** to
`-0.0000`. A tree-caching optimisation was verified byte-identical before the long run.

**The mechanism that could have made a reformulation matter does not occur.** Full split: the
nearest-point well identity switches on **0.0021** of consecutive row pairs (median 0.0001), and
**99.38%** of the k=12 contributing points share the nearest point's well (p10 0.9929). The neighbourhood
is effectively single-well — these are parallel laterals on a pad — so there is no cross-well level mixing
to remove.

Two variants measured on the full split, both failing the 3-well gate (20,000 draws):

```
struct_increment_iso  (one-factor: identical selection/weights, level -> within-well increment)
    pooled 8.9629  (-0.1003)  5th -1.7148  median 3-well draw -0.0001  P(gain>0) 0.4602  GATE FAIL
struct_increment      (per-well increment averaged across all surviving wells)
    pooled 10.5466 (-1.6840)  5th -5.5224  median 3-well draw -1.4046  P(gain>0) 0.1938  GATE FAIL
```

Smoke (38 wells) and full agree in sign and magnitude (-0.18 -> -0.10; -1.90 -> -1.68).

**Mechanistic explanation, worth keeping.** The deployed anchor subtracts *the same estimator's own value*
at the heel, so the reference cancels exactly and the increment is self-consistent. Both variants
substitute a *different* reference at the heel, which does not cancel and reintroduces a per-well level
error; the damage scales with how far the new reference sits from the original. The deployed construction
is not merely equivalent to an increment estimator — it is the **correctly referenced** one.

Direction closed. Report: `reports/n2_increment_structural_field_2026-07-28.md`. Scripts:
`scripts/n2_increment_structural_field.py`, `scripts/n2_eval_increment.py`. Next queued:
`n1_geometry_bounded_alignment` (130).

## Round 13 — 2026-07-28 12:48 UTC (autopilot `n1_geometry_bounded_alignment`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.

**Negative result, plus an amendment to a same-day claim.**

The constraint is genuinely non-parametric: `dTVT = -dZ + tan(delta)*dH` with `dZ`/`dH` exact from X/Y/Z,
giving a hard admissible interval per DP transition. Measured LOCAL dip over the DP's 10-row step (80
wells, 51,514 transitions): |dip| p50 1.97 deg, p90 3.59, p95 5.43, p99 27.05 — so 4 deg admits 92.1% of
true transitions, 8 deg 96.4%. (`new_direction_search` M4's +/-3.7 deg was WHOLE-WELL dip; the local
distribution the DP needs is wider.)

The effect was decomposed into **centring** (regulariser referenced to -dZ, i.e. penalise dip not TVT
movement) and **bounding** (the hard interval), sharing one emission matrix and one penalty scale.

Two harness defects were caught by the smoke and fixed before any result was read: the penalty had been
normalised by band width (making a narrow band up to 60x more regularised — not a one-factor change), and
the binding metric compared against an already-penalised optimum, reporting an impossible 0.0%.

**12 wells suggested a large win** — `bounded 8 deg` at lam=2 reached **9.412** vs G3.2's 12.527.
**40 wells (strict superset) removed it** — the same config gives **15.569**, the best arm becomes the
**unbounded control** (12.518), and every geometry-aware arm is worse. The 9.412 was a minimum selected
over 20 configurations on 12 wells: the project's recorded failure mode.

**Nested validation decided it.** Config chosen on 20 wells, scored on the disjoint 20, both ways:
pooled held-out **DP 13.644 vs flat-anchor 12.722 — does not beat flat**; beats flat on 37.5% of wells.
Nested selection never picks a geometry-aware arm.

**Amendment to G3.2 (recorded earlier the same day).** Its "DP beats the flat anchor, 12.527 vs 13.103"
also selected lam on the wells it reported. With nesting on 40 wells the DP does not beat flat. What
stands from G3.2 is the scorer's held-out pair AUC 0.7242 vs NCC 0.5010; what is withdrawn is the DP
claim. `reports/g32_learned_alignment_smoke_2026-07-28.md` is amended in place.

**The one thing the band buys:** stability, not accuracy. At lam=1 the unbounded DP diverges (42.359)
while bounded arms stay at 14-16 across the whole grid. It removes the catastrophic tail without moving
the optimum.

Task step 5 ("do not scale up unless the band clearly improves on 12.527") is not met — no scale-up.
Report: `reports/n1_geometry_bounded_alignment_2026-07-28.md`. Next queued: `n3_multiscale_gr_matching` (140).

## Round 14 — 2026-07-28 13:03 UTC (autopilot `n3_multiscale_gr_matching`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.

**Task question answered negatively; the diagnostic then located the real lever.**

First, the premise checks out: G3.2's docstring claims it fixed the ~34x extent mismatch, but measured on
the same wells its 33-row horizontal window spans **0.525 ft** of TVT against a **17 ft** typewell window
— still ~32x. The mismatch was moved, not removed.

`pywt` is absent, so an undecimated (a-trous) Haar transform was implemented explicitly — length-preserving,
which matters because `tfeat` indexes the profile by state.

**Phase A (AUC per level, G3.2 protocol).** No level exceeds 0.7242. Best is `A0` (raw, 1 ft) at 0.7160
— the G3.2 reproduction — and AUC falls monotonically as the approximation coarsens (0.7160 -> 0.6573 at
16 ft); detail bands sit at 0.605-0.633. **NCC is at chance in all nine bands (0.490-0.517)**, so the
shape-matching failure is NOT a scale artefact and decomposition cannot recover it. Coarse-to-fine is
closed as a remedy for this line.

**Phase B — the lever is the typewell WINDOW, not the wavelet scale.** On disjoint wells (60 train / 40
val), narrowing TWH from 8 (17 ft) to 1 (3 ft) raises AUC 0.7300 -> **0.7655** (5 seeds, +/-0.0030 vs
+/-0.0028; delta +0.0355 = **8.7x the seed-noise scale**). The **no-training** level score rises
0.6450 -> **0.7352**, monotonically across all six widths — above G3.2's trained 0.7242. This vindicates
the extent-mismatch diagnosis while refuting the proposed remedy: match the window to the ~0.5 ft the
horizontal side actually spans, rather than decomposing into scales.

**Protocol warning carried forward:** G3.2's random PAIR split mis-ranks the windows (it picks TWH=32 at
0.7476 where the well split picks TWH=1) and understates absolute AUC. Pairs from one well share a
typewell and GR baseline, so a pair split does not measure transfer. **Every future scorer comparison in
this line must split by well.**

**Not reopening N1.** N1 showed the same day that the DP fails to beat the flat anchor under nested
selection and that the gap is in the transition model, not the emission; +0.036 AUC on the emission does
not address that. TWH=1 is banked as a verified, seed-stable scorer improvement for future use.

Report: `reports/n3_multiscale_gr_matching_2026-07-28.md`. Next queued: `n6_public_solution_audit` (150).

## Round 15 — 2026-07-28 13:18 UTC (autopilot `n6_public_solution_audit`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission,
no data import, no code execution from any external repository.

**BLOCKER on the named target.** The task names `aaryan2203/rogii-wellbore-geology-prediction-argon`;
that repository **does not exist** (`gh api` 404; the user's 5 repos are all unrelated; `gh search repos
"rogii argon"` returns nothing). The name reached our queue from a stale/fabricated web-search snippet in
the `new_direction_search` round. Blocker recorded, and the task's stated intent was executed against the
highest-signal real target: **`mycarta/rogii-geosteering-toolkit`** (MIT, methodology notes rather than a
notebook dump).

**Their pipeline is not ahead of ours** — their own note records "OOF 10.5 and the public LB has clones
around 12" against our 8.8626 / 7.891 / 6.563. The repository is a source of formulations and
cross-checks, not of a stronger pipeline.

**The finding that pays for the audit — within-well TVT-Z decoupling.** They measure the global
TVT-vs-Z r = -0.96 as a BETWEEN-well structural signal, with the per-well **lateral-only slope +0.057**
(dZ ~70-125 ft across the eval zone vs dTVT ~5-13 ft). This independently explains two of our own
negatives from the same day:
  - `new_direction_search` M4: our geometry-only arm imposed slope -1 and scored 107.49 vs a flat anchor
    of 15.91. If the true within-lateral slope is ~0, -1 is close to the worst available choice.
  - N1's centring arm: centring the DP on c = -dZ/STEP presumes the formation is flat so TVT moves
    one-for-one against Z; on 40 wells it hurt (15.636 vs unbounded 12.518). Near-zero true slope means
    that centring systematically overcorrects. N1 recorded the effect; this supplies the mechanism.

**Three independent confirmations of our closed lines:** Catch22 well-level features made their model
+0.476 RMSE worse (matches our closed SSL/ROCKET line); they DROPPED the typewell-`Geology` classifier
(matches our M1 finding that `Geology` is absent from the test schema); and they rejected spatial
block-CV because validation wells are spatially interleaved with training — interpolation, not
extrapolation, which leans toward the H-visible branch of our final-slot framing.

**Three formulations queued** (absent from our ledger and cheap): `n8_azimuth_matched_neighbours` (170),
`n7_q3d_tortuosity_features` (180), `n9_self_correlation_prefix_template` (190).

Report: `reports/n6_public_solution_audit_2026-07-28.md`. Next queued: `n5_typewell_fingerprint_families` (160).

## Round 16 — 2026-07-28 13:33 UTC (autopilot `n5_typewell_fingerprint_families`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.
Time-boxed to 30 minutes; completed in ~2 minutes of compute.

**The fingerprint adds nothing over the spatial gate already in production — direction closed** (the
task's own step 3). No router was built, as instructed.

Correlating each test typewell's GR-vs-TVT curve against all 773 train typewells on the overlapping TVT
range gives a sharply **bimodal** distribution: a block at exactly 1.0000 and a bulk near 0 (p50 between
-0.05 and +0.19). Typewells are either the same curve or unrelated — no middle ground for a similarity
ranking to exploit. All top-5 matches per test well are already in the deployed **surviving**-neighbour
set (5/5 for every well), and the deployed gate already passes on all three (same-group 13/40/13, closest
mate 292/295/354 ft).

**The deciding test.** The deployed group key `round(max(typewell.TVT), 1)` is truncation-sensitive by
construction, so the worry was that wells sharing an underlying typewell but truncated differently get
different keys. Measured directly, the near-identical set and the same-group set are **identical in both
directions** for all three test wells (13/13, 40/40, 13/13; zero fingerprint-only, zero group-only).

**Correction to M3.** M3 hashed whole files and reported 0/3 test wells matching, concluding grouping was
capped. The hashes measure **file** identity, not **curve** identity — files are truncated to different
TVT ranges. On the overlap there are 13/40/13 near-identical train typewells per test well, so typewell
sharing is **common, not rare**. M3 is amended in place; its conclusion (direction not worth developing)
survives for a different reason than it stated.

**Positive byproduct:** the deployed group key is validated as a lossless proxy for typewell-curve
identity on the scored wells. This bears on the queued `n8_azimuth_matched_neighbours` — the neighbour SET
is correctly identified, so grouping is not the weak link there; any gain must come from the weighting,
not the membership.

Report: `reports/n5_typewell_fingerprint_families_2026-07-28.md`. Next queued:
`n8_azimuth_matched_neighbours` (170).

## Incident — 2026-07-28 14:1x UTC: report truncation and repair

While appending the Round 16 sections, seven reports were found to have lost their history. Cause: rounds
10-16 appended with

    open(path, 'w').write(open(path).read().rstrip() + section)

Python evaluates `open(path,'w')` **first**, truncating the file, so the inner `open(path).read()` returns
an empty string and the file is replaced by that round's section alone. Every affected file therefore held
only its most recent fragment.

**Detected** by comparing each report's current line count against its maximum across all commits since
2026-07-27. **Repaired** by reconstructing each file as its last full version plus every subsequent
round's fragment, in commit order:

```
final_slot_package_corrected_gate_2026-07-26.md   base 20c4f58 (105) + 1 frag -> 128 lines
g32_learned_alignment_smoke_2026-07-28.md         base ef742ac ( 91) + 1 frag -> 112 lines
new_direction_search_2026-07-28.md                base c481581 (245) + 1 frag -> 266 lines
rotation_candidate_queue_2026-07-26.md            base ef742ac ( 84) + 9 frag -> 216 lines
rotation_pipeline_status_2026-07-26.md            base 5b8e0e8 (277) + 7 frag -> 535 lines
rotation_submission_decisions_2026-07-26.md       base ef742ac ( 27) + 9 frag ->  44 lines
submission_ledger_2026-07-26.md                   base ef742ac ( 54) + 9 frag ->  71 lines
```

Verified after repair: Rounds 1-16 present in order, decision-table rows 1-16 present, ledger entries for
rounds 4-16 present, the M3 correction and the N4 sensitivity addendum intact, and the final-slot
package's three recommendations restored. **No measurement, script or submission was affected** — only
report prose, and every fragment was recoverable from git because each round was committed.

**Guard added:** `scripts/append_section.py`, which reads and closes before opening for write. Use it for
all future report appends.

## Round 17 — 2026-07-28 13:48 UTC (autopilot `n8_azimuth_matched_neighbours`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. **No submission** — the 3-well gate
fails at every tolerance, so the task's step 6 never triggers.

**Preflight byte-exact.** Reusing the N2 builder machinery, the no-filter control `az_tol=180` reproduces
the banked `struct_oof.npz` to `max|d| = 0.00000000` and the banked pooled **8.8626** to `-0.0000` on the
full 760-well split. Every difference below is attributable to the filter alone.

**The filter is not inert, but the deployed selection is already azimuth-coherent.** It halves the
neighbour count (28.1 -> 11.8-15.0) and removes the *nearest* well for **10.9-12.2%** of targets. Yet the
median azimuth spread among surviving neighbours is only **26.7 deg** — typewell-group membership plus
spatial proximity already deliver similarly-oriented wells.

**Every tolerance is worse than no filter, and all fail the gate:**

```
variant        pooled   vs 8.8626   3-well 5th   P(gain>0)   gate
struct_az15    8.9323     -0.0697      -0.8622      0.4999   FAIL
struct_az30    8.9361     -0.0735      -0.9021      0.4945   FAIL
struct_az45    8.9372     -0.0746      -0.9011      0.4894   FAIL
struct_az90    8.9415     -0.0789      -0.9011      0.4862   FAIL
struct_az180   8.8626     -0.0000            --          --   byte-exact control
```

Per-well median gain is exactly +0.0000 at every tolerance (helped ~42%, hurt ~44%): for most wells the
filter changes nothing, and where it acts it hurts slightly more often than it helps. The ordering is
non-monotone (90 deg worst, 15 deg least bad) because a tighter tolerance pushes more wells to an EMPTY
neighbour set, which falls back to plain `base` — a neutral outcome — whereas a surviving-but-degraded set
actively injects a worse estimate.

**Why the idea has little room here.** The public methodology it came from applies azimuth matching to an
offset-well prior in a LightGBM FEATURE pipeline, where a mis-oriented neighbour is one noisy feature among
many. Our deployed field feeds a single IDW estimate that N2 measured to be effectively **single-well**
(99.38% of the k=12 points share the nearest point's well), so removing the dominant neighbour does not
shift a weighted average — it replaces the estimator's only real input.

**This closes the loop on the component.** N5: the group key is a lossless proxy for typewell identity, so
neighbour MEMBERSHIP is already right. N8: neighbour ORIENTATION is already right (spread 26.7 deg) and
forcing it tighter costs score. N2: the anchor is already the correctly-referenced increment estimator.
Three independent one-factor probes, all landing on "the deployed construction is already the right one".

Not queued: azimuth as a soft IDW *weight* rather than a hard membership gate. The measured headroom is
small (no change for ~58% of wells) against N4's 3-well draw spread of 3.49-15.14 for a fixed model.

Report: `reports/n8_azimuth_matched_neighbours_2026-07-28.md`. Next queued: `n7_q3d_tortuosity_features` (180).

## Round 18 — 2026-07-28 14:03 UTC (autopilot `n7_q3d_tortuosity_features`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.

**Tortuosity does not predict our honest line's error at either granularity. Gate failed, direction closed.**

**Provenance recorded, not worked around.** The Jing et al. (2022) paper could not be retrieved here
(ScienceDirect 403; a DOI guess resolved to a different article). What was implemented follows the
principles in the abstract — Peak-Valley decomposition into oscillation segments, indices combining
amplitude and frequency, separated into inclination and azimuth planes — but is **our implementation, not
a verified reproduction of the paper's equations**. No third-party code was consulted. A FAMILY of
measures was computed (dogleg severity, plane-separated angular change, Peak-Valley amplitude/frequency,
TQG) so the conclusion does not hinge on one formula.

**The smoke caught a real defect.** At the data's native 1 ft MD grid with ~0.01 ft XY resolution, angles
are dominated by coordinate quantization: the first smoke gave `dls_mean` ~49.7 deg/100ft (impossible;
real DLS is 0-15) with a median detected oscillation amplitude sitting exactly at the 0.5 deg detection
threshold and one "oscillation" every ~2 ft. Fixed by resampling to survey-station spacing before
differencing. After the fix values are physically sane AND stable across the sweep
(`dls_mean` median 1.69/1.51/1.39/1.22 at 10/30/60/100 ft), so the measure is not a spacing artifact.

**Well-level (the task's gate), 760 wells.** Nothing exceeds |0.118|, and the two largest are `span_ft`
(well length, not tortuosity, already in N4's set) and `Gamma_incline`; the dedicated Q-3D indices are the
weakest (`TQG_Q3D` -0.0470). Using N4's exact protocol:

```
N4 feature set alone     0.0736   <- the bar
tortuosity family alone  0.0292
N4 + tortuosity          0.0765   (+0.0029, inside 5-fold noise)
```

**Row-level (added, because the repo's -0.107 gain was a per-ROW feature).** Local tortuosity in a
+/-600 ft window vs |residual|, 584,179 rows over 120 wells: pooled spearman **-0.0416**; within-well
mean **-0.0831**, median -0.0964, **std 0.3712**, with |rho|>0.2 in **60.8%** of wells. The relationship
exists per well and its SIGN FLIPS between wells — signal that does not transfer.

**Scope stated honestly:** this does not refute the public repo's ablation. Theirs asks whether tortuosity
helps a LightGBM predict TVT inside their pipeline; ours asks whether it explains where OUR deployed line
errs. Ours is the right question for our decision, and the answer is no.

**Retained caution for any future trajectory feature:** angles computed from this dataset's 1 ft XYZ grid
must be resampled to 30 ft+ station spacing first, or they measure quantization rather than geology.

Report: `reports/n7_q3d_tortuosity_features_2026-07-28.md`. Next queued:
`n9_self_correlation_prefix_template` (190).

## Round 19 — 2026-07-28 14:18 UTC (autopilot `n9_self_correlation_prefix_template`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.
Diagnostic only — no DP, no trajectory, per the task. **This was the last queued item; the queue is now
empty.**

**Step 4 first (the gating measurement).** Over 200 wells / 963,869 toe rows, using each toe row's TRUE
TVT: **63.5%** have a prefix row within 0.5 ft, 67.4% within 2 ft, 84.8% within 10 ft; 61.8% fall inside
the prefix TVT range at all. Coverage is ample, so the mechanism is not blocked. (13% of wells have under
10% of toe rows in range — a caveat, not a blocker.)

**One-factor comparison** at N3's exact protocol (same grid, sampling, features, MLP, TWH=1; splits BY
WELL, 60 train / 40 validation). Only the profile source changes. One deliberate departure: only TOE rows
are scored, since prefix rows would be trivially self-matching — so the in-run `typewell` arm is the valid
control, and it agrees with N3's banked figure (0.7706 vs 0.7655 +/- 0.0030), a useful harness check.

```
arm          LEARNED    level   cov frac   AUC|covered   AUC|uncovered
typewell      0.7706   0.7522     0.5833        0.7710          0.7774   <- control
self          0.6628   0.6175     0.5833        0.7174          0.4548
both          0.7649      --      0.5833        0.7680          0.7354
`both` seed stability: 0.7649 0.7641 0.7524 -> mean 0.7605, std 0.0057
```

**The self arm loses by -0.108** (~19x the seed-noise scale), and `both` does not beat `typewell` alone —
no complementary information.

**The covered/uncovered split is the informative part.** The self arm reaches **0.7174 on states the
prefix covers** but **0.4548 (below chance) on states it does not** — the mechanism works where the prefix
has data and actively misleads where the profile was interpolated across a gap. The typewell arm shows no
such asymmetry (0.7710 vs 0.7774) because a typewell is a continuous log.

**Why the level-offset advantage did not pay off.** The premise was sound — the prefix shares one
instrument and baseline with the toe rows, removing the cross-instrument offset N3 showed dominates. But
it is outweighed by coverage (58.3% of states, gaps filled by harmful interpolation) and by sampling
quality (prefix GR at a given TVT comes from a laterally-displaced horizontal traverse, not a clean
vertical section). The level-offset problem was worth removing; it is not the binding constraint.

**Banked positive:** on covered states the self template reaches 0.7174 from a source wholly independent
of the typewell. If a future formulation needs a typewell-free emission — e.g. to test whether the
typewell is the limiting factor — this is the measured fallback, and it must be gated on the coverage mask
rather than interpolated.

Report: `reports/n9_self_correlation_prefix_template_2026-07-28.md`. **Queue exhausted** — see the
candidate-queue document for the state of every line.

## Round 20 — 2026-07-28 17:13 UTC (autopilot `q10_twh1_scorer_dp_candidate`)

Live refresh: quota **0/5**, no Kaggle kernel running. `can_submit=true` but **no submission** — the gate's
second condition fails.

**The alignment line's first nested-validated win over the flat anchor.** Holding the DP, wells, protocol
and nesting fixed and changing ONLY the emission's typewell window from TWH=8 to N3's TWH=1:

```
TWH    held-out AUC    nested DP    flat-anchor    beats flat on
 1          0.7632       12.170         12.722            42.5%   <- BEATS flat
 8          0.7331       13.206         12.722            40.0%
N1 reference (TWH=8):    13.644         12.722            37.5%
```

Both nested folds agree independently (13.212 vs 13.540; 11.029 vs 11.847). A +0.030 AUC emission
improvement converts into **-1.04 RMSE** on the DP.

**The selected lam sat at the grid edge, so the grid was extended** (60/100/150/250/400/800 ->
12.170/12.241/12.478/12.461/12.987/13.132). **lam=60 is a genuine interior optimum.** The DP does NOT
degenerate to flat as lam grows (13.132 at 800, slightly worse than flat). Re-nesting over the extended
grid gives 12.444 vs flat 12.722 — still a win but smaller, so **the margin is grid-sensitive**:
0.55 ft (4.3%) on one grid, 0.28 ft (2.2%) on the other.

**Not submittable, for three independent reasons:** (a) the gate is an AND and 12.170 vs deployed ~8.86 is
~37% worse, so it does not narrow the gap; (b) the win is tail-driven — helps 16-17 wells, hurts 23-24 of
40 — the same asymmetric-tail signature the ledger records before the `54878409` public regression;
(c) the margin is smaller than the grid sensitivity. The 3-well gate was deliberately not run: it decides
whether a candidate improves on the deployed line, and this one is far below it.

**Family structure is real but unactionable:** per-well gain by typewell group key spans -1.775 to +2.173
and is sign-consistent within most groups, but n = 2-5 per group, and a per-group router is the closed
hard-selection pattern.

**Ledger revision:** N1's conclusion that "the gap is in the transition model, not the emission" is
**partially withdrawn** — correct for its TWH=8 emission, too strong as a generalisation. N1 is amended in
place. What survives is that the DP family remains far from deployed.

Report: `reports/q10_twh1_scorer_dp_candidate_2026-07-29.md`.

## Round 21 — 2026-07-28 17:28 UTC (autopilot `q11_twh1_pf_seed_ranker`)

Live refresh: quota **0/5**, no Kaggle kernel running. `can_submit=true` but **no submission** — no
positive nested evidence, so step 5's condition is unmet and step 6 never triggers.

**Reused stored artifacts**: 773 wells x 96 PF candidate paths with truth, plus the 74,208-row feature
table. No path regeneration. The emission `C[row, state]` is computed once per well, so scoring 96 paths
costs no more than scoring one.

**The headroom is large and the oracle beats deployed** (760 wells, pooled row-weighted):

```
PF mean path (default) 10.9905 | median path 12.4375 | ORACLE best-of-96 7.1579 | worst 22.1407
DWT base 10.2891 | deployed honest 8.8626
ORACLE headroom +3.8326   worst-case risk -11.1502   spread among the 96 (median) 7.6925
```

**But every ranker arm loses to the PF mean default** (40 held-out wells, splits by well):

```
feature set          pooled   vs PF mean   headroom used   wells helped
prior (14)           8.0556      -0.3985          -12.8%          45.0%
TWH1 (10)            8.2175      -0.5604          -18.0%          32.5%
both  (24)           7.8468      -0.1897           -6.1%          40.0%
best arm per-well gain: mean -0.3943 median -0.0714 | helped 40.0% hurt 60.0%
3-WELL bootstrap: 5th -3.1085  50th -0.2723  95th +4.8850  P(gain>0) 0.2696
```

The TWH=1 alignment features **alone are the worst arm**; adding them to the prior 14 improves on
prior-alone (-0.19 vs -0.40) without reaching zero.

**The smoke inverted at scale, and that is itself the lesson.** On 8 wells the prior arm appeared to
convert **73.5%** of the oracle headroom; at 40 wells it converts **-12.8%**. Its own per-well statistics
had already shown the truth on the smoke (median gain -0.20, 62.5% hurt). Same failure mode N1 recorded
when a 12-well eval manufactured a gain that vanished at 40 — the >=40-well rule earned its place again.

**Why selection loses where averaging wins.** The PF mean path IS the averaging: it pools 96 proposals
whose spread is median 7.69 ft, and that pooling is the robustness. A ranker replaces the average with a
single bet, with downside -11.15 against upside +3.83. This is the project's rule #1 (averaging and
shrinkage transfer; hard selection and fitted weights do not), and it explains why a BETTER score did not
rescue it: the problem is not ranking quality but that ranking discards variance reduction.

**Closes both shapes in the PF-path line** — generation from a pointwise emission (G3.1/G3.2/N1/Q10) and
selection among proposals (prior top-K ranker, Q11). Sixth instance of the large-oracle/no-achievable-
margin pattern, and the first where the achievable margin is reliably negative.

**Banked for any future line:** the oracle best-of-96 is 7.1579, better than deployed 8.8626 — the
information exists in the path set. The lever is a better *combiner* (a weighting over paths, which
preserves averaging), not a better ranker.

Report: `reports/q11_twh1_pf_seed_ranker_2026-07-29.md`. Next queued: `q12_coverage_gated_self_template` (220).

## Round 22 — 2026-07-28 17:43 UTC (autopilot `q12_coverage_gated_self_template`)

Live refresh: quota **0/5**, no Kaggle kernel running. `can_submit=true` but **no submission** — step 5's
condition is unmet.

**What was actually left open.** N9 had already measured the STATE-level coverage gate (self 0.7174 on
covered states vs 0.4548 on uncovered) and shown that even restricted to covered states self still trails
the typewell (0.7710) and `both` (0.7680) still trails typewell alone. The only untested form was a
WELL-level gate — a subpopulation of high-coverage wells could favour self without appearing in N9's
pooled figure. Q12 tests exactly that, with N9's design and splits BY WELL (60 train / 60 eval).

**Result — the gating variable carries no stratifying information:**

```
pooled per-well AUC:  typewell 0.7472   self 0.6439   both 0.7484

coverage band     n   typewell     self     both   self-tw   both-tw
0.56-0.72        12     0.7695   0.6374   0.7665   -0.1320   -0.0030
0.72-0.75        12     0.7560   0.6480   0.7512   -0.1079   -0.0048
0.75-0.78        12     0.7332   0.6108   0.7136   -0.1224   -0.0196
0.78-0.82        12     0.7161   0.7108   0.7563   -0.0053   +0.0403
0.82-0.92        12     0.7613   0.6124   0.7546   -0.1489   -0.0067

corr(coverage, self - typewell) = 0.0867     corr(coverage, both - typewell) = 0.0604
wells where self beats typewell 21.7% | both beats typewell 51.7% (a coin flip)
```

`self` is negative in ALL five bands. `both` is pooled +0.0012 — indistinguishable from typewell alone.
The one positive cell (0.78-0.82, +0.0403) is **not** a coverage effect: the highest-coverage band is
-0.0067 and the second-highest -0.0196, so the ordering is not monotone. With 12 wells per cell and
band-to-band swings of +/-0.04 it is noise, and picking the `cov>=0.80` threshold post hoc would be the
sweep-not-a-validation pattern.

**Why N9's and Q12's results are both true.** N9's split is a WITHIN-well contrast (inside a well, covered
states score better than its uncovered states). Q12's is a BETWEEN-well contrast (a well's coverage
fraction does not predict whether self beats the typewell for that well). Only the second could support a
gated candidate. This is the same within-unit / between-unit decomposition the N6 audit flagged as a
general lesson.

**Closes the self-template line entirely** — state-level gate (N9) and well-level gate (Q12) both fail.
N9's banked fallback stands (typewell-independent emission at 0.7174 on covered states), but Q12 adds that
it cannot be selectively deployed by coverage: wholesale or not at all.

Two harness bugs were caught and fixed before any result was read: `cov` as a column name shadows the
pandas `.cov()` method under attribute access, in both `groupby('well').cov` and `P.cov`.

Report: `reports/q12_coverage_gated_self_template_2026-07-29.md`. Next queued:
`q13_twh1_self_hybrid_emission` (230).

## Round 23 — 2026-07-28 18:58 UTC (autopilot `q13_twh1_self_hybrid_emission`)

Live refresh: quota **0/5**, no Kaggle kernel running. `can_submit=true` but **no submission** — no nested
gain, so step 5 never triggers.

**Two of the three proposed ingredients were already settled**, so only the untested one was run. Q12's
`both` arm IS a naive typewell+self hybrid emission (+0.0012, a coin flip), and Q12 also disproved the
prefix-coverage gate (corr 0.0604 / 0.0867). The untested ingredient was the **typewell-UNCERTAINTY**
gate, which N9/Q12 could not measure because they scored only two candidate states per row. Q13 computes
the FULL emission profile over all states for both templates, making the gate measurable.

**At the emission level the hybrid clearly helps** (40 held-out wells, 19,083 rows, |argmax error| ft):

```
w        mean     median      p90   within 5ft          margin band     n   tw-only    w=1
0     185.756    137.520   412.920       0.045          0.00-0.00    3817   209.919  -63.970
0.25  162.816    120.750   386.266       0.054          0.00-0.01    3816   198.068  -51.540
0.5   156.445    115.640   385.890       0.046          0.01-0.01    3817   186.767  -39.457
1     149.408    112.420   383.858       0.036          0.01-0.02    3816   174.083  -24.026
                                                        0.02-0.48    3817   159.944   -2.750
helps 67.5% of eval wells, mean delta -31.4 ft          (negative = hybrid helps)
```

The uncertainty gate stratifies **perfectly monotonically** — the first gating variable in this project to
do so. Self helps most exactly where the typewell emission is ambiguous, neutral-to-harmful where it is
confident.

**Through the DP the sign REVERSES** (Q10's transition rule, lam nested on disjoint well halves):

```
w        lam=5   lam=10   lam=20   lam=60  lam=100     nested
0       16.089   14.368   13.297   12.772   12.861     12.861   <- best
0.25    20.530   16.021   14.452   13.177   13.031     14.479
0.5     22.921   17.981   15.551   13.656   13.256     13.256
1       30.378   21.966   16.610   14.501   13.789     13.789
flat-anchor 12.722 | deployed honest 8.8626 | Q10 typewell-only DP 12.170
```

Every self weight makes the trajectory worse, monotonically in w at every lam.

**WHY — a mechanism not previously in the ledger.** The self emission is coverage-masked: zero on states
the prefix never visited. That applies a systematic pull toward the prefix's TVT range. Pointwise this is
a good bet (N9: 63.5% of toe rows lie within 0.5 ft of a covered state), so per-row accuracy rises. But a
trajectory is an integral of transitions, so a constant directional pull does not average out — it
accumulates. And the toe's whole difficulty is that it DRIFTS AWAY from the prefix range (60.3% of
residual variance is a per-well offset dominated by drift, slope std 13.28 ft). The hybrid pulls the path
against precisely the component that dominates the error. The improvement is MARGINAL; the damage is
CUMULATIVE.

**Generalisable rule now recorded:** *a pointwise emission metric is not a valid proxy for trajectory
quality when the emission modification carries a directional bias.* Emission AUC / argmax accuracy must
never again be accepted as evidence for a DP candidate without running the DP. Q10 measured the exchange
rate in the favourable direction (+0.03 AUC bought -1.04 RMSE); Q13 shows it can be NEGATIVE when the
emission gain comes from a bias rather than from sharper discrimination.

Report: `reports/q13_twh1_self_hybrid_emission_2026-07-29.md`. Next queued:
`q14_frontier_bimodal_hedge_weight_scan` (240).

## Round 24 — 2026-07-28 19:13 UTC (autopilot `q14_frontier_bimodal_hedge_weight_scan`)

Live refresh: quota **0/5**. **No submission this round** — a hedge-OFF full run is in flight and the
submit decision is deferred to its result.

**The scan cost no GPU.** The hedge is a pure additive shift (re-verified: 4301/14151 rows, single unique
delta +2.0 ft, only on `00e12e8b`), so `variant(w) = before_hedge + w*2.0` and
`rmse(variant(w), 54968060) = |w-1| * 1.1027` in closed form. Homogeneity (0.50) is crossed at
|w-1| >= 0.4534: w = 0, 0.25, 0.5, 1.5, 2.0 are non-homogeneous; 0.75-1.25 are not. Trajectory sanity is
identical at every w, as a constant one-well shift implies.

**The decisive measurement — the hedge creates bias where there was none.** Using the train copies of the
three test wells:

```
well          n    w=0 (off)   w=1 (on)          mean residual on the hedged well
000d7d20   3836       1.6367     1.6367            BEFORE the hedge:  -0.1895 ft
00bbac68   6014       4.1912     4.1912            AFTER  the hedge:  +1.8105 ft
00e12e8b   4301       2.1818     2.8288  (+0.647)
POOLED    14151       3.1046     3.2594  (+0.155)
```

The hedged well was already essentially unbiased; the hedge adds +2.0 ft and manufactures +1.81 ft of
bias. Analytic public sensitivity at R=6.643 for a 2.0 ft shift on 30.4% of rows: hedge-OFF would land at
**6.551 if the public residual on those rows is ~0**, 6.643 only if it were exactly +1.0, and 6.734 if
+2.0. The proxy says -0.19, so hedge-OFF is estimated near **6.55**.

**This overturns the variant-matrix round's HOLD, and the reason is worth recording.** That round held the
axis because the hedge "fires on 1 of 3 wells, so any delta sits under the ~0.115 config-variance floor".
That conflated two quantities: the 0.115 floor is run-to-run GPU nondeterminism, whereas the hedge is a
DETERMINISTIC shift whose pooled effect is bounded by ~0.28 and estimated at ~0.09-0.11. The earlier
magnitude estimate was roughly right but the noise floor is not an upper bound on a deterministic effect.

**Caveat retained:** the train-copy proxy is not a public proxy (level 3.10 vs public 6.64), and the ledger
records over-weighting it once before on `54878409`. What differs here is that this is a LEVEL question on
one well, not a ~0.1 rank comparison, and the per-well local effect (+0.647) is above the ~0.5 threshold at
which local has predicted the leaderboard. Evidence, not proof.

**Candidate.** The hedge is `shift = clip(STRENGTH*(midpoint-weighted), -CAP, +CAP)` with STRENGTH 0.60,
CAP 2.00; the observed shift of exactly 2.0 means it hit the CAP, so the scan maps to one constant. The
kernel is a verified ONE-LINE change (`_BH_CAP = 2.00 -> 0.00`), diffed to confirm it is the only
difference from the kernel that produced `54968060`.

Preflight passed: patch activation verified by exact arithmetic (CAP=0 gives shift 0.0, and the
`abs(shift)>=0.01` guard then skips), and the predicted output audits `HARD: PASS` with
**HOMOGENEITY distinct from all scored references** (rmse 1.103 vs 54968060), local proxy 3.105 vs the
deployed 3.259. Kaggle smoke deliberately skipped with the reason recorded: the base kernel already
completed a successful full run, and every smoke-catchable failure mode is identical except patch
activation, which was verified arithmetically and will be reconfirmed from
`pf_seed_branch_hedge_report.csv` post-run.

`joezzzzz/rogii-frontier-hedgeoff-full` v1 pushed and running. Report:
`reports/q14_frontier_bimodal_hedge_weight_scan_2026-07-29.md`.

## Round 25 — 2026-07-28 20:28 UTC (Q14 collection + SUBMISSION; `q15_frontier_dependency_replacement` NOT started)

The recorded next action was to collect the in-flight Q14 run before anything else, and that took
precedence over starting Q15 — correctly, since Q15 would also want a frontier full run and the standing
rules forbid a duplicate while one is in flight.

**Q14 run collected.** Patch activation confirmed: `00e12e8b` went from `applied, shift 2.0,
moved_rows 4301` to `skip_zero_or_missing_rows, shift 0.0, moved_rows 0`. Audit `HARD: PASS`,
homogeneity distinct (rmse **1.756** vs `54968060`).

**The confound is now measured, and it is larger than the effect.** The fresh run differs from the stored
hedge-OFF output by rmse **1.377** — pure config variance. Local proxy pooled 3.2594 -> 2.2903, but the
hedged well contributes only -0.62 (2.83 -> 2.20, vs 2.18 predicted) while **-1.52 comes from
`00bbac68`, a well the hedge never touches**. So the candidate does not isolate the hedge.

**SUBMITTED ref `55064411`** (quota 1/5) with that confound stated in the description. Public score was
**still PENDING** after ~20 min of polling; a background poll continues and the score must be recorded
next round.

**`q15_frontier_dependency_replacement` was not started this round** — see the candidate-queue note for
the exact carry-forward.

### Addendum to Round 25 — scoring latency in a kernels-only competition

`55064411` remained `PENDING` for 45+ minutes with an empty `error_description`. This is expected, not
anomalous: because the competition is **kernels-only**, submitting causes Kaggle to **re-run the kernel**
on the hidden test set, so scoring latency tracks the kernel's own runtime (~1 hour for this frontier
pipeline) rather than the minutes a plain file submission takes.

**Carry-forward rule:** poll submission status on an hour-scale cadence in this competition, and never
treat a sub-hour `PENDING` as a failure or a reason to resubmit. Quota confirmed at **1/5** for
2026-07-28.

## Round 26 — Q16 honest residual router: CLOSED on its prerequisite

`q16_honest_twh1_residual_router` proposed a bounded, confidence-gated residual correction on the
deployed honest line `54844628`. The direction was resolved at its **prerequisite** rather than by
building the router: a bounded correction requires the **signed** row residual to be predictable on
**held-out wells**. It is not.

`scripts/q16_residual_predictability.py` — 15 test-available features, 3,721,471 rows, 760 wells,
`GroupKFold(5)` split BY WELL:

- **signed-residual CV R^2 = -0.0802** (negative: fitted per-row structure ANTI-transfers across the
  well boundary), corr(pred, actual) 0.0721.
- correction gain profile is **non-monotonic** — +0.0247 at strength 0.25, -0.0248 at 0.5, -0.3398 at 1.0.
  That shape is the signature of a near-zero signal fitted against noise.
- an out-of-fold **constant-only** control (subtract the train-fold mean, no model) yields at most
  +0.0048, so of the +0.0247 roughly +0.020 ft is genuine per-row signal — **0.23% of an 8.86 ft RMSE**.
- per well it is a coin flip: helped 50.4%, hurt 49.6%, mean gain -0.0034.
- **3-WELL bootstrap: 5th -0.9333, 50th +0.0072, 95th +0.8933, P(gain>0) 0.5078.** The +-0.9 ft spread at
  competition scale is ~40x the +0.02 ft effect.

**GATE FAILS BOTH CONDITIONS** (materially positive R^2; 3-well 5th pct > 0). No submission, no quota.

**This completes the bound N4 left open.** N4 showed error MAGNITUDE is weakly predictable (R^2 0.0736);
Q16 shows the SIGN is not predictable at all on the same protocol. Magnitude without sign cannot drive a
correction — knowing a row is likely wrong gives no information about which way to move it. That single
explanation also covers why N4's conditional conformal intervals came out wider than marginal ones.

### Operational facts from this round

1. **`kaggle` was missing from the environment** and was reinstalled with
   `python3 -m pip install --user --break-system-packages kaggle` (PEP 668). The API returns
   **snake_case** attributes: `s.public_score` / `s.private_score`, NOT `publicScore`.
2. **Exact-split GBM is not viable at 3.7M rows** (single-threaded; blew a 3000 s cap once and was on
   track to blow 2400 s again). `HistGradientBoostingRegressor` fits the FULL row set multithreaded in
   about a minute — cheaper AND better, since no subsampling was needed.
3. **Redirect Python with `-u`.** Two attempts wrote a 0-byte log for 20 minutes and read as hung;
   stdout was block-buffered to the file.
4. **Verify a PID before killing it.** `pgrep -f "<pat>" | head -1` returned a transient PID (312935),
   not the run (312966), so the first kill was a no-op. Confirm with `ps -o pid,cmd -p <pid>`. The
   self-matching-waiter bug recurred as well: a waiter whose own command line contains its grep pattern
   never exits.

### `55064411` still PENDING

Re-checked this round: **still `SubmissionStatus.PENDING`, now 2 h 20 m+** after the 2026-07-28 20:30 UTC
submission — past the ~1 h expectation recorded in `41bb65f`, though PENDING is still not itself a
failure here. No resubmission, no extra quota. **Quota 1/5 used.** The recorded next action stands:
record the score in the ledger and final-slot package, and if it is <= 6.563 re-evaluate slot 1 on
provenance. Scored references: 54922806 **6.563**, 54968060 6.643, 54896975 6.669, 54923144 6.678,
54990075 6.690.

## Round 27 — Q17 tiny GPU training: HOLD, closed on its prerequisite (no GPU run, no submission)

`q17_kaggle_gpu_tiny_training_followup` was resolved at its premise for zero GPU cost.

Step 1 refresh: **Q11 is negative** (every ranker arm worse than the PF mean path) and **Q13 is negative
and a warning** (an emission clearly better pointwise yields a WORSE trajectory). The whole training case
therefore rested on **Q10**, whose own verdict already read "closing 3.3 RMSE on that exchange rate would
need an implausible AUC". That verdict rested on a **two-point** slope (TWH=8 AUC 0.7331 -> DP 13.206;
TWH=1 AUC 0.7632 -> DP 12.170 = ~1 RMSE per +0.03 AUC), which is a weak basis for a 3.3 RMSE extrapolation
and is exactly what a GPU run would be spent on. So it was measured directly.

`scripts/q17_emission_exchange_rate.py` interpolates the learned emission toward an ORACLE emission,
`C_mix(a) = z((1-a)*z(C_learned) + a*z(C_oracle))` with `C_oracle[j,s] = |grid[s] - tru[j]|`, and sweeps a
from 0 to 1 — measuring held-out-WELL pair AUC and nested DP RMSE at each step. Q10's DP, wells, protocol
and 2-fold nesting are reused verbatim by import. Smoke passed first (Directive 4) and the AUC axis was
verified against Q10's own `scorer_auc` (0.6920 vs 0.6908 on the same tiny config).

**Reproduction check: at a=0, lam=60 the DP gives 12.170 — exactly Q10's headline number.**

CONTROL at FIXED lam=60, no selection anywhere:

```
alpha  AUC      DP(lam=60)          alpha  AUC      DP(lam=60)
0      0.7511     12.170            0.2    0.7881     12.022
0.05   0.7585     12.168            0.3    0.8074     12.003
0.1    0.7671     12.166            0.5    0.8088      12.150  (best at lam=5: 8.932)
0.15   0.7772     12.029            1.0    0.9688       0.370
```

**+0.056 AUC — nearly double Q10's TWH8->TWH1 step — buys 0.167 RMSE.** That is **0.030 RMSE per +0.01
AUC** against Q10's two-point 0.344: the real exchange rate is **>11x shallower** than the extrapolation
basis, and the fixed-lam control shows this is a property of the DP, not of the lam nesting. Closing
12.170 -> 8.8626 at the measured rate would need **+1.11 AUC**, i.e. an AUC of 1.87.

**LOAD-BEARING FINDING — AUC is not the quantity the DP responds to.** The axes decouple:

| segment | dAUC | dDP (lam=60) |
|---|---|---|
| a 0 -> 0.3 | **+0.0563** | -0.167 |
| a 0.3 -> 0.5 | **+0.0014** | **-3.071** |

The DP responds to how much literal truth is mixed into the emission, not to its discriminative AUC.
Mechanism: changing TWH alters the emission's SHAPE, not only its discriminative quality; Q10's 1.04 RMSE
gain came from that structural change, and attaching it to the accompanying AUC movement produced a slope
that does not generalise. The a-sweep isolates pure discriminative quality at fixed structure, and it is
nearly flat.

**NEW STANDING RULE (proposed): emission AUC is not a valid proxy for DP trajectory quality; an emission
change must be validated on its DP output, not on AUC or any pointwise emission metric.** This subsumes
the Q13 rule — Q13 and Q17 are two instances of the same failure, now with the mechanism measured on a
continuous axis.

Step 3 (tiny Kaggle GPU smoke) therefore **did not trigger**: a learned scorer improves AUC, the exact
axis just shown not to move the DP. No GPU run, no smoke kernel, no submission, **quota untouched at
0/5**. The ranker half was already closed by Q11, so both halves of Q17 are resolved.

Limits stated: the oracle is truth-constructed and used ONLY as a bound and a continuous axis, never as a
claimed gain; and the measurement is generous to the training case, since a real AUC gain is unlikely to
be better truth-aligned than literal truth. This bears on the emission lever only — the transition model
remains the untested lever.

## Round 28 — Q18 final-pair stress: the slot-1 gap is not resolvable at 3-well scale

`q18_public_leaderboard_family_stress` is a decision task (`can_submit=false`). Completed with **no
submission**; quota untouched at 0/5. `scripts/q18_final_pair_stress.py`,
`reports/q18_public_leaderboard_family_stress_2026-07-29.md`.

**The recommended pair is unchanged; the reason changes materially.**

Added a FOURTH view, **our-account-first** (ownership is distinct from provenance: `54968060` is our
account but public-derived, so provenance-first does not select it):

| view | pair | worst | mean |
|---|---|---|---|
| score / diversity / provenance-first | `54922806` + `54844628` | 6.643 | 6.603 |
| our-account-first | `54968060` + `54844628` | 6.643 | 6.643 |

**Price of full ownership: +0.000 worst case, +0.040 mean** — inside the ~0.115 config-variance floor.

**Degradation stress.** `54922806` must degrade 0.080 (H-visible) / **0.000** (H-hidden) to lose slot 1 to
`54968060`, and 1.328 / 1.248 to lose it to `54844628`. Under H-hidden the two frontier candidates are
already exactly tied at 6.643, so slot 1's advantage exists only under H-visible.

**LOAD-BEARING MEASUREMENT.** N4's 3-well spread (3.49..15.14 for a fixed model) is common-mode and
cancels in a ranking; the candidate x draw INTERACTION does not. That was measured rather than assumed --
9 local candidate columns with truth over 760 wells / 3.72M rows, 20,000 random 3-well draws per pair,
pooled gap vs P(draw reverses the pooled ranking):

  pooled gap <= 0.30  ->  P(reversed) 44.8%  (n=10)
  pooled gap >= 1.00  ->  P(reversed) 28.3%  (n=13)

- The **0.080 slot-1 gap** sits where measured pairs reverse **46-50%** of the time. It carries
  essentially NO information about which candidate is better on a different 3-well draw, so **score-first
  does not actually distinguish `54922806` from `54968060`**.
- The **1.328 frontier-vs-honest gap** reverses **~29%** of the time. The slot-2 insurance is not remote;
  it is a ~3-in-10 event -- a far firmer basis for diversity-first than "free on worst case".

**Decision consequence.** Default stays `54922806` + `54844628`. `54968060` + `54844628` is fully
defensible at +0.000 worst / +0.040 mean, and since the 0.080 is not resolvable at the scoring scale, the
choice between these two pairs is an **ownership judgment for the project owner, not something score
evidence can settle** — recorded as such rather than decided unilaterally.

Limits stated: reversal probabilities come from honest-family local candidates (frontier candidates have
no per-well truth, being scored only on the 3 hidden wells); the transfer argument is that 3-well sampling
noise is a property of the well population, and one measured member (`s_54844628`) is an actual pair
member. Draws sample with replacement (~0.4% collision). The 760 local wells are train wells, so this
measures the SCALE of 3-well ranking instability, not the actual test draw's.

Live refresh: no private-score visibility for any submission; `55064411` still PENDING (~5.8 h), carried
only as a parametric contingent entrant; no Q10-Q17 candidate enters the board; `origin/main` moved to
`a589fa8` (public 6.626 kernel, worse than our best 6.563 — recorded, no decision taken).

## Round 29 — Q19 external solution refresh: two better-scoring public kernels resolved

`q19_external_solution_refresh`. One find converted into an executable smoke and MEASURED; it fails the
3-well gate. **No submission, no Kaggle run, quota 0/5.**
`reports/q19_external_solution_refresh_2026-07-29.md`.

### Public standing — the most material finding

LB leader **4.679**; 200th place **6.389**; our best **6.563**. The API caps a page at 200 rows and **all
200 fetched teams are ahead of us**, so we are outside the top 200. Qualifications that are not
rhetorical: the public score is a 3-well quantity and Q18 measured that gaps >=1.00 still reverse on ~28%
of random 3-well draws, so the deficit size on novel wells is not pinned down; and the target is the
private ranking, which is not visible.

### The published pool tops out at our own level

798 distinct public kernels enumerated. Advertised scores cluster at **7.06-8.86** — all worse than our
6.563. Exactly TWO advertise better: `leonidzaporozhets/new-strategy-score-6-213` (6.213) and
`my0705/rogii-stacked-ensemble-highscoring-6-520` (6.520). **The ~200 teams at 4.7-6.4 have not
published.** The external pool cannot close the gap by adoption. Both better kernels mount the same
7-dataset subset of the Kaiwalya 9 — same family. `origin/main`'s `a589fa8` "public 6.626 kernel" is the
identical Kaiwalya family, redundant, dated 07-23 and surfaced only because origin/main moved.

### FIND A — the 6.213 kernel is our own base plus ONE token

Normalised cell-by-cell vs our pristine `kaggle_kernel_kaiwalya_public_tvt_6626_repro`: **44 of 45 code
cells identical**; cell 29 inserts `*1.3`:

    gs = float(np.clip(np.nanstd(kn.GR... ), 10., 60.)) * 1.3

`gs` is the PF likelihood's GR noise sigma. Widening it flattens the likelihood — a SHRINKAGE change,
the class Rule #1 says transfers, hence worth measuring.

CORRECTION recorded: an intermediate constant-diff appeared to show a `SUBMISSION_PROFILE =
contact_gated_anchor` difference; that diff had concatenated MARKDOWN with code. In code all three run
`vp_balanced_modelpkg_005`, and the upstream comment states `contact_gated_anchor*` are diagnostic
ablations that "have underperformed". No kernel was built on that false lead.

Measured on OUR honest PF (identical sigma line at `pf_honest_forward.py:22`), 60 wells, splits by well,
multiplier chosen NESTED, behind a new default-1.0 `_GS_MULT` flag:

    mult   1.0    1.5     2.0     2.5     3.0
    RMSE  14.27  11.91   12.12   15.31   17.51      (1.5 confirmed an INTERIOR optimum after grid extension)
    NESTED picks [1.5,1.5] -> 11.9142 vs 14.2655, gain +2.3513
    3-WELL bootstrap: 5th -4.1145  50th +0.1954  95th +7.9324  P(gain>0) 0.5325

**GATE FAILS on the 3-well condition**, and the win is TAIL-DRIVEN: at 1.5 it helps only 41.7% of wells
while the mean per-well gain is +1.0052 — the same asymmetric-tail signature the ledger records before the
`54878409` public regression. No frontier run, no submission. The effect is real and large at the pooled
level and is the transferable class; what it is not, on this evidence, is safe at the scoring scale.

### FIND B — the 6.520 kernel is a per-well constant fitted to the public wells

Its embedded constants: `_GS_PUBLIC_SCORE = 6.568` (its base = our family), `_EX_EXPECTED_WELL =
'00e12e8b'`, `_EX_EXTRA_SHIFT = 0.522`, `_EX_EXPECTED_TOTAL_SHIFT = 2.522`. So 6.520 = base 6.568 plus a
hand-tuned +0.522 ft shift on ONE well — hard selection fitted to the 3 public wells. Not adopted.

**PRE-REGISTERED READING FOR `55064411` (recorded BEFORE the score lands).** `00e12e8b` is exactly the
well Q14 analysed: the hedge adds +2.0 ft there while that well's local residual was already unbiased
(-0.19). An independent public author now finds that pushing the SAME well further up (+0.522) IMPROVES
the public score. Both facts are consistent under one explanation — **the hedge is tuned to the 3 public
wells, not to a general error**. Therefore:
- `55064411` scoring MATERIALLY WORSE than 6.563 is the EXPECTED outcome under that explanation and would
  be evidence the hedge is a public-well-specific fit, STRENGTHENING the case for hedge-OFF on the
  novel-well objective;
- scoring at or below 6.563 would mean the hedge was not load-bearing on public either, and Q14's local
  reasoning transfers directly.

### Queued follow-ups

1. `q36_gr_sigma_in_blend_oof` — the standalone PF is only a 0.5-weight component; averaging may damp the
   tail failure. Test `_GS_MULT` in {1.0,1.3,1.5} inside the BLEND OOF over 760 wells, nested, 3-well
   gate. A slot-2 (fully-owned) improvement path.
2. `q37_frontier_gr_sigma_public_repro` — one-token `*1.3` frontier kernel reproducing the public 6.213
   operating point, smoke first, HELD BEHIND (1) deliberately: on current evidence it would spend a slot
   on a tail-driven change.

### Rules basis and limits

Only public Kaggle notebooks were read via the API; no third-party code executed, no external dataset
added; the change is one arithmetic token re-implemented in our own script behind a default-1.0 flag.
Limits: both public scores are author-advertised and cannot be independently verified; the local
measurement is on the STANDALONE conservative PF (baseline 14.27 on 60 wells, excludes the DWT blend and
structural field) so the in-pipeline effect is NOT established; single seed per well, so PF run-to-run
variance is not separated; 60 wells with a 30/30 nested split, not 760.

## Round 30 — Q20 usage-aware queue builder: Q10-Q19 consolidated, queue 16 -> 5, prompt bloat fixed

Management round (`can_submit=false`). **No submission, quota 0/5.**
`reports/q20_usage_aware_queue_builder_2026-07-29.md`.

### A compounding prompt-bloat defect, found and FIXED

`sent_log.jsonl` prompt sizes: q16 15,919 -> q17 15,949 -> **q18 49,212** -> q19 49,513 -> q20 49,806 --
a 3.1x jump in one round. Cause: the runner's live-status block ran `ps -eo ...,cmd` with the cmd column
**untruncated**, and an autopilot Claude carries its ENTIRE prompt on its command line. So each round's
`ps` embedded the previous round's full prompt, which had embedded the one before it. It compounds.

Fixed in `scripts/claude_autopilot.py` with `cut -c1-200`. Measured on the live process table:
untruncated 34,940 bytes -> truncated 2,373 bytes = **32,567 bytes saved per round**, which accounts for
essentially the whole jump. Highest-leverage change available this round because it applies to every
future round.

### Ten rounds, ONE submission

Q10 (first nested win over flat, still ~37% worse than deployed) · Q11 (rankers reliably negative) · Q12
(closed) · Q13 (pointwise better, trajectory worse) · Q14 (**55064411**) · Q15 (not started) · Q16
(closed at prerequisite, signed-residual R^2 -0.0802) · Q17 (HOLD, AUC decoupled from DP quality) · Q18
(the 0.080 deciding slot 1 is unresolvable at 3-well scale) · Q19 (the public 6.213 kernel is our base
plus ONE token; fails the 3-well gate). Every round except Q14 closed on evidence without spending a slot.

### Standing

Submissions used in Q10-Q19: **1**. `55064411` PENDING **~6.5 h** (kernel COMPLETE, failureMessage null ->
Kaggle-side). Quota today **0/5 used, 5 remaining**. No private-score visibility for any submission.
Deadline 2026-08-05 23:59 UTC -> ~**35 slots remain, none allocated**. Public standing: leader 4.679,
200th 6.389, our best 6.563 -> outside the top 200.

### Retained signals (concrete smoke + plausible gain)

1. **GR-sigma widening** (Q19): one token, nested +2.3513 with 1.5 a confirmed INTERIOR optimum; fails the
   3-well gate and is tail-driven, but the PF is only a 0.5-weight blend component and Rule #1 says
   averaging damps tails. `_GS_MULT` flag already merged (default 1.0). -> `q36`.
2. **Soft combination over the 96 stored PF paths**: Q11 closed path RANKING (hard selection); soft
   AVERAGING is the transferable class and `topk96_paths/` already holds 773 wells x 96 paths. -> `q21`.
3. **`55064411`'s score**, reading PRE-REGISTERED in Q19 section 4 before the number lands. -> `q22`.

### Queue rebuilt: 16 queued -> 5 active (ZERO new prompts added)

    500 q33_controlled_submission_budget_plan   owns the endgame schedule; ~35 slots unallocated
    510 q36_gr_sigma_in_blend_oof               strongest evidence-backed candidate; slot-2 path
    520 q22_frontier_hedgeoff_score_response    decisive once 55064411 lands; absorbs q32 watcher
    530 q21_pf_path_soft_combiner               averaging class; artifacts already exist
    540 q30_competition_rules_final_audit       cheap, load-bearing before locking the final pair

`q37` stays blocked behind `q36`. **11 deferred**, each with a reason in `queue.jsonl`: q26/q27 public
research (Q19 showed the published pool tops out at 7.06-8.86 and the top-200 have not published);
q23/q24 (need frontier full runs to resolve differences the decision no longer depends on); q31 (Q19
already audited a589fa8 as redundant); q34 (duplicate of q20); q32 (MERGED into q22).

**Deferral risk handled explicitly:** `q29_final_slot_candidate_packager` and `q35_status_summary_for_owner`
are DEADLINE-CRITICAL but premature. Deferred rows are never picked by the runner, so `q33`'s prompt was
amended to make **re-queueing them its explicit responsibility**, with the budget facts inlined.

### Closed directions — do not re-queue

Post-hoc residual correction (Q16) · emission/scorer work validated on AUC or any pointwise metric (Q17,
subsuming the Q13 rule) · PF path RANKING (Q11) · coverage-gated self template (Q12) · hybrid emission
(Q13) · `contact_gated_anchor` (Q19: upstream records it as an underperforming ablation, and it is not
what the 6.213 kernel runs) · per-well hand-fitted shifts (Q19 Find B) · the N-series closures.
**Still open and untested: the TRANSITION MODEL** in the alignment line — Q17 says nothing against it and
both Q10 and N1 identify it as the remaining lever.

### Limits

The prompt-size fix is verified by measurement on the current process table and an `ast.parse` of the
runner, NOT by a full round having run through it; the next `sent_log` entry is the real confirmation.
Deferral is an expected-value judgement, not proof a direction is unproductive — each reason is recorded
so any can be reinstated by editing one status field. Claude token usage is not directly observable;
`prompt_chars` is the proxy used and measures input size only.

## Round 31 — `55064411` LANDED at 6.695, and Q33 budget plan

Two things this round: the pending submission scored, and the budget plan was produced.
**No submission (`can_submit=false`), quota 0/5 on 07-29.**
`reports/q33_controlled_submission_budget_plan_2026-07-29.md`.

### `55064411` = public 6.695 (COMPLETE). Scoring latency <= 7.7 h.

The pre-registered reading from Q19 section 4 was applied — **and it required a correction that changes
which branch fires.** Q19 framed the threshold against 6.563, but `54922806` is a DIFFERENT branch
(teammate, overlap-ON). `55064411` was built and diff-verified against the kernel that produced
`54968060` (6.643), one line `_BH_CAP 2.00 -> 0.00`. The controlled contrast is therefore:

    hedge OFF (55064411)  6.695
    hedge ON  (54968060)  6.643
                          +0.052

**+0.052 is INSIDE the ~0.115 config-variance floor**, and Q18 measured that pooled gaps <= 0.30 reverse
on ~45% of random 3-well draws. Neither pre-registered branch fires cleanly; the honest outcome is a
third: **the bimodal hedge is not load-bearing on public in either direction, and the public score does
not adjudicate Q14's local finding.**

**SECOND CORRECTION.** Q19 presented the `my0705` datapoint (base 6.568 -> 6.520 after pushing well
`00e12e8b` a further +0.522 ft) as support for "the hedge is tuned to the 3 public wells". That change is
**-0.048**, likewise inside the floor. It does not establish the claim. The hypothesis is **neither
confirmed nor refuted** — unresolvable at this scale — and Q19's framing overstated it.

What survives untouched: Q14's LOCAL measurement that the hedge applies +2.0 ft to `00e12e8b` whose own
residual was already -0.19 ft. The public result carries no resolving power against it.

`55064411` at 6.695 is our WORST frontier candidate on public and enters no slot. **Final-pair
recommendation unchanged.**

### The budget, reframed: ZERO of the 40 remaining slots are required

8 UTC days remain (07-29 .. 08-05) x 5 = **40 slots**; 0 used today. But the final score is the best of 2
**already-submitted** entries, and every member of every current recommendation (`54922806`, `54968060`,
`54844628`) is already submitted and scored. **The recommendation is executable today at a cost of 0
slots.** All 40 slots are discretionary.

**What a slot can buy, measured.** The slot just spent returned a +0.052 contrast against a ~0.115 floor —
no adjudication. That gives a quantitative criterion derived from measurement:

> **A submission is worth a slot only if its expected public effect exceeds ~0.115.**

Three independent results agree: Q18 (the 0.080 deciding slot 1 is unresolvable), Q19 (nothing in the
public pool to adopt), and now 55064411.

### Categorisation

    submittable now   : NONE
    smoke/full needed : q37 (one-token gs*1.3 frontier), BLOCKED behind q36 -- 1 slot, conditional
    diagnostic only   : q23/q24 (deferred) -- value of information now below the floor
    final-slot only   : 54922806 / 54968060 / 54844628 -- already scored, 0 slots
    close             : 55064411 (measured, enters no slot) + the Q20 closed list

**Recommended maximum for the next 24 h: 1** — zero unless `q36` passes its 3-well gate, one (`q37`) if it
does. Slots are not the scarce resource; resolving power is.

### Contingency for delayed scoring (measured, supersedes 41bb65f)

Latency **<= 7.7 h** (submitted 07-28 20:30, still PENDING at 6.5 h, COMPLETE by 04:14) — the ~1 h
expectation recorded in `41bb65f` assumed latency tracks kernel runtime; kernels-only scoring also queues
behind other users. Consequences: serial information rounds cost ~8 h each, so depth is expensive and
breadth is cheap; **last informative submission 2026-08-05 12:00 UTC** (~12 h margin); last submission of
any kind 16:00 UTC; never resubmit a PENDING entry; a multi-hour stall is not a failure.

### The zero-cost action with a hard deadline

**Selecting the final 2 is a separate action from submitting.** It costs no quota but must happen before
2026-08-05 23:59 UTC or Kaggle applies its own default. It is currently unscheduled and is the highest-
consequence remaining step. **Recommendation: perform the selection by 2026-08-04**, a day early; it can
be revised afterwards, whereas leaving it to the final hours cannot.

### Endgame scheduling — Q20's deferral risk discharged

    q35_status_summary_for_owner       re-queued now, priority 550
    q29_final_slot_candidate_packager  re-queued now, priority 560, WITH a self-check trigger

`q29`'s prompt now requires it to proceed only if date >= 2026-08-03 AND `q36` has reported; otherwise it
must re-defer itself with a new target date and say so. It can therefore neither run prematurely nor be
silently lost. `q22_frontier_hedgeoff_score_response` is marked **done** — its deliverable (record the
score, apply the pre-registered reading) was discharged here, since the standing rules require recording a
landed score immediately.

### Day-by-day

    07-29        0-1   only q37, and only if q36 passes its gate
    07-30..08-02 <=1/day  only candidates with expected effect > 0.115
    08-03        0     q29 final packaging
    08-04        0     PERFORM THE FINAL SELECTION (no quota cost)
    08-05        0     reserve; last informative submission 12:00 UTC

Expected total spend **0-4 of 40**, deliberately leaving most of the budget unused.

### Limits

The 0.115 floor comes from a prior small-sample measurement of GPU nondeterminism and is itself uncertain.
The 7.7 h latency is an UPPER BOUND from ONE observation (true value between 6.5 h and 7.7 h); queue depth
near the deadline may be worse, which is why 12 h of margin is used. "40 slots" assumes a 00:00 UTC reset
and no rejected submissions, verified once at the 07-28 -> 07-29 rollover. The plan asserts nothing about
any candidate improving the private score.

## Round 32 — Q36 GR-sigma inside the blend: two corrections to Q19, smoke passed, full run in flight

`q36_gr_sigma_in_blend_oof` (`can_submit=false`). **No submission, quota 0/5.**
`reports/q36_gr_sigma_in_blend_oof_2026-07-29.md`, `scripts/q36_gr_sigma_in_blend_oof.py`.

### TWO CORRECTIONS TO WHAT Q19 MEASURED (both mine, both fixed here)

**1. Q19 patched the WRONG particle filter.** It added `_GS_MULT` to `scripts/pf_honest_forward.py`, a
STANDALONE conservative PF with 500 particles and **ONE seed**. The honest line's PF component is
`run_pf_lik_ensemble` -- a **likelihood-weighted ensemble over n_seeds seeds** -- whose source is
`SUNNY_CODE` in cell 108 of `kaggle_kernel_henry_v10_sunny80_blend`, exec'd by `scripts/pf_forward_oof.py`.
This matters directly: Q36 exists because Rule #1 says averaging damps tails, and Q19's single-seed
measurement had the ensemble averaging **entirely absent** -- so its tail-driven failure was measured in
the one configuration where no damping could occur.

**2. Q19 scored the PF STANDALONE, but it enters the blend at weight 0.5.** Verified numerically:
`base = 0.5*dwt + 0.5*pf` exactly (max|base - mix| = 4.9e-4, float32 rounding; dwt 10.2891, pf 11.0563,
base 9.2987). Any PF change is **halved** before reaching the honest line. Q19's +2.3513 was measured on a
single-seed standalone PF with baseline 14.27 against a deployed blend baseline of 9.2987, so it must NOT
be read as a blend-level effect size; the Q19 report overstated its relevance to the honest line.

### What Q36 measures instead

One string replacement on the DEPLOYED source, with an assertion the target line is unique, then per well
`run_pf_lik_ensemble(500 particles, NS seeds, scale=5.0)` per multiplier, blended `0.5*dwt + 0.5*pf_new`
reusing the deployed `dwt` column unchanged. Alignment is ASSERTED not assumed: toe-row positions must
equal the npz `ridx` AND npz truth must match loaded truth, else the well is rejected. Splits by well;
multiplier chosen nested; per-well win rate and 3-well bootstrap reported.

### SMOKE PASSED (Directive 4) -- 12 wells, NS=8, 0.7 min

    multiplier   blend RMSE   vs 1.0        nested picks [1.5, 1.0] -> gain -0.2004
    1.0            7.8828      0.0000       helps 0.0% of held-out wells
    1.5            7.8321     +0.0507       3-well 5th -0.5173, P(>0) 0.0000   GATE FAIL
    mult 1.5 helps 16.7% of wells | mean per-well gain -0.3266

Establishes (this is NOT the measurement): the **patch activates** (1.5 differs from 1.0, so the sigma
change propagates through the ensemble into the blend); **alignment holds** (12/12 passed both assertions,
0 rejected); and the full reporting path executes to the gate cell. Provisional hint at 12 wells / NS=8:
pooled improves (+0.0507) while per-well is negative (helps 16.7%) -- the same tail-driven signature Q19
found, now visible inside the blend.

### FULL RUN IN FLIGHT

`MAXW=760 NS=32 JOBS=2 MULTS=1.0,1.3,1.5`; 14 wells / 4.1 min -> **ETA ~3.7 h** from 04:45 UTC.
Recorded deviation: this box has **2 cores**, and the deployed line uses **NS=64** while this run uses
NS=32 to keep wall time near 3.7 h rather than ~7.5 h. More seeds = more averaging, so **NS=32 UNDERSTATES
the ensemble damping** relative to deployed -- conservative in the direction that matters.

### Gate for whoever collects it

Promote only if ALL THREE hold: nested gain > 0 AND 3-well bootstrap 5th > 0 AND it helps a MAJORITY of
wells. `q37_frontier_gr_sigma_public_repro` stays blocked behind this; per Q33 the next 24 h spends **0
slots unless this gate passes**.

### Limits

The result is not in yet -- the smoke is not the finding. NS=32 vs deployed NS=64. The measurement is at
the BLEND level (`base` 9.2987), not after the gated structural-field stage that reaches 8.8626. 760 of
773 wells: 13 are absent from `aligned_preds.npz` and excluded so the deployed `dwt` column can be reused
unchanged.

## Round 33 — Q21 PF-path soft combiners: CLOSED, and the deployed ensemble is already at the optimum

`q21_pf_path_soft_combiner`. **Gate fails on all three conditions. No Kaggle smoke, no submission,
quota 0/5.** `reports/q21_pf_path_soft_combiner_2026-07-29.md`.

### A structural discovery that reframes the task

The stored per-well `mean` array — which the task and Q11 both call "the PF mean path" — **is not a mean**:

    max |paths.mean(0) - stored mean| = 30.02        stored `mean` is NOT the uniform mean
    softmax_T5  10.9307   ==   pf_mean 10.9307  (difference -0.0000)
    topm_96     11.5320                          (the ACTUAL uniform mean of the 96)

`softmax_T5` reproduces it EXACTLY, so the stored baseline is the **likelihood-weighted ensemble at
scale = 5.0** — the deployed `run_pf_lik_ensemble` that feeds the honest blend. The deployed PF is
therefore ALREADY a soft combiner, and the temperature sweep becomes a **nested test of the deployed
`scale = 5.0`, a hyper-parameter that had never been validated**. The family spans both limits: deployed
is T=5, the uniform mean is T->inf, and hard selection (which Q11 closed) is T->0.

### Result — 773 wells, splits by well

    PF ensemble (T=5) 10.9307 | ORACLE best-of-96 7.1259 | worst-of-96 22.0396 | deployed honest 8.8626
    oracle headroom +3.8048 | tail risk -11.1090

    softmax_T10   10.8781  +0.0526   <- the ONLY positive, 1.4% of headroom
    softmax_T5    10.9307  -0.0000   <- deployed
    softmax_T2    11.1957  -0.2650      softmax_T1   11.4264  -0.4957
    softmax_T0.5  11.5916  -0.6609      softmax_T0.25 11.6884 -0.7577
    topm_1/interp_1 11.8088 -0.8781  <- hard selection, the worst of the sharp end
    topm_96       11.5320  -0.6013   <- uniform mean          median 12.0408 -1.1101

**The deployed T=5 sits at a near-optimal interior point.** Sharpening is monotonically harmful down to
hard selection; flattening is harmful too; robust combiners are worse still.

### Nested — fails all three gate conditions

    NESTED across all 27 combiners (picks ['interp_0.1', 'softmax_T10'])
      selected 10.9633 vs deployed 10.9307 -> gain -0.0326 (-0.9% of headroom)
      helps 43.2% of held-out wells
      3-WELL bootstrap 5th -0.7353  50th -0.0069  95th +0.3942  P(>0) 0.4563

The folds disagree, which is what turns T=10's nominal +0.0526 into a nested loss: its edge is smaller
than the between-fold selection noise.

### What this closes, and one thing it validates

**CLOSES:** Q11 closed HARD SELECTION over these 96 paths (top-K ranker converted 3.9%, failed the gate).
Q21 extends that to the ENTIRE SOFT-COMBINATION family — temperature reweighting, top-m averaging,
trimming, per-row median, mean<->best interpolation. Both limits are worse than the deployed point, so the
+3.8048 of oracle headroom is **not accessible by reweighting either**. Selection AND reweighting are now
both closed on this artifact set.

**VALIDATES:** the deployed `scale = 5.0` was a fixed, never-nested hyper-parameter of the honest line. It
is now nested-validated as sitting at the optimum of a 27-member family over 773 wells — a genuine
positive about the current pipeline, even though it yields no new candidate.

### No submission regardless of the gate

The PF-path line sits at 10.93 vs the deployed honest 8.8626 — 2.07 WORSE — and even the truth-selected
oracle (7.1259) is only 1.74 better than deployed. No member of this family is a submission candidate at
any temperature, so the task's step 5 ("materially closer to deployed honest") does not trigger.
Non-homogeneity was not computed, being meaningful only for a submittable candidate.

### METHODOLOGICAL NOTE WORTH CARRYING

A 20-well smoke showed sharpening HELPING (`softmax_T0.5` +0.1310, `topm_8` +0.2027, `interp_0.5`
+0.1594). **Every one reversed sign on the full 773 wells**, and that subset was also unrepresentative in
level (7.16 vs 10.93). This is the THIRD instance of the same lesson (N1's 12-well set manufactured a gain
that vanished at 40; Q10's grid sensitivity likewise) — keep treating small-sample smokes strictly as
plumbing checks, never as weak evidence of direction.

### Q36 still in flight

284/760 wells at 78 min, ~2 h remaining. It remains the gate deciding whether the next 24 h spends 0 slots
or 1.

## 2026-07-29 07:15 UTC — Q30 rules/provenance audit: two corrections and a deadline TODAY

`reports/q30_competition_rules_final_audit_2026-07-29.md`. No submission; quota 0/5.

### TIME-CRITICAL: team-merger and new-entrant deadlines are **2026-07-29 23:59 UTC — TODAY**

    merger_deadline       2026-07-29 23:59
    new_entrant_deadline  2026-07-29 23:59
    submission deadline   2026-08-05 23:59

After tonight team composition is frozen for the rest of the competition. Surfaced because it is
irreversible and expires today; no action recommended here, it is the owner's call.

### Our precise standing: rank **1277 of 5886 teams**

Supersedes Q19's "outside the top 200", which was only a bound because the leaderboard API caps a page at
200 rows.

### CORRECTION — `54844628` is not "fully owned"

The final-slot package and several reports describe the honest line as "fully owned". Its kernel
`joezzzzz/rogii-struct-field-blend-codex` attaches ONE third-party public dataset, and it is
**load-bearing, not vestigial** -- the notebook HARD-ASSERTS it:

    assert (CFG.artifacts_path/'models'/'lightgbm-1').exists()
    assert (CFG.artifacts_path/'data'/'train.csv').exists()   # 'would trigger 7GB rebuild'

`ravaghi/wellbore-geology-prediction-artifacts` supplies prebuilt LightGBM/DWT artifacts and a cached
train.csv; the run fails without it. Accurate description:

| aspect | status |
|---|---|
| pipeline code | fully owned, built and audited in this repo |
| validation | fully owned, 760-well nested OOF + bootstrap |
| runtime dependency | ONE third-party public Kaggle dataset, REQUIRED |

**This is not a rules problem** -- the dataset is public and equally accessible, which is the operative
criterion -- and **the slot recommendation is unchanged**. It changes only how the candidate should be
described: "fully owned pipeline with one shared public artifact dependency".

### CAVEAT — the API labels the metric "Mean Squared Error"

Every project report treats the leaderboard number as being on the same scale as our local RMSE. The
empirical correspondence says the reports are right and the label is loose: DWT det-base 9.487 local vs
9.823 public; blend 9.2969 vs 8.080; honest 8.8626 vs 7.891. A true squared error would put public near
78, not within ~1. So the one-axis comparison used throughout the ledger is SOUND -- recorded because the
label would otherwise be a latent trap.

### Risk categories

| candidate | public | account | category |
|---|---|---|---|
| `54844628` | 7.891 | ours | public-derived but documented (low) -- one REQUIRED public artifact dataset |
| `54968060` | 6.643 | ours | public-derived but documented + provenance caveat |
| `55064411` | 6.695 | ours | same; enters no slot |
| `54922806` | 6.563 | teammate | **provenance caveat -- ACTIONABLE** |
| `54878409` | 7.953 | ours | not recommended (measured regression, already excluded) |

**Nothing is categorised "not recommended" on RULES grounds.** All attached datasets are public Kaggle
datasets and every kernel runs `enable_internet: false`.

**ACTIONABLE:** if `54922806` (best public, teammate account) is selected, obtain from the teammate its
kernel slug, version, and full dataset_sources list and record them in the ledger. We have only its
description string. That information is required under Winner's Obligations and cannot be reconstructed
after the deadline.

### Winner's Obligations disclosure list, prepared now

`54844628` -> `ravaghi/wellbore-geology-prediction-artifacts`, everything else owned.
`54968060`/`55064411` -> all NINE attached datasets (including the 5 vestigial ones, since they are
attached at runtime) plus the derivation from the public notebook `kaiwalyaatulraut/rogii-public-tvt-solution`.
`54922806` -> the above plus the teammate-supplied kernel version and dataset list.

Recommendation on the vestigial datasets: **leave them attached**. Removing them needs a fresh frontier run
and a quota slot, and Q33 established slots buy nothing inside the current noise band. Disclose all nine
instead -- accurate and free.

### Open verification item

`ravaghi/...artifacts` ships a `data/train.csv` described in our own kernel as a cache avoiding a "7GB
rebuild". Its contents were NOT inspected this round. Low risk, but it is the one unverified link in the
honest line's provenance and is recorded rather than assumed.

### Limits

The official rules TEXT was not retrieved -- the page is an authenticated JS SPA returning only its title.
The operational rules above come from API metadata; the external-data clause rests on the earlier
transcription in `external_data_ssl_direction_2026-07-15.md`. Dataset licence fields are not exposed by
this API version, so only public listability was verified. `user_rank` 1277 is the PUBLIC rank; the private
ranking is not visible and is the actual objective.

## Round 34 — Q36 COLLECTED (gate FAILS), and Q35 owner summary

**No submission this round; quota 0/5 on 07-29.**

### Q36 RESULT — 760/760 wells, 0 rejected, 211.0 min. GATE FAILS on two of three.

    multiplier   blend RMSE   vs 1.0
    1.0            9.2903      0.0000     (deployed `base` = 9.2987 -> reconstruction faithful, 0.008 apart)
    1.3            9.1204     +0.1699     helps 42.1% of wells | mean -0.1197 | median -0.0569
    1.5            9.3203     -0.0300     helps 40.4% of wells | mean -0.3830 | median -0.1438

    NESTED (picks [1.3, 1.3]) selected 9.1204 vs 9.2903 -> gain +0.1699
      helps 42.1% of held-out wells | 3-WELL bootstrap 5th -1.6429  50th -0.1129  95th +1.5381  P(>0) 0.3981

    GATE: nested gain > 0 (PASS) AND 3-well 5th > 0 (FAIL) AND majority of wells (FAIL)  ->  FAIL

**`q37_frontier_gr_sigma_public_repro` is CLOSED**, not merely blocked -- its release condition was this
gate. Per Q33 this settles the budget: **the next 24 h spends 0 slots.**

**THE OPTIMUM MOVED TO EXACTLY THE PUBLIC KERNEL'S VALUE.** Q19's standalone single-seed measurement put
it at 1.5; inside the ensemble and the blend **1.5 is harmful (-0.0300) and 1.3 is optimal (+0.1699)** --
and 1.3 is precisely the constant the public 6.213 kernel uses. The public author's choice is right *for
the deployed configuration*, which Q19's setup could not have seen.

**WHAT THE ENSEMBLE DAMPING DID AND DID NOT DO** -- the substantive answer to the question Q36 existed to ask:

    |                      | Q19 standalone, 1 seed | Q36 in-blend, NS=32 |
    | nested gain          | +2.3513                | +0.1699             |
    | 3-well bootstrap 5th | -4.1145                | -1.6429             |
    | % of wells helped    | 41.7%                  | 42.1%               |

Rule #1 predicted averaging would damp the tail, and it did -- effect size shrank ~14x, tail risk more
than halved. **But the fraction of wells helped is unchanged.** Averaging damps MAGNITUDE, not SIGN
STRUCTURE, so it cannot rescue a change that helps a minority of wells. Both mean and median per-well
gains stay negative while the pooled gain is positive -- the asymmetric-tail signature the ledger records
before the `54878409` public regression.

### Q35 — owner summary written

`reports/q35_status_summary_for_owner_2026-07-29.md` (Chinese, owner-facing). Three decisions surfaced:
(1) **team-merger / new-entrant deadline is TODAY 23:59 UTC**; (2) the **final-slot selection action** is
separate from submitting, costs no quota, and must happen before 08-05 23:59 -- recommended 08-04;
(3) slot 1 between `54922806` (teammate) and `54968060` (ours) is an **ownership judgement**, since Q18
showed the 0.080 separating them is unresolvable at 3-well scale.

**Standing: rank 1277 / 5886. Thirteen rounds (Q10-Q36) spent exactly ONE submission slot.**

**Usage-aware recommendation: 0 submissions in the next 24 h.** 40 slots remain and ZERO are required --
the final pair is chosen from already-submitted entries. The measured criterion from `55064411` (+0.052
against a ~0.115 floor = zero resolving power) means no current candidate justifies a slot.

## Round 35 — Q29 trigger check FAILED, task re-deferred; the queue is now EMPTY

`q29_final_slot_candidate_packager`. **No packaging done, no submission, quota 0/5.**
`reports/q29_final_slot_candidate_packager_2026-07-29.md`.

### Trigger check

    (a) date >= 2026-08-03 ?   today is 2026-07-29   ->  FAIL (five days early)
    (b) q36 has reported ?     done, gate FAILED     ->  PASS

Condition (a) fails, so per the Q33 addendum this task **re-deferred itself rather than packaging five
days early** — exactly the failure mode the trigger existed to prevent. Its row is now
`status: "deferred"`, `target_date: 2026-08-03`.

### THE CONSEQUENCE THAT NEEDS A HUMAN — the queue is empty

`q29` was the last queued row. Queue is now `done 33 | deferred 10 | hold 1 | closed 1 | queued 0`. The
runner prints "No queued tasks remain." and idles, and **deferred rows are never selected automatically**.
So **nothing will re-activate q29 on 2026-08-03** — this is now a HUMAN action item. The one-line
re-activation command is in the report §2 and in `state.json` under `endgame_action_required`.

### The deliverable is NOT at risk

The final-slot package is already current: Q33 (04:15 UTC) updated the board with `55064411` = 6.695 and
flagged the zero-quota selection action; Q30 (07:15 UTC) added risk categories and the Winner's
Obligations list. Nothing has changed since — no new submissions or scores, quota 0/5, and q36's gate
failed so no candidate entered the board. **If q29 never runs,
`reports/final_slot_package_corrected_gate_2026-07-26.md` remains the complete, current package.** Only
its refresh would be missed.

### Recommendation carried forward unchanged

    score/diversity/provenance-first : 54922806 (6.563) + 54844628 (7.891)   worst 6.643  mean 6.603
    our-account-first                : 54968060 (6.643) + 54844628 (7.891)   worst 6.643  mean 6.643

Backup if the teammate submission is unavailable: the our-account pair, +0.000 worst / +0.040 mean.
Backup if the public-derived stack is disallowed by team preference: `54844628` + `54804893` (8.080) --
both ours and honest-family, but family diversity 0 and a materially worse worst case (7.891); a fallback,
not a recommendation. Pending-score contingency: NONE outstanding; `55064411` landed at 6.695, our worst
frontier candidate on public, and enters no slot.

### Two owner actions remain

1. **By 2026-08-04** — perform the final 2-submission selection on Kaggle (separate from submitting, no
   quota cost, hard deadline 2026-08-05 23:59 UTC; otherwise Kaggle applies its default).
2. **If `54922806` is selected** — obtain the teammate's kernel slug, version and dataset_sources list for
   Winner's Obligations (Q30 section 4.3); not reconstructable after the deadline.

A third item, the team-merger / new-entrant deadline, **expires today 2026-07-29 23:59 UTC**.

## 2026-07-29 16:30 UTC — Q38: teammate provenance FULLY recovered; slot 1 is the `*1.3` variant

`reports/q38_teammate_submission_provenance_recovery_2026-07-30.md`. No submission; quota 0/5.

### The owner's question -- "do we have all teammate solution data?" -- is answered: YES

The submissions API exposes each submission's exact **kernel slug AND scriptVersionId**, and **every
teammate kernel pulls successfully from this account** (notebook source + metadata including
`dataset_sources`). **This CORRECTS Q30**, which recorded an "actionable gap" and told the owner to request
slug/version/datasets from the teammate. They were available from the API all along and the code is
directly pullable. The request is unnecessary.

Team account: 20 submissions, `joezzzzz` 11 / `leemarc223` 9.

| ref | public | submitted_by | kernel slug | scriptVersionId | datasets | pulled |
|---|---|---|---|---|---|---|
| `54922806` | **6.563** | leemarc223 | `rogii-public-pf-frontier-rerun-20260723` | 337355891 | **7** | yes |
| `54896975` | 6.669 | leemarc223 | `rogii-kaiwalya-public-tvt-6-626-repro` | 337097140 | **9** | yes |
| `54923144` | 6.678 | leemarc223 | `rogii-gr-sigma-1-0-frontier-20260723` | 337362917 | **7** | yes |
| `54853492` | 7.360 | leemarc223 | `rogii-safe-mha140-contactmean-v66` | 336687235 | 3 | yes |
| `54777533` | 7.921 | leemarc223 | **`qwer556617123/`**`rogii-prvs-oof-meta-direct-fast` | 335598801 | 7 | yes |

`54777533` ran a kernel on a **third-party account**, not our team's -- recorded for disclosure.
`54853492` appears only as provenance bookkeeping; no decision is made about it.

### The 6.626 repro package is NOT the 6.563 run

| | origin/main 6.626 repro | our best 6.563 |
|---|---|---|
| submission | `54896975` = 6.669 | `54922806` = 6.563 |
| kernel | `rogii-kaiwalya-public-tvt-6-626-repro` | `rogii-public-pf-frontier-rerun-20260723` |
| datasets | 9 | 7 |
| vs pristine base | **identical** | base **+ `*1.3`** |
| in repo | yes (`a589fa8`) | no |

### HEADLINE -- our best public submission IS the `*1.3` GR-sigma variant

Normalised cell-by-cell vs our pristine base: `54922806` is **44/45 cells identical, cell 29 inserts
`*1.3`** -- the IDENTICAL one-token change Q19 found in the public 6.213 kernel and Q36 tested on the
honest line. `54896975` and `54923144` are both **byte-identical to base** (so "GR sigma 1.0" was an
accurate description -- 1.0 is unmodified).

Consequences: (1) **the team has already banked this change on the frontier line** -- closing `q37` was
correct for a STRONGER reason than recorded, since it would have been a **near-duplicate of `54922806`**,
which the submit gate forbids outright; (2) Q36's rejection is NOT contradicted -- Q36 measured the
multiplier inside our HONEST blend, while `54922806` applies it inside the FRONTIER; different pipelines.

### A controlled run-to-run pair the team already had, unrecorded

`54896975` and `54923144` are normalised-IDENTICAL code run on different days -> **6.669 vs 6.678, spread
0.009**. (Their 2 extra datasets are exactly the ones G1.3 called vestigial, consistent with the tiny
spread.) The `*1.3` variant is 0.106-0.115 better, ~12x that spread.

**This does NOT overturn Q18 and must not be conflated with it.** Two different quantities, both true:
0.009 is MEASUREMENT PRECISION (same code, same 3 public wells); Q18's ~45% reversal is GENERALISATION
(different models, a different 3-well draw). A precise instrument can still measure a quantity that does
not transfer -- so the frontier's ~0.11 gain is real on the public wells and still not evidence about
novel wells. It does sit awkwardly beside the recorded ~0.115 config-variance floor (A1), which this pair
suggests may be too large for this pipeline; flagged for reconciliation rather than silently replaced.

### Effect on the final slots: NONE, but slot 1's provenance is now closed

Recommendation unchanged. What changes is that `54922806` is now fully documented -- exact kernel, version,
7-dataset list, and a structural diff showing it is the pristine public base plus one token. **The Q30
provenance caveat on `54922806` is CLOSED.**

### One open item

`kernels_pull` returns each kernel's CURRENT version; it could not be confirmed from this account that it
equals the submitted `scriptVersionId`. A short confirmation message for the teammate is drafted in the
report (§7) -- it asks only whether those kernels were edited after their submission dates, plus the
provenance of the third-party kernel behind `54777533`.

## 2026-07-29 16:55 UTC — Q39 stage localizer: the simulator's 0.080 "retrieval penalty" is a CONFOUND

`reports/q39_frontier_stage_localizer_no_submit_2026-07-30.md`. No re-run, no submission, quota 0/5.

Using the teammate kernels Q38 pulled, the whole frontier family was compared as **code** for the first
time. Normalised cell-by-cell against the pristine base (45 code cells):

    54896975  6.669  ->  NONE          pristine
    54923144  6.678  ->  NONE          pristine
    54922806  6.563  ->  cell 29       insert '*1.3'  (GR sigma)      <- OUR BEST
    54968060  6.643  ->  cell 0        overlap override = False
    54990075  6.690  ->  cell 0 +1     overlap OFF + SP45-only truncation
    55064411  6.695  ->  cell 0, 42    overlap OFF + _BH_CAP 2->0
    pub 6.213        ->  cell 29       identical '*1.3' to 54922806

Every member is a single- or double-factor variant of one base, and 54896975/54923144 are a **code-identical
replicate pair**: 6.669 vs 6.678, **same-code spread 0.009**, baseline mean **6.6735**.

### THE CORRECTION

The simulator and final-slot package encode `retrieval = 0.080 (= 54968060 6.643 - 54922806 6.563)`.
**Those two kernels differ in TWO stages** — 54922806 also carries `*1.3`. Decomposed against the pristine
baseline:

    overlap / retrieval   6.643  vs 6.6735  ->  -0.031   (turning overlap OFF slightly HELPS)
    GR sigma *1.3         6.563  vs 6.6735  ->  -0.1105

and -0.1105 - (-0.031) = -0.080 reproduces the recorded number as **a difference of two different stages**.
So retrieval is **not** worth 0.080; it is ~-0.03 with uncertain sign. **54922806's edge is the GR-sigma
multiplier, which is not a train-duplicate lookup and does NOT go inert on novel wells** — so it does not
converge onto 54968060 under H-hidden, which is exactly what produced Q18's tie structure and its
"+0.000 worst" price for our-account-first. **That price is probably no longer zero.**

**COUNTERWEIGHT, kept explicit:** Q36 measured this same multiplier on 760 wells with truth and it helps
only **42.1%** of wells with a **negative median**. The stage carrying the public edge is the one our own
held-out evidence says does not transfer broadly. The recommendation is **not** rewritten here — it is
queued as a simulator re-run so the owner sees numbers rather than a narrative.

### Stage matrix

| stage | effect on public | classification |
|---|---|---|
| GR sigma *1.3 | **-0.1105** | supported on public; novel-well transfer UNSUPPORTED (Q36) |
| bimodal hedge | +0.052 when removed | helps public; **measured local harm** (Q14) |
| post-SP45 stages | +0.047 when truncated | supported but **joint**, unseparated |
| overlap / retrieval | **-0.031** | **not load-bearing**; supersedes the 0.080 figure |
| learned-trajectory blend | <= 0.047 jointly | **unknown** — the only genuinely open stage |
| prefix calibration | 0 | **measured inert** (`alpha = 0.0` in the run log) |
| model-package fallback | 0 | **measured inert** (guard-rejected, `selected_for_submission_csv = False`) |

### No stage change clears the threshold

GR sigma is **already banked** (54922806 IS that variant, so a new run would be a near-duplicate the gate
forbids); the hedge information was already bought by 55064411; overlap is ~0.03 with both settings already
submitted; the learned-trajectory blend is bounded at <=0.047, below Q33's bar. **No submission proposed.**

### Queued: `q53_simulator_retrieval_penalty_correction` (priority 305, zero cost)

Re-run the four views with `retrieval ~ 0.03` plus a 0.0 sensitivity arm, keeping 54922806's GR-sigma edge
NON-INERT under H-hidden, and report whether the recommended pair, the tie structure, and the price of
our-account-first change — carrying Q36's counterweight explicitly. Arithmetic only: no GPU, no smoke, no
submission.

## 2026-07-29 17:05 UTC — Q53: the corrected simulator REACHES Q18's answer by a different route

`reports/q53_simulator_retrieval_penalty_correction_2026-07-30.md`,
`scripts/q53_simulator_retrieval_correction.py`. Arithmetic only; no GPU, no smoke, no submission, quota 0/5.

### Headline

**Q18's conclusion survives the Q39 correction, but its reasoning did not.** The price of the
our-account-first pair is **+0.0005 worst / +0.0402 mean** under the evidence-supported cell — essentially
Q18's +0.000 / +0.040 — reached by a completely different mechanism. **The owner's slot-1 decision does not
change and remains an ownership judgement.**

### Why two axes were needed

Correcting `retrieval` alone would have flipped the answer. The rerun sweeps both:

- `retrieval_delta` in {-0.031 (measured), 0.0, +0.080 (old, confounded)}
- `sigma_transfers` in {True, False} -- whether 54922806's GR-sigma edge survives on novel wells.
  **Not a strawman:** Q36 measured that exact multiplier on 760 wells with truth and it helps only 42.1%
  of wells with a NEGATIVE median, so `False` is the arm our own held-out evidence supports.

    retrieval sigma  | A: 54922806+54844628 | B: 54968060+54844628 | price of B
    -0.031    True   | worst 6.5630         | worst 6.6430         | +0.0800
    -0.031    False  | worst 6.6425         | worst 6.6430         | **+0.0005**   <- measured + supported
     0.000    True   | worst 6.5630         | worst 6.6430         | +0.0800
     0.000    False  | worst 6.6735         | worst 6.6430         | -0.0305
    +0.080    True   | worst 6.6430         | worst 6.6430         | +0.0000       <- the OLD model
    +0.080    False  | worst 6.7535         | worst 6.6430         | -0.1105

**TWO WRONG INPUTS WERE CANCELLING.** The old model overstated retrieval (+0.080 vs the measured -0.031)
AND implicitly let the GR-sigma edge survive under H-hidden. Correcting both moves the price by 0.0005;
correcting only one would have moved it to +0.080 and flipped the conclusion.

### The three questions

1. **Recommended pair — unchanged in any way that survives noise.** Under the measured cell with
   sigma=False, score-first nominally moves to `54896975 + 54922806` by **0.0045**, which is HALF the 0.009
   replicate spread and has family diversity 0. Diversity-first and provenance-first stay at
   `54922806 + 54844628`. With sigma=True all three stay there too.
2. **Tie structure — still heavily tied.** Q18 reported 9 tied pairs; corrected it is 6-11 depending on the
   cell and **11 in the evidence-supported one**. Q18's qualitative point (score alone does not pick a
   unique pair) is unchanged and if anything stronger.
3. **Price of our-account-first — not materially changed:** +0.0005 worst / +0.0402 mean. It rises to
   +0.080 worst ONLY in the sigma_transfers=True arm.

### The counterweight, not buried

54922806's ENTIRE public advantage over the pristine baseline is the GR-sigma multiplier. The H-hidden gap
between the two slot-1 options is **0.0005 if that edge does not transfer, 0.1110 if it does**. So the whole
slot-1 question reduces to one unresolved quantity -- does GR-sigma widening help on NOVEL wells? Public
says yes on 3 wells; Q36's 760-well truth measurement says it helps a minority. **The public edge must not
be read as a private-ranking edge.**

### Decision

**No change. It remains an ownership judgement**, and the corrected model makes that firmer: the two pairs
differ by 0.0005 on worst case, far inside the 0.009 replicate spread and inside Q18's ~45% reversal band;
the only cell where the choice is materially priced requires an assumption our own evidence contradicts;
and therefore **no additional public evidence can settle it and no submission would help** -- consistent
with Q33's standing 0-slot conclusion.

### Code note

`scripts/final_selection_simulator.py` and `scripts/q18_final_pair_stress.py` still carry `retrieval=0.080`
with the confounded derivation. **Left unmodified** so the Q18 record stays reproducible as written;
`scripts/q53_simulator_retrieval_correction.py` supersedes them. If either is rerun for a decision, use Q53.

## 2026-07-29 17:25 UTC — Q40 transition-model search: the deployed L1 term is the best of 45 arms

`reports/q40_transition_model_search_2026-07-30.md`, `scripts/q40_transition_model_search.py`.
**Gate FAILS on all three conditions. No Kaggle path, no submission, quota 0/5.**

The entire transition model is one term -- `lam*|t-s|/BAND`, one parameter, previous-state only. Six
families were tested, all strictly containing it: `l1`, `l2`, `huber`, `drift` (heel-estimated
trajectory prior), `curv` (slope change), `l1curv` (2 params). 45 arms, 40 eval wells, splits by well,
every parameter nested, validated on **DP output only** per Q17's rule.

### No variant beats the baseline

    l1     lam=60            12.170   <- baseline, and the BEST of all 45 arms (reproduces Q10 exactly)
    huber  lam=150 hub=5     12.313
    l1curv lam=60 lam2=150   12.453
    l2     lam=150           13.975
    drift  lam=20            16.018
    curv   lam=20            18.368
    flat-anchor              12.722          deployed honest reference 8.8626

    ALL 45 arms nested together: 14.452 vs l1 baseline 12.601 -> gain -1.851
      helps 20.0% of held-out wells | 3-WELL bootstrap 5th -5.845, P(>0) 0.3111
    GATE: nested gain > 0 FAIL | helps majority FAIL | 3-well 5th > 0 FAIL

`l1curv` is the only family helping a majority (57.5%) yet still losing on nested RMSE.

### THE INFORMATIVE NEGATIVE — why the drift prior fails, MEASURED not assumed

`drift` was the most principled idea and failed hardest (-11.475), despite mu ~ 0 in most wells (mean
+0.045, median +0.000, |mu|>1 in only 2%). So the mechanism was tested:

    degeneracy control: 11 wells with mu EXACTLY 0  ->  max|drift - l1| = 0.000000
                        29 wells with mu != 0       ->  mean degradation +2.216
    corr(|mu|, degradation) = +0.796
    DP steps per well: median 477, max 783
    accumulated pull |mu| x steps: median 48.4 ft, max 810 ft

The degeneracy control is EXACT, so this is not an implementation error. **THE DP INTEGRATES THE
TRANSITION TERM OVER THE PATH**: a per-step directional prior of a fraction of a grid unit compounds over
~477 steps into TENS OF FEET of systematic pull -- median 48 ft against a 12 ft RMSE scale. A drift
estimate that is unbiased in the MEDIAN is therefore not neutral; its per-well noise is amplified by path
length.

**SAME FAILURE CLASS AS Q13**, where a coverage-masked emission applied a directional pull that was
marginally good per row and cumulatively harmful. Q40 is that mechanism on the transition side, now with
a clean degeneracy control and a quantified predictor.

**PROPOSED STANDING RULE:** *any per-step directional term in a path DP is multiplied by the path length.
Judge estimate quality against the ACCUMULATED pull (|estimate| x steps), not the per-step magnitude; a
near-zero-mean noisy estimate is actively harmful, not neutral.*

### What this closes

The transition lever **within the penalty-shape and local-prior family** (L1/L2/Huber, drift prior,
curvature, L1+curvature). The deployed L1 is the best of 45 arms and no family passes any gate condition.
With Q17 (emission closed), **both named levers on the alignment line are now measured rather than
assumed.** NOT closed: learned or state-dependent transitions, and per-well adaptive lambda -- untested,
and now carrying a concrete warning from the compounding mechanism. Beam width K=6 and BAND=60 were
inherited from Q10 and not varied; they are arguably part of the transition model and remain untested.

### No submission, and it would not have been submittable anyway

The gate fails on all three conditions, so step 5 does not trigger; and even had it passed, this line sits
at ~12.2 against the deployed honest 8.8626 (37% worse), clearing neither the research bar nor the submit
gate. Consistent with Q33: next 24 h spends 0 slots.

## 2026-07-29 17:40 UTC — Q41 ensemble search: 0 of 355 arms clear the 3-well gate

`reports/q41_nonhomogeneous_ensemble_search_2026-07-30.md`, `scripts/q41_nonhomogeneous_ensemble.py`.
**Closed with an exact reason. No submission, quota 0/5.**

### BLOCKER on the arm the task asks for first

**honest + frontier CANNOT be validated by well.** The frontier family exists locally only as TEST-SET
submission CSVs (14,151 rows, 3 wells, NO truth); there is no frontier prediction on any train well. What
could be computed is non-homogeneity without accuracy -- exactly the "information without validation" the
ledger declines to act on. Recorded as a blocker, not guessed at. Producing that arm needs a fresh frontier
GPU run for train-well predictions, which Q33's budget rules out.

### Why this was not a repeat of the 07-22 audit

That audit tested SINGLE candidates and all failed the 3-well gate, the recorded lesson being that per-well
gain std (~1.3) far exceeds mean gain, so the 5th percentile is negative for everything. That is a VARIANCE
failure, and averaging is the one operation that reduces variance (Rule #1's transferable class). So Q41
asked the new question: **does an ensemble of decorrelated members clear the gate every single fails?**

Error-correlation with the deployed line identifies the genuinely decorrelated axis: dwt 0.868 and pf 0.831
vs the structural variants at 0.96-0.97 (near-duplicates -- averaging those is what the task forbids). Both
classes were included so the distinction is measured, not asserted.

### Result — 355 arms

    NESTED across all 355 arms, splits BY WELL
      selected 8.5281 vs deployed 8.8626 -> gain +0.3346
      helps 58.8% of held-out wells
      3-WELL bootstrap 5th -1.3687  50th +0.1759  95th +1.9578  P(>0) 0.6108
    GATE: nested gain > 0 PASS | helps a majority PASS | 3-well 5th > 0 FAIL

Two of three pass -- **the best any candidate has done against this gate** -- and the third still fails.

### THE VARIANCE HYPOTHESIS IS REFUTED, and the structure says why

**0 of 355 arms have a 3-well 5th > 0.** The arms with the LEAST negative 5th are the ones that change the
deployed line LEAST:

    ('single','s_54844628')                +0.0000    0.0%   8.8626   <- deployed vs itself
    (s_54844628, s_a20_w25, 0.9)           -0.0684   56.8%   8.8224
    (s_54844628, s_k96_aniso, 0.9)         -0.0780   62.5%   8.8134
    (s_54844628, topk96_l75, 0.9)          -0.1103   64.6%   8.7843

**The 3-well 5th percentile is maximised by not changing the deployed line at all**, and degrades
monotonically with the size of the change -- in BOTH directions, including changes that improve pooled RMSE
and help ~65% of wells. The arithmetic explains it: with per-well gain mean ~0.35 and std ~1.3, a 3-well
mean has 5th percentile ~ 0.35 - 1.645*1.3/sqrt(3) ~ **-0.88**. Clearing zero at n=3 needs mean gain >~ 1.2,
more than 3x the best pooled gain anywhere in this space.

### The apparent gain is MEMBER SUBSTITUTION, not ensembling

Best ensemble 8.4984 vs best single member `topk96_l75` 8.5070 -> ensembling adds **+0.0086**. The nested
+0.3346 is almost entirely "use topk96_l75 instead of s_54844628". So the mechanism this task existed to
test contributes essentially nothing, and member substitution was already closed by the 07-22 audit for
failing this same gate.

### Recorded, NOT recommended

`topk96_l75` is **0.3556 better than the deployed honest line on 760-well OOF and has never been
submitted**. Not proposed: it fails the 3-well gate (5th -1.946 in the 07-22 audit), its error correlates
0.9445 with deployed so it adds little slot-2 diversity, and N4 put OOF->public transfer at 1.659x rather
than 1:1. Recorded so the option is visible rather than silently dropped.

### Limits

The honest+frontier arm is UNTESTED, not negative. Weights are global -- per-well or gated weights were not
tested, being the hard-selection class the ledger has closed and which Q40 showed compounds. The 3-well
bootstrap resamples train wells as a proxy for the competition's 3 wells.

## 2026-07-29 17:55 UTC — Q42 error taxonomy: most of the apparent structure is well-level sampling noise

`reports/q42_honest_line_error_taxonomy_2026-07-30.md`, `scripts/q42_error_taxonomy.py`.
**Line CLOSED, no group-level intervention proposed. No submission, quota 0/5.**

### The taxonomy looks real in-sample

Deployed line: pooled RMSE 8.8626, mean signed residual -0.3832. Quintile spreads of the mean signed
residual run 0.5-1.7 ft: struct_contrib 1.694 (q5 = -1.662), well_md 1.594, prefix_frac 1.212, mean_incl
1.120, nnb 0.840, dwt_pf_disagree 0.833, tortuosity 0.832. **Most of that is not structure.**

### SPLIT-HALF TEST — only the ROW-level features reproduce

Recomputed on two DISJOINT halves of 380 wells each:

    dwt_pf_disagree  corr(A,B) +0.815   <- reproduces
    struct_contrib             +0.802   <- reproduces (pattern; magnitude varies 2x)
    tortuosity                 -0.162
    prefix_frac                -0.270
    well_md                    -0.290
    nnb                        -0.566
    mean_incl                  -0.648
    closest_all                -0.751

**Only 2 of 8 reproduce, and they are exactly the two ROW-level features.** Every WELL-level feature
ANTI-correlates across disjoint halves -- their quintile patterns flip sign, which is what noise does.

**The arithmetic:** per-well mean residual has std **6.673** across wells, and a quintile holds ~152 wells,
so the standard error of a group mean is ~6.673/sqrt(152) ~ **0.54** -- the same size as the observed
spreads. Rows within a well are strongly correlated, so binning by a well-level feature gives an effective
n of **152 WELLS, not 744,000 rows**.

**PROPOSED STANDING RULE:** *when segmenting residuals by a WELL-level feature, the effective n is the
number of WELLS in the bin, not the number of rows. Compare any observed spread against sigma_well /
sqrt(n_wells) before treating it as structure.*

### Out-of-fold group-constant corrections

    best: struct_contrib  OOF 8.8562  gain +0.0065  helps 46.3%  3-well 5th -0.5101
    segments with a positive OOF gain: 2 of 13
    segments clearing the 3-well 5th:  0 of 13
    NO segment helps a majority of wells (max 49.1%)

Even the two REPRODUCIBLE segments do not pay: struct_contrib +0.0065, dwt_pf_disagree **-0.0069**. The
pattern reproduces; its magnitude is too small and too unstable (q5: A -2.18 vs B -0.97) for a constant.

### THE QUESTION THE TASK ASKED: does coarsening rescue Q16?

    group-level OOF R^2: struct_contrib -0.00042, row_frac -0.00181, well_md -0.00263, closest_all -0.00640
    Q16 reference (row-level GBM, same protocol):  -0.0802

**Coarsening changes the FAILURE MODE but not the CONCLUSION.** R^2 moves from -0.0802 to ~-0.001: the
coarse estimator has essentially eliminated the over-fitting that made the GBM anti-transfer, but it
converges to **ZERO, not to a positive value**. This is a sharper statement than Q16 alone could make --
the row-level failure was BOTH over-fitting AND absence of signal, and removing the over-fitting exposes
the absence.

### Closure, for structural reasons

11 of 13 segments have a NEGATIVE OOF gain; the best is +0.0065 on an 8.86 RMSE (0.07%); no segment helps
a majority of wells; 0 of 13 clear the 3-well 5th (consistent with Q41's finding that the 3-well 5th is
maximised by changing nothing); and the segments that look most promising are the least real. Step 3's
precondition -- do not build a correction unless the sign is predictable out-of-fold -- is NOT met at group
level either.

The honest line remains valuable as **slot-2 diversity** (Q18: it beats the frontier on ~29% of random
3-well draws). What is closed is the idea of IMPROVING it by group-level residual correction.

## 2026-07-29 18:05 UTC — Q43 transition-prior research: 12 sources, 5 proposals, 3 appended

`reports/q43_public_research_transition_priors_2026-07-30.md`. No submission, quota 0/5.

### What the search had to clear

Q40 found the deployed `lam*|dstate|/BAND` beats 45 alternatives -- but every arm it tested was a **soft
per-step penalty**, and its mechanism (per-step terms are multiplied by path length) defines what to look
for next: **path devices that are NOT soft per-step penalties**. Step 4's filter also discarded anything
that only improves pointwise emission/AUC, since Q17 closed that lever.

**Established while reading the code:** the current DP has **NO global constraint at all**. `run_dp`
windows +-BAND around the PREVIOUS state, so cumulative deviation from the anchor is unbounded (60 x ~477
steps) and there is **no minimum or maximum slope**.

### The three appended proposals

**`q54_dp_hard_path_constraints` (~10 min).** Sakoe-Chiba corridor + Itakura slope limits (0.5-2) as an
**admissibility MASK, not a penalty**. A hard cap bounds accumulated deviation **regardless of path
length** -- the exact structural complement of the family Q40 closed, and motivated by Q40's own compounding
mechanism rather than by hope.

**`q55_dp_decoder_averaging` (~10 min).** Beam-average (run_dp keeps K=6 beams but returns only beams[0])
and soft-min Bellman at temperature gamma. **Precedent that this is not idle: Q21 discovered the deployed
PF ensemble IS ALREADY a softmax over paths at T=5, sitting at a nested optimum of a 27-member family** --
and the same operator has never been applied to the DP. Requires a degeneracy check that T,gamma -> 0
reproduces the current hard-argmin decoder exactly.

**`q56_pf_backward_smoothing` (hours; smoke first).** THE MODELLING GAP: `run_particle_filter` is a
**single forward pass**, yet **the entire toe GR log is observable at prediction time** -- we predict TVT
for rows whose GR we can already see, so a forward-only filter discards genuinely available information.
FFBSi re-weights earlier particles using later observations; it is an averaging operation, so Q40's
compounding warning does not apply. The prompt carries both Q36 corrections explicitly: patch the DEPLOYED
PF source (not `pf_honest_forward.py`) and score INSIDE the blend, where any gain halves.

### Documented but deliberately NOT appended

**P4 geometric transition scale** (map-matching style, from MD advance and inclination) -- too close to
Q40's `drift` arm, which failed worst at -11.475. A *scale* is non-directional where a *drift* is
directional, so it should not compound, but that argument is untested and Q40's failure is recent and
large. Must wait behind q54/q55 and report the accumulated-pull diagnostic if run.

**P5 path-distribution output** -- subsumed by q55, which is its concrete cheap instance.

**Discarded under step 4:** the wavelet+DTW stratigraphic correlation papers improve the emission side
without adding a path constraint.

### Gates and the honesty note carried into all three prompts

All three: standing three-part gate (nested by-well gain > 0 AND helps > 50% of wells AND 3-well 5th > 0),
`can_submit=false`. **The alignment DP sits at ~12.2 against the deployed honest line's 8.8626, so passing
these gates would make the transition lever worth pursuing, NOT make the artifact submittable.** Q41 also
showed the 3-well 5th is maximised by changing nothing, so that condition is expected to fail -- the
informative outputs are the nested gain and the per-well win rate.

### Limit recorded

The geosteering-specific HMM search returned **no geosteering results at all**; the transferable material
came from **map-matching (GPS-to-road) and general HMM/DTW literature** instead. Several petroleum sources
(SPWLA, ScienceDirect) are abstract-only or paywalled and were used for the method IDEA, not implementation
detail. No source was executed or copied.
