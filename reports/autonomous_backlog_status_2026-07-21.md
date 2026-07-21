# Autonomous backlog status — 2026-07-21

Continuous optimization queue, directions 0–9. Neutral technical language throughout.
Round complete. One submission made: **`54878409`** (L4 anisotropic structural field) — see
`reports/submission_anisotropic_field_2026-07-21.md`. The top-K line is closed in
`reports/topk_path_ranker_final_2026-07-21.md`.

## 0. True current state (judged from artifacts, not from state files)

`state.json` was stale again this round: it claimed a K=48 rerun was queued, but **no artifacts or
processes existed** — K=48 had never run. State was therefore re-derived from artifacts and logs.

| item | value |
|---|---|
| honest slot (submitted, verified) | **`54844628`**, public **7.891**, OOF **8.8626** |
| composition | `base = 0.5·DWT + 0.5·PF`; gated rows `0.85·base + 0.15·struct` |
| deployment gate | `nnb ≥ 4` AND `closest_mate < 1000 ft`, fixed `W = 0.15` |
| coverage | 87.3% of rows gated; 760 wells / 3,721,471 toe rows |
| component standalone OOF | DWT 10.2891 · PF 11.0563 · struct 26.0024 · base 9.2987 |
| submissions used this round | **1** (`54878409`, L4 anisotropic field) of 5 daily |
| git | clean, all work committed and pushed |

## 1. The organizing result of this round

Direction 6's diagnostic measured the residual's structure along the wellbore:

```
residual autocorrelation:  lag1 +0.9998   lag100 +0.9497   lag500 +0.6365   lag2000 -0.041
```

The remaining error has **essentially no high-frequency component**. It is a smooth, slowly-varying,
**per-well bias** with a coherence length of roughly 500–2000 rows.

This one measurement explains every negative in this round, and reframes them from a list of failures
into a single consistent finding:

- there is **no noise left to average away** → smoothing gains only +0.0160 (direction 6)
- a smooth per-well bias is **not predictable from test-available features** → residual models
  anti-correlate out-of-fold (direction 2)
- the bias is **per-well, not per-group** → group calibration's optimum is exactly zero (direction 3)
- a smooth bias **shifts all candidates together** → near-uniform 38/31/31 oracle mix, so routing has
  nothing identifiable to route on (direction 4)
- **fitted weights degrade a conservatively-shrunk incumbent** → nested LS refit −0.1685 (direction 7)

Two further mechanisms were confirmed, both consistent with prior rounds:

> **Averaging and shrinkage transfer; hard selection and fitted weights do not.**
> Confirmed now in directions D (top-K), 4 (router), 7-P1 (LS weights) and 7-P2 (robust combiners).

> **An oracle number is not evidence of an achievable gain.** Direction 4's oracle said +1.49 while the
> honest nested router lost −0.61.

## 2. Directions run this round, with metrics

| # | direction | headline result | gain vs 8.8626 | verdict |
|---|---|---|---|---|
| 1 | D top-K path ranker, K=48 / K=96 | K=96 nested-λ 8.7134; bootstrap 5th −0.0158, frac>0 92%; no guard constructible | **+0.1264** (gate fails on stability) | no submission |
| **L4** | **anisotropic structural field** | nested (A,W) 8.7020; bootstrap 5th **+0.0490**, frac>0 **99%**; leakage cleared | **+0.1606** | **SUBMITTED `54878409`** |
| 2 | residual correction | ridge nested 8.8626; hgb nested 8.9156 | **+0.0000 / −0.053** | negative |
| 3 | group offset / trend | offset −0.5153 · shrunk −0.1366 · trend −0.6255 | **−0.14 … −0.63** | negative |
| 4 | multi-signal router | oracle 7.3763 vs nested 9.4684 | **−0.6057** | negative |
| 5 | CNN/Siamese GR scorer | NCC 0.524 · learned 0.636–0.647, plateaued | GPU not spent | root-caused |
| 6 | sequence / MTP / MDN | nested smoothing +0.0160; GMM k=2 ≫ k=1 | **+0.016** (≤ noise) | negative |
| 7 | five cheap probes (P1–P5) | all negative, best is the incumbent | **−0.065 … −0.886** | negative |

Of these, only **L4 reached the pre-registered +0.10 gate with a stably positive bootstrap**, and it was
the only candidate submitted. The top-K line reached a +0.1492 point estimate at K=96 but failed the
stability condition at both K=48 and K=96, and was held back — consistent with quota discipline
(direction 8).

