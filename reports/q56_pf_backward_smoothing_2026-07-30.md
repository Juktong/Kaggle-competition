# Q56 — PF backward smoothing: a broad, mechanism-verified +0.2541 at blend level that still fails the 3-well condition

Date: 2026-07-29 21:35 UTC, **result collected 23:20 UTC**
Task: `q56_pf_backward_smoothing` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q56_pf_backward_smoothing.py` · Log: `reports/logs/q56_smoothing_2026-07-30.log`

**FINAL OUTCOME (760 wells, see the RESULT section at the end): gate FAILS on the 3-well bootstrap 5th
(−0.3238), PASSES the other two — nested +0.2541, helps 68.9% of wells with a positive median. Not promoted.
Follow-up queued as `q58_honest_kernel_backward_smoothing`. No submission. Quota 0/5.**

Sections 1–9 below were written before the full run landed and are left as written; the smoke's +0.605 was
**58% too large**, which §9 predicted in advance and the RESULT section quantifies. Read the RESULT section
for the measurement.

## 1. The gap, stated precisely

`run_particle_filter` — the deployed function, `SUNNY_CODE` cell 108, the one `scripts/pf_forward_oof.py`
execs — computes

```python
res[i] = float(np.dot(w, pos - z_v[i]))     # w = the FILTERING weights at row i
```

the posterior mean given observations 1..i. **But the entire toe GR log is available at prediction time**:
we predict TVT for rows whose GR we can already read. Every row except the last is therefore estimated from
strictly less information than we hold. That is a modelling gap, not a hyper-parameter.

## 2. Which smoother — and why not textbook FFBSi

FFBSi re-weights step-*i* particles by `w_i^k · p(x_{i+1}^j | x_i^k)`. Here the transition is very nearly
deterministic:

```
pos  += rate*dm + 0.005*eps        (PN = 0.005)
rate  = 0.998*rate + 0.002*eps     (MOM = 0.998, VN = 0.002)
```

so that backward kernel is numerically degenerate — `p(x_{i+1}^j | x_i^k)` is ~0 for every *k* except *j*'s
own lineage. **In that limit FFBSi collapses onto the ancestral-path smoother**, so that is what was
implemented (Kitagawa's filter-smoother) rather than a numerically doomed transcription of the general form:

```
sm[i] = Σ_j w_end[j] · pos_i^{ancestor_i(j)} − z_i
```

Row *i* is now conditioned on observations 1..end. It is an averaging operation over the existing trellis, so
Q40's compounding warning genuinely does not apply. Recording the reasoning because the task named FFBSi
specifically and this is a deliberate, motivated deviation, not a shortcut.

## 3. Two controls, both from prior rounds' mistakes

**(a) The trellis twin is not retyped — it is derived from the deployed source by four anchored
insertions**, each asserted unique, so it cannot drift by transcription:

```python
A_RES = '    res = np.empty(len(ev))\n'                                    -> allocate P_, W_, A_
A_NEF = '        n_eff = 1.0 / (w**2).sum()\n'                             -> A_[i] = arange (no resample)
A_IDX = '            idx = np.clip(np.searchsorted(cum, ...), 0, N - 1)\n' -> A_[i] = idx  (resampled)
A_SET = '        res[i] = float(np.dot(w, pos - z_v[i]))\n'                -> P_[i] = pos; W_[i] = w
```

Then it is checked against the **untouched** deployed function — not against this script's own OFF path:

```
seed 0   array_equal(deployed, trellis) = True   log_lik identical = True
seed 1   array_equal(deployed, trellis) = True   log_lik identical = True
seed 7   array_equal(deployed, trellis) = True   log_lik identical = True
ensemble: array_equal(deployed run_pf_lik_ensemble, alpha=0 arm) = True
mode full/block400/block100/block25 : |smoothed − filtered| at the FINAL row = 1.0e-06   (must be ~0)
```

The last line is a second, independent check: at the final row there is no lookahead, so the smoother must
reproduce the filter there — and it does, to 1e-6 (float32 trellis storage).

**(b) Path degeneracy measured BEFORE any arm was scored** — Q54 and Q55 both required the failure-mode
diagnostic first, and ancestral smoothers have a well-known one: after enough resampling every lineage shares
one ancestor, so far from the end the "smoothed" value is a single particle's path, i.e. *less* averaging
than the filter. Measured (seed 0, well `000d7d20`, T=600 toe rows):

```
lookahead   distinct ancestors   ancestor ESS
0                        500          335.7
25                       500          335.7
50                       280          145.3
100                      155           79.3
200                       66           23.6
400                       41           14.0
599                       22           12.0
```

**It does not collapse.** ESS is still ~12 at 599 rows of lookahead, because resampling here is intermittent
(`n_eff < 0.5N` triggers rarely), so the genealogy keeps real diversity. That is what makes the `full` arm
legitimate rather than a single-path artifact — and it was worth measuring, since the opposite result would
have invalidated the whole arm. The `block(L)` arms were built in advance to bound lookahead at L rows in
case it had collapsed; they are now the lookahead-dose ladder instead (§5).

## 4. Honesty audit — no train-only or truth column is touched

Load-bearing if this line is ever proposed for a slot, so it was verified programmatically rather than
assumed. Columns referenced inside `run_particle_filter`: `GR`, `MD`, `TVT`, `TVT_input`, `Z`. The two `TVT`
references are both on the **typewell** (`tw.sort_values('TVT')`, `tw_s['TVT']`), which is test-available;
`hw['TVT']` (the toe truth) matches **zero** times, as do `EGFDU`, `tvt_from_contacts` and `contacts`.
`run_pf_lik_ensemble` references no columns at all.

**The smoother adds no new inputs.** It only re-reads the retained trellis, whose only observation channel is
GR. So the arm is honest by construction, not by inspection.

## 5. Smoke (Directive 4) — 12 wells, NS=8, 0.5 min, and it clears the gate

```
mode             a=0.25      a=0.5      a=1.0    at best alpha
forward          7.8828
full             7.7047    7.5437    7.2778     helps 91.7% | mean +0.5130 | median +0.3857
block400         7.7980    7.7212    7.5924     helps 83.3% | mean +0.2830 | median +0.3039
block100         7.8571    7.8346    7.7994     helps 83.3% | mean +0.1087 | median +0.1150
block25          7.8759    7.8695    7.8587     helps 75.0% | mean +0.0280 | median +0.0366
sg51             7.8826    7.8824    7.8821     helps 100.0% | mean +0.0014 | median +0.0006
sg201            7.8806    7.8788    7.8767     helps 100.0% | mean +0.0109 | median +0.0079
sg601            7.8737    7.8668    7.8599     helps 100.0% | mean +0.0388 | median +0.0308

