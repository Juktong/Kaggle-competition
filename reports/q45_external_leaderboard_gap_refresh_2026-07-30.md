# Q45 — external gap refresh: an independent public measurement pins the noise floor, and advertised scores turn out not to be measurements

Date: 2026-07-29 20:45 UTC
Task: `q45_external_leaderboard_gap_refresh` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Scripts: `scripts/q45_external_gap_refresh.py`, `scripts/q45_lineage_diff.py`
Logs: `reports/logs/q45_external_refresh_2026-07-30.log`, `reports/logs/q45_arch_scan_2026-07-30.log`,
snapshot `reports/logs/q45_kernel_snapshot_2026-07-30.json`
Outcome: **no submission, no Kaggle run, quota 0/5. One follow-up queued (`q57`), two finds classified
information-only, and one recorded project number corrected.**

## 1. Leaderboard refresh

| | Q19 (2026-07-29 early) | now (2026-07-29 20:34 UTC) |
|---|---|---|
| leader | 4.679 | **4.679** (unchanged, `shu01`, set 2026-07-25) |
| 200th place | 6.389 | **6.372** |
| our best public | 6.563 (`54922806`) | 6.563 |
| teams | 5886 | **5914** |
| our rank | 1277 | **1339** |

All 200 fetched rows are still ahead of our 6.563, and **we lost 62 places in ~16 hours without our score
changing** — the board is moving under us. 114 of the top 200 sit inside [6.20, 6.60], and ranks 190–200 span
6.366–6.372, i.e. **7 thousandths of a foot covers eleven ranks**. That density is the single most
decision-relevant number in this round, and §3 explains why.

## 2. Kernel pool refresh — the pool grew 42% and still contains nothing at the 5.x level

Enumerated by both `dateRun` and `dateCreated`, 40 pages each: **1136 distinct public kernels**, against
Q19's 798. 131 carry a parseable advertised score. Sorted best-first, after Q19's two known entries, the
next-best advertised is **6.594** and the pool then runs 6.6–8.9 exactly as Q19 recorded.

**So the refreshed answer to Q19's question is the same and is now on 42% more data: the ~200 teams at
4.7–6.4 have not published their methods.** Nothing published sits below 6.2.

21 kernels were last run on/after 2026-07-26. Three cleared the filter "advertised ≤ 6.5 and not already
resolved by Q19":

```
6.391  my0705/rogii-stacked-ensemble-highscoring-6-391   2026-07-29 14:50   <- new today
6.451  arnavsalkade/rogii-public-6-451-base              2026-07-23 06:00   <- Q19 missed it
4.383  yangrangrong/rogii-notebook4383-v8                2026-06-12 02:57   <- FALSE PARSE
```

**The 4.383 is a false parse and was checked rather than assumed:** `notebook4383` is Kaggle's
auto-generated notebook name, the notebook claims no score anywhere, and a public 4.383 would be **rank 1**
(the leader is 4.679). It is nonetheless a real find for a different reason — see Find C. The parser was
also fixed mid-round after `sans6262q/...` read as "6.262" from the *username*; scores are now parsed from
the slug only.

## 3. Find B first, because it reprices everything else — advertised scores are not measurements