### Direction 5 detail — why GPU was deliberately not spent

The previous round's `val_auc 0.657` was uninterpretable because the incumbent NCC cost had never been
measured on the same pairs. It is **0.524 (chance)**. Three structurally different architectures then
converged to 0.636 / 0.636 / 0.647 while training loss kept falling — an information ceiling, not an
architecture problem. My translation-invariance hypothesis was **refuted** (position-preserving pooling
scored identically to average pooling).

Root cause, quantified: a 64-row horizontal MD window spans a **median 0.95 ft** of TVT against the
**32 ft** typewell window it is paired with — a **~34× scale mismatch**, with 71% of windows spanning
under 2 ft. Per-window z-scoring then destroys the one surviving cue (level match AUC 0.578 > shape
match 0.509). The honest repair converges to the PF emission model already deployed. ~90 s of CPU plus
two measurements replaced a multi-hour GPU run.

## 3. Small probes completed (direction 7 requires ≥5)

| probe | result |
|---|---|
| P1 3-way nested LS weight refit | 9.0312 (−0.1685); fitted .378/.415/.206 vs deployed .425/.425/.150 |
| P2 robust combiners (shrink-to-median, closer-to-struct) | −0.148 / −0.593; plain mean best |
| P3 continuous `W(nnb, closest)` vs binary gate | −0.065 … −0.206; binary gate wins |
| P4 isotonic calibration of the final prediction | −0.8855 |
| P5 per-well weighting | 8.9542 (−0.092) |
| (5-a) NCC baseline on identical Siamese pairs | 0.524 — the missing control |
| (5-b) horizontal-vs-typewell window scale audit | 34× mismatch quantified |
| (5-c) level-vs-shape cue decomposition | level 0.578 > shape 0.509 |
| (6-a) residual autocorrelation along MD | +0.9998 → 0 at lag 2000 |
| (6-b) nested-bandwidth smoothing | +0.0160 |
| (6-c) residual mixture structure | GMM k=2 BIC 1,376,501 vs k=1 1,438,494 |

**P1 is worth keeping in view as a positive robustness result:** the deployed hand-set weights beat a
nested least-squares refit, so the submitted slot is not merely untuned — it sits in a
shrinkage-favorable regime that fitting degrades.

## 4. Larger proposals (direction 7 requires ≥5), ranked by evidence

Ranked by fit to the organizing result: the target is the **smooth per-well bias**, and the only two
historical wins (PF forward, structural field) both came from adding **decorrelated information**, not
from re-processing existing predictions.

**Re-ranked after `reports/per_well_bias_structure_2026-07-21.md`**, which located the remaining error:
60.3% of residual variance is a **per-well offset**, dominated by **drift along the toe** (slope std
13.28 ft) rather than an initial level offset (std 4.72 ft). Since truth stops at the heel, that drift is
largely unobservable at test time — which promotes the structural-information proposals and demotes L1.

| # | proposal | rationale | est. cost | risk |
|---|---|---|---|---|
| **L4** ✓ | **Anisotropic / dip-aware structural kernel** — *run this round, MET the gate, SUBMITTED `54878409`* | The prediction held: the dominant error term is per-well **drift**, and a dip-aware kernel attacks drift rather than level. Nested (A,W) gain **+0.1606**, bootstrap 5th **+0.0490**, frac>0 99%. Leakage cleared; kernel bit-exact; visible-well +0.181 matches OOF. | done | shipped |
| **L3** ✗ | **Separate conservative path for the 12.7% ungated rows** — *run this round, negative* | Tested immediately since it needed only existing arrays. On ungated rows the structural field has **RMSE 62.23** against base 12.81, so there is nothing to add: the nested weight fits to **0.0109** (≈ zero) and the nested result is **−0.0218**. A sub-gate at `closest < 2000 ft` gives **+0.0208**, at `< 3000 ft` **+0.0181** — both at or below the ~0.02 transfer-noise threshold and far under the gate. **The deployed gate is correctly placed**; this is a further robustness confirmation of the submitted slot. | done (~2 min) | closed |
| **L5** ↑ | **A third decorrelated forward model** | Both historical wins came from new decorrelated information, and section 1 argues that is now the only class that can reach the dominant error term. Candidates: a resistivity/other-log-driven forward model, or a differently-parameterized particle filter. | 1–2 days | high cost, but the only class with a track record here |
| **L2** = | **Seed scaling of the PF weighted mean (K=96)** | Extends the one confirmed mechanism (shrinkage/averaging). Gain already scaled with data: 128 losing → 256 +0.038 → 384 +0.053 → 773 +0.0939. K=48 is the live test of scaling in seeds. | ~4 h if K=48 shows scaling | low — mechanism confirmed, but gains are sub-gate so far |
| **L6** = | **Multi-seed DWT averaging** | Applies the confirmed variance-reduction mechanism to the DWT component rather than the PF. | moderate | low |
| **L1** ↓ | **Heel-residual bias carry** — *downgraded, do not run as specified* | The mechanism is real and large (within-well carry upper bounds +0.46 … +1.43), but those bounds use toe-row truth. The test-available part is small (a bias from the first 100 rows explains only 5% of whole-well bias variance) and the existing heel anchor already removes it by construction. | would have been 2–4 h | now assessed low-value |

