# Q55 — decoder averaging: the DP objective is misaligned, and the beam's suboptimality is protective

Date: 2026-07-29 19:55 UTC
Task: `q55_dp_decoder_averaging` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q55_dp_decoder_averaging.py` · Log: `reports/logs/q55_decoder_2026-07-30.log`
Outcome: **gate FAILS on all three arms. No submission. Quota 0/5.**
**But the round produced the most consequential structural finding of the alignment line (§3).**

## 1. Beam spread — Q54 required this before anything else

```
lam      mean row range  p90 row range  max row range  rmse b0 vs bK
20                0.091          0.131         15.000          0.191
60                0.070          0.175          6.000          0.192
150               0.132          0.277          6.000          0.238
```

The six beams agree to **~0.1 grid units (≈0.1 ft) on average**, with the whole beam's best-vs-worst path
differing by only **0.19–0.24 RMSE**. **Q54's prediction is confirmed**: the K=6 beam holds six
near-identical paths, so averaging it can only move the answer ~0.1 ft. That was worth measuring first —
it says the beam-average arm is inert by construction rather than by evidence.

**Degeneracy control.** Beam average at T→0 must recover `beams[0]`:
`max|beam_avg − run_dp|` = 0.0060 (λ=20), 4.0e-5 (λ=60), 4.1e-8 (λ=150). It converges as T→0 as intended;
the 0.006 residual at the coarsest λ is T=0.01 not being exactly zero, not a discrepancy in the operator.

## 2. Arms and the gate

```
lam            base | T=0.01  T=0.1   T=0.5   T=2     T=10    | g=0.05  g=0.2   g=1     g=5
20           13.169 | 13.169  13.165  13.155  13.152  13.151  | 32.433  33.129  31.799  277.706
60           12.170 | 12.170  12.169  12.166  12.161  12.160  | 15.375  15.053  22.025   60.785
150          12.478 | 12.478  12.469  12.445  12.434  12.429  | 12.623  11.352  12.152   21.093
```

```
NESTED beam average only : 12.566 vs 12.601  gain +0.035 | helps 52.5% | 3-well 5th -0.007  -> FAIL
NESTED soft-min only     : 12.370 vs 12.601  gain +0.230 | helps 32.5% | 3-well 5th -1.420  -> FAIL
NESTED both              : 12.370 vs 12.601  gain +0.231 | helps 65.0% | 3-well 5th -1.419  -> FAIL
```

All three fail on the 3-well 5th percentile. Two things are worth recording rather than glossing:

- **`both` helps 65.0% of held-out wells** — the highest per-well win rate the alignment line has produced,
  and it clears two of the three conditions.
- **`fb` at λ=150, γ=0.2 gives 11.352 pooled** — the best single number the alignment line has ever
  produced, against Q10's 12.170. Nested, it delivers only +0.230, because the two folds pick different
  arms. That gap between best-pooled (11.352) and nested (12.370) is ordinary selection noise, and the
  nested figure is the honest one.

## 3. THE HEADLINE — solving the objective *better* makes predictions *worse*

The smoke showed the soft-min posterior converging on a state far from the anchor with ~180 RMSE. That
looked like a bug. It is not. A diagnostic confirmed the posterior was fully peaked (effective support
**1.0 state**, not flat), so the operator was working — it was finding a *different* optimum. So an
**exact Viterbi** over all states was added, solving the *same objective* `run_dp` approximates:

```
lam           beam cost     EXACT cost |    beam RMSE   exact RMSE
20               -597.6         -617.4 |       13.169       32.609
        exact cost lower on 38/40 wells, yet exact RMSE worse on 23/40
60               -569.7         -591.5 |       12.170       15.390
        exact cost lower on 31/40 wells, yet exact RMSE worse on 19/40
150              -554.2         -565.5 |       12.478       12.628
        exact cost lower on 25/40 wells, yet exact RMSE worse on 13/40
```

**The exact solver achieves a strictly lower objective cost — as it must — and a worse RMSE at every λ.**
The DP objective (`emission + λ·|Δstate|`) is **misaligned with the metric it is a proxy for**.

Three consequences, and they reframe three earlier rounds:

1. **The beam's greedy suboptimality is protective, not a defect.** `run_dp` scores 12.170 only because it
   *fails* to find the objective's true optimum at 15.390. Improving the solver degrades the answer.
2. **This is the mechanism behind Q54's "over-damped" observation.** Q54 measured the DP path deviating
   ±3.0 ft while truth moves ±19.4, and asked why constraints could not help. The answer: the beam is
   damped *because it is greedy*, and that damping is the only thing keeping it near the anchor. A
   constraint cannot add what greediness is already supplying.
3. **λ's real job is not what the sweeps assumed.** Note the exact-vs-beam gap *shrinks monotonically*
   with λ — 19.4 → 3.2 → 0.15 RMSE. A large λ does not "regularise the path"; it **flattens the objective's
   landscape until its true optimum coincides with what greedy search was doing anyway**. So Q10's λ=60,
   Q40's 45 penalty arms, and Q54's corridors were all tuning an objective whose exact optimum is worse
   than the approximate solver's answer.

## 4. What this closes

**Decoder averaging is closed.** The beam average is inert (six paths agreeing to 0.1 ft); the soft-min
posterior, which is the correct and general form of the operator, concentrates on an optimum that is worse
than the beam's answer. Both fail the gate.

**More broadly:** the alignment line is now closed on the emission side (Q17: AUC decoupled from DP
quality), the transition side (Q40 soft penalties, N1 per-step geometric bounds, Q54 global corridors), and
now the decoder side. The remaining lever is not a *tuning* lever at all — it would be **redefining the
objective** so that its optimum is closer to low RMSE. Nothing in the current family does that, and with
the deployed honest line at 8.8626 against this line's ~12.2, that is not a small redesign.

## 5. Limits

- One emission (TWH=1), one scorer seed, 40 eval wells, split seed shared with Q10/Q40/Q54.
- The exact Viterbi uses the same ±BAND transition support as the beam, so it is the exact optimum
  *within that support*, not over unrestricted transitions. That is the right comparison — it is the
  objective `run_dp` approximates — but it is not "the global optimum over all conceivable paths".
- The soft-min posterior is reported as its **mean**. A posterior *median* or *mode* would behave
  differently; only the mean was tested.
- γ interacts strongly with λ (at λ=20 every γ is catastrophic; at λ=150 γ=0.2 is the best number in the
  table), so the γ grid is not separable from λ and both were swept jointly and nested together.
- The 3-well 5th failing for every arm is consistent with Q41, which showed that condition is maximised by
  changing nothing at all.

## 6. Next

`q56_pf_backward_smoothing` — unaffected by any of this, since it targets the PF rather than the DP.
`q29_final_slot_candidate_packager` reactivates **2026-08-03**; the final selection action is due by
**2026-08-04** and costs no quota.
