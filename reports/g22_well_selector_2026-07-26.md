# G2.2 — well-level selector (2026-07-26)

Local smoke only, no Kaggle run, **no submission**. Tool: `scripts/g22_well_selector_smoke.py`.

Question: can we choose **per well** between the scored outputs — frontier overlap-OFF (`54968060`),
frontier SP45-only (`54990075`), honest (`54844628`) — and beat every single output?

Design constraint: only 3 wells are scored, so any rule fitted on them would be fitting 3 points. The
smoke therefore measures the **oracle** (truth-selected) margin first — if a truth-selected per-well
choice cannot beat the best single output, no honest feature-based selector can.

## Result

```
well       54968060_overlapOFF  54990075_sp45only  54844628_honest   best
000d7d20         1.637               1.416              3.104        sp45only
00bbac68         4.191               3.802              3.972        sp45only
00e12e8b         2.829               1.429              3.720        sp45only

pooled proxy RMSE:  sp45only 2.7034 | overlapOFF 3.2594 | honest 3.6772

ORACLE per-well selection -> sp45only on all 3 wells
  oracle 2.7034   best single 2.7034
  ORACLE MARGIN = +0.0000 ft
```

**The oracle margin is exactly zero.** One model (SP45-only) is best on every well, so per-well selection
degenerates to "always pick that model". There is no well-level structure for a selector to exploit —
not a modelling shortfall, but an absence of the opportunity itself.

## The second, more important finding: the proxy inverts the ranking it would be used for

```
candidate            proxy RMSE   public
54990075 sp45only      2.7034      6.690   <- proxy BEST, public WORST of the frontier pair
54968060 overlapOFF    3.2594      6.643   <- proxy WORSE, public BETTER
54844628 honest        3.6772      7.891   <- proxy worst, public worst  (ordering correct here)
```

Across **families** (frontier vs honest) the proxy orders correctly. **Within** the frontier family it
orders backwards: it prefers `54990075`, which is measurably the weaker of the two on the leaderboard.

This is the sharpest statement yet of the regime boundary the pipeline has been circling:

- **large differences (≥ ~1 ft proxy / ≥ ~1 public)** — the train-copy proxy is directionally reliable
  (frontier ≪ honest, confirmed by 6.6 vs 7.9);
- **small differences (within a family)** — the proxy is unreliable and here actively inverted.

A selector would have to operate exactly in the small-difference regime, where its only available
supervision signal is the one that inverts. That closes the direction on evidence rather than on cost.

## Disposition

**G2.2 closed — no selector opportunity, no submission.** Two reusable conclusions:

1. Per-well selection among the current candidates has zero headroom even with oracle knowledge.
2. The train-copy proxy must not be used to rank candidates within a family. This retires it as a
   ranking tool for the remaining rotation candidates; only a structural argument or a leaderboard
   result can separate close candidates. (Consistent with `54990075` = 6.690 settling the SP45 question
   in the opposite direction to the proxy's preference.)
