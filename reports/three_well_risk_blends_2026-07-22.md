# Conservative blends under 3-well risk (2026-07-22)

Direction 4. Optimise for 3-well **downside**, not 760-well OOF. Tool: `scripts/three_well_blends.py`.
Baseline `s_54844628` (public 7.891).

## Result

```
blend                             OOF    oofGain | 3w_5th  3w_25th  3w_50th  P>0  | gate
s_54878409 a=0.05               8.8414  +0.0213 | -0.040  -0.002   +0.014   72%  | FAIL
s_54878409 a=0.10               8.8213  +0.0413 | -0.082  -0.005   +0.027   71%  | FAIL
s_54878409 a=0.20               8.7850  +0.0776 | -0.174  -0.013   +0.051   70%  | FAIL
s_54878409 a=0.30               8.7539  +0.1088 | -0.272  -0.027   +0.069   68%  | FAIL
s_54878409 a=0.50               8.7071  +0.1555 | -0.510  -0.069   +0.095   65%  | FAIL
topk96_l75 a=0.05               8.8224  +0.0403 | -0.068  -0.003   +0.024   73%  | FAIL
topk96_l75 a=0.30               8.6551  +0.2076 | -0.451  -0.039   +0.120   69%  | FAIL
s_k96_aniso a=0.05              8.8373  +0.0254 | -0.048  -0.003   +0.017   71%  | FAIL
median(dwt,pf,s1)               8.9631  -0.1004 | -0.345  -0.041   +0.000   50%  | FAIL
median(s1,s54878409,topk)       8.6650  +0.1976 | -1.139  -0.182   +0.104   61%  | FAIL
trimmed 0.5*(s1+s54878409)      8.7071  +0.1555 | -0.510  -0.069   +0.095   65%  | FAIL
min-move base+clip(cand-base,±2) 8.7124 +0.1502 | -0.595  -0.133   +0.114   62%  | FAIL
```

## The math is confirmed empirically: shrinkage cannot pass the gate

As `alpha → 0` the 3-well 5th percentile approaches 0 **from below** and never becomes positive
(a=0.05: 5th −0.040; a=0.10: −0.082; …). Shrinking toward baseline scales *both* the mean gain and the
tail by ~`alpha`, so the sign of the 5th percentile is invariant. The best any blend achieves is a 25th
percentile of essentially zero (`a=0.05`, 25th −0.002, P>0 72%) — i.e. "almost never hurts, almost never
helps".

Robust combiners (median / trimmed) are worse, not better: `median(s1, s54878409, topk)` has 3w_5th
−1.139 because taking a per-row median across disagreeing fields injects large moves on the rows where
they disagree most, which is exactly the tail that a 3-well draw is sensitive to.

## Conclusion

**No blend passes the corrected 3-well gate.** This is not a search failure — it is forced by the
per-well gain distribution (median ≈ 0, std ≈ 1.3): no linear shrinkage of a tail-dominated signal can
produce a positive small-sample lower bound. The only path that could change the *shape* of the
distribution rather than its scale is a **guard that removes the harmful cases** (per-row or per-well),
which is tested separately in `reports/test_well_selector_guard_2026-07-22.md`.

The closest-to-safe option on record is `s_54878409 a=0.05` (25th ≈ 0, P>0 72%, OOF +0.021), but "almost
never hurts" is not the same as "passes the gate", and it does not clear the bar for spending a slot.
No submission from this direction.
