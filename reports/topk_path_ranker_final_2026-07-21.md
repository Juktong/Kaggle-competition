# Top-K path ranker — final verdict at K=48 (2026-07-21)

**Direction 1** of the continuous optimization queue. Status: **point estimate clears +0.10, bootstrap
stability condition fails → no submission.** The seed-scaling trend is confirmed, and K=96 has been
launched as the evidence-backed follow-up.

Scripts: `scripts/pf_topk_path_dump.py` (dump), `scripts/topk_ranker_full.py` (verdict),
`scripts/topk48_nested_lam.py` (nested-λ verdict).

## What was run

`state.json` claimed a K=48 rerun was queued; **no artifacts or processes existed**, so K=48 had never
run. It was smoke-tested (192 rows = 4×48, paths shape (48, 6004), 0 errors), then run to completion:
**773/773 wells, 37,104 paths**.

The candidate replaces the PF likelihood-weighted mean inside the deployed pipeline with a
ranker-selected path, optionally shrunk back toward that mean. Everything else — the 0.5/0.5 DWT/PF
split, the 0.15 structural weight, the `nnb ≥ 4 ∧ closest < 1000 ft` gate — is identical to submitted
slot `54844628`, so the comparison isolates the PF component.

Honesty properties (audited): ranker inputs are **only test-available** path features
(`loglik, w, lik_rank, smooth, jumps, total_move, dir_changes, seam, out_of_range, d_dwt, d_struct,
d_mean, n_eval, heel_drift`); `path_rmse` is the training target and **never an input**; path selection
is nested by well via GroupKFold.

## Result

```
deployed pipeline with K=48 PF mean   8.8428     (submitted 54844628 used a 24-seed PF: 8.8626)
  -> seeds-only effect, 24 -> 48, NO ranker            +0.0198

max-likelihood path pick              9.0027
ORACLE best path (upper bound)        7.4726

lam=0.00  8.8428  +0.0000
lam=0.25  8.7595  +0.0833
lam=0.50  8.7152  +0.1276
lam=0.75  8.7103  +0.1325
lam=1.00  8.7451  +0.0977      <- hard pick, worse than shrinkage
```

### The λ-nesting check

Direction 2 rejected an HGB result because λ had been chosen by reading the sweep ("a λ sweep is not a
validation"). The same standard was applied here — λ selected on training-half wells, applied to the
held-out half, 5 seeds:

```
lambda picks across 10 nested folds: [0.75, 0.5, 0.75, 0.75, 0.75, 0.75, 1.0, 0.5, 0.75, 0.5]
NESTED-lambda result = 8.7303
  gain vs deployed(K=48)     +0.1125
  gain vs SUBMITTED 8.8626   +0.1323
```

**This one survives.** λ = 0.75 is picked in 7 of 10 folds and the nested result (+0.1125) is close to
the grid best (+0.1325), so it is a genuine optimum rather than a post-hoc selection artifact. The
distinction matters: it is the same test that killed direction 2's apparent +0.031.

### Bootstrap — the blocking condition

```
bootstrap(400 well-resamples) vs K=48 deployed:
  mean +0.1308   5th pct -0.0230   1st pct -0.0796   frac>0 91%

GATE (+0.10 AND stably positive bootstrap): DOES NOT MEET
```

## Decision: no submission

The pre-registered gate is **+0.10 with a stably positive bootstrap**. The point estimate clears the
first condition (+0.1125 nested, +0.1323 against the submitted slot) but **fails the second**: 9% of
well-resamples show a loss and the 5th percentile is −0.023.

No submission was made. Relaxing a pre-registered gate because the point estimate looks attractive is
the specific failure mode the gate exists to prevent, and the cost of waiting is low — the verified
honest slot `54844628` (public 7.891) is already banked, and the deadline is 2026-08-05.

## Confirmed: shrinkage is the mechanism, and it scales with seeds

Two results reinforce the round's organizing finding that **averaging transfers and hard selection does
not**:

- the **hard pick (λ=1.0) is worse than shrinkage** at every K tested (+0.0977 vs +0.1325);
- the max-likelihood pick (9.0027) is worse than simply taking the weighted mean (8.8428).

And the gain scales with the number of seeds, as the variance-reduction account predicts:

| K | gain vs deployed |
|---|---|
| 24 (773 wells) | +0.0939 |
| **48 (773 wells)** | **+0.1125** (nested λ) |

The ORACLE path (7.4726) remains far above what is achievable — consistent with direction 4, an oracle
number is not evidence of an achievable gain.

## Next step, already running

**K=96 launched** (proposal L2), pid 77156, detached with **PPID = 1**, checkpointing to
`topk96_feat.csv`, `todo=773`. Rationale: the mean gain is rising with K while the bootstrap spread is
roughly constant (5th ≈ mean − 0.154). If K=96 adds the ~+0.02–0.03 the trend implies, the 5th
percentile crosses zero and the gate is met on both conditions rather than one. Expected ~3 h.

A secondary, zero-risk result to keep in view: the **seeds-only effect** (+0.0198 from 24→48 seeds, no
ranker, no new model) is currently at the ~0.02 transfer-noise threshold, but it may become
independently useful if it also grows with K.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
NS=48 MAXW=773 BATCH=16 CKPT=$SH/topk48_feat.csv OUTDIR=$SH/topk48_paths \
  python3 scripts/pf_topk_path_dump.py                       # dump (~90 min, checkpointed)
FEAT=$SH/topk48_feat.csv PATHDIR=$SH/topk48_paths python3 scripts/topk_ranker_full.py
python3 scripts/topk48_nested_lam.py                          # nested-lambda verdict
```
with `SH=/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp`. Logs in `reports/logs/`.