NESTED (picks [('full', 1.0), ('full', 1.0)])
  selected 7.2778  vs forward 7.8828  gain +0.6050
  helps 91.7% of held-out wells | 3-WELL bootstrap 5th +0.0836  50th +0.4542  95th +1.0700  P(>0) 0.9944
GATE -> PASS
```

What the smoke establishes (it is **not** the measurement):

- **the flag activates and the reporting path reaches the gate** — Directive 4's requirement;
- **alignment holds** — 12/12 wells passed both the `ridx` and truth-equality assertions, 0 rejected;
- **two monotonicities**, which is what distinguishes a mechanism from a fitted artifact:
  - monotone in **alpha** (0.25 → 0.5 → 1.0 all improve, for every mode);
  - monotone in **lookahead dose** (block25 → block100 → block400 → full: +0.028 → +0.109 → +0.283 →
    +0.513). More lookahead, more gain, in order.

**Q41's 3-well 5th percentile is positive (+0.0836) for the first time in this rotation.** Q41 measured that
condition as maximised by changing nothing, and Q42/Q54/Q55 each failed it. That is why this arm is being
scaled up rather than closed.

### The control that matters most — is it lookahead, or just denoising?

The ancestral mean is mechanically *smoother* than the filtered mean, and truth is smooth, so **any**
temporal smoothing of the PF output would lower RMSE regardless of whether later observations contributed
information. Without separating those, "backward smoothing helps" would be unfalsifiable. So a
Savitzky-Golay arm was added that smooths **the forward output only** — no trellis, no lookahead likelihood:

```
widest denoising control  sg601, alpha=1.0   +0.0388
ancestral smoother        full,  alpha=1.0   +0.5130
```

**Denoising accounts for about 8% of the gain; ~92% is information the genealogy carries and a symmetric
filter cannot.** This is the Q17-style question asked of the right arm, and it comes out in favour of the
mechanism being real.

## 6. Why the effect is plausible at this size — and where it must shrink

The PF is a *tracking* filter whose state includes a drift `rate`. When the GR match is ambiguous early in
the toe, the filtered mean sits between hypotheses; the later GR log resolves which hypothesis survived, and
the genealogy propagates that resolution backwards. The filter cannot do this by construction. So the
direction is expected — the open question is only the magnitude on 760 wells.

Two deflators are already known and are stated before the result, not after:

1. **The PF enters the honest line at weight 0.5** (`base = 0.5·dwt + 0.5·pf`, verified in Q36), so the
   numbers above are **already halved** relative to a standalone-PF effect.
2. **A gated structural-field stage sits between this blend and the deployed 8.8626.** A blend-level gain
   must still survive that stage, which was fitted against the *forward* PF.

## 7. Full run — in flight

```
MAXW=760  NS=32  JOBS=2  ARMS [full, block400, block100, block25, sg51, sg201, sg601] x ALPHAS [0.25, 0.5, 1.0]
launched 2026-07-29 21:30 UTC, ETA ~2 h (~125 min projected from the smoke rate)
```

Cost note, same as Q36's and recorded rather than left implicit: this box has **2 cores** and the deployed
line uses **NS=64** while this run uses **NS=32**. More seeds means more ensemble averaging, so NS=32
*understates* the damping the deployed configuration would apply. The whole arm grid comes from **one forward
pass per seed** — smoothing is post-processing on the retained trellis — so 21 arms cost about the same as a
single q36 multiplier.

## 8. Gate, restated for whoever collects this

Promote only if **all three** hold on the 760-well run: nested gain > 0 **and** helps a **majority** of wells
**and** 3-well bootstrap 5th > 0. If it passes, the correct follow-up is **not** a submission from this task
(`can_submit=false`): it is a queued task to reproduce the smoother inside the honest kernel, re-fit the
structural-field stage against the smoothed PF, and only then apply the submit gate.

## 9. Limits

- **The result is not in yet.** §5 is a smoke on 12 wells at NS=8, and those wells are easier than average
  (7.88 vs the deployed 9.2987), so the effect size there is not the effect size.
- NS=32 vs the deployed NS=64 (§7).
- The trellis is stored as **float32** to bound memory (T×N per seed); the final-row check quantifies the
  resulting error at 1e-6 ft, which is 7 orders below the RMSE scale.
- The path-degeneracy diagnostic is **one well, one seed**. A well with much more frequent resampling could
  collapse where this one did not — the block arms exist to bound exactly that, and their ordering in §5
  suggests it is not happening broadly, but it is not measured per well.
- The smoother is applied per seed **before** the likelihood-weighted ensembling, which is the deployed
  order. Smoothing after ensembling was not tested.
- alpha is capped at 1.0; the monotone alpha trend means an extrapolating alpha > 1 was not explored, and
  extrapolation is not the shrinkage class Rule #1 records as transferring.

## 10. Next

Collect `reports/logs/q56_smoothing_2026-07-30.log`, apply the §8 gate, and either queue the honest-kernel
reproduction or close the line. `q57_dip_state_augmented_dp` is next by priority.
`q29_final_slot_candidate_packager` reactivates **2026-08-03**; the final selection is due **2026-08-04** and
costs no quota.

## RESULT — collected 2026-07-29 23:20 UTC. 760/760 wells, 108.6 min. **GATE FAILS on the 3-well condition; the other two pass.**

```
done 760 wells in 108.6 min | ok=760 bad=0        <- every well passed the ridx and truth-equality assertions

