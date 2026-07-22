# Corrected-gate re-audit of all candidates (2026-07-22)

Infrastructure B. Every candidate with local artifacts re-scored under the corrected 3-well gate.
Tool: `scripts/eval_three_well_gate.py`. Driver: `scripts/corrected_gate_reaudit.py`.
Baseline throughout: `s_54844628` (OOF 8.8626, public **7.891**).

## Result

```
candidate           OOF  oofGain | ref760_5th |   3w_5th  3w_25th  3w_50th   P>0 | gate
s_54878409       8.6825  +0.1802 |    +0.0501 |   -1.262   -0.244   +0.098   58% | FAIL   (public 7.953, confirmed)
s_a20_w25        8.6790  +0.1837 |    +0.0495 |   -1.196   -0.222   +0.090   59% | FAIL
s_k96_aniso      8.6547  +0.2080 |    +0.0555 |   -1.520   -0.290   +0.130   58% | FAIL
base_k96         9.2555  -0.3928 |    -0.6542 |   -2.021   -0.688   -0.144   41% | FAIL
topk96_l75       8.5070  +0.3556 |    +0.1397 |   -1.946   -0.396   +0.171   59% | FAIL
dwt             10.2891  -1.4264 |    -1.9261 |   -6.067   -2.593   -1.057   29% | FAIL
pf              11.0563  -2.1936 |    -2.6032 |   -7.493   -3.240   -1.303   28% | FAIL
base             9.2987  -0.4360 |    -0.6919 |   -1.910   -0.674   -0.168   37% | FAIL
```

`residual correction`, `router/selector`, `L3 ungated`, and the older DWT/PF blends were all
OOF-negative vs baseline in prior rounds, so they fail the corrected gate a fortiori and were not re-run.

## The finding: no candidate passes, and OOF rank ≠ 3-well robustness

**Every candidate fails the 3-well gate**, including `topk96_l75`, which has the *best* OOF (+0.3556) and
the best 760-well reference (5th +0.1397). At 3-well scale its 5th percentile is **−1.946** and it beats
baseline in only **59%** of 3-well draws — essentially the same coin-flip as every struct variant.

The reason is structural and identical across candidates: **per-well gain has median ≈ 0 with std ≈ 1.3**,
while the mean is only ≈ +0.1–0.35. So the pooled OOF gain is an asymmetric-tail effect, and any 3-well
realisation is dominated by which 3 wells land in the draw, not by the small mean.

Two consequences worth stating plainly:

1. **Ranking candidates by 760-well OOF is not informative about a 3-well outcome.** `topk96_l75` is
   +0.20 better than `s_54878409` in OOF but has a *worse* 3-well 5th percentile (−1.95 vs −1.26).
2. **The 3-well "5th > 0" gate is close to unreachable for any candidate whose per-well gain has a
   negative well-level 5th percentile** — which is all of them, because per-well std (1.3) far exceeds
   per-well mean (0.1). Shrinking a candidate toward baseline by `alpha` scales both the mean gain and
   the tail by ~`alpha`, so the 5th percentile approaches 0 *from below* and never becomes strictly
   positive. This is tested directly in `reports/three_well_risk_blends_2026-07-22.md`.

## Implication for the gate and for strategy

The literal "3-well 5th > 0" pass is a very high bar that no honest candidate meets, because 3 wells
cannot resolve a per-well effect of this size. That is itself the key result: **the public leaderboard
is not a usable discriminator at the ±0.1 effect scale of our candidates.**

This redirects the remaining work away from "maximise 760-well OOF" and toward the two questions that
actually bear on the private ranking:

- **Does the candidate improve the SAME 3 test wells on their held-out rows?** (public↔private are row
  splits of the same 3 wells) — `reports/row_split_stability_audit_2026-07-22.md`.
- **Can per-well downside be reduced so the effect is not tail-dominated?** — the anti-harm guard
  (`reports/test_well_selector_guard_2026-07-22.md`) and conservative blends
  (`reports/three_well_risk_blends_2026-07-22.md`).

## Disposition

No candidate passes the corrected gate. **No submission is warranted on the strength of OOF gain.**
`54844628` (7.891) remains the honest slot as the only option validated on the actual test wells.
