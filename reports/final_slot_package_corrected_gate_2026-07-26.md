# Final-slot package — 2026-07-26 (rewritten; supersedes all earlier versions)

Deadline **2026-08-05 23:59 UTC**. Final score = **best of the 2 selected submissions** on the private
set, so the object being chosen is a **pair**, not two independent picks.

This version replaces the earlier text, which contained a contradiction: the top recommended
`54844628` for slot 2 while a later section still recommended `54968060` unless provenance was weighted.
The three criteria are now separated explicitly and each is stated in full.

## Board (live 2026-07-26 15:09 UTC)

| ref | public | side | family | provenance | OOF |
|---|---|---|---|---|---|
| `54922806` | **6.563** | teammate | frontier (overlap-ON) | public-derived | no |
| `54968060` | 6.643 | ours | frontier (overlap-OFF, validated no-retrieval) | public-derived | no |
| `54896975` | 6.669 | teammate | frontier (overlap-ON) | public-derived | no |
| `54923144` | 6.678 | teammate | frontier (GR-sigma) | public-derived | no |
| `54990075` | 6.690 | ours | frontier (SP45-only) | public-derived | no |
| `54844628` | 7.891 | ours | **honest** (DWT+PF+structural field) | **fully owned** | **yes** |
| `54878409` | 7.953 | ours | honest variant | fully owned | yes — excluded (regression) |

## The three recommendations

Produced by `scripts/final_selection_simulator.py` (pair-level best-of-2 under H-visible / H-hidden /
mixed; retrieval penalty = the **measured** 0.080 = 6.643 − 6.563).

### score-first → `54922806` (6.563) + `54844628` (7.891)
Minimise the modelled private score, ignoring lineage. Worst case **6.643**, mean **6.603** — the best
available. Note that **9 pairs tie** within 0.01 of this worst case, because under H-hidden `54922806`
degrades exactly to 6.643, which is the level of every no-retrieval candidate. Score alone therefore
does **not** pick a unique pair.

### diversity-first → `54922806` (6.563) + `54844628` (7.891)
Among the score-tied pairs, prefer members that fail independently. Every frontier+frontier pair has
family diversity 0 — a family-wide problem in the frontier stack (third-party artifacts, or a
visible-well-specific fit beyond the measured overlap term) would remove **both** slots at once. Pairing
the frontier with the honest line gives family diversity 1 at **the same worst case (6.643)**, so the
insurance is free. Among the diverse pairs, `54922806` has the better mean (6.603 vs 6.643).

### provenance-first → `54922806` (6.563) + `54844628` (7.891)
Require at least one slot to be a fully-owned, OOF-validated pipeline. `54844628` is the only candidate
meeting that bar (760-well nested OOF + bootstrap, every component built and audited in this repo).
Among pairs containing it, the best worst case is again with `54922806`.

## Consolidated recommendation

**All three criteria converge on `54922806` + `54844628`.** There is no criterion under which a second
frontier candidate improves the pair: slot 1 already represents the frontier line, so adding
`54968060` / `54990075` / `54896975` / `54923144` as slot 2 is redundant (family diversity 0, identical
worst case), while `54844628` supplies independent-failure insurance at no modelled cost.

## Where the other candidates stand

- `54968060` (6.643) — fully validated no-retrieval frontier run, and the natural **replacement for
  slot 1** if an our-account frontier representative is ever preferred over the teammate branch. It is
  redundant as a *second* slot.
- `54990075` (6.690) — SP45-only. Its result **settled an open question** (below), but it is neither the
  best frontier variant nor diverse, so it is not a slot candidate.
- `54878409` (7.953) — excluded, measured regression.

## What `54990075` = 6.690 settled

Pre-registered reading (2026-07-26 round 2): `< 6.643` → post-SP45 stages are net-negative;
`6.643–6.678` → neutral; `> 6.678` → the stages earn their place. **Result 6.690 → the last branch.**

The frontier's post-SP45 stages (learned-trajectory blend, prefix calibration, model-package correction,
bimodal hedge) **do** contribute on the leaderboard, and the local proxy that favoured SP45-only
(2.703 vs 3.259 vs train-copy TVT) pointed the **wrong way**. This is a direct, independent confirmation
of the G1.2 §3 saturation finding: proximity to train-copy TVT is a weak and sometimes misleading signal.
Practical consequence for the pipeline: **a proxy-only preference is not sufficient evidence to re-rank
candidates** — it must be paired with either a large effect or a structural argument.