`arnavsalkade/rogii-public-6-451-base` normalises to **45 code cells, positionally identical to the
pristine base except cell 29**, whose entire difference is the insert `*1.3` on the GR-sigma line. That is
byte-for-byte the same change as `leonidzaporozhets/new-strategy-score-6-213` (Q19's Find A) **and the same
change our own `54922806` carries**. Dataset attachments:

```
kernel                                           code                    datasets      score
leemarc223/...-pf-frontier-rerun (OUR 54922806)  base + cell29 '*1.3'    7             6.563  MEASURED
leonidzaporozhets/new-strategy-score-6-213       base + cell29 '*1.3'    same 7        6.213  advertised
arnavsalkade/rogii-public-6-451-base             base + cell29 '*1.3'    those 7 + yuki16/rogii-model-package   6.451  advertised
```

Identical code, and for `leonidzaporozhets` an **identical attachment list**, yet the advertised numbers span
**0.350** against our measured one. Two mechanisms had to be ruled out before reading that as noise:

- **mutable artifact datasets.** Kernels record dataset *slugs*, not versions, so an artifact updated
  between runs would silently change the inputs. Checked: all eight slugs were last updated between
  **2026-05-09 and 2026-06-27**, i.e. every one of them was frozen weeks before all three runs. **Not the
  explanation.**
- **run-to-run variance.** Addressed in §4 with an external measurement — and it is far too small.

**Conclusion: a score advertised in a public kernel's title or slug is not a measurement of the code that
kernel currently contains.** The title is written once; the notebook keeps moving. That matters
methodologically because Q19's pool survey — and the first half of this round — reads the published field
through exactly those parsed numbers. Their correct use is *triage only*: to decide which kernels to pull
and diff. Every effect size must come from a score measured on our own account.

Secondary mechanism, recorded because it is not excluded: the family contains a **discrete stochastic gate**
— `_gold_alpha` returns 0.0 outright when `delta_p95 > p['p95_hard']`, and G1.3 observed exactly that
rejection in our run (`p95 diff 29.464 > 25.000`, `selected_for_submission_csv=False`). A run in which the
gate *passes* would take a different branch and could jump much further than any Gaussian noise term. Our
own six family submissions (6.563 / 6.643 / 6.669 / 6.678 / 6.690 / 6.695) show **no second mode**, so there
is no internal support for this, but it cannot be refuted from outside a run.

## 4. The noise floor, measured independently — and one of our recorded numbers is wrong

The recency scan surfaced `georgymamarin/measure-your-noise-floor-before-believing-a-lever` (88 votes,
2026-07-27, 0% code overlap with the family). It is a diagnostic notebook, and it contains the measurement
this project has needed for two rounds: **five kernels resubmitted fourteen times between them with nothing
changed inside any of them.**

```
kernel                                   reruns   public scores                      spread     sd
A  ayodeji branch-conservative v599        4      6.700 6.726 6.641 6.671            0.085    0.037
B  baidalinadilzhan lb-7.201               4      7.219 7.240 7.259 7.282            0.063    0.027
C  aevionlabs 7.159 family                 2      7.216 7.305                        0.089      -
D  bernubritz public rebuild               2      7.246 7.280                        0.034      -
E  a fork + the author's own corrector     2      7.535 7.647                        0.112      -
```

**This settles the disagreement recorded in Q39 §4.** Our two figures were a same-code pair at **0.009** and
an older recorded config-variance floor of **~0.115**, and Q39 flagged that they conflict. On 14
resubmissions the truth is in between and closer to the larger one: **sd ≈ 0.027–0.037, with observed
spreads up to 0.112 over as few as two reruns.** Our 0.009 pair was a lucky draw from a distribution whose
sd is ~0.03 — a 0.009 gap is entirely ordinary, and it was never evidence that the family is resolvable at
the third decimal.

### Consequence — Q39's stage matrix, re-read at sd ≈ 0.03

| stage | effect on public | Q39 classification | **re-read against sd ≈ 0.03** |
|---|---|---|---|
| GR sigma ×1.3 | −0.1105 | supported benefit | **holds** — ~3 sd, and measured entirely on our own account |
| bimodal hedge | +0.052 when removed | supported benefit [floor-confounded] | **downgraded to unresolved** — ~1.7 sd |
| post-SP45 stages, jointly | +0.047 when truncated | supported benefit, joint | **downgraded to unresolved** — ~1.6 sd |
| overlap / retrieval | −0.031 | not load-bearing, uncertain sign | **unchanged** — ~1 sd, i.e. indistinguishable from noise |

So of the four stages Q39 could price, **one survives as resolvable and three do not.** Q39 hedged these as
"confounded by which floor applies"; the floor is now measured, and the hedge resolves against them.

**Practical threshold for Q33:** a single submission can only *read* an effect of about **0.1 (≈3 sd)** or
larger. Anything smaller cannot be distinguished from a rerun of the same code, so it cannot justify a slot.

That also independently corroborates our own final-slot reasoning from the outside: the author reports the
bronze line at **6.470** with about **570 teams inside ±0.037 ft of 6.473** on a 2026-07-26 snapshot. Our
own refresh (§1) measures the same density directly — eleven ranks inside 0.007 ft. A private reshuffle at
that density is not a tail scenario; it is the expected case.

**We do not adopt anything from this kernel.** It attaches an external dataset
(`georgymamarin/geosteering-world-cup-2021-expert-interpretations`), and the standing rule requires the
competition rule basis to be confirmed and written down before any external data is used. Only the author's
*own resubmission scores on this competition* are used above, which is public leaderboard information, not
external training data.

## 5. Find A — the new best-advertised kernel (6.391) resolves into four factors, three already closed

`my0705/rogii-stacked-ensemble-highscoring-6-391`, last run **2026-07-29 14:50 UTC** — the same author as
Q19's 6.520. 48 cells, **42 of them verbatim in the pristine base (88%)**. Aligned cell-by-cell, the whole
functional difference is three tokens plus three appended cells:

```
cell 29   base[2090] insert '*1.5'                     GR-sigma multiplier   (Q19's kernel used *1.3)
cell 34   PP.w_sub1  0.60 -> 0.50                      post-processing blend weight
cell 40   _gold_alpha: min(cap, max(0, alpha*1.30))  ->  alpha*1.75    model-package "gold profile" alpha
cell 43   _EX_* block: _EX_EXTRA_SHIFT = 0.522 on well '00e12e8b'      (identical to Q19's 6.520 find)
cell 45   run-summary audit cell                       no effect on predictions
cell 47   read-only visual appendix, _GS_PUBLIC_SCORE = 6.568          no effect on predictions
```

| factor | our own evidence | classification |
|---|---|---|
| `_EX_EXTRA_SHIFT = 0.522` on well `00e12e8b` | Q19 resolved this exact block: a hand-fitted per-well constant tuned against the 3 public wells | **not useful** — the hard-selection class, closed repeatedly |
| GR sigma `*1.5` | Q19 measured 1.5 as the interior optimum of the *standalone* PF (11.914); Q36 measured it **inside the deployed blend on 760 wells**: 1.5 → 9.3203, *worse* than 1.3's 9.1204 and worse than 1.0's 9.2903, helping 40.4% of wells with a negative median | **not useful** — already measured, and 1.5 is the worse of the two multipliers where it actually acts |
| `_gold_alpha` `1.30 → 1.75` | this is the model-package/gold-profile alpha. G1.3 observed the guard **reject** it at runtime (`delta_p95 > p95_hard` → `return 0.0`); Q39 classified the stage **measured inert**. Scaling a term that is zeroed before use cannot change the output | **information-only** — probably inert; would need a run to confirm the guard state |
| `PP.w_sub1` **0.60 → 0.50** | genuinely new. It is the weight between `sub1` (model-delta with warmup) and `lp` (likelihood-PF at scale_5): `delta = w_sub1·sub1 + (1−w_sub1)·lp`. Moving 0.60 → 0.50 is a move **toward equal weights**, i.e. Rule #1's averaging class, which is the class our ledger records as transferring | **information-only, not queued** — see below |

**Why `w_sub1` is not queued despite being the one new and structurally-favourable item.** It lives inside
the frontier's post-processing, where `sub1` and `lp` are frontier-internal quantities we have no honest
out-of-fold access to; measuring it would require reproducing the frontier's OOF, which this project has
repeatedly found is not honestly measurable. Measuring it on *public* instead would cost a GPU run plus a
slot to read an effect that is bundled with a hand-fitted per-well shift and is almost certainly below the
0.1 threshold §4 just established. **Worth recording, not worth a slot.**

One convergence is worth stating plainly: **our own honest line already sits at exactly 0.5/0.5**
(`base = 0.5·dwt + 0.5·pf`, verified in Q36). An independent public author has now moved the analogous
weight from 0.60 toward 0.50. That is external agreement with Rule #1's averaging class, arrived at
separately.

## 6. Find C — an independent public implementation of exactly what `q56` proposes

`yangrangrong/rogii-notebook4383-v8` (the false-parse kernel) is **not the Kaiwalya family at all** — 9
cells, 10.9k chars, 0% shared. Its own header: *"Particle Filter with sequence awareness, RTS smoothing, and
multi-feature likelihood."* It defines `apply_rts_smoother` (a backward RTS pass over the retained particle
trellis) and `apply_fixed_lag_smoother`, with `N_PARTICLES=200, N_SEEDS=64`.

