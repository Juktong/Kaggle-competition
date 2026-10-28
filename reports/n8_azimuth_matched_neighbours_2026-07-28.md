# N8 — azimuth-matched neighbour selection for the structural field, 2026-07-28

Autopilot task `n8_azimuth_matched_neighbours` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). Scripts: `scripts/n8_azimuth_matched_neighbours.py` (builder),
`scripts/n8_eval_azimuth.py` (evaluation + 3-well gate). Logs:
`reports/logs/n8_full_{build,eval}_2026-07-28.log`.

**Result: negative at every tolerance. No submission — the 3-well gate fails for all four variants, so
the task's step 6 never triggers.** Quota untouched at 0/5. The risk N2 flagged is confirmed
quantitatively, and the round also explains *why* the idea has so little room to work here.

## 1. Construction and preflight

The deployed builder's machinery was reused from `scripts/n2_increment_structural_field.py` (loading,
caching, KD-trees). The only change is an azimuth-similarity filter applied to the **surviving**-neighbour
set, after the 150 ft duplicate guard. Group key, IDW kernel, k=12, anchor length, gate and W all stay at
deployed values.

Per-well azimuth is the step-length-weighted mean drilling direction from X/Y (test-available), and the
difference is taken on the **full circle** — 0° and 180° are *not* equivalent, which is the whole point of
the updip/downdip argument.

**Preflight (required before reading any variant):** `az_tol=180` disables the filter and must reproduce
the banked field exactly.

```
struct_az180 vs banked struct_oof.npz : max|d| = 0.00000000   over 180,041 smoke rows
struct_az180 pooled on the full split : 8.8626   (delta vs banked -0.0000)
```

The control is byte-exact, so every difference below is attributable to the filter.

## 2. What the filter actually does (full 760-well split)

```
az_tol     mean nnb    nnb=0 %   lost nearest well %
15            11.79       2.6%                 12.2%
30            14.26       1.4%                 11.3%
45            14.82       1.3%                 11.2%
90            14.95       1.1%                 10.9%
180 (control) 28.09       0.0%                  0.0%

median azimuth spread among surviving neighbours: 26.7 deg
```

Two things stand out before any scoring:

- **The filter is not inert** — it halves the neighbour count and removes the *nearest* well for
  10.9–12.2% of targets. Roughly one target in nine has its closest mate drilled in a materially
  different direction, which is exactly the population the updip/downdip argument is about.
- **But the deployed selection is already azimuth-coherent**: the median azimuth spread among surviving
  neighbours is only **26.7°**. Typewell-group membership plus spatial proximity already deliver
  similarly-oriented wells, so an explicit azimuth filter is largely redundant with constraints the
  pipeline enforces for other reasons.

## 3. Scores — every tolerance is worse than no filter

```
variant           pooled    vs 8.8626   rows falling back to base
struct_az15       8.9323      -0.0697                       0.6%
struct_az30       8.9361      -0.0735                       0.3%
struct_az45       8.9372      -0.0746                       0.3%
struct_az90       8.9415      -0.0789                       0.3%
struct_az180      8.8626      -0.0000                       0.0%   <- control
```

3-well gate against the deployed `54844628`, 20,000 draws:

```
struct_az15   pooled gain -0.0697 | per-well mean -0.0831 median +0.0000 | helped 42.4% hurt 43.8%
              3-well: 1st -5.2175  5th -0.8622  25th -0.0000  50th +0.0000  95th +0.8248
              P(gain>0) 0.4999 | actual 3 test wells -0.0990 | GATE PASS: False
struct_az30   pooled gain -0.0735 | 5th -0.9021 | P(gain>0) 0.4945 | GATE PASS: False
struct_az45   pooled gain -0.0745 | 5th -0.9011 | P(gain>0) 0.4894 | GATE PASS: False
struct_az90   pooled gain -0.0789 | 5th -0.9011 | P(gain>0) 0.4862 | GATE PASS: False
```

The per-well **median gain is exactly +0.0000** with helped ≈ 42% and hurt ≈ 44% at every tolerance: for
most wells the filter changes nothing (their neighbours already share an azimuth), and where it does act
it hurts slightly more often than it helps.

Note the ordering is non-monotone — the 90° filter is the *worst* (−0.0789) and the 15° filter the least
bad (−0.0697). That is not a paradox: a tighter tolerance pushes more wells to an empty neighbour set
(2.6% at 15° vs 1.1% at 90°), and an empty set falls back to plain `base`, which is a *neutral* outcome,
whereas a surviving-but-degraded neighbour set actively injects a worse estimate. Losing the neighbour
entirely costs less than keeping a poor one.

## 4. Why the idea has little room here — and it is consistent with the rest of the ledger

The public methodology this came from (`reports/n6_public_solution_audit_2026-07-28.md`) applies azimuth
matching to an offset-well prior in a **LightGBM feature** pipeline, where a mis-oriented neighbour
contributes a noisy feature among many. In our deployed field the neighbour set feeds a **single
IDW-weighted estimate** that is then blended at W=0.15, and N2 measured that estimate to be effectively
**single-well** (99.38% of the k=12 contributing points share the nearest point's well). Removing the
dominant neighbour therefore does not shift a weighted average — it replaces the estimator's only real
input. That is why an argument that is sound in general costs us score here.

This closes the loop with the two neighbouring results from the same day:

- **N5** showed the deployed group key `round(max(typewell.TVT), 1)` is a *lossless* proxy for typewell
  identity — neighbour **membership** is already right.
- **N8** (here) shows neighbour **orientation** is already right too (median spread 26.7°), and forcing it
  tighter costs score.
- **N2** showed the deployed **anchor** is already the correctly-referenced increment estimator.

Three independent one-factor probes of the same component, all landing on "the deployed construction is
already the right one". The remaining error in this component is not in membership, orientation or
referencing.

## 5. Gate decision

Task step 6 ("only if the 3-well gate passes: pre-submit audit, then the submit gate") **does not
trigger**. All four variants fail the corrected gate with 5th percentiles between −0.86 and −0.90 and
P(gain>0) ≈ 0.49 — indistinguishable from a coin flip, and negative in the mean. On the actual three test
wells the OOF proxy gain is −0.0990 for every tolerance.

**No submission. Direction closed.**

## 6. What remains

The azimuth *signal* is not disproven — 10.9% of targets do have a nearest mate at a materially different
orientation, and the updip/downdip mechanism is real geology. What is disproven is that a **hard filter on
neighbour membership** is the way to use it inside this estimator. A softer form — azimuth as a *weight*
in the IDW kernel rather than a *gate* on membership — is untested and would not remove the dominant
neighbour, only down-weight it. It is not queued now: the measured headroom is small (the filter changes
nothing for ~58% of wells) and the 3-well gate demands a much larger effect than that to clear, per N4's
measured draw spread of 3.49→15.14 for a fixed model.