## Sensitivity

The only input that could move this is the retrieval penalty (measured 0.080). If the true H-hidden
degradation of overlap-ON branches were much larger, `54922806` would fall behind `54844628` under
H-hidden and the pair's worst case would be set by the honest slot — which strengthens, not weakens, the
case for keeping `54844628` in slot 2. The recommendation is stable across the plausible range.

## Provenance reservation — narrowed by the G1.3 audit (2026-07-28)

Earlier wording described the frontier line as depending on "9 third-party public datasets". Measured
against source and run logs (`reports/frontier_dependency_provenance_audit_2026-07-28.md`):

> Frontier candidates depend on **one** third-party public dataset that is not already part of our own
> stack — `fleongg/rogii-claude-models-pub` (learned-trajectory model, blend weight 0.40), whose measured
> public value is **≈0.047** (`54990075` SP45-only 6.690 vs `54968060` 6.643), i.e. inside the
> ~0.115 config-variance floor. Of the rest: `ravaghi/…artifacts` is **shared with our own honest line**,
> `koolbox-offline` supplies offline pip wheels only, `pilkwang/rogii-model-package` was
> **guard-rejected at runtime** (`p95 diff 29.464 > 25.000`, `selected_for_submission_csv = False`), and
> five datasets are **vestigial** (zero source references, zero log appearances).

**Amended same day (variant-matrix round).** The ≈0.047 above was derived on the assumption that the
other post-SP45 stages were inert. That assumption was wrong: the **PF bimodal branch hedge applies
+2.0 ft to all 4,301 rows of `00e12e8b`** (`reports/frontier_variant_matrix_lite_2026-07-28.md`). So
`54990075` and `54968060` differ across **two** active stages, and ≈0.047 is a **joint upper bound** for
the learned-trajectory blend *and* the bimodal hedge — the `fleongg` dataset's own share can only be
smaller. The dependency count (one prediction-affecting third-party dataset) is unaffected.

**The slot recommendation is unchanged** — all three criteria still converge on
`54922806 + 54844628`. What changes is the *argument*: the frontier's dependency exposure is a single
quantified dataset worth ≈0.047, not a nine-dataset surface. Provenance-first still prefers `54844628`
in slot 2, but on the grounds that it is the only fully-owned, 760-well-OOF-validated candidate — a
different property from dependency count.

## Sensitivity addendum — the scored scale's own variance (N4, 2026-07-28)

`reports/n4_conformal_well_uncertainty_2026-07-28.md` measured, for the deployed honest line held FIXED,
the pooled row-weighted RMSE of a random 3-well draw:

```
5th 3.491   25th 5.040   median 6.708   75th 8.990   95th 15.138
```

The scored quantity itself spans more than 4x between its 5th and 95th percentiles for an unchanged model.
Two consequences for this package:

1. The public gaps that separate the frontier family from the honest line (6.563 vs 7.891, i.e. 1.33) are
   comfortably larger than the config-variance floor (~0.115) but are **not** large relative to 3-well
   draw variance. The *ranking* used here is still the best available evidence — it is measured on the
   same 3 wells for every candidate, so draw variance is common-mode and cancels — but no absolute
   private score should be inferred from it.
2. The recommendation is unchanged: `54922806` + `54844628` under score-first, diversity-first and
   provenance-first. Draw variance strengthens the diversity argument, since it raises the value of
   holding two members that fail independently.

Also measured: OOF on the 3 test wells 4.756 vs public 7.891 = **1.659x**. OOF-derived bounds are not
leaderboard bounds and must not be quoted as such in this package.

## Q18 stress test (2026-07-29) — the slot-1 gap is not resolvable at 3-well scale

`reports/q18_public_leaderboard_family_stress_2026-07-29.md`, `scripts/q18_final_pair_stress.py`.
**The recommended pair is unchanged. The reason for it changes materially.**

### A fourth view: our-account-first

Ownership is distinct from provenance — `54968060` is our account but *public-derived*, so
provenance-first does not select it while our-account-first does.

