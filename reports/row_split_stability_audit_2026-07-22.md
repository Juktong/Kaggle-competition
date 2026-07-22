# Public-vs-private row-split stability audit (2026-07-22)

Direction 3. The whole test set is 3 wells; public and private are **row splits of those same 3 wells**.
So the question that determines private is not "does the gain hold on other wells" but "does the gain on
one row-subset of these wells hold on the complementary subset". Tool: `scripts/row_split_audit.py`.

## Result

```
mode = RANDOM row split (Kaggle-typical), candidate vs s_54844628
candidate     corr(A,B)  P(B<0|A<0) | 3-testwell OOF-proxy: mean  P(gain<0)   5th    95th
s_54878409       0.999      99.1%    |         +0.2906            0.0%      +0.272 +0.309
s_a20_w25        0.999      98.0%    |         +0.3388            0.0%      +0.318 +0.359
s_k96_aniso      0.999      98.5%    |         +0.3934            0.0%      +0.374 +0.413
topk96_l75       0.999      98.6%    |         +0.4982            0.0%      +0.474 +0.522

mode = CONTIGUOUS block split
s_54878409    corr(A,B)=0.097  P(B<0|A<0)=47.9%  3-testwell mean +0.4049  P(gain<0)=0.0%
topk96_l75    corr(A,B)=0.145  P(B<0|A<0)=49.2%  3-testwell mean +0.5584  P(gain<0)=0.0%
```

## Interpretation — the split geometry decides everything, and we don't know it

**Under a random row split**, `corr(A,B) = 0.999`: one row half predicts the other almost perfectly
(within-well residual autocorrelation is +0.9998). On this assumption public would be an almost exact
predictor of private, and the OOF proxy on the 3 test wells would say the candidate *always* improves
(P(gain<0) = 0.0% across 4000 random half-splits). **But `54878409` got worse on public.** So either the
split is not random, or the OOF proxy (train copies) does not represent the test versions.

**Under a contiguous block split**, `corr(A,B)` collapses to **0.10–0.15**: the gain on the first half of
each well's rows barely predicts the gain on the second half, and `P(B<0|A<0) ≈ 48%` — a coin flip. For
MD-ordered wellbore data where the heel is known and the toe is predicted, a block-structured split is
plausible, and under it **public carries almost no information about private**.

The observed contradiction — OOF proxy +0.29 on the 3 test wells vs public −0.062 — is exactly what the
block-split row shows: different row blocks of the same well can have opposite-signed gains (corr 0.10).
Combined with the fact that the test versions predict a *different, larger* toe region (only 26.4% of
test rows are known heel vs the train copies' split), the local proxy and the public score legitimately
disagree.

## Consequences

1. **No local proxy reliably predicts public or private for these candidates.** The 760-well OOF, the
   3-well bootstrap, and the OOF-proxy-on-the-3-test-wells all disagree with the one real observation
   (`54878409` public −0.062).
2. **A candidate that is robust to the split must help on *every* row block**, not on average. That is
   the anti-harm-guard / conservative-blend target: reduce per-row downside so the sign of the gain does
   not depend on which rows are scored.
3. **`54844628` remains the honest slot** — it is the only configuration with a real, measured public
   score on the actual test wells, and no local statistic available to us overturns that.

## What a submittable candidate would need

Row-split consistency `corr(A,B)` high **and** the block-split mean gain strictly positive with a
positive block-split 5th percentile — i.e. the candidate improves regardless of how the rows are
partitioned. None of the current candidates has a positive block-split 5th (they inherit the same
tail-dominated per-well distribution). This is tested per-candidate in
`reports/three_well_risk_blends_2026-07-22.md` and `reports/test_well_selector_guard_2026-07-22.md`.
