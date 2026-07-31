# Q36 — GR-sigma widening inside the DWT+PF blend: two corrections to Q19, smoke passed, full run in flight

Date: 2026-07-29 04:45 UTC
Task: `q36_gr_sigma_in_blend_oof` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q36_gr_sigma_in_blend_oof.py`
Log: `reports/logs/q36_blend_oof_2026-07-29.log`
Outcome: **smoke PASSED; the full 760-well run is in flight (ETA ~3.7 h). No submission — the task forbids
one. Quota untouched at 0/5.**

## 1. Two corrections to what Q19 actually measured

Setting this task up surfaced that Q19's measurement was not on the path it claimed. Both errors are
mine, both are fixed here, and both matter for how the Q19 number should be read.

### Correction 1 — Q19 patched the wrong particle filter

Q19 added `_GS_MULT` to `scripts/pf_honest_forward.py`, a **standalone conservative PF: 500 particles,
ONE seed**. The honest line's PF component is not that. It is `run_pf_lik_ensemble` — a
**likelihood-weighted ensemble over `n_seeds` seeds** of `run_particle_filter` — and its source is
`SUNNY_CODE` in cell 108 of `kaggle_kernel_henry_v10_sunny80_blend`, which `scripts/pf_forward_oof.py`
execs at runtime.

This matters directly for the hypothesis under test. Q36 exists because Rule #1 says **averaging damps
tails**, and Q19's single-seed measurement had the ensemble averaging **entirely absent**. So Q19's
tail-driven failure was measured in the one configuration where no damping could occur.

### Correction 2 — Q19 scored the PF standalone, but it enters the blend at weight 0.5

Verified numerically on `aligned_preds.npz`:

```
dwt 10.2891   pf 11.0563   base 9.2987   s_54844628 8.8626
0.5*dwt + 0.5*pf  ->  9.2987      max|base - mix| = 4.9e-4  (float32 rounding)
```

`base = 0.5·dwt + 0.5·pf` exactly. Any change to the PF is therefore **halved** before it reaches the
honest line, and halved again in relevance by the structural-field stage downstream (9.2987 → 8.8626).
Q19's standalone RMSE of 14.27 on 60 wells is not the quantity that matters.

**Consequence for the Q19 headline:** its +2.3513 was measured on a single-seed standalone PF whose
baseline is 14.27, against a deployed blend baseline of 9.2987. It should not be read as a blend-level
effect size, and the Q19 report's framing overstated its relevance to the honest line.

## 2. What this script measures instead

The multiplier is applied where it actually acts — one string replacement on the **deployed** source, with
an assertion that the target line is unique:

```python
GS_SRC = "    gs = float(np.clip(np.nanstd(kn['GR'].fillna(0).values - tw_at_k), 10., 60.))"
assert funcs.count(GS_SRC) == 1
funcs = funcs.replace(GS_SRC, GS_SRC + f' * {mult!r}')     # mult=1.0 is byte-equivalent, unpatched
```

Then per well: run `run_pf_lik_ensemble(n_particles=500, n_seeds=NS, scale=5.0)` for each multiplier,
blend `0.5·dwt + 0.5·pf_new` reusing the **deployed `dwt` column unchanged**, and score against truth.

Alignment is asserted rather than assumed: the toe-row positions must equal the npz `ridx` for that well
**and** the npz truth must match the loaded truth, or the well is rejected as `MISALIGN` / `TRUTHDIFF`.
Protocol: splits **by well**; multiplier chosen **nested** (one half selects, the disjoint half scores,
both ways); per-well win rate and a **3-well bootstrap** reported, not just pooled RMSE.

## 3. Smoke — passed (Directive 4)

`MAXW=12 NS=8 MULTS=1.0,1.5`, 0.7 min:

```
wells to run 12 | MULTS [1.0, 1.5] | NS 8 | JOBS 2
done 12 wells in 0.7 min | ok=12 bad=0

multiplier     blend RMSE    vs mult=1.0
1                  7.8828         0.0000
1.5                7.8321        +0.0507
  mult 1.5   helps 16.7% of wells | mean per-well gain -0.3266 | median -0.3670

NESTED (picks [1.5, 1.0])  selected 8.0832  vs mult=1.0 7.8828  gain -0.2004
  helps 0.0% of held-out wells | 3-WELL bootstrap 5th -0.5173  50th -0.1740  95th +0.0000  P(>0) 0.0000