| view | pair | worst | mean | famDiv |
|---|---|---|---|---|
| score-first | `54922806` + `54844628` | 6.643 | 6.603 | 1 |
| diversity-first | `54922806` + `54844628` | 6.643 | 6.603 | 1 |
| provenance-first | `54922806` + `54844628` | 6.643 | 6.603 | 1 |
| **our-account-first** | `54968060` + `54844628` | 6.643 | 6.643 | 1 |

**Price of the our-account constraint: +0.000 worst case, +0.040 mean** — inside the ~0.115
config-variance floor.

### Degradation stress

How far must `54922806` degrade beyond the modelled retrieval penalty to lose slot 1?

| rival | H-visible | H-hidden |
|---|---|---|
| `54968060` | 0.080 | **0.000** |
| `54844628` | 1.328 | 1.248 |

Under H-hidden the threshold against `54968060` is already **zero** — both sit at 6.643, because that
hypothesis makes the overlap contribution inert and 6.643 IS the measured overlap-OFF level. Slot 1's
advantage exists only under H-visible, and there it is 0.080.

### The load-bearing measurement — is 0.080 resolvable on 3 wells?

N4 measured that the scored quantity spans 3.49..15.14 across random 3-well draws for a FIXED model, but
that spread is **common-mode and cancels in a ranking**. What does not cancel is the candidate x draw
INTERACTION. That was measured, not assumed: 9 local candidate prediction columns with truth over 760
wells / 3.72M rows, 20,000 random 3-well draws per pair, pooled gap vs P(the draw reverses the pooled
ranking).

| pooled gap band | mean P(reversed) | n |
|---|---|---|
| <= 0.30 | **44.8%** | 10 |
| >= 1.00 | **28.3%** | 13 |

- **Slot-1 gap 0.080** — nearest measured pairs (0.024, 0.028, 0.043) reverse **46-50%** of the time. A
  0.080 public advantage carries essentially NO information about which candidate is better on a
  different 3-well draw. **Score-first does not actually distinguish `54922806` from `54968060`.**
- **Frontier-vs-honest gap 1.328** — nearest measured pair (1.426) reverses **29.1%**. The honest line
  beats the frontier line on roughly **3 in 10** random 3-well draws. The slot-2 insurance is not a
  remote contingency; it is a ~29% event, which is a far firmer basis for diversity-first than
  "free on worst case".

### Consequence for the decision

- **Default unchanged: `54922806` + `54844628`.**
- **`54968060` + `54844628` is fully defensible** at +0.000 worst / +0.040 mean, and the 0.080 separating
  them is not resolvable at the scoring scale. Choosing between these two pairs is an **ownership
  judgment for the project owner, not something score evidence can settle** — recorded as such rather
  than decided unilaterally.
- **Slot 2 is now settled on firmer ground:** family-independent insurance that pays on ~29% of draws at
  zero modelled worst-case cost.

### Limits

Reversal probabilities are measured on honest-family local candidates, since frontier candidates have no
per-well truth (they are scored only on the 3 hidden wells). The transfer argument is that 3-well
sampling noise is a property of the well population rather than of a pipeline, and one measured member
(`s_54844628`) is an actual pair member. Draws sample with replacement (~0.4% collision over 3 draws).
The 760 local wells are train wells, so this measures the SCALE of 3-well ranking instability, not the
specific instability of the actual test draw.

### Live-refresh confirmations

No new private-score visibility (`privateScore` empty for every submission; never used). `55064411` still
PENDING (~5.8 h) and carried only as a parametric contingent entrant: below 6.563 it takes slot 1 on all
four views; between 6.563 and 6.643 it is the best our-account frontier and takes slot 1 on
our-account-first only — but that band sits inside the same coin-flip region, so it would be **ownership
evidence, not score evidence**. No Q10-Q17 candidate enters the board.

## 2026-07-29 04:15 UTC — `55064411` scored 6.695; recommendation unchanged; selection deadline flagged

`55064411` (Q14 frontier hedge-OFF, our account) landed at **public 6.695**. Against `54968060` (6.643),
the kernel it was diff-verified against, hedge-OFF costs **+0.052** — inside the ~0.115 config-variance
floor and inside the band Q18 measured as a coin flip at 3-well scale. It is our **worst** frontier
candidate on public and **enters no slot**.

