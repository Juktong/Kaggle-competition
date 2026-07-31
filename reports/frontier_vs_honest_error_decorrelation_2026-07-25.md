# Overlap-OFF frontier vs honest slot — error decorrelation (D3, 2026-07-25)

Refines the D1 preview (which compared *predictions*, corr 1.0). What matters for a blend and for the
H-hidden question is *error* correlation and relative strength. Measured on the 3 test wells' train-copy
TVT (a proxy — the leaderboard truth differs at fine scale, per 2026-07-22; use for relative comparison).

## Result

```
A2 overlap-OFF frontier RMSE = 3.259     54844628 RMSE = 3.677    (vs train-copy TVT, 14151 rows)
corr(err_frontier, err_54844628) = +0.7653   (pooled; per-well 0.871 / 0.873 / 0.939)
min-variance blend w*_frontier = 0.970 -> RMSE 3.244  (≈ frontier alone; blend adds ~nothing)
```

## Two findings that refine the picture

1. **The overlap-OFF frontier is STRONGER than our honest slot in the local truth space** (RMSE 3.259 vs
   3.677). Its non-overlap PF/beam/SP45/visible-prefix stack beats our DWT+PF+struct on these wells — so
   the frontier's *modeling*, independent of the overlap lookup, is genuinely good.

2. **Errors are only moderately correlated (0.765), not 1.0** — but the min-variance blend weight is 0.97
   on the frontier, i.e. the optimal combination is essentially "just use the frontier". A blend with our
   honest slot does not reduce variance materially (3.244 vs 3.259), because the honest slot is both
   weaker and 0.765-correlated. So **D1/D3 blend verdict stands: no useful ensemble** — but for a new
   reason (the frontier dominates rather than decorrelates).

## Consequence for the final slot — `54968060` may be more than a diagnostic

Earlier framing (D1) treated the overlap-OFF frontier as "corr 1.0 with honest → equal under H-hidden,
diagnostic only". D3 corrects this: on the local truth space the overlap-OFF frontier is **better** than
our honest slot. So under **H-hidden** (novel wells, overlap inert) the frontier's non-overlap stack
could **outperform** `54844628`, making `54968060` a *candidate* H-hidden hedge, not merely a diagnostic.

**Caveat (decisive):** this is measured against train-copy TVT, and 2026-07-22 established that local
truth-space accuracy does not predict the leaderboard at the ≲0.1 scale (our own 54878409 was better
locally, worse on public). So "frontier better locally" is suggestive, not conclusive. The pending public
score of `54968060` is the real test:

- `54968060` **≤ ~7.5** (near or below our honest 7.891) → the overlap-OFF frontier is a genuinely
  strong non-overlap model and a **better H-hidden hedge than `54844628`** → it should be considered for
  slot 2, replacing our honest slot.
- `54968060` **materially worse (> 8)** → its local strength did not transfer; `54844628` (OOF-validated)
  remains the slot-2 hedge.

## PUBLIC CONFIRMATION: `54968060` = 6.643

The pending test resolved, and **it agrees with the local D3 measurement in direction and in magnitude
class**:

```
local (train-copy TVT):  overlap-OFF frontier 3.259   vs   54844628 3.677     -> frontier better
public:                  overlap-OFF frontier 6.643   vs   54844628 7.891     -> frontier better by 1.248
```

The pre-registered thresholds were: `54968060` ≤ ~7.5 → better H-hidden hedge than `54844628`;
> 8 → local strength did not transfer. The result (**6.643**) is far inside the first branch.

Two points worth recording:

1. **This local→public transfer succeeded**, unlike the `54878409` case (2026-07-21) where a local gain
   of +0.18 became a public loss of −0.062. The difference in scale explains it: here the local gap was
   0.42 ft RMSE between structurally different pipelines and the public gap is 1.25 — a *large*
   difference, the regime where local evidence does track the leaderboard. The 54878409 case was a ~0.1
   difference, the regime where it does not (2026-07-22 finding). The two results are consistent.
2. **Error-corr 0.765 with the min-var weight at 0.97** still means no useful blend: the frontier
   dominates rather than decorrelates. That verdict is unchanged.

## Disposition

D3's revision is confirmed by public: the overlap-OFF frontier is a **live slot-2 candidate**, better on
both local and public than our honest slot, with a lineage/provenance caveat (public-notebook derivative
+ third-party datasets, no 760-well OOF). No blend is warranted. Weighting recorded in
`reports/final_slot_package_corrected_gate_2026-07-25.md`.
