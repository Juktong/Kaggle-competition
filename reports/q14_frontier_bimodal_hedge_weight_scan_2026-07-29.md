# Q14 — frontier bimodal hedge weight scan, 2026-07-29

Autopilot task `q14_frontier_bimodal_hedge_weight_scan` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). Script: `scripts/q14_bimodal_weight_scan.py`. Log:
`reports/logs/q14_weight_scan_2026-07-29.log`. Kernel: `kaggle_kernel_frontier_hedgeoff_full/`.

**Result: the local evidence says the hedge HURTS, and it does so by a mechanism that is easy to state —
it adds +2.0 ft to a well whose predictions were already unbiased.** A hedge-OFF variant passes the audit
and the homogeneity axis, and the full Kaggle run is in flight. **No submission made in this round**
(quota **0/5**); the submit decision waits on the run.

## 1. The hedge is a pure additive shift, so the scan costs nothing

Re-verified from the stored full-run intermediates:

```
final - submission_before_branch_hedge:  4301/14151 rows changed (30.4%), single unique delta = +2.0 ft
  000d7d20  n=3836  changed 0
  00bbac68  n=6014  changed 0
  00e12e8b  n=4301  changed 4301   delta exactly +2.0
```

So `variant(w) = before_hedge + w·2.0` on that one well, and the diff against the submitted `54968060` is
closed-form:

```
rmse(variant(w), 54968060) = |w-1| · 2.0 · sqrt(4301/14151) = |w-1| · 1.1027
```

The static matrix reproduces that exactly, so no GPU was needed to build it:

```
w        vs 54968060   vs 54990075   vs 54844628   max|d|   non-homogeneous
0.00        1.1026        1.1391        2.0066     2.000     YES
0.25        0.8270        1.1906        2.0978     1.500     YES
0.50        0.5513        1.2998        2.2198     1.000     YES
0.75        0.2757        1.4538        2.3677     0.500     no
1.00        0.0000        1.6399        2.5370     0.000     no   <- the submitted 54968060
1.25        0.2757        1.8485        2.7238     0.500     no
1.50        0.5513        2.0729        2.9246     1.000     YES
2.00        1.1026        2.5519        3.3583     2.000     YES
```

Homogeneity (threshold 0.50) is crossed at |w−1| ≥ 0.4534. Trajectory sanity is unchanged at every w —
a constant shift on one well leaves every step statistic identical (`max|step|` 0.069 / 1.000 / 0.073).

## 2. The decisive measurement: the hedge creates bias where there was none

The three test wells are duplicated in train, so their toe truth is available as a local proxy:

```
well          n      w=0 (hedge off)   w=1 (hedge on)
000d7d20   3836              1.6367           1.6367
00bbac68   6014              4.1912           4.1912
00e12e8b   4301              2.1818           2.8288    <- +0.647 worse
POOLED    14151              3.1046           3.2594    <- +0.155 worse

mean residual on the hedged well BEFORE the hedge:  -0.1895 ft
mean residual on the hedged well AFTER  the hedge:  +1.8105 ft
```

**The hedged well's predictions were already essentially unbiased (−0.19 ft). The hedge adds +2.0 ft and
turns that into +1.81 ft of bias.** A shift can only help if it corrects an existing offset; here there
was almost nothing to correct.

Analytic public sensitivity, from `R = 6.643` and a constant 2.0 ft shift on 4301 of 14151 rows:

```
mean residual on hedged rows   ->  hedge-OFF public   delta
        -2.0 ft                          6.363        -0.280
        -1.0 ft                          6.457        -0.186
         0.0 ft                          6.551        -0.092
        +1.0 ft                          6.643         0.000
        +2.0 ft                          6.734        +0.091
```

For the hedge to be *helping* on public, the frontier's public predictions on that well would have to be
systematically ≈2 ft too low. The local proxy says they are 0.19 ft too **high**. If the public residual
is near zero, hedge-OFF lands near **6.55**.

### This overturns the variant-matrix round's HOLD, and the reason matters