**Board updated:**

| ref | public | side | family |
|---|---|---|---|
| `54922806` | **6.563** | teammate | frontier (overlap-ON) |
| `54968060` | 6.643 | ours | frontier (overlap-OFF) |
| `54896975` | 6.669 | teammate | frontier |
| `54923144` | 6.678 | teammate | frontier |
| `54990075` | 6.690 | ours | frontier (SP45-only) |
| `55064411` | **6.695** | ours | frontier (hedge-OFF) — new, enters no slot |
| `54844628` | 7.891 | ours | **honest**, fully owned, 760-well OOF |

**Recommendation unchanged:**

| view | pair | worst | mean |
|---|---|---|---|
| score / diversity / provenance-first | `54922806` + `54844628` | 6.643 | 6.603 |
| our-account-first | `54968060` + `54844628` | 6.643 | 6.643 |

### THE FINAL SELECTION IS A SEPARATE ACTION, AND IT IS UNSCHEDULED

Selecting the 2 submissions on Kaggle **costs no quota** but must be done before **2026-08-05 23:59 UTC**,
or Kaggle applies its own default choice. The pair needs **0 additional slots** — every member is already
submitted and scored, so the recommendation is executable today.

**Q33 recommends performing the selection by 2026-08-04**, a day early. It can be revised afterwards;
leaving it to the final hours cannot. This is the highest-consequence remaining step in the project.

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

## Q45 CORRECTION (2026-07-29 20:45 UTC) — the same-code noise floor is now MEASURED, and two priced stages fall below it

An independent public diagnostic, `georgymamarin/measure-your-noise-floor-before-believing-a-lever`
(2026-07-27, 88 votes, 0% code overlap with our family), resubmitted **five kernels fourteen times with
nothing changed inside any of them**:

```
kernel                                  reruns   public scores                    spread     sd
A  ayodeji branch-conservative v599       4      6.700 6.726 6.641 6.671          0.085    0.037
B  baidalinadilzhan lb-7.201              4      7.219 7.240 7.259 7.282          0.063    0.027
C  aevionlabs 7.159 family                2      7.216 7.305                      0.089      -
D  bernubritz public rebuild              2      7.246 7.280                      0.034      -
E  a fork + the author's own corrector    2      7.535 7.647                      0.112      -
```

**This settles the conflict Q39 §4 flagged.** Our two figures were a same-code pair at 0.009 and an older
recorded config-variance floor of ~0.115. The measured answer is **sd ≈ 0.027–0.037, with spreads up to
0.112 over as few as two reruns** — so the 0.009 pair was a lucky draw and was over-trusted, and ~0.115 is
about the outer edge rather than a mystery.

Q39's stage matrix re-read against sd ≈ 0.03:

| stage | effect | previous classification | re-read |
|---|---|---|---|
| GR sigma ×1.3 | −0.1105 | supported benefit on public | **holds** (~3 sd, and measured wholly on our own account) |
| bimodal hedge | +0.052 when removed | supported benefit [floor-confounded] | **unresolved** (~1.7 sd) |
| post-SP45 stages, jointly | +0.047 when truncated | supported benefit, joint | **unresolved** (~1.6 sd) |
| overlap / retrieval | −0.031 | not load-bearing, uncertain sign | **unchanged** (~1 sd) |

**Operational threshold:** one submission can only *read* an effect of roughly **0.1 ft (≈3 sd)** or larger.
Below that, a candidate is indistinguishable from a rerun of the same code, so it cannot justify a slot.
This tightens Q33's bar with a measured number instead of a disputed one.

**Board density, from our own refresh the same evening:** 114 of the top 200 sit inside [6.20, 6.60], and
ranks 190–200 span 6.366–6.372 — **eleven ranks inside 0.007 ft**. A private reshuffle at that density is
the expected case, not a tail scenario. `georgymamarin` independently reports the bronze line at 6.470 with
~570 teams inside ±0.037 ft of 6.473 on a 2026-07-26 snapshot.

