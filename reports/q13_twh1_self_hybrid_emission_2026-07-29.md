# Q13 — TWH=1 typewell + coverage-gated self hybrid emission, 2026-07-29

Autopilot task `q13_twh1_self_hybrid_emission` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). Script: `scripts/q13_hybrid_emission.py`. Logs:
`reports/logs/q13_hybrid_2026-07-29.log`, `reports/logs/q13_hybrid_dp_2026-07-29.log`.

**Result: no nested gain — closed. But the round produced the most informative negative of the Q-series:
a hybrid emission that is clearly BETTER pointwise produces a clearly WORSE trajectory.** No submission;
quota untouched at **0/5**.

## 1. Two of the three proposed ingredients were already settled

- **Naive combination — already closed.** Q12's `both` arm *is* a typewell+self hybrid emission (the two
  feature blocks concatenated into one scorer): +0.0012 pooled over 60 held-out wells, beating typewell on
  51.7% of them. A coin flip.
- **The prefix-coverage gate — already closed.** Q12 measured `corr(coverage, both − typewell) = 0.0604`
  and `corr(coverage, self − typewell) = 0.0867`, with `self` negative in all five coverage bands. So
  "self helps where prefix coverage is high" is disproven.
- **The typewell-UNCERTAINTY gate — untested, and the only thing this round could add.** N9 and Q12 only
  ever scored two candidate states per row (the true state and one negative), so no emission profile
  existed from which to compute uncertainty. Q13 computes the **full** profile over all states for both
  templates, which makes the gate measurable for the first time.

Gate definition, test-available: `u(row) = top1 − top2 margin` of the typewell emission. Small margin =
ambiguous. Hybrid: `C_h = C_tw + w · C_se · covered`.

## 2. At the emission level the hybrid clearly helps, and the gate is clean

40 held-out wells, 19,083 toe rows, splits by well. Metric is `|argmax error|` — how far the emission's
best state lies from the true TVT.

```
w        mean     median      p90    within 5ft
0     185.756    137.520   412.920        0.045      <- typewell only
0.25  162.816    120.750   386.266        0.054
0.5   156.445    115.640   385.890        0.046
1     149.408    112.420   383.858        0.036
```

Monotone improvement, −36.3 ft (−19.6%) at w=1, helping **67.5%** of eval wells.

And the uncertainty gate stratifies **perfectly monotonically** — this is the first gating variable in
this project to do so:

```
typewell margin band     n   tw-only err    w=0.25     w=0.5       w=1
0.00-0.00             3817       209.919   -45.491   -55.616   -63.970
0.00-0.01             3816       198.068   -37.342   -45.072   -51.540
0.01-0.01             3817       186.767   -26.307   -32.521   -39.457
0.01-0.02             3816       174.083   -11.902   -16.659   -24.026
0.02-0.48             3817       159.944    +6.344    +3.315    -2.750
        (negative = the hybrid helps)
```

The self signal helps most exactly where the typewell emission is ambiguous, and is neutral-to-harmful
where it is confident. Precisely the hypothesised behaviour.

## 3. Through the DP the sign reverses

An `|argmax error|` of ~150 ft is an emission diagnostic, not a candidate. Feeding the same profiles into
Q10's beam DP with λ chosen nested on disjoint well halves:

```
w        lam=5   lam=10   lam=20   lam=60  lam=100     nested
0       16.089   14.368   13.297   12.772   12.861     12.861    <- best
0.25    20.530   16.021   14.452   13.177   13.031     14.479
0.5     22.921   17.981   15.551   13.656   13.256     13.256
1       30.378   21.966   16.610   14.501   13.789     13.789

flat-anchor on these 40 wells 12.722 | deployed honest 8.8626 | Q10 typewell-only DP 12.170
```

**Every self weight makes the trajectory worse, monotonically in w at every λ.** The best arm is w=0 —
typewell only. There is no nested gain, so task step 4 applies: close and record why.

## 4. Why a better emission gives a worse trajectory

This is the round's real content, and it is a mechanism not previously in the ledger.

The self emission is **coverage-masked**: zero on states the prefix never visited, non-zero on states it
did. Adding it therefore applies a systematic pull toward the prefix's TVT range.

- **Pointwise that is a good bet.** N9 measured prefix coverage at 63.5% of toe rows within 0.5 ft of
  their true TVT, so a row drawn at random is more often near a covered state than not. Biasing each row
  independently toward covered states raises the per-row hit rate — which is exactly what section 2 shows.
- **Chained through a DP it is a systematic error.** A trajectory is an integral of transitions, so a
  constant pull in one direction does not average out; it accumulates. The toe's whole difficulty is that
  it *drifts away* from the prefix's stratigraphic range — the banked residual decomposition attributes
  60.3% of variance to a per-well offset dominated by drift (slope std 13.28 ft). Pulling the path back
  toward the prefix range is therefore pulling it against precisely the component that dominates the
  error.

So the improvement is **marginal** (each row independently more likely to be near truth) while the damage
is **cumulative** (the path is biased along its whole length). A metric that scores rows independently
cannot see this; only the trajectory metric can.

**Generalisable lesson for the ledger:** *a pointwise emission metric is not a valid proxy for trajectory
quality when the emission modification carries a directional bias.* Emission-level AUC or argmax accuracy
should never again be accepted as evidence for a DP candidate without the DP being run. Q10 established
the exchange rate in the favourable direction (+0.03 AUC bought −1.04 RMSE); Q13 shows the exchange rate
can be **negative** when the emission gain comes from a bias rather than from sharper discrimination.

## 5. Verdict

- **No nested gain; direction closed.** w=0 (typewell only) is the best arm at 12.861; every hybrid weight
  is worse. Step 5 never triggers, so no Kaggle smoke and **no submission**.
- **Retained finding:** the typewell-uncertainty gate is real and monotone at the emission level. If a
  future line ever needs to modulate an emission by confidence, this is the measured, test-available gate
  — but Q13 also shows that an emission-level gain is not sufficient evidence on its own.
- **Also retained:** the coverage mask is the source of the directional bias. Any future use of the self
  template inside a sequential model must avoid making its availability correlate with the state.
- Slot recommendation unchanged: `54922806` + `54844628` under all three criteria.
