# Q54 — hard path constraints: the DP is over-damped, not under-constrained

Date: 2026-07-29 19:25 UTC
Task: `q54_dp_hard_path_constraints` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q54_dp_corridor.py` · Log: `reports/logs/q54_corridor_2026-07-30.log`
Outcome: **gate FAILS on all three conditions. No submission. Quota 0/5.**

## 1. Scope correction, made before running anything

The task asked for "Sakoe-Chiba corridor **+ Itakura slope limits**". **The slope-limit half is already
closed by N1**, and with a strictly better constraint than the generic Itakura cap I would have written.
N1 derived the admissible **per-step** interval from well geometry —

```
t − s  ∈  [ (−dZ − tan(δmax)·dH)/STEP ,  (−dZ + tan(δmax)·dH)/STEP ]
```

— and tested `unbounded` / `centred` / `bounded(δmax)` at 4°/8°/16° under nested selection. Verdict:
negative. The band binds 83–97% of transitions, so it is not inert, but it does not improve the DP.
Re-running a generic per-step cap would be a weaker repeat, so it was not done.

**What was genuinely untested is the CUMULATIVE corridor.** N1's bound is per-step; Sakoe-Chiba's is
global. That distinction is exactly Q40's mechanism — ~477 steps each permitted a fractional move still
permit unbounded *total* drift, so a per-step allowance does not bound accumulation. This round tests only:

```
admissible states at step j:   |state_j − anchor| ≤ C      (hard mask, not a penalty)
```

## 2. Two controls, both from prior mistakes

**Degeneracy control** — `C = ∞` must reproduce the unconstrained `run_dp` exactly:

```
lam 5    max|corridor(inf) − run_dp| = 0.0000000000
lam 20   ... = 0.0000000000     lam 60 ... = 0.0000000000     lam 150 ... = 0.0000000000
```

**Binding diagnostic** — N1's first smoke reported its band binding on 0.0% of transitions, which was an
artefact of asking the wrong question and cost a debugging round. Measured directly here:

```
C=2 → 21.9%    C=3 → 14.7%    C=5 → 5.3%    C=10 → 1.4%    C=20 → 0.4%    C=inf → 0.0%
```

The first smoke of this task did exactly what N1's did: at `C=40` the corridor bound **0.0%** and changed
nothing. Rather than report that as "no effect", the cause was measured — see §3 — and the grid was
re-chosen so the constraint actually bites.

## 3. The headline — the DP does not wander too far, it wanders far too little

Deviation of the **unconstrained DP path** from the anchor, against the deviation the **truth** actually
requires (12 wells, grid units ≈ ft):

```
lam          median        p90        max     TRUTH max
5              11.0       14.0       15.0        19.4
20              2.5        3.0        4.0        19.4
60              2.5        3.0        3.0        19.4
150             2.0        2.5        2.5        19.4
```

**At the optimal λ=60 the DP moves ±3.0 ft from the anchor while the truth moves ±19.4 ft.** The DP is
**over-damped**, not under-constrained. A corridor can only restrict movement further, so it cannot
address the actual failure — and any corridor tight enough to bind at λ=60 (C < 3) would exclude the truth
outright.

This also explains Q10's headline directly: the DP scores 12.170 against the flat anchor's 12.722 because
**its path is nearly the flat anchor**, with ±3 ft of wiggle.

## 4. Result — corridor and penalty are substitutes, not complements

```
lam     C=2      C=3      C=5     C=10     C=20    C=inf
5     12.972   12.887   13.048   13.164   13.325   16.009      <- corridor rescues +3.12 here
20    12.982   12.950   12.664   12.612   13.139   13.169
60    12.992   12.970   12.321   12.138   12.170   12.170      <- best overall 12.138 (+0.032)
150   13.025   12.991   12.501   12.478   12.478   12.478
```

The λ=5 row is the informative one: a hard corridor **rescues a badly-tuned low-λ DP by +3.12**
(16.009 → 12.887), landing it right at the level λ alone achieves. So the corridor genuinely does the same
job as the penalty.

**But it does not do it better.** Best with corridor+λ = **12.138**; best with λ alone = **12.170**. The
two devices are **substitutes**: both suppress movement, and they reach the same place.

That is a direct answer to Q43's premise. The hypothesis was that a hard cap would do something a soft
penalty structurally cannot — bound accumulation regardless of path length. Measured, they converge to the
same optimum, because in this problem the binding issue is not accumulation.

## 5. Gate

```
NESTED (picks [(60, C=10), (150, C=10)])
  selected 12.570  vs unconstrained 12.601  gain +0.031
  helps 2.5% of held-out wells
  3-WELL bootstrap 5th -0.518  50th +0.000  95th +1.528  P(>0) 0.0724
```

| condition | required | observed | verdict |
|---|---|---|---|
| nested gain | > 0 | **+0.031** | PASS (negligibly) |
| helps a majority of wells | > 50% | **2.5%** | **FAIL** |
| 3-well bootstrap 5th | > 0 | **−0.518** | **FAIL** |

**2.5% is the lowest win rate anything has produced in this project**, and it is consistent: at λ=60 the
selected C=10 binds only 1.4% of steps, so on ~97% of wells the corridor changes nothing at all.

## 6. What this closes, and what it implies for the queued follow-ups

**Closes:** hard global path constraints on the alignment DP. Together with N1 (geometric per-step bound,
negative) and Q40 (45 soft penalty arms, none better than the deployed L1), **the transition model is now
closed across soft penalties, per-step hard bounds, and global hard corridors.**

**A prediction for `q55_dp_decoder_averaging`, recorded now rather than after the fact:** if the DP's paths
already sit within ±3 ft of the anchor, averaging over near-optimal paths will average near-identical
near-flat trajectories and should move very little. That is a prediction, not a closure — beam averaging
could still matter if the K=6 beam spans genuinely different hypotheses rather than ±1-unit variations,
and q55 should measure the beam's spread first and report it before anything else.

**`q56_pf_backward_smoothing` is unaffected.** It targets the PF, a different component that enters the
honest blend directly, and the over-damping diagnosed here is a property of the DP alignment line.

**The deeper box:** Q17 showed emission AUC is decoupled from DP quality (+0.056 AUC bought 0.167 RMSE),
and Q54 now shows the transition side is at its optimum in three separate families. The alignment line is
constrained from both sides, and neither lever moves it toward the deployed honest line's 8.8626.

## 7. Limits

- One emission (TWH=1) and one scorer seed; the deviation diagnostic is on 12 wells, the main grid on 40.
- The corridor is centred on the **anchor**. A corridor centred on a geometric prediction (N1's `centred`
  arm applied globally rather than per-step) was not tested — though N1 found centring alone negative.
- `C` is a constant per well. A well-specific corridor scaled by a test-available quantity was not tested;
  it would be the hard-selection class the ledger has closed.
- Beam K=6 and BAND=60 remain inherited from Q10 and unvaried.

## 8. Next

`q55_dp_decoder_averaging`. `q29_final_slot_candidate_packager` reactivates **2026-08-03**; the final
selection action is due by **2026-08-04** and costs no quota.
