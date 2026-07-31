# Q48 — deferred-task review: one re-opened because its own trigger fired, six closed, four confirmed deferred

Date: 2026-07-30 00:25 UTC
Task: `q48_reopen_deferred_value_check` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **11 rows reviewed. 1 re-queued (narrowed), 6 closed, 4 confirmed deferred with re-verified reasons.
No submission. Quota 0/5.**

## 1. What counted as a new fact

The task's default is *still-deferred*, and re-opening requires a new fact that changes expected value. The
facts available since these rows were written are Q38–Q47 plus Q56/Q57:

| new fact | round |
|---|---|
| same-code public noise floor **measured** at sd 0.027–0.037 (14 unchanged resubmissions, external) | Q45 |
| advertised public scores are **not** measurements of the pullable code (0.350 spread on byte-identical code) | Q45 |
| pool 798 → **1136** kernels, still nothing published below 6.2 | Q45 |
| best-of-2 is a **call option on variance**; diverse pair worth ~0.46 mean / 0.94 tail; slot-1 dispute ≤0.077 | Q44 |
| three teammate kernels now return **byte-identical** output → at least two re-run since submission | Q46 |
| final selection is UI-only and **unverifiable by API**; both defaults exclude `54844628` | Q47 |
| PF backward smoothing: **+0.2541** nested at blend level, helps 68.9% with positive median | Q56 |
| alignment DP closed on **four** sides; binding constraint located in the emission's **directional** content | Q57 |

## 2. Decisions

| row | prior status | decision |
|---|---|---|
| `q23_frontier_stage_localizer` | deferred | **CLOSED — superseded** |
| `q24_frontier_run_variance_control` | deferred | **CLOSED — objective achieved externally, free** |
| `q25_submission_ensemble_nonhomogeneous` | deferred | **CLOSED — measured mechanism against it** |
| `q26_public_research_geosteering_methods` | deferred | still deferred, **reason strengthened** |
| `q27_public_research_sequence_models` | deferred | still deferred; narrower successor identified, **not queued** |
| `q28_meta_validation_protocol_audit` | deferred | **RE-OPENED as a narrowed successor** |
| `q29_final_slot_candidate_packager` | deferred | still deferred (date), **scope reduced** |
| `q31_teammate_mark_repo_refresh` | deferred | still deferred, **re-verified** |
| `q32_score_watcher_and_recovery` | deferred | **CLOSED — merged away, and q22 is done** |
| `q34_new_high_value_queue_from_evidence` | deferred | **CLOSED — duplicate, and q20 is done** |
| `q17_kaggle_gpu_tiny_training_followup` | **hold, no reason recorded** | **CLOSED** |

### The one re-opening — `q28`, because its own condition fired

`q28` was deferred with the explicit condition *"revisit only if a measurement error recurs."* **It has
recurred four times in roughly six hours**, every one caught before it reached a conclusion but only because
somebody looked:

1. **Q56** — a 12-well smoke over-stated its effect by **58%** and, worse, *passed* the three-part gate
   (+0.6050 / 91.7% / 3-well 5th **+0.0836**) where the 760-well run *failed* it (+0.2541 / 68.9% / **−0.3238**).
2. **Q57** — an 8-well smoke supported the conclusion "the DP declines the freedom it is given"; at 40 wells
   the dip was active on 42–46% of steps and path deviation rose 4.9 → 21.1 ft. The report was corrected.
