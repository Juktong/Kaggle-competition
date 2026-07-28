# N2 — increment-target refinement of the deployed structural field, 2026-07-28

Autopilot task `n2_increment_structural_field` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). Scripts: `scripts/n2_increment_structural_field.py` (builder),
`scripts/n2_eval_increment.py` (evaluation + 3-well gate).

**Result: the direction is closed on evidence, and the task's own premise turned out to be wrong.**
No submission — the 3-well gate fails for every variant tested. Quota untouched at 0/5.

## 1. The premise does not hold — the deployed field is ALREADY an increment estimator

The task specified "the deployed field interpolates the TVT level; swap it for the heel-referenced
increment". Reading the actual builder behind `54844628` (`struct_oof_produce.py`) shows this is not what
it does. Its construction is:

```
r        = TVT + Z                                  (stratigraphic residual)
r_pred   = IDW(k=12, w=1/(d+1)) over the pooled points of all surviving neighbour wells
anchor   = mean(r_true - r_pred) over the target's own last 100 known heel rows
pred     = r_pred + anchor - Z
```

Substituting the anchor:

```
pred = ( r_pred - mean(r_pred over heel) ) + mean(r_true over heel) - Z
        \_________ the increment __________/   \___ the target's own heel level ___/
```

**The level of `r_pred` cancels exactly.** Adding any constant to every neighbour's `r` leaves the output
unchanged — the field is heel-anchored and level-invariant, i.e. it already interpolates the increment
and takes the level from the target's own known heel. A literal level→increment swap is a no-op.

This premise came from my own `new_direction_search` round earlier today, which described the deployed
field as interpolating the level. That description was wrong and is corrected here.

## 2. Preflight — the reimplementation is byte-exact

Before testing any variant, the builder reproduces the deployed field from scratch and is compared with
the banked artifact:

```
reimplementation vs banked struct_oof.npz : max|d| = 0.00000000   over 180,041 rows
```

The evaluation harness was checked the same way: recombining `base` with the banked struct at the
deployed gate (`nnb>=4 AND closest_all<1000`, 87.28% of rows) and W=0.15 reproduces the banked pooled
figures exactly — **8.8626** for `54844628` and **9.2987** for the base. So any difference measured below
is attributable to the variant, not to the harness.

## 3. The mechanism that would have made a reformulation matter does not occur

If the pooled-point IDW drew its k=12 contributing points from *different* neighbour wells sitting at
different stratigraphic levels, then the increment could absorb a cross-well level step whenever the
nearest-well identity changed along the path. That was the one substantive way a reformulation could
help. Measured in the builder:

```
nearest-point WELL identity switches on 0.0002 of consecutive row pairs (median over wells 0.0000)
fraction of the k=12 contributing points sharing the nearest point's well:
    mean 0.9986   median 1.0000   p10 0.9959
```

**The deployed neighbourhood is effectively single-well.** 99.86% of contributing points come from the
same well as the nearest point, and the nearest well essentially never changes along a lateral — the
neighbour wells in a typewell group are parallel laterals on the same pad. There is no cross-well level
mixing to remove.

## 4. Two variants tested anyway, both worse

| variant | construction |
|---|---|
| `struct_increment_iso` | **one-factor isolation** — identical neighbour selection, identical IDW weights, identical gate/W; the ONLY change is that each contributing point enters as a within-well increment (`PR - H[owner]`) instead of a level |
| `struct_increment` | per-well increment computed inside each surviving neighbour, then averaged across wells with `1/(d+1)` well-level weights |

### 4a. Smoke subset (38 wells, 180,041 rows)

3-well gate against the deployed `54844628` (the only gate that decides):

```
struct_increment_iso        [38-well smoke]
  pooled gain vs deployed: -0.1822
  per-well gain: mean -0.1113  median +0.0000  std 0.9474 | helped 42.1%  hurt 36.8%
  3-WELL bootstrap: 1st -3.1600  5th -2.1641  25th -0.0003  50th +0.0002  95th +0.2991
  P(gain>0) = 0.5982
  actual 3 test wells (OOF proxy): -2.9738
  GATE PASS: False   (conditional: False)

struct_increment            [38-well smoke]
  pooled gain vs deployed: -1.8975
  per-well gain: mean -1.5283  median -1.2624  std 2.8061 | helped 15.8%  hurt 63.2%
  3-WELL bootstrap: 1st -6.6439  5th -5.4200  25th -0.0000  50th -1.5480  95th +1.4241
  P(gain>0) = 0.1732
  actual 3 test wells (OOF proxy): -1.9368
  GATE PASS: False   (conditional: False)
```

### Why they are worse — the anchor's exact cancellation is the thing being broken

The deployed anchor subtracts **the same estimator's own value** at the heel, so the reference cancels
exactly and the increment is self-consistent. Both variants replace that with a **different** reference
quantity at the heel (the nearest-point level `H[j]`, or a well-level weighted mean), which does not
cancel and therefore reintroduces a per-well level error. The size of the damage tracks how far the new
reference sits from the original: `iso` changes it slightly (−0.18), the all-wells average changes it a
lot (−1.90). The deployed construction is not merely equivalent to an increment estimator — it is the
*correctly referenced* one, and that is a property worth recording.

## 5. Gate decision

Step 4 of the task ("if and only if the 3-well gate passes, run the pre-submit audit and the submit
gate") does not trigger. Both variants fail the corrected gate: 5th percentile −2.16 and −5.42, both far
below 0, and `struct_increment_iso`'s median gain is +0.0002 — i.e. at best indistinguishable from the
deployed field, which is exactly what section 1 predicts algebraically.

The N4 result from the previous round sharpens this: for one fixed model, a random 3-well draw already
spans 3.49 → 15.14 pooled RMSE, so a candidate whose median gain is +0.0002 carries no usable signal at
the scored scale.

**No submission. Direction closed.**

## 6. What remains open in this area

The drift component that motivated N2 is still the dominant residual (slope std 13.28 ft vs level std
4.72 ft), and the deployed field addresses it with a single-well, IDW-smoothed increment. What this round
rules out is *re-referencing* that increment. What it does **not** rule out is changing the estimator of
the increment itself — for example fitting a slope over the neighbour's r along the path rather than
smoothing its values pointwise. That is a different factor from the one tested here and is recorded as a
possible future item, not queued now, because the same-pad parallel-lateral geometry measured in
section 3 means a single neighbour supplies most of the information and the achievable margin is bounded
by how well that one lateral's drift transfers.