Deprioritized as a class, on this round's evidence: post-hoc residual correction, group calibration,
routing/selection, fitted blend weights, monotone recalibration, and local-window learned scorers.

## 5. Currently running

- **K=48 — COMPLETE** (773/773, 37,104 paths). Verdict in
  `reports/topk_path_ranker_final_2026-07-21.md`: nested-λ **8.7303**, **+0.1125** vs the K=48 deployed
  reference and **+0.1323** vs the submitted slot. λ=0.75 survives nested re-selection (7/10 folds), so
  unlike direction 2 this is not a sweep artifact. **Blocked on bootstrap stability alone** —
  5th pct −0.0230, frac>0 91% — so the pre-registered gate is not met and no submission was made.
  Secondary: the **seeds-only** effect (24→48 seeds, no ranker) is **+0.0198**.
- **K=96 — COMPLETE, and it closes the top-K line.** Nested-λ **8.7134** (+0.1264), but bootstrap 5th
  **−0.0158** (frac>0 92%). The 5th percentile improved only **+0.0072 per doubling of K**, so reaching
  zero would need K≈384+ with diminishing returns. Per-well: helped 54.1% / hurt 45.7%, median +0.011 —
  the pooled gain is a net of two large opposing flows, so well-resampling genuinely flips it. A guard
  is **not constructible**: every test-available guard signal has near-zero correlation with per-well
  gain (best `dmean_min` +0.131). No submission.
- **L4 anisotropic structural field — COMPLETE and SUBMITTED (`54878409`).** See
  `reports/submission_anisotropic_field_2026-07-21.md` and
  `reports/anisotropic_structural_field_2026-07-21.md`. Public score pending at time of writing.

A defect was fixed in this run: `pf_topk_path_dump.py` derived `INPUT_DIR` from a **cwd-relative** path,
so resuming from a different working directory silently globbed an empty dataset and exited with
`todo=0` — reporting "DONE" while doing nothing. Now pinned to an absolute path.

## 6. Submission and quota discipline (direction 8)

- **1 submission used** (`54878409`, L4 anisotropic field), of 5 daily. Every other candidate was held
  back: directions 2/3/4/6/7 were negative, and the top-K line reached a +0.1492 point estimate but
  failed bootstrap stability at both K=48 and K=96.
- `54844628` (public 7.891) remains banked and unaffected. If `54878409` scores better on public and the
  OOF / visible-well agreement holds, it supersedes it for the honest slot; otherwise the existing
  recommendation stands.
- **Submission mechanics:** this competition is kernels-only (`is_kernels_submissions_only = True`), so
  `kaggle competitions submit -f` returns **400 by design**. Use
  `api.competition_submit_code(kernel=..., kernel_version=...)`.
- Per standing instruction, no decisions were made around any teammate/external pending submission.

## 7. Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
python3 scripts/residual_correction.py     # direction 2
python3 scripts/group_and_router.py        # directions 3 + 4
python3 scripts/siamese_v2.py              # direction 5 (MAXW=80 EPOCHS=6 MAXPAIRS=40000)
python3 scripts/seq_headroom.py            # direction 6
python3 scripts/probes_d7.py               # direction 7 probes P1-P5
```
Shared artifacts live in `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/` (stable across sessions
by design — per-session job dirs would orphan checkpoints). Logs under `reports/logs/`.