3. **Q58** — the aligned frame's per-row `nnb` / `closest_surv` are **not** the deployed structural-field
   gate (the deployed gate is `struct_oof.npz`'s per-well meta): 2139 rows wrong, 6 boundary wells.
4. **Q46** — `api.kernels_output(slug)` serves the **latest** version, not the submitted artifact; three
   teammate kernels scoring 6.563 / 6.669 / 6.678 all returned one byte-identical file.

Re-opened as **`q28_measurement_traps_ledger`** (priority **672**, `can_submit=false`, no CPU), and
deliberately *not* the general introspective audit the original proposed: one page of pre-flight checks plus
the incident table, with an explicit requirement to separate traps **already enforced in code** from those
that are only conventions a reader must remember. It changes no conclusion.

### The closure worth the most — `q25`, which is now harmful rather than merely unevidenced

`q25` proposed a non-homogeneous **ensemble** of two submitted artifacts. It was deferred for a weak reason
("no evidence yet that it beats either member"). Q44 supplies a mechanism, and it points the other way.

Best-of-2 keeps the *better* of two realisations, so it is a call option on variance and decorrelation is the
asset. **An ensemble has lower variance than its members by construction — exactly the wrong direction.**
Simulated at Q44's implied per-candidate draw sd of 1.70 ft (cross-family difference sd 2.40 = √2 × 1.70),
400k draws, against the closed forms:

```
kept value (lower is better)              simulated     closed form
min(p1, p2)   two distinct members          -0.9541     -0.564*sigma = -0.9588
min(E,  p1)   ensemble + one member         -0.4750     -0.282*sigma = -0.4794
E             ensemble in both slots        +0.0037      0
```

- replacing one member with an ensemble of the two costs **+0.479 ft — it exactly halves the option value**;
- putting the ensemble in both slots costs **+0.958 ft**, destroying the option outright.

That is consistent with Q44's independently measured diverse-pair value of **0.456 ft**, because it is the
same quantity arrived at from the other direction. The ensemble is therefore harmful here **before** the
third-artifact slot cost is even counted. Closed on evidence, not on cost.

### The cheapest closure — `q24`, bought for free by someone else

`q24` would have spent several GPU full runs plus quota to measure the frontier's run-to-run variance.
Q45 found an external public diagnostic that resubmitted **five kernels fourteen times with nothing
changed** — sd 0.027–0.037, spreads to 0.112. That is a larger and cleaner measurement than this task could
have produced, at zero cost, and it settled the project's own 0.009-vs-0.115 conflict. Nothing left to buy.

### The bookkeeping closures

- **`q23`** — Q39 performed this stage localisation **with no frontier run**, from normalised cell-by-cell
  code diffs; Q45 then re-priced the output against the measured floor, and the hedge (+0.052, ~1.7 sd) and
  joint post-SP45 stages (+0.047, ~1.6 sd) fell **below readability**. Re-opening could only re-measure
  quantities now known to sit under the floor.
- **`q32`** — merged into `q22`, which is done. **`q34`** — duplicate of `q20`, which is done. Neither should
  sit in `deferred`, which implies it may return.
- **`q17_kaggle_gpu_tiny_training_followup`** — was on `hold` with **no reason recorded at all**, while
  carrying `can_submit=true, max_submit_cost=1`. A submission-capable row with no rationale is exactly the
  bookkeeping risk this review exists to remove. `HOLD` was in fact the outcome its own prompt specified
  (*"If none of them show a real signal, mark this task HOLD and move on"*), and it is also closed on
  substance: it proposes a tiny learned scorer, i.e. an **emission** improvement, and Q17 measured that a
  +0.056 AUC gain bought 0.167 RMSE of DP quality while Q57 located the constraint in the emission's
  *directional* content — which an AUC-trained scorer does not supply. The line sits at ~12.2 against the
  deployed honest 8.8626 and could not reach a submittable artifact before the deadline regardless.

### The four that stay deferred, each re-verified rather than assumed

- **`q26`** — Q45's refresh **strengthens** it: 1136 kernels (+42%), nothing below 6.2, and the parsed-score
  channel is triage-only.
- **`q27`** — stays deferred, and the narrower successor is recorded but **not queued**: Q57 sharpened the
  constraint to *directional* content, so the well-posed question is "does any test-available signal predict
  the **sign** of the next TVT move out-of-fold?" It is not queued because the alignment line cannot become a
  submittable artifact before 2026-08-05, so its expected value for the outcome is ~0 whatever the answer.
  Recorded so the framing survives.
- **`q29`** — date trigger still not met (needs ≥ 2026-08-03; today is 2026-07-30). Two changes noted on the
  row: the idle-queue risk it warned about is gone (five rows are queued), but that also means nothing
  re-activates **it** automatically, so `state.json`'s `endgame_action_required` command remains the only
  mechanism; and its **scope should shrink**, because Q46 already delivered the asset map and Q47 the
  selection checklist. What remains is a one-page consolidation, not a fresh package.
- **`q31`** — `git fetch` on 2026-07-30 confirms `origin/main` is **still at `a589fa8`**, unmoved since Q19
  audited it. Q46's teammate-kernel finding does **not** re-open this: those are Kaggle-side artifacts, not
  this repo, and the corresponding action is already an owner action in Q46/Q47.

## 3. Queue state after this round

```
done 49 | closed 8 | queued 5 | deferred 4 | in_progress 1

queued:  672 q28_measurement_traps_ledger        (re-opened here, narrowed)
         680 q49_transition_prior_smoke_from_research
         690 q50_ownership_first_candidate_search
         700 q51_owner_message_pack
         710 q52_next_queue_builder_after_q38_q51
in_progress: 629 q58_honest_kernel_backward_smoothing   (NS=64 producer, 158/760 at 35.3 min)
deferred: q26, q27, q29 (date-gated 2026-08-03), q31
```

Every row now carries an explicit reason, and `deferred` no longer contains anything that cannot return.

## 4. Limits

- The `q25` closure rests on Q44's noise model (Gaussian, per-candidate sd 1.70 implied by the cross-family
  difference sd of 2.40 calibrated from Q18's 29% reversal rate). The *sign* of the conclusion does not
  depend on that calibration — `E[min(E,p1)] = ½·E[min(p1,p2)]` holds for any symmetric draw with equal
  means — but the 0.479 ft magnitude does.
- `q26`/`q27` are judged on the pool as enumerated by Q45 (`dateRun` and `dateCreated`, 40 pages each). A
  public but never-listed kernel would be missed.
- Six closures are a bookkeeping change, not new evidence about the competition. Nothing in this round
  changes any score, slot recommendation, or measurement.
- `q29`'s date trigger is checked against the runner's clock; if the endgame is handled early the row should
  be flipped manually rather than waited on.

## 5. Next

`q28_measurement_traps_ledger` (672) is next by priority, then `q49`–`q52`. **`q58`'s NS=64 producer is in
flight** (158/760 wells at 35.3 min → ETA ~02:30 UTC) and remains the only live positive lead; it is
collected with `scripts/q58_struct_refit.py`, which is fast and re-runnable.
`q29_final_slot_candidate_packager` reactivates **2026-08-03**; the final selection is due **2026-08-04**
(hard deadline 2026-08-05 23:59 UTC) and costs no quota — and per Q47, **doing nothing discards the
recommended pair**.
