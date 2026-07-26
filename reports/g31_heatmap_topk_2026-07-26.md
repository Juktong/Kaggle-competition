# G3.1 — stratigraphic misfit heatmap + top-K path search (2026-07-26)

Local smoke on TRAIN wells with the toe masked (competition simulation). **No Kaggle run, no
submission.** Tool: `scripts/g31_heatmap_topk_smoke.py`.

Distinct from the earlier top-K work: that *ranked existing PF seed paths*. Here an explicit cost matrix
is built and searched with our own DP.

```
cost[i,s]  = |GR_horizontal(row i) - GR_typewell(state s)|, per-row normalised
transition = LAM * |s - s'| / band      (TVT changes slowly along MD)
start      = last known heel TVT (anchor)
search     = beam, K=8, keeping distinct current states -> top-K paths
```

## Result — the emission term does not add information

```
LAM      DP top-1    DP oracle top-8    flat-anchor baseline
  4       29.178        29.143               11.830
 20       16.526        16.419               13.278
 60       13.638        13.079               13.278
reference: honest pipeline OOF on train toe rows ~8.86 ft
```

(The flat baseline differs between rows because the well subsets differ; the comparison that matters is
within each row.)

As the transition penalty rises, the DP **converges toward the flat-anchor baseline from above and never
crosses it**. At `LAM=60` the path search is still slightly worse than simply holding the anchor TVT
constant (13.638 vs 13.278), and the whole family sits far above the honest pipeline's ~8.86 ft.

The reading is unambiguous: **every amount of GR-emission influence makes the prediction worse than
ignoring GR entirely.** The optimum of this formulation is the degenerate one.

The beam adds nothing either: top-1 → oracle top-8 improves by 0.035 / 0.107 / 0.559 ft across the three
settings. The K paths are near-duplicates, so a ranker over them (the earlier top-K line) would have
nothing to choose between — consistent with that line's own negative result.

## Root cause (already on record, now confirmed in a third formulation)

Pointwise GR matching is ambiguous:
- the typewell GR profile is **non-monotonic in depth**, so one GR value is consistent with many TVT
  states — the cost matrix has many near-equal minima and the path wanders between them;
- measured directly on 2026-07-21: a pointwise GR difference explains **0.0% of variance** in the TVT
  difference between wells;
- measured on 2026-07-20: the hand-written NCC alignment baseline scores **AUC 0.52** (chance).

This is why the PF works where a per-row DP does not: the PF integrates GR **sequentially along the
whole trajectory** with a motion model, rather than matching row-by-row.

## Disposition

**G3.1 closed on evidence.** One repair iteration (raising the transition penalty) was used to confirm
the diagnosis rather than to rescue the result; the direction is closed because its optimum is the
degenerate flat path, not because of tuning cost. No Kaggle quota was spent.

Any future revival would need a formulation where the emission term is **not pointwise** — e.g. matching
a whole trajectory segment against the typewell with an explicit motion model, which is what the existing
PF already implements.
