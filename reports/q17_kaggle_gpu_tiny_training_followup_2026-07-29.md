# Q17 — Kaggle GPU tiny training follow-up: HOLD, closed on its prerequisite

Date: 2026-07-29
Task: `q17_kaggle_gpu_tiny_training_followup` (`requires_gpu=true`, `can_submit=true`, `max_submit_cost=1`)
Script: `scripts/q17_emission_exchange_rate.py`
Log: `reports/logs/q17_emission_exchange_2026-07-29.log`
Outcome: **HOLD — no Kaggle GPU run, no smoke kernel, no submission. Quota untouched at 0/5.**

## 1. Step 1 — live refresh of Q10 / Q11 / Q13

| task | result | signal for training? |
|---|---|---|
| **Q10** TWH=1 scorer as DP emission | first nested-validated win over the flat anchor, 12.170 vs 12.722, both folds agree | **yes, narrowly** — but its own arithmetic says the emission lever cannot close the gap |
| **Q11** TWH=1 PF seed / path ranker | **every ranker arm worse than the PF mean path**; first reliably *negative* achievable margin | no |
| **Q13** hybrid emission | emission clearly better pointwise (−36.3 ft argmax error, helps 67.5% of wells) yet the trajectory gets **worse** through the DP | no — and it is a warning |

Q17's step 2 says to HOLD if none show a real signal. Q11 and Q13 are negative, so the whole case rests
on Q10. Q10's own verdict already reads: *"closing 3.3 RMSE on that exchange rate would need an
implausible AUC, so the next real lever is still the transition model."*

That verdict rests on an exchange rate estimated from exactly **two points** (TWH=8: AUC 0.7331 → DP
13.206; TWH=1: AUC 0.7632 → DP 12.170), i.e. ~1 RMSE per +0.03 AUC. A two-point slope is a weak basis for
a 3.3 RMSE extrapolation, and it is precisely the premise Q17 would spend a GPU run on. So the premise was
measured directly instead — at **zero GPU cost**.

## 2. Method — replace the two-point slope with the whole curve

There is no local GPU on this box (`nvidia-smi` absent), so any training would consume a Kaggle GPU run.
Before spending one, interpolate the learned TWH=1 emission toward an **oracle** emission and sweep:

```
C_mix(α) = z( (1−α)·z(C_learned) + α·z(C_oracle) ),    C_oracle[j,s] = |grid[s] − tru[j]|
```

