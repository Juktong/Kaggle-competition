# Q21 — soft combiners over the 96 PF paths: the deployed ensemble is already at the optimum

Date: 2026-07-29
Task: `q21_pf_path_soft_combiner` (`requires_gpu=false`, `can_submit=true`, `max_submit_cost=1`)
Script: `scripts/q21_pf_path_soft_combiner.py`
Log: `reports/logs/q21_soft_combiner_2026-07-29.log`
Outcome: **CLOSED — the gate fails on all three conditions. No Kaggle smoke, no submission. Quota
untouched at 0/5.**

## 1. A structural discovery that reframes the task

The stored per-well artifacts contain `paths` (96 × n), `loglik` (96), and `mean` (n). The task and Q11
both describe `mean` as "the PF mean path". **It is not a mean.**

```
max |paths.mean(0) - stored mean| over wells: 30.02   -> stored `mean` is NOT the uniform mean
softmax_T5   10.9307
pf_mean      10.9307     (difference -0.0000)
topm_96      11.5320     (the actual uniform mean of the 96)
```

`softmax_T5` reproduces the stored `mean` **exactly**, while the true uniform mean is 0.60 worse. So the
stored baseline is the **likelihood-weighted ensemble at scale = 5.0** — i.e. the deployed
`run_pf_lik_ensemble(..., scale=5.0)` that feeds the honest blend.

This makes the task sharper than it was posed. The deployed PF is *already a soft combiner*, and the
temperature sweep is a **nested test of the deployed `scale = 5.0`, a hyper-parameter that had never been
validated**. The family is well-posed because it spans both limits:

> the deployed ensemble is the T = 5 point; the uniform mean is T → ∞; hard selection — which Q11
> closed — is T → 0.

## 2. Result — 773 wells, splits by well

References on these wells (Q11's figures in parentheses, on a slightly different well set):

```
PF ensemble (T=5)  10.9307   (10.9905)
ORACLE best-of-96   7.1259   ( 7.1579)
worst-of-96        22.0396   (22.1407)
deployed honest     8.8626
oracle headroom +3.8048 | tail risk -11.1090
```

Every combiner, pooled:

```
combiner               RMSE   vs deployed T=5   % of oracle headroom
softmax_T10         10.8781           +0.0526                  1.4%   <- the only positive
softmax_T5          10.9307           -0.0000                  0.0%   <- deployed
interp_0.1          10.9363           -0.0056                 -0.1%
softmax_T25         10.9616           -0.0309                 -0.8%
topm_8              11.0703           -0.1396                 -3.7%
topm_16             11.0826           -0.1519                 -4.0%
softmax_T100        11.1552           -0.2245                 -5.9%
topm_4              11.1853           -0.2546                 -6.7%
softmax_T2          11.1957           -0.2650                 -7.0%
topm_2              11.3623           -0.4316                -11.3%
softmax_T1          11.4264           -0.4957                -13.0%
topm_96             11.5320           -0.6013                -15.8%
trim_0.05           11.5819           -0.6512                -17.1%
softmax_T0.5        11.5916           -0.6609                -17.4%
softmax_T0.25       11.6884           -0.7577                -19.9%
topm_1 / interp_1   11.8088           -0.8781                -23.1%
median              12.0408           -1.1101                -29.2%
```

**The deployed T = 5 sits at a near-optimal interior point.** Sharpening is monotonically harmful
(T = 2 → −0.265, T = 1 → −0.496, T = 0.5 → −0.661, T = 0.25 → −0.758) and bottoms out at hard selection
(−0.878). Flattening is also harmful (T = 25 → −0.031, T = 100 → −0.225, uniform mean → −0.601). Robust
combiners are worse still — the per-row median costs −1.11.

Only `softmax_T10` beats it, by **+0.0526 = 1.4%** of the oracle headroom.

## 3. Nested — the gate fails on all three conditions

```
NESTED across all 27 combiners (picks ['interp_0.1', 'softmax_T10'])
  selected 10.9633  vs deployed T=5 10.9307  gain -0.0326  (-0.9% of oracle headroom)
  helps 43.2% of held-out wells
  3-WELL bootstrap: 5th -0.7353  50th -0.0069  95th +0.3942  P(gain>0) 0.4563
```

| gate condition | required | observed | verdict |
|---|---|---|---|
| beat the deployed ensemble, nested | gain > 0 | **−0.0326** | FAIL |
| 3-well bootstrap 5th percentile | > 0 | **−0.7353** | FAIL |
| helps a majority of wells | > 50% | **43.2%** | FAIL |

The two folds disagree (`interp_0.1` vs `softmax_T10`), which is what turns the nominal +0.0526 into a
nested loss: T = 10's edge is smaller than the selection noise between folds.

## 4. What this closes, and one thing it validates

**Closes:** Q11 established that *hard selection* over these 96 paths does not transfer (its top-K ranker
converted 3.9% of headroom and failed the gate). Q21 extends that to the **entire soft-combination
family** — temperature reweighting, top-m averaging, trimming, per-row median, and mean↔best
interpolation. Both limits of the family are worse than the deployed point, so the +3.8048 of oracle
headroom over these paths is **not accessible by reweighting either**. Combined, selection *and*
reweighting are now both closed on this artifact set.

**Validates:** the deployed `scale = 5.0` was a fixed, never-nested hyper-parameter of the honest line.
It is now nested-validated as sitting at the optimum of a 27-member family on 773 wells. That is a
genuine positive result about the current pipeline, even though it produces no new candidate.

## 5. Why no submission regardless of the gate

The whole PF-path line sits at **10.93** against the deployed honest line's **8.8626** — 2.07 worse. Even
the truth-selected oracle (7.1259) is only 1.74 better than deployed. So no member of this family is a
submission candidate at any temperature, and step 5 of the task ("if stable and materially closer to
deployed honest") does not trigger. Per Q33 the next 24 h spends **0 slots unless Q36's gate passes**;
this task does not change that.

**Non-homogeneity** was not computed against the deployed submission, because it is only meaningful for a
candidate that could be submitted, and none here can.

## 6. A methodological note worth carrying

A 20-well smoke (the alphabetically first wells) showed sharpening *helping*: `softmax_T0.5` +0.1310,
`topm_8` +0.2027, `interp_0.5` +0.1594. **Every one of those reversed sign on the full 773 wells.** The
20-well subset was also unrepresentative in level (PF ensemble 7.16 there vs 10.93 overall).

This is the third instance of the same lesson in this project — N1's 12-well set manufactured a gain that
vanished at 40, and Q10's grid sensitivity did likewise. It is a reason to keep treating small-sample
smokes strictly as plumbing checks, never as weak evidence of direction.

## 7. Limits

- The 96 paths are a stored artifact from a specific PF configuration. A different path *generator* is
  not tested here; only the combination over these paths.
- The oracle is truth-selected and is used only as a headroom denominator, never as an achievable target.
- Measured on 773 train wells against toe truth; the 3-well bootstrap is the competition-scale statistic.
- `softmax_T10`'s +0.0526 is a real but small pooled effect. The claim is not that it is exactly zero —
  it is that it does not survive nesting, does not help a majority of wells, and is far inside 3-well
  noise.

## 8. Round status

`q36_gr_sigma_in_blend_oof`'s 760-well run remains **in flight** (284/760 at 78 min; ~2 h remaining). It
is still the gate that decides whether the next 24 h spends 0 slots or 1.

## 9. Next

Collect Q36, then `q30_competition_rules_final_audit`.