That is **`q56_pf_backward_smoothing` (Q43's proposal P3), implemented publicly**. Two readings, both
recorded:

- **as a reference implementation** it de-risks q56's mechanics (which quantities to retain, where the
  backward pass attaches);
- **as evidence it works, it is nothing** — the kernel advertises **no score at all** and was last run
  2026-06-12, long before the current family. A public author implementing a lever and never publishing a
  number is weak evidence *against*, not for.

`q56`'s queue row has been annotated with this reference. It is **not** a new task and **not** a duplicate.

## 7. Different-architecture scan of the recency window — one genuinely new structure

Six recent kernels with real vote counts were pulled and measured by shared-normalised-cell overlap against
the pristine base:

```
kernel                                                cells   shared w/ base   verdict
romanrozen/catboost-baseline               (25 votes)   48        90%          Kaiwalya family, renamed
blacklions/well-level-gbdt-gate                         51        84%          family + a well-level GBDT gate
tamerlanomralinov/hahaha-det-agi           (44 votes)   54        61%          family hybrid
lucifer19/rogii-geoanchor                  (74 votes)   50        42%          partial-family hybrid
georgymamarin/measure-your-noise-floor...  (88 votes)   26         0%          diagnostic, no predictor  -> §4
tiktoktrendz/rogii-dip-aware-hmm-gbm                     1         0%          GENUINELY DIFFERENT -> below
```

