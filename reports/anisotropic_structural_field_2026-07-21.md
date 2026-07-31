# Anisotropic (dip-aware) structural field — proposal L4 (2026-07-21)

**Status: meets the pre-registered gate; duplicate-leakage concern investigated and cleared; inference
kernel built and verified bit-exact; Kaggle smoke running.** This is the first candidate of this queue
to satisfy both gate conditions.

Scripts: `scripts/struct_aniso_produce.py`, `scripts/eval_aniso_all.py`, `scripts/eval_aniso_capped.py`,
`scripts/eval_ctrl.py`, `scripts/weight_origin.py`, `scripts/verify_kernel_equiv.py`.
Kernel: `kaggle_kernel_struct_aniso/` (+ `_smoke` variant).

## Motivation

`reports/per_well_bias_structure_2026-07-21.md` located the dominant remaining error: 60.3% of residual
variance is a per-well offset, and it is dominated by **drift along the toe** (slope std 13.28 ft), not
an initial level offset (std 4.72 ft). The structural field is the only component that reaches that
term — and the deployed version weights group-mates by **isotropic** XY distance, ignoring that
geological structure varies slowly along strike and quickly along dip.

## Method

Identical to the deployed field except for the distance metric:

1. fit a plane `r ~ a + b·X + c·Y` over the surviving group-mates → dip direction `u = (b,c)/|(b,c)|`,
   strike direction `v ⊥ u`
2. anisotropic distance `d² = (Δ·u)² + (Δ·v)²/A²` — strike distances compressed by `A`
3. IDW k=12, `w = 1/(d+1)`; anchor on the target's own last 100 known heel rows; `TVT = r_pred + anchor − Z`

`A = 1` reduces exactly to the deployed field. **No new inputs**: group key from the target's own
typewell, mates are TRAIN wells, anchor from the target's own known rows, same `MIN_SEP = 150 ft`
duplicate guard, same `nnb ≥ 4 ∧ closest < 1000 ft` deployment gate.

## Result

Full run, 760 wells, 3,721,471 rows, 87.3% gated. The `A=1` control reproduces the deployed OOF
**exactly** (8.8626), confirming the generalization is correctly implemented.

```
   A | fixed W=.15 | nested-W  fitW |  gain(fix)  gain(nest)
   1 |      8.8626 |   8.9517  0.203 |   +0.0000    -0.0890
   2 |      8.8230 |   8.8433  0.241 |   +0.0396    +0.0194
   3 |      8.8227 |   8.8244  0.239 |   +0.0399    +0.0382
   5 |      8.8225 |   8.8051  0.248 |   +0.0401    +0.0575
   8 |      8.8179 |   8.7812  0.258 |   +0.0447    +0.0815
  12 |      8.8155 |   8.7611  0.266 |   +0.0471    +0.1015
  20 |      8.8144 |   8.7415  0.276 |   +0.0483    +0.1211
  50 |      8.8267 |   8.7472  0.292 |   +0.0360    +0.1154
```

**Attribution is clean.** At unchanged `W = 0.15`, anisotropy alone is worth only **+0.0483**; but
re-weighting the *isotropic* field alone is worth **−0.0890**. The gain therefore comes from anisotropy
**earning** a larger weight, not from the weight change by itself — the same refit applied to `A=1`
moves the wrong way.

### Nesting both A and W

`A = 20` was initially chosen by reading the table — the same "a sweep is not a validation" failure used
to reject direction 2. Both `A` and `W` were therefore re-selected **nested** (training-half wells →
held-out half, 6 seeds / 12 folds).

`W` was capped at **0.25** on **prior** evidence — the 2026-07-20 stress test showed aggressive blanket
weights push weak-neighbour wells from 10.19 to 15.61. The cap was set from that prior, not chosen to
make the gate pass; the uncapped variant is reported alongside it.

```
uncapped (W <= 0.35): NESTED (A,W) = 8.7453  gain +0.1173
   deployable config A=50, W=0.35 -> bootstrap 5th -0.0513, frac>0 89%   [FAILS stability]

capped   (W <= 0.25): NESTED (A,W) = 8.7234  gain +0.1393
   deployable config A=50, W=0.25 -> full-data 8.6818 (+0.1808)
   bootstrap(1000): mean +0.1794  5th +0.0499  1st +0.0006  frac>0 99%
   per-well: helped 47.9% hurt 38.6% median(gated) +0.095
   worst 5 wells: -6.99 -6.55 -6.35 -5.71 -5.58   (uncapped: -10.58)

GATE (+0.10 AND stably positive bootstrap): MEETS
```

Capping `W` **raised the honest gain and tripled the safety margin** — `W = 0.35` was overfitting. This
repeats the structural field's own history, where gating tripled the gain and cut worst-case regression.