**A second Q45 finding limits how the external channel may be used at all:** `arnavsalkade/rogii-public-6-451-base`
and `leonidzaporozhets/new-strategy-score-6-213` are both byte-identical to our own `54922806`
(pristine base + the single `*1.3` token at cell 29), and `leonidzaporozhets` carries an identical 7-dataset
attachment list, yet the advertised numbers span **0.350** against our *measured* 6.563. All eight attached
dataset slugs were last updated 2026-05-09…2026-06-27, so mutable artifacts are excluded, and 0.350 is ~10 sd
of the measured floor. **A score advertised in a kernel title or slug is therefore not a measurement of the
code that kernel contains.** Advertised numbers are triage only; every effect size must come from a score
measured on our own account. Full detail: `reports/q45_external_leaderboard_gap_refresh_2026-07-30.md`.

## Q44 addendum (2026-07-29 21:05 UTC) — the pair decision, re-derived with the draw modelled

`scripts/q44_private_risk_stress.py`, 24 scenario cells, Monte Carlo over the draw rather than a point
estimate. Degeneracy control: at draw scale 0 the two pairs value at 6.6425 vs 6.6430, reproducing Q53's
+0.0005.

**1. The second slot is the largest positive term in the whole decision.** H-hidden, measured cell, value of
the pair versus its slot-1 candidate alone:

```
pair                                        mean     p95   | gain over slot-1 alone
A  54922806 + 54844628  (diverse)         6.1818  8.5017   |  mean -0.4561   p95 -0.9389
B  54968060 + 54844628  (diverse, ours)   6.1829  8.5022   |  mean -0.4560   p95 -0.9302
C  54922806 + 54968060  (frontier only)   6.5783  9.3671   |  mean -0.0595   p95 -0.0735
```

A diverse pair is worth **~0.46 ft in the mean and ~0.94 in the bad tail**; a second frontier member is worth
0.060 / 0.074. **Best-of-2 is a call option on variance** — you keep the better realisation, so decorrelation
and draw uncertainty both *add* value. Q18's "free insurance at zero modelled cost" was the most a point
model could say; with the draw modelled the honest slot is the decision's biggest positive.
**Whatever happens in slot 1, `54844628` holds slot 2.**

**2. The slot-1 dispute is bounded at 0.077 ft.** Price of ownership-first (B) over score-first (A) across all
24 cells: worst **+0.0773 mean / +0.0653 p95**; **+0.0013** in the measured + evidence-supported cell
(retrieval −0.031, GR-sigma edge does not transfer); **strictly negative in 8 of 24 cells** (every cell with
retrieval ≥ 0 and no sigma transfer, and every spurious-match stress cell, down to −0.157).

**3. Score-first's discriminator is below the measured resolution.** Its case is the 0.080 public gap
(`54922806` 6.563 vs `54968060` 6.643). Q45's measured same-code floor is sd 0.03, so 0.080 is **2.7 sd**,
under the ~0.09 needed to rank two variants. Q39 splits it into GR-sigma (−0.1105, 3.7 sd, resolvable) and
overlap (+0.031, ~1 sd, noise) — and Q36 measured that GR-sigma multiplier on 760 wells with truth: **helps
42.1% of wells, negative median**. So on novel wells score-first's only resolvable component is the one our
own held-out evidence says does not transfer. **The two pairs are tied on measurement**, and the tie should
be broken on the axis that is not noise-limited: ownership and verifiability.

**4. Two axes turn out not to discriminate at all.** Dependency risk: both recommended pairs contain
`54844628` plus exactly one frontier member, so their dependency sets are **identical** — this axis should
stop being cited as favouring either. Draw representativeness: the A-vs-B gap stays ≤0.001 at every draw
scale. Losing access to *every* teammate submission costs ~0.004 ft, and the ours-only optimum is pair B.

**5. Rank context.** Local density ≈7700 teams/ft: 0.03 ft ≈ 231 ranks, our 0.093 ft gap to bronze ≈ 716
ranks, and one sd of draw noise exceeds the whole board. Since the top-200 is dominated by the same public
family as our frontier slot, most rivals' private shifts are correlated with it — **`54844628` is the only
submission we hold whose error is decorrelated from the crowd**, so it is also the only source of *relative*
rank movement.

Full detail and limits: `reports/q44_frontier_private_risk_stress_2026-07-30.md`.