`blacklions/well-level-gbdt-gate` is worth one line: a well-level GBDT gate is the family of thing Q16
(row-level residual GBM, CV R² = −0.0802) and Q42 (group-level constants, 2 of 13 positive, 0 of 13 clearing
the 3-well 5th) both closed on our own line with truth. **Not adopted**, and our evidence against it is
stronger than a kernel title is for it.

### `tiktoktrendz/rogii-dip-aware-hmm-gbm` — the one structural idea this round found

29k chars in a single cell, Numba-JIT, no attached artifact datasets. Its own working note describes: a
parallel **forward-backward HMM** over a TVT grid returning posterior mean **and posterior std**; a
600-particle PF; **14 beam-search configurations**; and a `HistGradientBoostingRegressor` meta-learner
consuming `hmm_std` as an uncertainty feature. Most of that is already closed on our line:

- forward-backward posterior mean — **Q55 measured this two hours ago.** The soft-min/forward-backward
  posterior concentrates on an optimum that scores *worse* than the greedy beam, because the DP objective is
  misaligned with RMSE. Independent implementation does not change that measurement.
- uncertainty-aware GBM stacking on residuals — Q16 and Q42.

**But one element is structurally new:** its transition model searches **41 dip rates with a momentum
factor**, i.e. the state is effectively **(TVT, dip)** rather than TVT alone. Everything our transition line
has closed operated on a *TVT-only* state: Q40's 45 soft per-step penalties on |Δstate|, N1's per-step
geometric bound, Q54's global corridors, Q55's decoders. **A dip/velocity dimension in the state space makes
dip continuity a property of the state instead of a penalty on the increment** — which is precisely the
"redefine the objective rather than tune it" direction Q55's closure pointed at, arrived at from outside.

