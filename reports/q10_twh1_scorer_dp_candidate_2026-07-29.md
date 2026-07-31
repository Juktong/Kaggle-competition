# Q10 — TWH=1 scorer as a DP emission, 2026-07-29

Autopilot task `q10_twh1_scorer_dp_candidate` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). Script: `scripts/q10_twh1_scorer_dp.py`. Logs:
`reports/logs/q10_twh1_dp_2026-07-29.log`, `reports/logs/q10_lam_extension_2026-07-29.log`.

**Result: the alignment line's first nested-validated win over the flat anchor — and it still does not
qualify for a submission.** The TWH=1 emission takes the DP from 13.206 to **12.170**, crossing below the
flat anchor's 12.722. But the task's gate is *beats flat AND materially narrows the gap to deployed*, and
at 12.170 against the deployed honest line's **~8.86** the candidate remains ~37% worse. No Kaggle smoke
was prepared, no submission made; quota untouched at **0/5**.

## 1. What this tests

N3 measured an **emission** improvement: narrowing the typewell window from TWH=8 (17 ft) to TWH=1 (3 ft)
raised held-out-WELL scorer AUC from 0.7300 ± 0.0028 to 0.7655 ± 0.0030.

N1 measured, with a TWH=8 emission, that the beam DP **does not** beat the flat anchor once the transition
hyper-parameter is chosen nested (13.644 vs 12.722, beating flat on 37.5% of wells), and concluded that
*the gap is in the transition model, not the emission*.

Q10 is the direct one-factor test of that conclusion: hold the DP, the wells, the protocol and the nesting
fixed; change only the emission's TWH.

Protocol fixed by the standing rules established this round — splits **by well** never by pair (N3),
**40 eval wells** (N1: a 12-well set manufactured a gain that vanished at 40), and every transition
hyper-parameter chosen **nested** (selected on one half of the eval wells, scored on the disjoint half,
both ways).

## 2. Result

```
TWH    held-out AUC    nested DP    flat-anchor    beats flat on
 1          0.7632       12.170         12.722            42.5%
 8          0.7331       13.206         12.722            40.0%
N1 reference (TWH=8, same protocol):  13.644  vs  12.722            37.5%
```

**A +0.030 AUC emission improvement converts into −1.04 RMSE on the DP and flips the flat-anchor
comparison from lose to win.** Both nested folds agree — fold 1: DP 13.212 vs flat 13.540; fold 2: DP
11.029 vs flat 11.847 — so this is not a single-fold artifact.

The TWH=8 arm reproduces N1's finding (13.206 here vs N1's 13.644; the small difference is that Q10 seeds
the pair sampler while N1 used the global RNG). Both fail to beat flat, as N1 recorded.

### The selected λ was at the grid edge, so the grid was extended

Both folds picked λ=60, the largest value in the original grid, and the sweep was monotone toward it —
which would leave the optimum unresolved. Extending to λ=800:

```
lam        60      100      150      250      400      800     flat
DP     12.170   12.241   12.478   12.461   12.987   13.132   12.722
```

**λ=60 is a genuine interior optimum.** Note the DP does not degenerate to the flat anchor as λ grows
(13.132 at λ=800, slightly *worse* than flat) — even a large movement penalty leaves the beam taking the
argmin of a finite candidate set, so it never reduces exactly to carrying the anchor forward.

Re-running the nesting over the extended grid gives DP **12.444** vs flat 12.722 — still a win, but
smaller. **The margin is grid-sensitive**: 0.55 ft (4.3%) on the 1–60 grid, 0.28 ft (2.2%) on the 60–800
grid. Adding candidates to the selection grid degraded the nested estimate, which is ordinary selection
noise and a direct measure of how fragile the margin is.

## 3. Why it is still not submittable

Three independent reasons, any one of which is sufficient:

1. **The gate is an AND, and the second half fails.** "Beats flat **and** materially narrows the gap to
   deployed." 12.170 vs deployed ~8.86 is ~37% worse. Nothing about this candidate is close to the
   deployed honest line, standalone or as a component.
2. **The win is tail-driven.** It helps 16–17 wells and hurts 23–24 of 40 — the pooled gain comes from a
   few large wins (up to +4.8) outweighing many small losses. That is the exact signature the ledger
   records before the `54878409` public regression: *"the pooled +0.18 is an asymmetric tail, not a broad
   shift"*. A candidate that is worse on the majority of wells is not one to spend a slot on, especially
   given N4's measurement that a fixed model's own 3-well draw already spans 3.49 → 15.14.
3. **The margin is smaller than the grid sensitivity.** 0.28–0.55 ft of nested advantage against a
   selection-noise effect of the same order.

The 3-well gate was not run, and deliberately so: that gate exists to decide whether a candidate improves
on the deployed line. This one is ~37% below it, so the question does not arise.

## 4. Failure structure by well family

Mean per-well gain grouped by the deployed typewell group key (`round(max(typewell.TVT), 1)`), eval wells
with ≥2 members:

```
gkey        n   mean_gain            gkey        n   mean_gain
11366.5     3     -1.775             12051.8     4     +0.232
11592.0     2     -0.843             11122.5     2     +0.700
12157.0     2     -0.784             10881.6     3     +0.970
11537.4     5     -0.780             11350.9     3     +1.025
11594.5     3     -0.146             12182.0     2     +1.492
                                     12874.7     2     +2.173
```

**There is real family structure** — the spread runs from −1.78 to +2.17 and is consistent in sign within
most groups. That is a genuine observation, but it is **not actionable**: n = 2–5 wells per group, and a
per-group router is precisely the hard-selection pattern the ledger has closed repeatedly (*"averaging and
shrinkage transfer; hard selection and fitted weights do not"*, and the router oracle +1.49 vs honest
−0.61). Recorded, not queued.

Worst individual wells: `3d96d897` (−4.45), `c96c018a` (−3.65), `7ff89f8f` (−3.45).
Best: `e25f1537` (+4.84), `2fa01aa6` (+4.76), `bd4ae5da` (+4.65).

## 5. What this revises in the ledger

N1 concluded that *"the gap is in the transition model, not the emission"*. Q10 **partially revises**
that. The measurement N1 made was correct for its TWH=8 emission, but the generalisation was too strong:
a better emission moved the DP by 1.04 RMSE and crossed the flat-anchor line that N1's emission could not.
**The emission does matter, and it had not been saturated.**

What survives from N1 unchanged is the practical conclusion: the DP family remains far from the deployed
honest line, and no member of it is a submission candidate. Both statements are now on the record with the
numbers behind them.

## 6. Verdict

- **No Kaggle smoke, no submission.** Task step 5's condition ("beats flat **and** materially narrows the
  gap to deployed") is not met; step 6 therefore does not trigger. Quota untouched at 0/5.
- **Banked positive:** the first nested-validated, both-folds-consistent win over the flat anchor in the
  alignment line (12.170 vs 12.722, λ=60 an interior optimum), together with the finding that emission
  quality was not saturated.
- **Open and now better-posed:** the remaining 12.17 → 8.86 gap. Emission improvements move it ~1 RMSE per
  +0.03 AUC; closing 3.3 RMSE on that exchange rate would need an implausible AUC, so the next real lever
  is still the transition model — but N1's version of that claim was overstated and is corrected above.
- Slot recommendation unchanged: `54922806` + `54844628` under all three criteria.
