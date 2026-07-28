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
