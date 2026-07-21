# Anisotropic (dip-aware) structural field — proposal L4, first results (2026-07-21)

Status: **consistent positive trend, still below the +0.10 gate; a higher-anisotropy sweep is running.**
Scripts: `scripts/struct_aniso_produce.py`, `scripts/eval_aniso.py`.

## Motivation

`reports/per_well_bias_structure_2026-07-21.md` located the dominant remaining error: 60.3% of residual
variance is a per-well offset, and that offset is dominated by **drift along the toe** (slope std
13.28 ft) rather than an initial level offset (std 4.72 ft). The structural field is the only component
that reaches this term, and the deployed version weights group-mates by **isotropic** XY distance —
which ignores that geological structure varies slowly along strike and quickly along dip.

## Method

Identical to the deployed field except for the distance metric:

1. fit a plane `r ~ a + b·X + c·Y` over the surviving group-mates → dip direction `u = (b,c)/|(b,c)|`,
   strike direction `v ⊥ u`
2. anisotropic distance `d² = (Δ·u)² + (Δ·v)²/A²`, so strike distances are compressed by factor `A`
3. IDW k=12, `w = 1/(d+1)`; anchor on the target's own last 100 known heel rows; `TVT = r_pred + anchor − Z`

`A = 1` reduces exactly to the deployed isotropic field. Everything used is test-available: the group key
comes from the target's own typewell, mates are TRAIN wells, and the anchor uses the target's own known
rows. The same `MIN_SEP = 150 ft` duplicate guard applies. All `A` values are computed in one pass
because loading mate point clouds dominates the cost.

## Validation of the implementation

Smoke (MAXW=12) and the full run both confirm the generalization is correct:

```
max |A=1 - deployed field| = 0.000000        (control reproduces the incumbent exactly)
full run, A=1, W=0.15      = 8.8626          (matches the deployed OOF exactly)
mean |A - A=1| : A=2 5.95 ft, A=3 7.80 ft, A=5 9.11 ft
median dip magnitude 0.037 (~2.1 deg), dip azimuth spread 7.6 deg
```

## Result (760 wells, 3,721,471 rows, 87.3% gated)

```
fixed W=0.15, varying anisotropy:
  A=1  8.8626  +0.0000      A=2  8.8230  +0.0396
  A=3  8.8227  +0.0399      A=5  8.8225  +0.0401

nested-W refit per anisotropy (fit half the wells, apply to the held-out half, 3 seeds):
  A=1  8.9517  -0.0890   (fitted W=0.203)
  A=2  8.8433  +0.0194   (fitted W=0.241)
  A=3  8.8244  +0.0382   (fitted W=0.239)
  A=5  8.8051  +0.0575   (fitted W=0.248)

two-field combination (isotropic + anisotropic, 2 nested coefficients):
  A=1 + A=2  +0.0190      A=1 + A=3  +0.0328      A=1 + A=5  +0.0603
```

## Interpretation

**Anisotropy helps, and the effect is real but modest so far.** Two features of the table matter:

1. **At fixed W = 0.15 the gain saturates at ≈ +0.040**, but under a **nested-W refit it keeps rising**
   with A (+0.019 → +0.038 → +0.0575). The reason is that a better field earns a larger weight: the
   fitted W rises to ≈ 0.24–0.25 against the deployed 0.15.
2. **Refitting W on the isotropic field alone *hurts* (−0.0890, fitted W = 0.203).** This reproduces the
   direction-7 P1 finding from a different angle: the hand-set W = 0.15 sits in a shrinkage-favorable
   regime that fitting degrades. The anisotropic field is therefore not merely absorbing a weight
   change — it earns its higher weight legitimately, since the same refit applied to A=1 goes the wrong
   way.

The best honest result so far is **+0.0575** (A=5, nested W) or **+0.0603** (two-field A=1 + A=5), both
well below the +0.10 gate. The most conservative deployable form — A=5 at the **unchanged** W = 0.15 —
gives a clean **+0.0401** with no refitting at all.

## Running

The nested gain had **not saturated by A = 5**, so a higher sweep is running: `A ∈ {5, 8, 12, 20, 50}`,
detached (PPID = 1), with the evaluation chained. `A → ∞` is the well-defined limit in which distance is
measured **only along dip** and strike separation is ignored entirely, so the sweep brackets the
mechanism rather than merely extending a grid.

The evaluation was extended to include a **400-sample well-level bootstrap** of the best variant. That is
a direct lesson from the top-K line (`reports/topk_path_ranker_final_2026-07-21.md`), where a +0.1492
point estimate failed on stability because 45.7% of wells were hurt; a point gain is not enough to act
on, so stability is now measured in the same run rather than afterwards.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
MAXW=12 ANISOS=1,2,3,5 OUT=$SH/struct_aniso_smoke.npz python3 scripts/struct_aniso_produce.py   # smoke
MAXW=10000 ANISOS=1,2,3,5 OUT=$SH/struct_aniso.npz  python3 scripts/struct_aniso_produce.py     # full
python3 scripts/eval_aniso.py
```
with `SH=/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp`.
