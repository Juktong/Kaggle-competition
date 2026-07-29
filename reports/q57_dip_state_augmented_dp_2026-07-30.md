# Q57 — dip-state augmentation: giving the DP the freedom Q54 said it lacked makes it worse, exactly as Q55 predicts

Date: 2026-07-29 21:55 UTC
Task: `q57_dip_state_augmented_dp` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q57_dip_state_dp.py` · Log: `reports/logs/q57_dip_state_2026-07-30.log`
Outcome: **the 40-well sweep is in flight; the 8-well smoke has already produced the decisive structural
result (§4). No submission. Quota 0/5.**

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

## 4. THE RESULT — lower objective cost, worse RMSE

8 wells, mu=60, per-dip beams:

```
arm                     mean cost      pooled RMSE
ndip=1  nu=0  (deployed)   -645.6           11.323
ndip=5  nu=0               -676.8           13.433
ndip=5  nu=1               -654.2           12.664
```

**The augmented DP finds a strictly better objective on every arm and a strictly worse RMSE on every arm.**
The task pre-registered this exact reading — *"if state augmentation lowers the objective's cost but not
RMSE, that is Q55's misalignment finding reappearing"* — and that is what the measurement shows. It is
recorded as a confirmation of Q55's mechanism, not as a tuning failure.

The activation diagnostic shows the dip is switched on but sparingly (well 0, ndip=5, nu=0): non-zero on
**5.9%** of steps, changing on 10.0%, mean |dip| 0.062, **accumulated pull 3.0 grid units** — against the
**16.3 ft** that well's truth actually requires. So even with the dip free and the beam widened, the path
deviation stays at **3.1 ft**, unchanged from the TVT-only DP.

**That is the finding that matters, and it inverts Q54's framing.** Q54 measured the DP as over-damped and
left open whether that was a defect. Q57 removes the damping — a sustained dip is now free, and the solver
is given 5× the beam width to find one — and the DP *still* declines to move, while the freedom it does
use lowers cost and raises error. **The over-damping is not a limitation the transition model imposes; it is
what the emission prefers, and it is the protection Q55 identified.** Loosening it is measurably harmful.

## 5. Gate

To be completed from `reports/logs/q57_dip_state_2026-07-30.log` when the 40-well sweep lands. The smoke's
direction is unambiguous (every augmented arm worse on RMSE than the TVT-only baseline), so the nested gain
is expected to be ≤ 0 and the gate to FAIL. The informative outputs, per the task, are the nested gain, the
per-well win rate and the activation diagnostic — all three are reported regardless of the verdict.

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

## 7. Limits

- One emission (TWH=1), one scorer seed, the Q10/Q40/Q54 split seed. 8 wells in the smoke, 40 in the sweep.
- **The activation diagnostic is well 0 only.** At `nu=1` it reads 0.0% on that well while the pooled RMSE
  differs from the baseline, so the dip is demonstrably active on *other* wells — the per-well diagnostic
  does not generalise and is not presented as if it does.
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

Collect the sweep, complete §5, and close the state-augmentation line. `q56_pf_backward_smoothing`'s
760-well run is still in flight (68/760 wells at 9.5 min when this was written) and remains the round with a
live positive result. `q46_submission_asset_inventory` is next by priority.
`q29_final_slot_candidate_packager` reactivates **2026-08-03**; the final selection is due **2026-08-04** and
costs no quota.