The variant-matrix round held this axis on the grounds that the hedge "fires on 1 of 3 wells, so any
public delta sits under the ~0.115 config-variance floor". That reasoning conflated two different
quantities. The ~0.115 floor is **run-to-run GPU nondeterminism**; the hedge is a **deterministic +2.0 ft
shift** whose effect on the pooled score is bounded by ~0.28 and estimated at ~0.09–0.11 in the direction
the proxy indicates. The earlier estimate was directionally right about the magnitude but wrong to treat
the noise floor as an upper bound on a deterministic effect.

**Standing caveat retained:** the train-copy proxy is not a public proxy (its level is 3.10 vs public
6.64, different heel/toe split), and the ledger records over-weighting it once before, on `54878409`. What
makes this case different is that the question is a *level* question on one well, not a ~0.1 rank
comparison between two similar models — and the local per-well effect (+0.647) is above the ~0.5 threshold
at which local has predicted the leaderboard. It is evidence, not proof.

## 3. The candidate, and its preflight

The hedge is implemented as

```
shift = clip(_BH_STRENGTH · (midpoint − weighted_center), −_BH_CAP, +_BH_CAP)
_BH_STRENGTH = 0.60      _BH_CAP = 2.00
```

`00e12e8b`'s shift of exactly 2.0 means it hit the **cap**, so the weight scan maps onto a single
constant. The candidate kernel is a **one-line change**, verified by diff to be the only difference from
the kernel that produced `54968060`:

```
-_BH_CAP = 2.00
+_BH_CAP = 0.00  # Q14 hedge-OFF: cap the PF bimodal branch shift to zero
```

Preflight, all passed before pushing:

- **Patch activation verified by exact arithmetic**: with `CAP = 0.00`, `clip(3.3334, −0, 0) = 0.0`, and
  the guard `abs(shift) >= 0.01` is then False, so the branch records
  `skip_zero_or_missing_rows` and applies nothing. Confirmed against the same arithmetic at CAP = 2.0 /
  1.0 / 0.5, which reproduce shifts of 2.0 / 1.0 / 0.5.
- **Predicted output audited** (`scripts/rotation_candidate_audit.py` on
  `submission_before_branch_hedge.csv`): `HARD: PASS` — 14,151 rows, columns `[id,tvt]`, no duplicate ids,
  all finite, id set and order match. Trajectory spans 15.2 / 39.3 / 22.8 ft, `max|step|` ≤ 1.00.
  **Homogeneity: distinct from all scored references** (rmse 1.103 vs `54968060`) → submit allowed on that
  axis. Local proxy 3.105 vs the deployed run's 3.259.

**Kaggle smoke deliberately skipped, with the reason recorded** as the standing rules require. The base
kernel (`rogii-kaiwalya-overlap-off-full`) has already completed a successful full run producing
`54968060`; the change is a single numeric constant in a late post-processing cell that executes after all
heavy work. Every failure mode a smoke would catch — imports, dataset availability, GPU, output path,
schema — is identical to that successful run, and the one smoke-specific check, patch activation, was
verified by exact arithmetic above and will be confirmed post-run from
`pf_seed_branch_hedge_report.csv` (expected reason `skip_zero_or_missing_rows`, `moved_rows 0`).
**Residual risk:** an unrelated transient failure, which costs GPU time but no quota.

## 4. Status and the submit decision

`joezzzzz/rogii-frontier-hedgeoff-full` version 1 pushed and running. **No submission this round.** The
decision is deferred to the completed run, and the gate it must pass is:

1. `pf_seed_branch_hedge_report.csv` shows the hedge inactive (`moved_rows 0`) — confirms patch activation;
2. output passes `rotation_candidate_audit.py` HARD checks;
3. rmse vs `54968060` ≥ 0.50 (expected ≈ 1.10, modulo config variance);
4. the submit gate's information-value condition — already argued: it decomposes G1.3's joint bound over
   the learned-trajectory blend and the hedge, and if it lands near 6.55 it gives us an **own-account**
   frontier candidate competitive with the teammate's `54922806` (6.563), which is a genuine final-slot
   improvement in provenance at equal or better score.

Note the rerun reintroduces ~0.115 of config variance, so the *measurement* of the hedge's exact
contribution will be confounded at that scale even though the *candidate's* score is exact. The
decomposition of G1.3's bound is therefore approximate, not clean.

Slot recommendation unchanged pending the result: `54922806` + `54844628`.
