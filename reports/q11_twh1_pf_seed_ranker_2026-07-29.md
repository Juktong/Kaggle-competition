# Q11 — TWH=1 PF seed / path ranker, 2026-07-29

Autopilot task `q11_twh1_pf_seed_ranker` (`requires_gpu=false`, `can_submit=true`, `max_submit_cost=1`).
Script: `scripts/q11_twh1_path_ranker.py`. Log: `reports/logs/q11_path_ranker_2026-07-29.log`.

**Result: every ranker arm is worse than simply using the PF mean path. No positive nested evidence, so
no Kaggle smoke and no submission.** Quota untouched at **0/5**. This is the sixth independent instance of
the project's large-oracle / no-achievable-margin pattern — and the first where the achievable margin is
not merely small but reliably **negative**.

## 1. Stored artifacts reused — no path regeneration needed

`rogii_sprint_shared/tmp/topk96_paths/` holds **773 wells × 96 PF candidate paths** with truth, the PF
mean path, and a 74,208-row feature table (`topk96_feat.csv`). Everything Q11 needs already exists.

Efficiency: the scorer emission `C[row, state]` is computed **once per well over all states**, then each of
the 96 paths simply indexes into it — so scoring 96 paths costs no more than scoring one.

## 2. The headroom is large, and the oracle even beats deployed

Pooled row-weighted RMSE on toe rows, all 760 wells with stored paths:

```
PF mean path (the default)   10.9905
median path of the 96        12.4375
ORACLE best-of-96             7.1579     <- better than deployed honest
worst-of-96                  22.1407
DWT base                     10.2891
deployed honest 54844628      8.8626

ORACLE headroom vs PF mean   +3.8326        worst-case risk  -11.1502
wells where the PF mean already beats the best single path: 2.4%
spread among the 96 (worst - best): median 7.6925
```

So a perfect selector would beat the deployed honest line by 1.70. That is the appeal — and the trap: the
oracle is **truth-selected**, and the downside of a wrong pick is −11.15 against an upside of +3.83.

## 3. The one-factor question

The ledger records a prior top-K ranker over these same paths reaching **+0.1492** pooled — 3.9% of the
oracle headroom — and failing the gate (5th percentile negative, 45.7% of wells hurt, no guard
constructible). Its 14-feature set (`loglik, w, lik_rank, smooth, jumps, total_move, dir_changes, seam,
out_of_range, d_dwt, d_struct, d_mean, n_eval, heel_drift`) contained **no alignment-to-typewell score at
all**. Q11 adds exactly that: ten TWH=1 alignment summaries per path — mean/p10/p25/p75/std/worst of the
learned score along the path, prefix gap, smoothness, range pressure, and deviation from the mean path.

## 4. Result — 40 held-out wells, splits by well

```
eval-well references:  PF mean 7.6571 | ORACLE best 4.5414 | worst 16.3061

feature set          pooled   vs PF mean   headroom used   wells helped
prior (14)           8.0556      -0.3985          -12.8%          45.0%
TWH1 (10)            8.2175      -0.5604          -18.0%          32.5%
both  (24)           7.8468      -0.1897           -6.1%          40.0%
```

**Every arm is worse than the PF mean default.** The TWH=1 features alone are the *worst* arm. Adding them
to the prior set improves on prior-alone (−0.19 vs −0.40) but does not reach zero, let alone positive.

Best arm (`both`) against the PF mean default:

```
per-well gain: mean -0.3943  median -0.0714  std 3.2860 | helped 40.0%  hurt 60.0%
3-WELL bootstrap of the mean gain: 5th -3.1085  50th -0.2723  95th +4.8850   P(gain>0) 0.2696
```

### The smoke inverted at scale — worth recording

On an 8-well smoke the `prior` arm appeared to convert **73.5%** of the oracle headroom. At 40 wells the
same arm converts **−12.8%**. The smoke's pooled figure was driven by one or two large wins while its own
per-well statistics already showed the truth (median gain −0.20, 62.5% of wells hurt, 3-well P(gain>0)
0.48). This is the same failure mode N1 recorded when a 12-well eval manufactured a 25% gain that vanished
at 40 wells, and it is why the standing rule requires ≥40 wells.

## 5. Why selection loses where averaging wins

The mechanism is the project's own rule #1: *averaging and shrinkage transfer; hard selection and fitted
weights do not.*

The PF mean path **is** the averaging. It pools 96 proposals whose spread is median 7.69 ft, and that
pooling is what makes it robust. A ranker replaces that average with a single bet on one path. With a
downside of −11.15 against an upside of +3.83 and a selector that is far from oracle-accurate, the
expected value of the bet is negative — which is precisely what the measurement shows.

This also explains why adding a *better* signal did not rescue it. The problem is not the quality of the
score used to rank; it is that ranking discards the variance reduction that the mean path provides. A
better score improves the ranking slightly (`both` beats `prior` by 0.21) without changing the sign.

## 6. Verdict

- **No positive nested evidence.** Task step 5's condition is not met, so step 6 (Kaggle smoke/full/submit)
  never triggers. No submission; quota untouched at 0/5.
- **Direction closed**: ranking or selecting among PF candidate paths, with or without alignment features.
  Together with G3.1/G3.2/N1/Q10 (generate a path from a pointwise emission) this closes both distinct
  shapes in the PF-path line — generation *and* selection.
- **Banked measurement:** the oracle best-of-96 is **7.1579**, better than the deployed honest 8.8626. The
  information genuinely exists inside the PF path set; no test-available selector has been able to reach
  it, and the two attempts so far (prior +0.1492 pooled over 760 wells; Q11 −0.19 over 40 held-out wells)
  both fail. If a future line wants this headroom, the lever is not a better ranker but a better *combiner*
  — a weighting over paths rather than a choice among them, since weighting preserves the averaging.
- Slot recommendation unchanged: `54922806` + `54844628` under all three criteria.
