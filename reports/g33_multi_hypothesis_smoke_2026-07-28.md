# G3.3 — multi-hypothesis (MTP) trajectory smoke (2026-07-28)

Autopilot task `g33_multi_hypothesis_smoke` (`requires_gpu=true`, `can_submit=true`,
`max_submit_cost=1`). **Outcome: closed on evidence — no Kaggle run, no submission, 0 quota used.**
Tool: `scripts/g33_multi_hypothesis_smoke.py`. Local CPU (`torch 2.12.1+cpu`); per the standing rules a
GPU run requires a local smoke with real signal first, and the masked split below does not provide one.

## Design

Parameterised from the measured residual structure (2026-07-21): a well's toe residual relative to a flat
anchor is dominated by a constant offset plus a drift (drift std **13.28 ft** vs level-offset std
**4.72 ft**). Each hypothesis is therefore a pair `(offset, slope)` describing the toe trajectory relative
to the flat-anchor line; the model emits **K hypotheses + K probabilities**, trained with a best-of-K
(MTP) loss plus a cross-entropy term on which hypothesis won.

Inputs are **test-available only**: known-prefix statistics (length, GR mean/std, TVT std, prefix drift
rate), typewell GR summary, and trajectory geometry (MD/Z spans, heel→toe GR level shift).

The decisive framing: under RMSE the optimal single output is the conditional mean, which K=1 already
produces. Multi-hypothesis can only pay if a hypothesis can be **selected at inference**, so oracle and
achievable numbers are reported side by side rather than the oracle alone.

## Result (400 wells, 100 held out, K=5)

```
training: K=1 best-loss 1.9911 -> 0.6559 | K=5 best-loss 1.7413 -> 0.2754     (loss decreases)
hypothesis diversity: mean std of offset across K = 9.734 ft                  (nonzero)

flat-anchor baseline                     15.833
K=1 regression                           18.475     <- WORSE than the flat baseline
K=5 argmax-probability (ACHIEVABLE)      16.877
K=5 probability-weighted mean            16.848
K=5 ORACLE best-of-K (upper bound)       12.768
deployed honest pipeline OOF reference    ~8.86

ORACLE MARGIN over K=1  = +5.707 ft
ACHIEVABLE MARGIN over K=1 = +1.598 ft
```

All three of the task's smoke checks pass — the training loop runs, the loss decreases, top-K diversity
is nonzero (9.7 ft, large relative to the 4.72 ft level-offset std), and the reconstructed trajectories
are anchored, monotone-in-parameterisation and physically sane.

## Reading

**1. The K=1 regression is worse than doing nothing (18.475 vs flat 15.833).** Predicting a well's
`(offset, slope)` from test-available features actively hurts: the model emits non-zero corrections that
are wrong more often than right. This is a **fourth independent confirmation** that the per-well residual
is not predictable from test-available information — after the residual-correction models that
anti-correlated out-of-fold (direction 2), the group calibration whose optimum was exactly zero
(direction 3), and the anti-harm guard at AUC 0.53 (direction 1).

**2. The multi-hypothesis structure does help relative to its own K=1 version (+1.598 achievable).**
Notably the probability head carries *some* usable selection signal, which is a slight departure from the
earlier selector results where selection was pure noise. But the achievable margin recovers only 28% of
the oracle margin (+1.598 of +5.707).

**3. It does not matter, because the whole family sits below a trivial baseline.** The best achievable
configuration (16.877) is still worse than simply holding the anchor flat (15.833), and all of it is far
from the deployed pipeline (~8.86). There is nothing here to carry forward into a candidate.

**4. The large oracle/achievable gap repeats the established pattern.** Oracle +5.707 vs achievable
+1.598 is the same shape as the top-K path ranker (oracle far above achievable) and the well-level
selector (oracle margin 0.0000 once the best single model dominated). An oracle number remains not
evidence of an achievable gain.

## Disposition

**Closed on evidence.** No variant was built, no Kaggle smoke or full run was launched, the submit gate
was never reached, 0 of today's 5 quota used. `54844628` and the slot recommendation are unchanged.

### Minimal next smoke, if this direction is ever revisited

The task asks for a concrete next smoke rather than a broad plan. The one change that would address the
actual failure mode — that the *inputs* do not determine the per-well offset — is **not** a bigger model
or a larger K. It is to give the model an input that is known to carry per-well information:

> Feed the **PF's own per-well posterior spread** (seed dispersion and bimodality separation, already
> computed by the deployed pipeline and available at inference) as an input feature, and train K
> hypotheses only on wells where that spread is large. This tests whether multi-hypothesis output helps
> *specifically on the ambiguous wells the PF already flags*, instead of on all wells uniformly.

That is a ~1-hour local smoke reusing `pf_unc.npz`, and it is falsifiable the same way: report the
achievable margin, not the oracle margin.
