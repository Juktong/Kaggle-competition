# Anti-harm guard / test-well-safe selector (2026-07-22)

Direction 1. Can a test-available guard remove the harmful rows so the candidate's 3-well 5th percentile
becomes positive? Tool: `scripts/anti_harm_guard.py`. Candidate `s_54878409`, baseline `s_54844628`.

## Method

Per-row harm label = candidate increases squared error vs baseline. Guard = HistGradientBoosting
classifier on **test-available** features: `|cand−base|`, `closest_surv`, `nnb`, dip `gradmag`,
per-row `nn_dist`, PF `pf_unc`. Trained **leave-well-out (5-fold nested)**. Candidate applied only where
`P(harm) < threshold`; baseline kept elsewhere. Evaluated with the corrected 3-well gate.

## Result

```
gated rows (cand != base) = 87.2%   harm rate on those rows = 48.1%
AUC of the harm predictor (gated rows) = 0.5315   <- essentially chance

guard threshold     appliedFrac    OOF    oofGain | 3w_5th  3w_25th  P>0
ungated (all)          87.2%     8.6817  +0.1809 | -1.282  -0.245   58%
P(harm)<0.60           70.4%     8.6961  +0.1666 | -1.003  -0.178   58%
P(harm)<0.55           60.9%     8.7054  +0.1572 | -0.883  -0.153   58%
P(harm)<0.50           49.0%     8.7218  +0.1409 | -0.782  -0.122   58%
P(harm)<0.45           35.4%     8.7605  +0.1021 | -0.682  -0.090   57%
P(harm)<0.40           23.4%     8.7786  +0.0841 | -0.550  -0.053   56%
```

## Interpretation

**The harm predictor is at chance (AUC 0.5315).** Whether the candidate helps or hurts a given row is not
recoverable from any test-available feature — the same result the earlier multi-signal router reached
(max |corr| 0.131 with per-well gain), now confirmed at the per-row level for the specific harm target.

Tightening the threshold does raise the 3-well 5th (−1.282 → −0.550), but only because it applies *less*
of the candidate — `P(gain>0)` stays pinned at ~58% throughout, exactly as random subsampling would. The
guard is therefore indistinguishable from alpha-shrinkage (direction 4) and, like shrinkage, never
reaches a positive 5th.

## Conclusion

**A per-row anti-harm guard cannot rescue the candidate at 3-well scale**, because the harm is not
predictable from test-available information. This is the third independent confirmation that per-well /
per-row win-loss on this problem is noise with respect to any signal we can compute at test time
(router, top-K guard, and now the harm classifier). No submission from this direction.
