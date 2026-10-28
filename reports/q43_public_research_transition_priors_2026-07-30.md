# Q43 — targeted research for transition/path priors

Date: 2026-07-29 18:05 UTC
Task: `q43_public_research_transition_priors` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **12 sources collected, 5 proposals written, 3 appended to the queue. No submission. Quota 0/5.**

## 1. What the search had to clear

Q40 tested 45 transition arms and found the deployed `lam·|Δstate|/BAND` is the best of all of them. But
every arm it tested was a **soft per-step penalty** — L1, L2, Huber, a drift prior, curvature. Q40 also
produced the mechanism that constrains what to look for next:

> a per-step directional term in a path DP is multiplied by the path length; over ~477 DP steps a
> fractional per-step bias compounds into tens of feet.

So the research target is narrow and well-defined: **path/transition devices that are NOT soft per-step
penalties**, because that family is closed and its failure mode is understood. Per step 4, anything that
only improves pointwise emission/AUC is discarded — Q17 already closed that lever and showed emission AUC
is decoupled from DP quality.

Also relevant: the current DP has **no global constraint at all**. `run_dp` uses
`lo, hi = max(0, s−BAND), min(S, s+BAND+1)` — a ±60 window around the *previous* state — so cumulative
deviation from the anchor is unbounded (60 × ~477 steps), and there is no minimum or maximum slope.

## 2. Sources and the one idea each contributes