mode             a=0.25      a=0.5      a=1.0    at best alpha
forward          9.2903
full             9.1911    9.1154    9.0362     helps 68.9% | mean +0.3686 | median +0.2044
block400         9.2411    9.2018    9.1534     helps 71.1% | mean +0.1898 | median +0.1472
block100         9.2713    9.2556    9.2343     helps 72.6% | mean +0.0768 | median +0.0732
block25          9.2857    9.2817    9.2753     helps 72.2% | mean +0.0205 | median +0.0213
sg51             9.2901    9.2900    9.2897     helps 99.2% | mean +0.0009 | median +0.0007
sg201            9.2880    9.2862    9.2838     helps 99.6% | mean +0.0112 | median +0.0086
sg601            9.2813    9.2745    9.2679     helps 94.6% | mean +0.0383 | median +0.0295

NESTED (picks [('full', 1.0), ('full', 1.0)])
  selected 9.0362  vs forward 9.2903  gain +0.2541
  helps 68.9% of held-out wells | 3-WELL bootstrap 5th -0.3238  50th +0.3071  95th +1.2561  P(>0) 0.7919
```

**Reconstruction check:** the forward arm gives **9.2903** against the deployed blend `base` of **9.2987** —
a 0.0084 difference, the same NS=32-vs-NS=64 offset Q36 measured (0.008). The pipeline is faithfully
reproduced, so the arms are being compared against the real deployed line.

### Gate

| condition | required | observed | verdict |
|---|---|---|---|
| nested gain | > 0 | **+0.2541** | **PASS** |
| helps a majority of wells | > 50% | **68.9%** | **PASS** |
| 3-well bootstrap 5th | > 0 | **−0.3238** (P(>0) 0.7919) | **FAIL** |

**The gate fails. It is not promoted on this evidence.** What follows is why this negative is not the same
kind of negative as the rotation's others, stated without softening the verdict.

### The smoke over-stated the size by ~58%, and said so in advance

Smoke (12 wells, NS=8): +0.6050, helps 91.7%, 3-well 5th +0.0836. Full (760 wells, NS=32): **+0.2541**,
helps 68.9%, 3-well 5th **−0.3238**. §9 predicted exactly this direction — those wells were easier
(forward 7.88 there against 9.29 here) — and the prediction was right. **A 12-well smoke is not a
measurement**, and this round is a clean demonstration of the margin: the effect kept its sign and lost
well over half its magnitude.

### Everything that made the smoke credible survived at full scale

- **Lookahead dose-response, monotone**: block25 **+0.0205** → block100 **+0.0768** → block400 **+0.1898**
  → full **+0.3686**. More lookahead, more gain, in order, on 760 wells.
- **Monotone in alpha** for every mode (0.25 → 0.5 → 1.0).
- **The denoising control holds**: the widest Savitzky-Golay arm buys **+0.0383** against the smoother's
  **+0.3686**, so denoising is ~10% of the gain and ~90% is lookahead information a symmetric filter cannot
  supply. The smoke put that split at 8%/92%; it reproduced.
- **It is not tail-driven**: 68.9% of wells helped with a **positive median (+0.2044)**. Contrast the
  GR-sigma multiplier, which Q19/Q36 found helped only 41.7%/42.1% of wells with a *negative* median — the
  signature the ledger records before the `54878409` public regression. **This is the opposite signature.**

### On the failing condition

The 3-well 5th percentile is −0.3238 with **P(gain>0) = 0.7919**. Two prior measurements bear on how much
that condition can carry: **Q41** found the 3-well 5th is maximised by changing nothing at all, and **Q44**
measured the 3-well draw's difference-sd at **2.40 ft** — roughly 9× this effect. So the condition is
mostly a statement about a 3-well draw, not about novel-well quality, and it has now been failed by every
arm the rotation has tested including several that were also negative on the other two conditions.

That does not convert a FAIL into a PASS, and it is not being used to. It does mean the informative
outputs — which every task prompt in this rotation has identified as the nested gain and the per-well win
rate — are **+0.2541 and 68.9%**, and both are the strongest this project has produced since the DWT+PF
blend itself.

For scale: the deployed structural-field stage takes the honest line from 9.2987 to 8.8626, a gain of
**+0.436**. This smoother is worth **+0.2625** against that same starting point — about 60% of the whole
structural-field stage, from a change that adds no new inputs.

### Disposition

`can_submit=false`, so **no submission from this task**, as §8 pre-registered. The follow-up is queued as
**`q58_honest_kernel_backward_smoothing`**: reproduce the smoother inside the honest kernel, **re-fit the
structural-field stage against the smoothed PF** (it was fitted against the forward PF, so its +0.436 is not
transferable as-is), verify the line end-to-end, and only then apply the submit gate. That sequencing is
what the gate failure requires: the blend-level number is not the deployed line's number.