## The duplicate-leakage investigation

`A = 50` divides strike distance by 50, so a mate just past the `MIN_SEP = 150 ft` guard **along strike**
has an effective distance of ≈3 ft and could dominate the IDW. The guard was calibrated at *isotropic*
distance (audit: 0/52 duplicate signatures), so anisotropy could in principle re-admit the near-twins it
was built to exclude. Two independent checks were run before considering a submission.

**1. Where does the IDW weight come from?** (40 wells)

```
                weight from mates <400ft   <250ft   median sep of SELECTED mates
A=1  (isotropic)          52.4%            12.9%            357 ft
A=50 (anisotropic)        46.6%            11.6%            375 ft
```

`A=50` draws *less* weight from close mates and selects mates at *slightly greater* isotropic
separation. It reorganizes **which** mates are used (along strike), it does not pull in twins.

**2. Isotropic control at matched guards** — the decisive test. Advantage of `A>1` over `A=1` at the
**same** `MIN_SEP`:

```
 MIN_SEP    A    W=0.25  |  vs A=1 at same guard
     150    1    8.8477  |   +0.0000
     150   20    8.6799  |   +0.1678
     150   50    8.6818  |   +0.1659
     400    1   10.0877  |   +0.0000
     400   20    9.2378  |   +0.8499
     400   50    9.2178  |   +0.8699
     800    1   12.3805  |   +0.0000
     800   20   10.3085  |   +2.0720
     800   50   10.2694  |   +2.1112
```

**The advantage grows as the guard tightens** (+0.17 → +0.85 → +2.11). Leakage would vanish under a
stricter guard; instead the isotropic field degrades far worse when only distant mates remain.

This also explains an earlier alarming intermediate result. Comparing `A=20/50` at `MIN_SEP=400/800`
against the *deployed* `A=1/MIN_SEP=150` showed −0.375 and −1.44, which looked like leakage collapse.
It was not: ~50% of IDW weight comes from mates within 400 ft for **both** fields, so tightening the
guard is plain information loss — and it hits the isotropic kernel harder. Recording this because the
naive comparison would have produced the wrong conclusion in either direction.

Mechanistically this is the expected geology: with only distant mates available, **direction matters
more**, because isotropic averaging pulls in down-dip mates sitting at the wrong structural level.

## Inference implementation and verification

`kaggle_kernel_struct_aniso/` patches cell 27 of the submitted kernel: plane fit over surviving mates →
rotate into the (dip, strike/A) frame → same KDTree query; `ANISO = 50`, `STRUCT_W = 0.25`.

`scripts/verify_kernel_equiv.py` runs the patched kernel's code path on 18 train wells as pseudo-targets
(self excluded from mates, as the producer does) and compares against `struct_aniso_hi.npz` `A=50`:

```
wells compared=18  rows=88229  gated_off=7
MAX |kernel_logic - validated_producer| = 0.00000000 ft   -> EQUIVALENT (float32-exact)
```

An initial reading of 0.00049 ft was **float32 storage precision** (8000 ft × 2⁻²³ = 0.00095 ft), not a
logic difference — the producer stores `struct` as float32.

## Pre-submit audit status

- **(a) test-availability** — inherited from the audited deployed field. Inputs are the target's own
  typewell (group key), the target's own heel `TVT_input` (anchor), and TRAIN mates' `(X, Y, TVT+Z)`.
  The plane fit uses only those same TRAIN mate coordinates. No structural surfaces, no Geology, no
  train-membership gate, no hidden-label leakage. **PASS**
- **(b) format / finiteness / row order / diff-vs-baseline** — pending the smoke log and the
  presubmit gate on the full output.

**Smoke running** (`joezzzzz/rogii-struct-aniso-smoke`, `PF_SMOKE` forced on: 3 wells, NS=8), per
Directive 4. The full run and any submission remain gated on reading its completed log.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
SH=/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp
MAXW=10000 ANISOS=1,2,3,5   OUT=$SH/struct_aniso.npz     python3 scripts/struct_aniso_produce.py
MAXW=10000 ANISOS=5,8,12,20,50 OUT=$SH/struct_aniso_hi.npz python3 scripts/struct_aniso_produce.py
python3 scripts/eval_aniso_all.py        # full A sweep + bootstrap
python3 scripts/eval_aniso_capped.py     # nested (A,W), W capped 0.25  -> the headline number
python3 scripts/eval_ctrl.py             # isotropic control at MIN_SEP 150/400/800
python3 scripts/weight_origin.py         # where the IDW weight comes from
python3 scripts/verify_kernel_equiv.py   # kernel-vs-producer equivalence
```
Logs in `reports/logs/aniso_*.log`.
