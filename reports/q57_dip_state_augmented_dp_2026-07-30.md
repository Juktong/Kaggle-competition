# Q57 — dip-state augmentation: giving the DP the freedom Q54 said it lacked makes it worse, exactly as Q55 predicts

Date: 2026-07-29 21:55 UTC
Task: `q57_dip_state_augmented_dp` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q57_dip_state_dp.py` · Log: `reports/logs/q57_dip_state_2026-07-30.log`
Outcome: **gate FAILS on all three conditions — nested selection picks the un-augmented baseline in both
folds. No submission. Quota 0/5.**
**Headline: the augmentation cures the over-damping Q54 diagnosed — path deviation 4.9 ft → 21.1 ft against
36.0 ft of truth — and the RMSE gets up to 7.8 ft WORSE. The damping was protection, not a limitation.**

## 1. The model, and why it strictly contains the deployed one

State becomes `(s, d)` — TVT grid index and dip rate — instead of `s` alone:

```
cost((s,d) -> (s',d'))  =  C[j, s']  +  mu * |s' - (s + d')| / BAND  +  nu * |d' - d| / DSC
                                         ^ deviation from the dip PREDICTION   ^ dip-change penalty
```

With the dip grid `{0}` and `nu = 0` this collapses to `C[j,s'] + mu*|s'-s|/BAND`, which **is** `run_dp` with
`lam = mu`. The augmented DP therefore contains the deployed one exactly, and the degeneracy control is an
equality check rather than an approximation:

```
mu 60     max|dip_dp(ndip=1, nu=0) - run_dp| = 0.0000000000
```

**Why this was the right lever to try, from Q54's own measurement.** The deployed transition charges
`lam*|Δs|/BAND` on *every* step, so a sustained dip of 1 grid unit per step over ~477 steps costs
`60*477/60 = 477`. The DP cannot afford to move steadily — which is precisely Q54's finding that at the
optimal λ=60 the DP path deviates ±3.0 ft from the anchor while the truth deviates ±19.4 ft. Under state
augmentation a *constant* dip is free in both terms. If over-damping were the defect Q54's framing implied,
this is the change that should cure it.

## 2. The first smoke was inert — and the cause is arithmetic, not a bug

The activation diagnostic (mandatory, after N1 and Q54 each nearly reported an inert constraint as "no
effect") caught it immediately:

```
ndip / nu / mu      dip!=0   dip chg   mean|dip|  accum pull   path dev  truth dev
1 / 0 / 60            0.0%      0.0%       0.000         0.0        3.1       16.3
5 / 5 / 60            0.0%      0.0%       0.000         0.0        3.1       16.3     <- identical
```

Identical RMSE **and** identical cost to the TVT-only DP: the dip was never selected once. The cause was
priced rather than guessed:

```
to move s -> s+1 in one step (mu=60, BAND=60, emission C is z-scored so its spread is ~±3):
  d'=0 :  C + 60*|(s+1)-(s+0)|/60            = C + 1.00
  d'=1 :  C + 60*|(s+1)-(s+1)|/60 + nu*|1-0| = C + 0.00 + nu
=> a dip is worth choosing for a ONE-STEP move only if nu < 1.00.
   Sustained, switching the dip on costs nu ONCE and saves mu*|d|/BAND on every LATER step —
   ~477 saved for a one-off nu. The payoff is real but DEFERRED.
```

Every `d ≠ 0` candidate carries `+nu` immediately, so with `nu` above the emission spread a globally greedy
top-K beam prunes all of them before the deferred payoff can ever be realised. **The augmentation was not
failing — it was unreachable.**

### The fix, and what it means

`perdip`: keep K beams **per dip value** instead of K overall (and widen the per-beam shortlist to
`K·nD` so the global top-K cannot silently re-impose the pruning). This is not a tuning knob; it is what
makes the arm testable at all.

It also gives the augmented model **more search than the baseline gets** — `K·nD = 30` beams against the
TVT-only DP's 6. That asymmetry favours the augmented arm, which matters for reading §4.

**This is Q55's finding seen from the other side.** There, the beam's greedy suboptimality was *protective*
— the exact optimum scored worse. Here the same greediness *blocks a structurally different model from
being explored at all*. Same property of the same solver, opposite consequences, and neither is visible
from the objective value alone.

## 3. Cost control (task step 3), measured before the sweep

```
ndip 1    1.63 s / 8 wells
ndip 5   35.30 s / 8 wells      (per-dip beams: 5x the beams, each 5x the candidates)
```

Projected to 40 wells: ~176 s per config at ndip=5. The full `3 mu × 4 nu × {5,9}` grid would be ~141 min,
far over the ~40 min budget. Per the task's instruction — *reduce the λ grid, not the well count* — the
sweep runs **all 40 eval wells** at the single λ that Q10/Q54 established as optimal (`mu = 60`), across a
dip-width ladder and `nu ∈ {0, 0.25, 1}`. The dip **width** is the dose dimension that tests the mechanism,
so it is the one kept at resolution.

**One in-flight change, recorded rather than silently made.** The first launch used `ndip ∈ {1, 5, 9}`. Its
`ndip=9` timing block alone ran past 4.5 min on 8 wells, projecting **60+ min** for that arm — and both
this sweep and Q56's 760-well run share a **2-core** box, so that time comes directly out of the round that
has the only live positive result in the rotation. The sweep was stopped (by verified PID, not `pkill -f`)
and relaunched with `ndip ∈ {1, 3, 5}`: `ndip=3` costs ~0.36× the `ndip=5` arm, so the three-point width
ladder survives at roughly a tenth of the cost. What is given up is the widest dose point; what it buys is
~50 min back for Q56. The trade is stated because it is a real reduction in this round's coverage, and the
monotonicity check the ladder exists for is preserved.

## 4. THE RESULT — 40 wells, and it is not what the smoke implied

The baseline arm reproduces Q10's recorded number exactly, which validates the harness before anything is
read from it: `ndip=1, nu=0, mu=60` → **12.170**, the `l1 lam=60` figure Q10/Q40/Q54 all use.

```
ndip / nu        pooled RMSE     mean cost
1 / 0                 12.170        -569.7      <- deployed (= run_dp lam=60); flat anchor 12.722
3 / 0                 14.850        -624.4
3 / 0.25              15.935        -605.7
3 / 1                 17.279        -586.7
5 / 0                 19.929        -633.6
5 / 0.25              18.725        -611.7
5 / 1                 16.569        -594.6
```

**Every augmented arm finds a strictly lower objective cost and a strictly worse RMSE.** The dip-width
ladder is monotone in both directions at nu=0 — cost −569.7 → −624.4 → −633.6 while RMSE 12.170 → 14.850 →
19.929 — so this is a dose-response, not a single unlucky configuration. At `ndip=5` the DP is **worse than
the flat anchor (12.722)**: it would be beaten by predicting no change at all.

The task pre-registered this reading — *"if state augmentation lowers the objective's cost but not RMSE,
that is Q55's misalignment finding reappearing"* — and that is what the measurement shows.

### The activation diagnostic contradicts what the 8-well smoke suggested

```
ndip / nu / mu      dip!=0   dip chg   mean|dip|  accum pull   path dev   truth dev
1 / 0 / 60            0.0%      0.0%       0.000         0.0        4.9        36.0
3 / 0 / 60           42.4%     41.7%       0.424        15.0       16.1        36.0
3 / 0.25 / 60        23.4%     10.7%       0.234        18.0       20.1        36.0
3 / 1 / 60           15.0%      2.8%       0.150         7.0       28.1        36.0
5 / 0 / 60           46.2%     53.9%       0.645        18.0       21.1        36.0
5 / 0.25 / 60        25.6%     11.5%       0.274        18.0       20.1        36.0
5 / 1 / 60           15.0%      2.8%       0.150         7.0       28.1        36.0
```

On the smoke's easier well the dip stayed nearly off (5.9% of steps, path deviation unchanged at 3.1 ft),
and the draft of this report concluded from that "the DP declines the freedom it is given". **On the 40-well
set that is wrong and is corrected here.** The dip is active on **42–46%** of steps, it changes on up to
54%, and the path deviation rises from **4.9 ft to 16.1–21.1 ft** against the **36.0 ft** this well's truth
requires. Q40's accumulated-pull quantity reaches **15–18 grid units** of end-to-end displacement.

**So the augmentation does exactly what Q54's diagnosis asked for.** Q54 measured the DP moving ±3.0 ft
where truth moves ±19.4 and called it over-damped; give it a dip state and it moves 16–21 ft where truth
moves 36 — the over-damping is *cured*, the mobility is in the right ballpark, and **the RMSE gets 2.7 to
7.8 ft worse.**

That is a sharper statement than "the DP declines to move", and it is the round's actual finding:

> **The DP can be made to move the right amount. Moving the right amount in the wrong direction is worse
> than not moving at all.** The damping was never a limitation of the transition model — it was protection
> against an emission that cannot say *which way* to go. Extra mobility does not add information; it
> amplifies the emission's error, which is why the objective improves while the metric degrades.

This closes the loop with Q17 (emission AUC decoupled from DP quality) and Q55 (lower cost, worse RMSE) from
a third direction: all three say the binding constraint is the emission's *directional* content, and every
device that gives the path more freedom to act on that emission makes things worse.

One secondary pattern, recorded because it is consistent: the useful `nu` moves with the dip width. At
`ndip=3` the best arm is `nu=0` (14.850) and the worst is `nu=1` (17.279); at `ndip=5` the ordering reverses
— `nu=1` best (16.569), `nu=0` worst (19.929). More freedom needs more damping, and in every case the best
augmented arm is the one closest to being switched off.

## 5. Gate — FAIL, and by the widest margin the rotation has produced

```
NESTED (splits BY WELL, both directions)
  picks [('ndip=1','mu=60','nu=0'), ('ndip=1','mu=60','nu=0')]
  selected 12.170  vs TVT-only baseline 12.170  gain +0.000
  helps 0.0% of held-out wells | 3-WELL bootstrap 5th +0.000  50th +0.000  95th +0.000  P(>0) 0.0000
GATE -> FAIL
```

| condition | required | observed | verdict |
|---|---|---|---|
| nested gain | > 0 | **+0.000** | **FAIL** |
| helps a majority of wells | > 50% | **0.0%** | **FAIL** |
| 3-well bootstrap 5th | > 0 | **+0.000** | **FAIL** |

The zeros are not a degenerate run: **nested selection picked the un-augmented baseline in both folds**, so
the selected model *is* the baseline and every per-well difference is identically zero. That is the
cleanest possible negative — the augmentation is never chosen on held-out wells at any width or penalty.

## 6. What this closes

With Q57 the alignment DP is closed on **four** sides, not three:

| side | round | verdict |
|---|---|---|
| emission | Q17 | AUC is decoupled from DP quality (+0.056 AUC bought 0.167 RMSE) |
| transition — soft penalties | Q40 | 45 arms, deployed L1 best |
| transition — hard bounds | N1, Q54 | per-step geometric bound and global corridor both negative; corridor and penalty are substitutes |
| decoder | Q55 | beam average inert; exact optimum has lower cost and ~10× worse RMSE |
| **state space** | **Q57** | **augmenting the state lowers cost and raises RMSE; the DP declines the freedom it is given** |

Q55 concluded that the remaining lever was *"redefining the objective so that its optimum is closer to low
RMSE"*, and noted that state augmentation was the one untested direction. Q57 tested the most concrete
instance of it, taken from an independent public architecture, and the objective's optimum moved **further**
from low RMSE. **Redefining the objective in this direction makes the misalignment worse, not better.**

**And it locates the binding constraint.** Because the augmented path demonstrably *can* travel the
distance truth travels (§4), the failure is not one of reach, expressiveness or tuning — it is that the
emission does not carry enough directional information to aim that travel. Any future work on this line has
to raise the emission's directional content; no further transition, decoder or state-space device can help,
because three of them have now each made things worse in the same way. Q17 already measured that a large
AUC gain does not deliver that content, so this is not a small ask.

## 7. Limits

- One emission (TWH=1), one scorer seed, the Q10/Q40/Q54 split seed. 8 wells in the smoke, 40 in the sweep.
- **The activation diagnostic is well 0 of each run only**, and the two runs have different eval sets
  (`MAXW_TRAIN` differs), so their "well 0" is a different well. That is exactly how the smoke misled the
  first draft of §4 — its well kept the dip nearly off, the sweep's well switches it on 42-46% of the time.
  The per-well diagnostic is indicative, not a population statement, and the correction is left visible in
  §4 rather than quietly rewritten.
- The λ grid is reduced to `mu = 60` (§3). A dip effect that only appears at a λ far from the TVT-only
  optimum would be missed; against that, Q54 measured the corridor/penalty trade at four λ values and found
  no interaction that changed the optimum's location.
- The dip grid is unit-spaced in grid units (~1 ft) per DP step and centred on 0; a finer or asymmetric dip
  grid was not tested.
- `DSC = 1.0`, so `nu` is directly on the z-scored emission scale. That is why the `nu` grid is
  `{0, 0.25, 1}` rather than the initial `{0, 5, 20}`, which §2 showed is entirely above the emission
  spread and therefore inert by construction.
- Per-dip beams give the augmented arm **more** search than the baseline (§2). The comparison is therefore
  conservative *against* the conclusion drawn — a fairer, equal-budget comparison would make the augmented
  arm look worse still.

## 8. Next

**The state-augmentation line is closed.** `q56_pf_backward_smoothing`'s 760-well run is still in flight
(158/760 wells at 28.1 min) and remains the only round with a live positive result — note that it acts on
the PF, which enters the deployed honest line, whereas this DP line sits at ~12.2 against that line's
8.8626 and was never submittable. `q46_submission_asset_inventory` is next by priority.
`q29_final_slot_candidate_packager` reactivates **2026-08-03**; the final selection is due **2026-08-04** and
costs no quota.