| # | source | the transferable idea |
|---|---|---|
| 1 | [Constrained DTW (Tavenar, HDR)](https://rtavenar.github.io/hdr/parts/01/dtw/dtw_warping_length.html) | **Sakoe-Chiba band** — a *global* corridor keeping the path near the diagonal, distinct from a per-step window |
| 2 | [DTW: Itakura vs Sakoe-Chiba](https://www.researchgate.net/publication/334764334_Dynamic_Time_Warping_Itakura_vs_Sakoe-Chiba) | Neither dominates; the choice is dataset-dependent — so both are worth an arm, not one |
| 3 | [tslearn DTW user guide](https://tslearn.readthedocs.io/en/stable/user_guide/dtw.html) | The **Itakura parallelogram is not a global constraint** — it *arises from local slope restrictions*: min slope 0.5, max slope 2 |
| 4 | [DTW in stratigraphic pattern alignment (MARUM)](https://paloz.marum.de/dtwBook/dtwGeologyBackground.html) | Itakura slope limits are used in **stratigraphic** alignment specifically — the closest published analogue to our task |
| 5 | [dtw R package: windowing functions](https://rdrr.io/rforge/dtw/man/dtwWindowingFunctions.html) | Windowing is implemented as an **admissibility mask** on the cost matrix — a hard constraint, cheap to add |
| 6 | [Automated seismic-to-well ties (arXiv 1209.0201)](https://arxiv.org/pdf/1209.0201) | A constraint that keeps stretch/squeeze "within reasonable bounds" is what makes automated well-ties usable |
| 7 | [Stochastic DTW for well-log correlation (SPWLA)](https://onepetro.org/SPWLAALS/proceedings-abstract/SPWLA22/5-SPWLA22/D051S023R001/487830) | Treat the correlation as a **distribution over paths**, not one path |
| 8 | [Tropical Viterbi tubes (arXiv 2606.17181)](https://arxiv.org/pdf/2606.17181) | A **pathwise uncertainty set** around the Viterbi optimum: all paths within tolerance of the best score |
| 9 | [Soft-DTW (arXiv 1703.01541)](https://arxiv.org/abs/1703.01541) | Replace the hard `min` in the Bellman recursion with a **soft-min at temperature γ** — a closed-form average over near-optimal paths |
| 10 | [Differentiable DP for structured prediction (Mensch & Blondel)](https://proceedings.mlr.press/v80/mensch18a/mensch18a.pdf) | The same smoothing generalises to any DP max/min operator |
| 11 | [FFBSi / particle smoothing (arXiv 1011.2153)](https://arxiv.org/abs/1011.2153), [smoothing survey (IMA)](https://cdn.ima.org.uk/wp/wp-content/uploads/2015/11/Smoothing-methods-for-particle-filters-in-tracking-applications.pdf) | **Forward-filter backward-simulate**: a backward pass over the particle trellis uses *later* observations to refine *earlier* states |
| 12 | [Snapping GPS tracks to road segments (USPTO 8718932)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8718932) | HMM map-matching sets transition cost from **geometric feasibility** (how far the object could actually have moved), not from a fitted drift |

**Discarded under step 4:** the wavelet+DTW stratigraphic correlation papers improve the *feature/emission*
side without adding a path constraint. Q17 closed that lever and measured AUC as decoupled from DP quality,
so they do not qualify.

## 3. Five proposals

### P1 — Hard global band + Itakura slope limits *(highest value; appended as `q54`)*

Sources 1, 3, 4, 5, 6. The DP currently has **no** cumulative constraint and **no** slope limits. Add them
as an **admissibility mask**, not a penalty:

- cumulative: `|state_j − anchor| ≤ C` for a swept corridor `C`;
- slope: `slope_min ≤ Δstate/Δstep ≤ slope_max` (Itakura's classic 0.5–2, generalised).

**Why this is the right thing to test after Q40:** Q40 showed soft per-step terms *compound* over path
length. A hard cap does the opposite — it bounds accumulated deviation **regardless of path length**. This
is structurally the complement of everything Q40 tested, and it is motivated by Q40's own mechanism rather
than by hope.

### P2 — DP decoder averaging: beam-average and soft-min Bellman *(appended as `q55`)*

Sources 8, 9, 10. Two cheap changes to the *decoder*, leaving emission and transition untouched:

- **beam average** — `run_dp` keeps K=6 beams and returns `beams[0]` only; average the beam weighted by
  `exp(−cost/T)` instead;
- **soft-min recursion** — replace the DP's hard `min` with a soft-min at temperature γ.

**Precedent that this is not idle:** Q21 discovered the deployed PF ensemble *is already* a softmax over
paths at T=5, and that T=5 sits at a nested optimum of a 27-member family. The same operator has never been
applied to the DP. It is also Rule #1's averaging class.

### P3 — Backward smoothing of the PF (FFBSi) *(appended as `q56`; higher cost)*

Source 11. Our PF (`run_particle_filter`) is a **single forward pass**. But **the entire toe GR log is
observable at prediction time** — we predict TVT for rows whose GR we can already see. A forward-only
filter therefore discards genuinely available information, which is a real modelling gap rather than a
tuning knob.

A backward pass re-weights earlier particles using later observations. It is an averaging/smoothing
operation over the existing trellis, not a directional prior, so Q40's compounding warning does not apply.
Cost is higher: the particle trellis must be retained, and the PF enters the honest blend at weight 0.5, so
any gain halves before it reaches the line.

### P4 — Geometric transition scale from survey data *(documented, NOT appended)*

Source 12. Map-matching sets transition cost from how far the object could plausibly have moved. The
analogue: scale the transition term by the well's own MD advance and inclination between consecutive toe
rows, instead of a constant λ.

**Not appended, and the reason matters:** this is uncomfortably close to Q40's `drift` arm, which failed
worst (−11.475). The distinction is that a *scale* is non-directional while a *drift* is directional, so it
should not compound — but that argument is untested, and Q40's measured failure is recent and large. It
should wait behind P1/P2, and if run must report the accumulated-pull diagnostic Q40 introduced.

### P5 — Path-distribution output rather than a single path *(documented, NOT appended)*

Sources 7, 8. Treat the correlation as a distribution over paths and report its mean. Not appended because
it is largely **subsumed by P2** — beam-averaging and soft-min are the cheap, concrete instances of exactly
this idea. Recorded so the general framing is not lost.

## 4. Gates and expected cost

All three appended tasks carry the standing gate — **nested by-well gain > 0 AND helps a majority of wells
AND 3-well bootstrap 5th > 0** — and all are `can_submit=false`.

| task | proposal | expected cost | notes |
|---|---|---|---|
| `q54_dp_hard_path_constraints` | P1 | ~10 min, reuses the Q40 harness | a mask in `run_dp`; corridor and slope swept, nested |
| `q55_dp_decoder_averaging` | P2 | ~10 min, same harness | beam-average + soft-min γ, nested |
| `q56_pf_backward_smoothing` | P3 | hours (trellis retention, 2 cores) | smoke on ≤12 wells first, per Directive 4 |

**A required honesty note carried into all three prompts:** the alignment DP sits at ~12.2 against the
deployed honest line's 8.8626. Passing these research gates would make the transition lever worth
pursuing; it would **not** make the artifact submittable. Q41 additionally showed the 3-well 5th condition
is maximised by changing nothing, so it is expected to fail — the informative output is the nested gain and
the per-well win rate.

## 5. Limits

- Search is US-only web search; several petroleum-specific sources (SPWLA, ScienceDirect) are
  **abstract-only or paywalled** and were used for the method *idea*, not for implementation detail. The
  geosteering-specific HMM search returned no geosteering results at all — the transferable material came
  from map-matching and general HMM/DTW literature instead. Recorded rather than papered over.
- No source was executed or copied; each contributes one idea to be implemented from first principles here.
- The proposals are ranked on *structural distinctness from what Q40 closed*, not on any claimed effect
  size. None carries a predicted gain.

## 6. Next

`q54_dp_hard_path_constraints` (appended, priority 625). `q29_final_slot_candidate_packager` reactivates
**2026-08-03**; the final selection action is due by **2026-08-04** and costs no quota.

Sources: as linked inline in §2.
