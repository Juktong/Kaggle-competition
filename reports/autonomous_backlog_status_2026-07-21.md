# Autonomous backlog status — 2026-07-21

Continuous optimization queue, directions 0–9. Neutral technical language throughout.
Live update: the K=48 top-K dump is still running; its verdict lands in
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
| submissions used this round | **0** |
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
| 1 | D top-K path ranker, K=48 | dump running (112/773 at last check) | — | in progress |
| 2 | residual correction | ridge nested 8.8626; hgb nested 8.9156 | **+0.0000 / −0.053** | negative |
| 3 | group offset / trend | offset −0.5153 · shrunk −0.1366 · trend −0.6255 | **−0.14 … −0.63** | negative |
| 4 | multi-signal router | oracle 7.3763 vs nested 9.4684 | **−0.6057** | negative |
| 5 | CNN/Siamese GR scorer | NCC 0.524 · learned 0.636–0.647, plateaued | GPU not spent | root-caused |
| 6 | sequence / MTP / MDN | nested smoothing +0.0160; GMM k=2 ≫ k=1 | **+0.016** (≤ noise) | negative |
| 7 | five cheap probes (P1–P5) | all negative, best is the incumbent | **−0.065 … −0.886** | negative |

Nothing reached the pre-registered **+0.10** gate, so **no submission was made** — consistent with
quota discipline (direction 8).

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

| # | proposal | rationale | est. cost | risk |
|---|---|---|---|---|
| **L1** | **Heel-residual bias carry** | Directly targets the coherence finding. Truth **is** known on heel rows, so a measurable per-well bias exists there; with a 500–2000-row coherence length it should partly carry into the toe. Untested: `heel_drift` in the current feature set is the dip *rate* (`median\|dTVT/dMD\|`), **not** the model's heel residual. Targets the DWT specifically — PF and struct anchor on the heel by construction. | re-run DWT OOF retaining heel rows, ~2–4 h CPU | medium — the toe may sit beyond the coherence length |
| **L2** | **Seed scaling of the PF weighted mean (K=96)** | Extends the one confirmed mechanism (shrinkage/averaging). Gain already scaled with data: 128 losing → 256 +0.038 → 384 +0.053 → 773 +0.0939. K=48 is the live test of scaling in seeds. | ~4 h if K=48 shows scaling | low — mechanism confirmed, but gains are sub-gate so far |
| **L3** | **Separate conservative path for the 12.7% ungated rows** | Currently these rows get no structural information at all. A weaker, separately-tuned treatment cannot disturb the gated majority, so downside is bounded by construction. | ~2–3 h | low |
| **L4** | **Anisotropic / kriging-style structural kernel** | The deployed IDW is isotropic. A dip-aware anisotropic kernel could track the smooth bias the current field misses. The earlier dip probe was negative but used gradient-only integration, a different formulation. | ~3–6 h | medium — variant sweep suggests a local optimum |
| **L5** | **A third decorrelated forward model** | Both historical wins came from new decorrelated information. Candidates: a resistivity/other-log-driven forward model, or a differently-parameterized particle filter. | 1–2 days | high cost, but the only class with a track record here |
| **L6** | **Multi-seed DWT averaging** | Applies the confirmed variance-reduction mechanism to the DWT component rather than the PF. | moderate | low |

Deprioritized as a class, on this round's evidence: post-hoc residual correction, group calibration,
routing/selection, fitted blend weights, monotone recalibration, and local-window learned scorers.

## 5. Currently running

- **K=48 top-K path dump** — pid 73986, **detached with PPID = 1**, survives disconnection.
  Checkpointed to `topk48_feat.csv` (resumable). ~112/773 wells at last check, ~5.9 wells/min,
  roughly 1.9 h remaining. Verdict → `reports/topk_path_ranker_final_2026-07-21.md`.

A defect was fixed in this run: `pf_topk_path_dump.py` derived `INPUT_DIR` from a **cwd-relative** path,
so resuming from a different working directory silently globbed an empty dataset and exited with
`todo=0` — reporting "DONE" while doing nothing. Now pinned to an absolute path.

## 6. Submission and quota discipline (direction 8)

- **0 submissions used this round.** No candidate reached the +0.10 gate, and none was close enough to
  justify a slot on an exploratory basis.
- The honest slot remains `54844628` (public 7.891). The final-2 recommendation is unchanged.
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