Lower `C` is better in this DP, so `C_oracle` is a perfect emission. Sweeping α from 0 to 1 walks the
emission continuously from what we actually have to perfect, measuring at each step both the held-out-WELL
pair AUC (Q10's negative-sampling protocol, so the axis is comparable to N3's and Q10's numbers) and the
nested DP trajectory RMSE (Q10's DP, wells, protocol and 2-fold nesting reused verbatim via import).

Protocol inherited unchanged: splits **by well**, **40 eval wells**, λ chosen **nested**.

**Smoke first** (Directive 4): `SMOKE=1 MAXW_TRAIN=20 MAXW_EVAL=6 ALPHAS=0,0.5,1.0 LAMS=5,60` ran
end-to-end in seconds, monotone and sane (α=1 → AUC 0.9844, DP 3.279 vs flat 10.533), and its α=0 AUC
0.6920 matched Q10's own `scorer_auc` on the same tiny config (0.6908) — confirming the AUC axis is the
same quantity Q10 and N3 report. Full run then scaled to 60 train / 40 eval wells.

**Reproduction check:** at α=0, λ=60 the DP gives **12.170** — exactly Q10's headline number.

## 3. Result — nested

```
alpha         AUC    nested DP       flat  beats flat %      lam picks
0          0.7511       12.601     12.722         37.5%         60/150
0.025      0.7546       12.599     12.722         37.5%         60/150
0.05       0.7585       12.542     12.722         37.5%         60/150
0.1        0.7671       12.539     12.722         37.5%         60/150
0.15       0.7772       12.029     12.722         45.0%          60/60
0.2        0.7881       12.598     12.722         42.5%           5/60
0.3        0.8074       14.205     12.722         45.0%           60/1
0.5        0.8088        9.903     12.722         72.5%            5/1
0.75       0.8715        3.506     12.722         92.5%            1/1
1          0.9688        0.370     12.722        100.0%            1/1
```

The λ picks are unstable across α (60/150 → 5/60 → 60/1), so the flatness at low α could be nesting noise
rather than a property of the system. That required a control.

## 4. Control — fixed λ, no selection at all

```
alpha        AUC     lam=1    lam=5   lam=20   lam=60  lam=150  lam=400
0         0.7511    34.169   16.009   13.169   12.170   12.478   12.987
0.025     0.7546    26.175   16.022   12.935   12.168   12.468   12.987
0.05      0.7585    23.718   15.926   12.877   12.168   12.408   12.987
0.1       0.7671    20.382   13.318   12.784   12.166   12.406   12.983
0.15      0.7772    19.088   13.106   12.712   12.029   12.465   12.517
0.2       0.7881    17.706   12.541   12.662   12.022   12.451   12.527
0.3       0.8074    13.902   12.613   12.507   12.003   12.445   12.631
0.5       0.8088     9.138    8.932   11.863   12.150   12.379   12.966
0.75      0.8715     3.506    8.338   11.430   12.185   12.571   12.587
1         0.9688     0.370    3.842    8.565   11.127   12.478   12.787
flat-anchor 12.722
```

At **fixed λ=60**, with no selection anywhere:

| AUC | 0.7511 → 0.8074 | change |
|---|---|---|
| DP RMSE | 12.170 → 12.003 | **−0.167** |

**+0.056 AUC — nearly double the TWH=8→TWH=1 step Q10 measured — buys 0.167 RMSE.** That is
**0.030 RMSE per +0.01 AUC**, against Q10's two-point estimate of 0.344. The real exchange rate at the
operating point is **more than 11× shallower** than the extrapolation basis, and the control shows this is
a property of the DP, not of the λ nesting.

Extrapolating honestly at the measured rate, closing 12.170 → 8.8626 (3.31 RMSE) would require
**+1.11 AUC** — an AUC of 1.87. The emission lever cannot close the gap, and this is now measured rather
than inferred from two points.

## 5. The load-bearing finding: AUC is not the quantity the DP responds to

The two axes decouple, and the control makes it unambiguous:

| segment | ΔAUC | ΔDP (λ=60) |
|---|---|---|
| α 0 → 0.3 | **+0.0563** | −0.167 |
| α 0.3 → 0.5 | **+0.0014** | **−3.071** |

Between α=0.3 and α=0.5 the AUC barely moves (+0.0014) while the DP improves by 3.07 RMSE. Between α=0
and α=0.3 the AUC rises 40× more and the DP barely moves. **The DP responds to how much literal truth is
mixed into the emission, not to the emission's discriminative AUC.**

This also explains the mechanism cleanly. Changing TWH alters the emission's *shape* over the typewell,
not only its discriminative quality; Q10's 1.04 RMSE gain came from that structural change, and attaching
it to the accompanying AUC movement produced a slope that does not generalise. The α-sweep isolates pure
discriminative quality at fixed structure, and it is nearly flat.

**New standing rule (proposed):** *emission AUC is not a valid proxy for DP trajectory quality; an
emission change must be validated on its DP output, not on AUC or any pointwise emission metric.* This
subsumes the rule Q13 produced (a pointwise emission metric is not a valid proxy when the modification
carries a directional bias) — Q13 and Q17 are two instances of the same failure, now with the mechanism
measured on a continuous axis.

## 6. Verdict against Q17's own steps

- **Step 2 (HOLD if no real signal):** Q11 and Q13 are negative. Q10's signal is real but its training
  premise is now measured and does not hold: the quantity a learned scorer would improve (AUC) is ~11×
  less effective than assumed and is decoupled from the objective.
- **Step 3 (prepare a tiny Kaggle GPU smoke):** **not triggered.** A tiny learned scorer would improve
  AUC — the exact axis just shown not to move the DP. Spending a Kaggle GPU run on it is not warranted.
- **Step 4 (expand only if the smoke improves held-out-WELL metrics):** moot.
- **Step 5 (submit only after full audit and gate):** no candidate reached the gate. **No submission.**

**Task marked HOLD.** The ranker half of Q17 was already closed by Q11 (every arm worse than the PF mean
path), so both halves of the proposal are resolved.

## 7. Negative results and limits, stated plainly

- The oracle emission is truth-constructed. It is used here **only as a bound and as a continuous axis**,
  never as a claimed gain — the achievable end of the axis is α=0.
- α is not a linear proxy for "a better model": mixing in truth improves the emission in a specific,
  truth-aligned way that a real scorer would not reproduce exactly. This makes the measurement, if
  anything, **generous** to the training case — real AUC gains are unlikely to be better aligned with
  truth than literal truth is, so the true exchange rate is at best the one measured.
- The nested α=0 result here is 12.601 vs Q10's 12.170/12.444, because the λ grid differs
  ({1,5,20,60,150,400} vs Q10's two grids). This *reinforces* Q10's own recorded observation that the
  margin over flat is grid-sensitive and fragile: on this third grid the TWH=1 win over flat is 0.12 RMSE
  and beats flat on only **37.5%** of wells — the same fraction N1 recorded for TWH=8.
- This measures the emission lever only. It says nothing against the transition model, which Q10 and N1
  both identify as the remaining lever and which remains untested at this scale.

## 8. Live-refresh notes

- `origin/main` (Marc0823) moved: `a589fa8 Add reproducible public 6.626 ROGII kernel`. Recorded only —
  6.626 is worse than our best own-account public 6.563 (`54922806`), and no decision is taken on it.
- `55064411` remains **PENDING** (~5.5 h). Kernel status is `COMPLETE, failureMessage null`, so the stall
  is Kaggle-side. Not resubmitted.
- Quota: the UTC day rolled over, so today is **0/5 used, 5 remaining**. This task consumed none.
- No local GPU (`nvidia-smi` absent); no Kaggle kernel launched by this task.

## 9. Next

`q18_public_leaderboard_family_stress`. `q15_frontier_dependency_replacement` remains blocked on the same
condition as before — it needs its own frontier full run, and `55064411`'s kernel re-run is still in
flight.
