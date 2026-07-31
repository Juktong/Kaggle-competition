# ROGII — top-K path ranker follow-up (direction D, 2026-07-20)

Session `e5b89aa5`. Convert the previously-quantified oracle gap into a *deployable* path selector, measured
against the current honest slot **54844628** (DWT+PF + gated structural field, honest OOF 8.8626, public
7.891). Scripts: `scripts/pf_topk_path_dump.py`, `scripts/topk_path_ranker.py`. Neutral technical language.

## D1 — PF re-run retaining all K paths
The shipped PF keeps only the likelihood-weighted mean. The dump retains every seed path plus, per path,
features that are **all test-available at inference**: `loglik, softmax weight, lik_rank, smooth (std of 2nd
diff), jumps, total_move, dir_changes, seam (anchor consistency), out_of_range (typewell pressure), d_dwt,
d_struct, d_mean, n_eval, heel_drift`. `path_rmse` is stored only as the ranker's training target and is
never an input. Checkpointed / resumable / detached.

**Performance root-cause + fix (worth recording):** the worker closed over the 3.78 M-entry `dwt`/`sidx`
dicts, so joblib pickled them to each worker every batch → **30 s/well**. Pre-slicing per-well reference
arrays removed the pickling: **12 wells NS=8 in 0.3 min (~35× faster)**, 0 errors.

## D2 — tiny smoke (6 wells, NS=8) PASS
Oracle headroom per well (weighted-mean → best seed): +3.81, +4.11, +2.96, +0.82, +0.61, +0.15.
Feature → `path_rmse` correlations: **loglik −0.425 · smooth +0.413 · d_struct +0.283 · jumps +0.281 ·
d_dwt +0.229**. Note `d_struct` (agreement with the structural field) is a ranking feature the earlier
oracle-gap test did not have.

## D3/D4 — nested ranker vs the deployed pipeline (GroupKFold by well, 5 folds)
Every row evaluates the **full deployed pipeline** (`0.5·DWT + 0.5·PF_selected`, then gated structural field
at W=0.15), i.e. exactly what a submission would ship, differing only in how the PF component is formed.

| wells | deployed (PF w-mean) | max-lik pick | ORACLE | ranker hard-pick | **best shrinkage** |
|---|---|---|---|---|---|
| 128 | 10.2781 | 10.1998 | 9.6218 | ridge 10.2907 / lgbm 10.3437 | (not yet tested) |
| 256 | 9.3483 | 9.4176 | 8.3671 | ridge 9.3495 / lgbm 9.3954 | **9.3100 (lgbm λ=0.5, +0.038)** |
| 384 | 9.0461 | 9.1969 | 7.9431 | **ridge 9.0153 (+0.031)** / lgbm 9.0846 | **8.9927 (ridge λ=0.5, +0.053)** |

## Findings
1. **Hard max-likelihood selection is consistently worse than averaging** (9.4176 vs 9.3483; 9.1969 vs
   9.0461), reproducing the earlier 15-well result at much larger scale. Likelihood alone is not a usable
   ranking signal.
2. **The key mechanism is shrinkage, not selection.** The likelihood-weighted mean *is* a variance-reduction
   estimator; substituting a single path discards it. Blending the ranker's pick back toward the mean
   (λ ≈ 0.5) turns a losing hard pick into a positive gain at every size tested.
3. **The gain scales with training data**: best shrinkage gain 128 → losing, 256 → **+0.038**, 384 → **+0.053**;
   at 384 wells even the ridge hard-pick edges ahead (+0.031). The ranker is data-limited, not signal-free —
   the opposite of the PF-uncertainty router (direction B), whose correlation flipped sign with more data.
4. **Oracle headroom stays large and unclaimed** (−0.66 → −1.10 as wells accumulate); the deployable share
   captured so far is roughly 5 % of it.

## FULL VERDICT — 773 wells / 18,552 paths (artifacts verified complete: 773×24 rows, 0 errors, 773 path files)
```
deployed (PF weighted mean)  = 8.8682   <- incumbent 54844628 pipeline
max-likelihood path pick     = 8.9978   (worse, as at every scale)
ORACLE best path             = 7.6871   (headroom -1.18, ~92% unclaimed)
ranker[ridge] hard-pick      = 8.8301   (+0.0380)
ranker[ridge] shrink 0.75    = 8.8185   (+0.0496)
ranker[lgbm]  hard-pick      = 8.8312   (+0.0369)
ranker[lgbm]  shrink 0.75    = 8.7839   (+0.0843)
ranker[lgbm]  shrink 0.50    = 8.7742   (+0.0939)  <- BEST
ranker[lgbm]  shrink 0.25    = 8.8024   (+0.0657)
bootstrap (200 well-resamples): mean +0.0920 · 5th pct +0.0073 · frac>0 = 96%
```
**Scaling held exactly as predicted:** best shrinkage gain 128 wells (losing) → 256 **+0.038** → 384
**+0.053** → 773 **+0.0939**. The mechanism is confirmed at full scale: hard max-likelihood selection is
worse than averaging, hard ranker selection recovers only +0.037, and **shrinking the ranker pick toward the
weighted mean (λ=0.5) roughly doubles that**.

**Decision vs the pre-registered threshold (≥ +0.10 with a stably positive bootstrap): DOES NOT MEET.**
- gain **+0.0939**, i.e. 94 % of the threshold — close, but below it;
- bootstrap **5th pct +0.0073** with 4 % of resamples negative — this is *not* a stably positive lower bound
  (contrast the structural field: 5th pct +0.2356, 100 % positive).
The threshold was registered in advance precisely so a near-miss is not re-argued after the fact.
**No submission from D.** The incumbent 54844628 (public 7.891 / OOF 8.8626) stands.

### What would move D over the line (recorded for the next round)
1. **More seeds per well (K = 48 instead of 24).** Every scale increase so far raised the gain, and more
   paths give both a better oracle pool and more ranking evidence. Cost ≈ one more PF dump (~2 h detached).
2. A richer ranker target (pairwise/listwise rather than normalised RMSE regression).
3. Re-check the bootstrap lower bound: the gate should require 5th pct comfortably > 0, not merely > 0.

## Gate status (superseded by the FULL VERDICT above)
The best measured gain (**+0.053** at 384 wells) is above the ~0.02 transfer-noise threshold used in this
project but remains an **order of magnitude below the structural field's +0.436**, while the inference build
is materially heavier: the notebook would have to retain K PF paths, recompute all path features at test
time (including `d_struct`, which requires the structural field to be computed first), ship a trained ranker,
and apply shrinkage. **No submission from D this round.**

**Full 773-well dump is still running** (detached, checkpointed). To finish the direction:
```
tail -1 /home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/topk.log     # progress
python3 /home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/topk_ranker.py   # full-scale verdict
```
Decision rule for next round: if the full-scale shrinkage gain reaches **≥ +0.10** with a stably positive
well-bootstrap, the inference build is justified; below that, D is recorded as a quantified partial-positive
and the effort is better spent on a channel with a larger effect size.
