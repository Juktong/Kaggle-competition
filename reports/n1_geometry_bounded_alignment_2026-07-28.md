# N1 — geometry-bounded monotonic alignment, 2026-07-28

Autopilot task `n1_geometry_bounded_alignment` (`requires_gpu=false`, `can_submit=false`,
`max_submit_cost=0`). Script: `scripts/n1_geometry_bounded_alignment.py`. Logs:
`reports/logs/n1_{geometry_bounded,geometry_bounded_lowlam,nested}_2026-07-28.log`.

**Result: negative. The band is not inert — it binds 83–91% of transitions — but it does not improve the
alignment DP.** A large apparent gain on 12 wells did not survive expansion to 40, and under nested
hyper-parameter selection the whole DP family fails to beat the flat anchor. That last point also
qualifies a number recorded in G3.2 earlier today.

## 1. The constraint, and why it is not a hyper-parameter

TVT is a stratigraphic thickness, so along a known path `dTVT = -dZ + tan(δ)·dH`, with `dZ` and `dH`
known exactly from X/Y/Z at test time. Between consecutive evaluated rows this gives a hard admissible
interval on the state change:

```
t - s  ∈  [ (-dZ - tan(δmax)·dH)/STEP ,  (-dZ + tan(δmax)·dH)/STEP ]
```

Two separable things follow, and the run separates them rather than lumping them:

- **Centring.** G3.2's regulariser `lam·|t − s|` pulls toward *no TVT change*. That prior is
  geometrically wrong whenever the well changes TVD — if the wellbore climbs or drops, TVT must change.
  The geometric centre is `c = −dZ/STEP`, so `lam·|t − s − c|` penalises **dip** rather than TVT movement.
- **Bounding.** The hard interval, which forbids implausible dip.

Arms: `unbounded` (exact G3.2 transition rule, the control), `centred` (centring only), and
`bounded(δmax)` (centring + hard bound). The emission matrix `C[row, state]` does not depend on the
band, so it is computed once per well and reused by every arm — the arms differ **only** in the
transition rule, and the penalty scale is identical in all of them.

### Calibrating δmax against measured local dip

Local apparent dip over the DP's 10-row step, measured on train truth (80 wells, 51,514 transitions):

```
|dip| p50 1.97°   p90 3.59°   p95 5.43°   p99 27.05°   max 78.90°
frac |dip| ≤ 1° = 0.129   ≤ 2° = 0.501   ≤ 4° = 0.921   ≤ 8° = 0.964
```

So a 4° band admits 92% of true transitions and 8° admits 96%, with a heavy tail beyond. `new_direction_search`
M4's ±3.7° figure was the *whole-well* dip; the *local* distribution is what the DP transition needs, and
it is wider.

## 2. Two harness defects the smoke caught first

The first smoke reported the band binding on **0.0%** of transitions, which is impossible for a ±0.35 ft
interval. Two defects, both fixed before any result was read:

1. **The penalty was normalised by band width** (`lam·|Δ|/width`). A narrow band therefore made the
   regulariser up to 60× steeper — the bounded arms were not a one-factor change but a band *plus* a large
   regularisation change. Fixed to divide by `BAND` in every arm.
2. **The binding metric compared against an already-penalised optimum**, which the steep penalty had
   already pulled inside the band. Fixed to ask the meaningful question: does the bound exclude the state
   the **emission alone** would pick?

After the fix the band binds 83–97%, as the geometry implies.

## 3. What the sweep showed — and why it is not the answer

Control check: the flat-anchor baseline on the 12-well eval set reproduces G3.2's recorded **13.103**
exactly, confirming the same eval wells. The scorer retrains to AUC **0.7096** (G3.2 recorded 0.7242;
the original left its pair-sampling RNG unseeded, so the model is not bit-reproducible — the internal
arm-to-arm comparison is the valid one, and the G3.2 numbers are an external reference).

**12 eval wells, low λ** — this looked like a large win:

```
arm                lam=2     lam=5    lam=10    lam=20      best
unbounded         20.782    13.083    14.089    15.152    13.083
centred           21.348    13.629    11.433    12.074    11.433
bounded  4°       11.831    11.353    11.090    12.005    11.090
bounded  8°        9.412    10.562    10.251    12.540     9.412   <- 25% below G3.2's 12.527
bounded 16°       10.446    12.281    11.348    12.039    10.446
flat-anchor 13.103
```

**40 eval wells (a strict superset of the 12), same sweep** — it does not survive:

```
arm                lam=1     lam=2     lam=5    lam=10    lam=20      best   band binding
unbounded         42.359    24.695    16.072    13.003    12.518    12.518          0.0%
centred           43.089    23.532    17.751    15.636    17.502    15.636          0.0%
bounded  4°       14.864    14.542    14.096    15.334    19.566    14.096         91.4%
bounded  8°       15.836    15.569    14.718    15.376    19.484    14.718         88.5%
bounded 16°       22.016    20.757    16.740    15.989    17.535    15.989         83.0%
flat-anchor 12.722
```

`bounded 8°` at lam=2 goes from **9.412** on 12 wells to **15.569** on 40. The best arm on 40 wells is the
**unbounded control**, and every geometry-aware arm is worse. The 9.412 was a minimum selected over 20
configurations on a 12-well sample — the project's recorded failure mode (*a parameter sweep is not a
validation*), and the reason the sweep was not accepted as the result.

## 4. Nested validation — the deciding test

Configuration chosen on one half of the eval wells, scored on the disjoint other half, both ways:

```
select on 20 wells -> unbounded lam=10  |  held-out 20 wells: DP 13.097  flat 13.540
select on 20 wells -> unbounded lam=20  |  held-out 20 wells: DP 14.170  flat 11.847
POOLED HELD-OUT: DP 13.644   flat-anchor 12.722   -> does NOT beat flat
per-well: DP beats flat on 37.5% of held-out wells (n=40)
```

Nested selection never picks a geometry-aware arm, and the resulting DP **does not beat the flat anchor**.

### This qualifies a G3.2 number recorded earlier today

G3.2 reported "its DP beats the flat anchor, 12.527 vs 13.103, interior optimum at lam=60". That
comparison selected λ on the same 12 wells it reported. On 40 wells with the λ choice nested, the DP
lands at **13.644 vs a flat anchor of 12.722** — it does not beat flat. The G3.2 result should therefore
be read as *the learned scorer carries real signal* (AUC 0.7242 vs NCC 0.5010 — that part is a clean
held-out pair comparison and stands), but **not** as *the DP beats the flat anchor*. The
`reports/g32_learned_alignment_smoke_2026-07-28.md` claim is amended accordingly.

## 5. The one thing the band does buy

At weak regularisation the unbounded DP diverges — 42.359 at lam=1, 24.695 at lam=2 — because nothing
stops the path drifting. The bounded arms stay in the 14–16 range across the whole λ grid. **The
geometric bound delivers stability, not accuracy**: it removes the catastrophic tail without moving the
optimum, and the optimum it protects is worse than the tuned unbounded arm. Recorded because a future
formulation that needs a weak regulariser for other reasons can rely on the bound to stay physical.

## 6. Verdict

- The band is **binding** (83–91% of transitions), so the constraint is active, not inert.
- It does **not** improve the DP: on 40 wells every geometry-aware arm is worse than the unbounded
  control, and nested selection never chooses one.
- The DP family as a whole does not beat the flat anchor under nested selection (13.644 vs 12.722,
  beating flat on 37.5% of wells), so it remains far from the deployed honest line (~8.86).
- Task step 5 ("do not scale up unless the band produces a clear improvement over 12.527") is not met.
  **No scale-up, no submission.** Quota untouched at 0/5.

Still open in the alignment line: the learned scorer's held-out pair AUC of 0.7242 vs NCC 0.5010 is a
genuine signal that no DP formulation tried so far has converted into a trajectory better than a flat
anchor. The gap is in the *transition model*, and neither a soft distance penalty (G3.1, G3.2) nor a hard
geometric bound (this round) closes it.