Queued as **`q57_dip_state_augmented_dp`**: smoke-testable (reuses the Q10/Q40/Q54 harness, same split
seed), non-duplicate (no prior arm augmented the state), and carrying the standing three-part gate. Cost
control is explicit in the prompt: the state space multiplies by the dip-grid size, so the grid starts small
(9–13 values) with the existing beam.

## 8. Classification summary (task step 4)

| candidate | lineage | exact change | class |
|---|---|---|---|
| `my0705/...-6-391` 6.391 | base + 3 tokens + 3 cells (88% verbatim) | GR-σ ×1.5; `w_sub1` 0.60→0.50; `_gold_alpha` ×1.75; `_EX_` +0.522 ft on `00e12e8b` | **information-only** (hand-fit not useful; σ×1.5 already measured worse; alpha inert; `w_sub1` new but not honestly measurable) |
| `arnavsalkade/...-6-451` 6.451 | base + cell 29 `*1.3` | identical to `54922806` | **not useful as a method; load-bearing as evidence** — §3 |
| `leonidzaporozhets/...-6-213` 6.213 | re-verified: base + cell 29 `*1.3` | identical to `54922806` | **not useful as a method; load-bearing as evidence** — §3 |
| `yangrangrong/rogii-notebook4383-v8` | not the family | sequential PF + RTS + fixed-lag smoothing | **information-only** — reference implementation for `q56` |
| `georgymamarin/measure-your-noise-floor...` | not the family | 14 unchanged resubmissions of 5 kernels | **information-only, and the most valuable item in the round** — §4 |
| `tiktoktrendz/rogii-dip-aware-hmm-gbm` | not the family | (TVT, dip) state, 41 dip rates + momentum | **adoptable class → queued as `q57`** |
| `romanrozen`, `blacklions`, `tamerlanomralinov`, `lucifer19` | 42–90% family | renames / gates / hybrids | **not useful** |

## 9. Negative results, stated as such

- **The refreshed pool does not close the gap.** 1136 kernels, 338 more than Q19 saw, and the best genuinely
  new method-bearing kernel is a hand-fitted per-well constant. Nothing published is at the 5.x level.
- **No adoptable public method was found.** One queued follow-up came from an *architecture*, not from a
  score, and it is measured against our own truth, not adopted.
- **Our position got worse without our doing anything**: rank 1277 → 1339 in 16 hours, and 200th place moved
  from 6.389 to 6.372.
- **The 4.383 lead was a parser artefact**, and the parser also mis-read a username as a score before being
  fixed. Both are recorded rather than quietly corrected.
- **One of our own recorded numbers was wrong.** The 0.009 same-code spread from Q39 was over-trusted; the
  external 14-resubmission measurement puts the sd near 0.03, which retroactively demotes two of Q39's four
  priced stages to unresolved.

## 10. Limits

- The leaderboard API caps a page at 200 rows, so ranks 201–5914 are not visible; our own rank comes from
  the competition endpoint, not from the page.
- Advertised scores are self-reported (§3) and are used for triage only.
- The pool enumeration is by `dateRun` and `dateCreated` over 40 pages each; a kernel that is public but
  never run and never listed under either sort would be missed.
- `georgymamarin`'s measurement is **his** five kernels, not ours; the sd is transferred as a family-level
  order of magnitude, not as our own line's variance. Two of his five kernels have only 2 reruns each.
- Kernel sources are pulled at their *latest* version; the diffs above therefore describe the current code,
  which is exactly the point of §3.

## 11. Next

`q46_submission_asset_inventory` is next by priority. **`q44_frontier_private_risk_stress` is still
unfinished** — its runner turn ended on an API-529 before any work was done, and its queue row is marked
`blocked` with that infrastructure detail rather than an evidence-based outcome; §1 and §4 of this report
feed it directly (board density, and a measured floor for the "public 3-well draw representative or not"
axis). `q57_dip_state_augmented_dp` is appended at priority 628. `q29_final_slot_candidate_packager`
reactivates **2026-08-03**; the final selection action is due by **2026-08-04** and costs no quota.