GATE -> FAIL
```

What the smoke establishes (it is **not** the measurement):

- **the patch activates** — 1.5 produces a different blend RMSE from 1.0, so the sigma change propagates
  through the ensemble into the blend;
- **alignment holds** — 12/12 wells passed both the `ridx` and truth-equality assertions, 0 rejected;
- **the full reporting path executes** end-to-end to the gate, which is the cell Directive 4 requires a
  smoke to reach.

An early and unsurprising hint, to be treated as provisional at 12 wells and NS=8: the pooled number
improves (+0.0507) while the **per-well** picture is negative (helps 16.7%, mean −0.3266). That is the
same tail-driven signature Q19 found, now visible inside the blend. Whether ensembling at NS=32 over 760
wells damps it is exactly what the full run decides.

## 4. Full run — in flight

```
MAXW=760  NS=32  JOBS=2  MULTS=1.0,1.3,1.5
progress: 14 wells / 4.1 min  ->  ETA ~3.7 h
```

Cost note: this box has **2 cores**, and the deployed line uses **NS=64** while this run uses **NS=32**
(the `pf_forward_oof.py` default) to keep the wall time near 3.7 h rather than ~7.5 h. More seeds means
more averaging, so **NS=32 understates the ensemble damping** relative to deployed — i.e. the choice is
conservative in the direction that matters: if the multiplier passes at NS=32 it should also pass at
NS=64, and if it fails at NS=32 that is weaker evidence against it than a NS=64 failure would be. This
deviation from the deployed configuration is recorded here rather than left implicit.

## 5. Gate, restated for whoever collects this

Promote only if **all three** hold: nested gain > 0 **and** 3-well bootstrap 5th percentile > 0 **and** it
helps a **majority** of wells. A tail-driven pooled gain does not pass. `q37_frontier_gr_sigma_public_repro`
remains blocked behind this result; per Q33 the next 24 h spends **0 slots unless this gate passes**.

## 6. Limits

- The result is not in yet. Nothing here should be read as the finding; §3 is a smoke.
- NS=32 vs the deployed NS=64, as recorded in §4.
- The measurement is at the **blend** level (`base`), not after the structural-field stage that takes the
  honest line to 8.8626. A multiplier effect surviving into the blend would still have to survive that
  gated stage.
- 760 of 773 wells: 13 are absent from `aligned_preds.npz` and are excluded so the deployed `dwt` column
  can be reused unchanged.

## 7. Next

Collect `reports/logs/q36_blend_oof_2026-07-29.log` (~3.7 h from 04:45 UTC), apply the §5 gate, and
either release or close `q37`.

## RESULT — collected 2026-07-29 08:30 UTC. GATE FAILS.

The 760-well run finished in 211.0 min, **760/760 wells usable, 0 rejected** — every well passed both the
`ridx` and truth-equality assertions.

```
multiplier     blend RMSE    vs mult=1.0
1                  9.2903         0.0000
1.3                9.1204        +0.1699
1.5                9.3203        -0.0300
  (deployed blend `base` = 9.2987; honest line after the structural field = 8.8626)
  mult 1.3   helps 42.1% of wells | mean per-well gain -0.1197 | median -0.0569
  mult 1.5   helps 40.4% of wells | mean per-well gain -0.3830 | median -0.1438

NESTED (picks [1.3, 1.3])  selected 9.1204  vs mult=1.0 9.2903  gain +0.1699
  helps 42.1% of held-out wells
  3-WELL bootstrap 5th -1.6429  50th -0.1129  95th +1.5381  P(>0) 0.3981
```

**Reconstruction check:** `mult=1.0` gives 9.2903 against the deployed `base` of 9.2987 — a 0.008
difference, attributable to NS=32 here versus NS=64 deployed. The pipeline is faithfully reproduced.

### Gate

| condition | required | observed | verdict |
|---|---|---|---|
| nested gain | > 0 | **+0.1699** | PASS |
| 3-well bootstrap 5th | > 0 | **−1.6429** | **FAIL** |
| helps a majority of wells | > 50% | **42.1%** | **FAIL** |

**Two of three fail. No frontier run, no submission.** Per Q33 this settles the budget question: the next
24 h spends **0 slots**. `q37_frontier_gr_sigma_public_repro` is **closed**, not merely blocked — its
release condition was this gate.

### The interesting part: the optimum moved to exactly the public kernel's value

Q19's standalone single-seed measurement put the optimum at **1.5**. Inside the ensemble and the blend,
**1.5 is harmful (−0.0300) and 1.3 is optimal (+0.1699)** — and 1.3 is precisely the constant the public
6.213 kernel uses. The public author's choice is the right one *for the deployed configuration*, which
Q19's setup could not have seen.

### What the ensemble damping did and did not do

| | Q19 standalone, 1 seed | Q36 in-blend, NS=32 |
|---|---|---|
| nested gain | +2.3513 | **+0.1699** |
| 3-well bootstrap 5th | −4.1145 | **−1.6429** |
| **% of wells helped** | **41.7%** | **42.1%** |

Rule #1 predicted that averaging would damp the tail. It did — the effect size shrank ~14× and the tail
risk more than halved. **But the fraction of wells helped is unchanged.** So the ensembling damped the
*magnitude* while leaving the *sign structure* intact: the multiplier helps the same minority of wells
either way, and hurts the majority a little. Both the mean (−0.1197) and median (−0.0569) per-well gains
are negative while the pooled gain is positive — the asymmetric-tail signature the ledger records before
the `54878409` public regression.

That is the substantive answer to the question Q36 was created to ask: **averaging damps magnitude, not
sign structure**, so it cannot rescue a change that helps a minority of wells.
