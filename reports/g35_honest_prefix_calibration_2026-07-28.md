# G3.5 — honest prefix calibration for `54844628` (2026-07-28)

Autopilot task `g35_honest_prefix_calibration` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). **Outcome: closed on evidence. No Kaggle run, no submission, 0 quota used.**
Tool: `scripts/g35_prefix_cut_smoke.py`.

## Static audit — what `54844628` already does

```
base   = 0.5*DWT + 0.5*PF
output = base, with 0.85*base + 0.15*struct on gated rows
gate   = nnb >= 4 AND closest SURVIVING mate < 1000 ft   (87% of rows)
```

The structural field **already anchors on the target's own last 100 known heel rows**
(`anchor = mean(r_true − r_pred)` over those rows). So plain heel-level anchoring is not an available
improvement — it is already in the deployed pipeline.

The mechanism the honest line does **not** have is the frontier's **prefix-cut self-calibration**: cut
the well's own known prefix, predict the held-out part of it, and use that measured error to calibrate a
bounded correction on the toe. It uses only the well's own known heel, so it is private-compatible and
carries no train-copy lookup.

## Decisive prerequisite, tested before building anything

> Does a well's error on a held-out slice of its **own** known prefix predict its error on the **toe**?

Per well: cut the known prefix at `CUT`; re-run the PF forward with only `K_cal` known; measure the error
on the held-out prefix slice (the signal available at inference) and the error on the toe (the target).

**A confound had to be separated first.** If the signal and the target are both taken from the *same
truncated run*, they share the degradation caused by having a shorter prefix, which inflates the
correlation. The deployment-honest pairing is: signal from the **truncated** run (that is what inference
can compute), target from the **full-prefix** run (that is the error a correction must fix).

## Result (30 train wells, PF forward, both cut fractions)

```
CUT = 0.70   held-out median 493 rows | toe median 5182 rows
  [confounded]  corr(bias_hold, bias_toe from the SAME truncated run) = +0.6589  -> 43.4%
  [deployment]  corr(bias_hold, bias_toe from the FULL-prefix run)    = +0.1862  ->  3.5%
  corr(drift_hold, drift_toe) = +0.1431 -> 2.0%
  best scalar a=0.408: toe-bias std 7.632 -> 7.500; variance removed 3.4% (IN-SAMPLE upper bound)

CUT = 0.50
  [confounded]  +0.3762 -> 14.1%
  [deployment]  +0.0735 ->  0.5%
  corr(drift_hold, drift_toe) = +0.1433 -> 2.1%
  variance removed 0.4% (IN-SAMPLE upper bound)
```

**The apparent signal is almost entirely the confound.** Separating the runs drops the explained variance
from 43.4% → 3.5% (CUT 0.70) and 14.1% → 0.5% (CUT 0.50). What remains is an *in-sample* upper bound of
3.4% / 0.4% of toe-bias variance, fitted on the same 30 wells — a nested or bootstrapped estimate would
sit at or below zero. Both cut fractions agree.

For reference, the 2026-07-21 per-well bias analysis found the raw heel level explains ~5% (first 100
rows) to ~17% (first 500 rows) of whole-well bias variance. The prefix-cut signal does **not** beat that;
it is weaker.

## Why the mechanism is thin here

The residual is a **smooth per-well drift** accumulated along the toe (slope std 13.28 ft vs initial level
offset std 4.72 ft, measured 2026-07-21). A prefix cut can only observe the pipeline's behaviour inside
the *known heel*, which is before that drift accumulates — and `drift_hold → drift_toe` correlates at only
+0.14. The deployed anchor already removes the part of the level offset that the heel does expose.

## Disposition

**G3.5 closed on evidence. No variant was built, no Kaggle smoke or full run was launched, no submission
was made, 0 of today's 5 quota used.** The submit gate was never reached because step 3 (local smoke) did
not produce a coherent improvement to carry forward.

`54844628` is unchanged and remains the slot-2 recommendation under all three criteria.

### Transferable finding (worth carrying into any future calibration work)

**Never measure a calibration signal and its target on the same truncated run.** Doing so inflated the
apparent correlation by 3–4× here (0.659 vs 0.186; 0.376 vs 0.074). Any prefix-calibration design — ours
or the frontier's — must pair a truncated-run signal with a full-prefix target, or it will report a
signal that does not exist at inference. This is consistent with what the frontier's own calibration does
in practice: G1.2 found its selected `balanced` profile applied `alpha = 0.0` (no movement at all), and
`54990075` showed the post-SP45 stages as a whole are only mildly useful on public.
