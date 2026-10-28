# L5 third decorrelated forward model — data audit + GR-weighted field smoke (2026-07-21)

Task 4 of the parallel queue. Status: **data audit complete and decisive; the first mini-smoke does not
achieve decorrelation.** Scripts: `scripts/l5_gr_struct.py`, `scripts/eval_l5_gr.py`.

## Step 1 — data availability audit (the binding constraint)

```
file kinds (train and test): horizontal_well.csv, typewell.csv   [no other sources]

horizontal TRAIN: MD, X, Y, Z, ANCC, ASTNU, ASTNL, EGFDU, EGFDL, BUDA, TVT, GR, TVT_input
horizontal TEST : MD, X, Y, Z, GR, TVT_input
  train-only (leakage if used): ANCC, ASTNL, ASTNU, BUDA, EGFDL, EGFDU, TVT

typewell TRAIN: TVT, GR, Geology        typewell TEST: TVT, GR
  train-only: Geology

TEST coverage: MD/X/Y/Z 100%, GR 80.3%, TVT_input 26.4% (the heel)
```

**The only test-available log channel is GR.** The extra curves are train-only, and their identity is
informative: `Geology` takes 18 values whose most frequent are literally `ANCC`, `EGFDL`, `ASTNL`,
`BUDA`, `ASTNU` — i.e. those columns are **formation-surface depths**, the "structural surfaces" line
already closed on evidence (oracle-positive, achievable-negative: any predictor of them is a function of
the test-available inputs the DWT already saturates). They correlate with GR at only +0.05, confirming
they carry information that simply is not reachable at test time.

**Consequence:** a third decorrelated forward model cannot come from a new data channel — none exists.
It must be a *different computation* over `{MD, X, Y, Z, GR, TVT_input}` + typewell `{TVT, GR}`. This
matches how both historical wins arose: the PF is a new computation over GR, the structural field a new
computation over cross-well geometry.

## Step 2 — the candidate: GR-weighted cross-well structural field

The structural field uses **only geometry**: IDW over group-mates' `r = TVT + Z` at matched XY. It never
looks at the mates' GR. Two horizontal wells at the same structural level should read similar GR, so
weighting each mate point by GR agreement as well as proximity is a genuinely different computation and
is fully test-available (target GR is given; mate GR and mate TVT are train data):

```
w = 1/(d_aniso + 1) * exp(-(gr_target - gr_mate)^2 / (2*sigma^2))
```

## Step 3 — smoke result (58 wells, 281,375 rows, ungated subset)

```
base(DWT+PF) = 7.3893     geometry-only struct standalone = 19.6527
GR-weighted standalone: sigma=10 33.2655 | sigma=20 20.1908 | sigma=40 19.3273

nested weight fit (3 seeds):
  geometry-only (L4 A=50)   nested 7.5119   gain vs base -0.1226
  GR-weighted sigma=20      nested 7.4724   gain vs base -0.0831
  -> increment vs geometry-only +0.0395

corr(err_geo, err_GRweighted) = +0.9194
corr(err_base, err_geo)       = +0.2310
corr(err_base, err_GRweighted)= +0.2217

two-field nested (geo + GR-weighted, 2 coefficients): 7.7417  (-0.2298 vs geometry-only)
```

## Interpretation

GR weighting produces a small increment (+0.0395) over the geometry-only field on this subset, but
**it fails the objective of the direction**: the error correlation with the geometry-only field is
**+0.9194**. It is a re-weighting of the same field, not a decorrelated second source. The two-field
combination being *worse* than either alone (−0.2298) confirms the redundancy — there is nothing
independent for a second coefficient to buy.

Caveat on absolute values: this subset is **ungated** and easy (base 7.39 vs the global 9.30), so the
structural field is net-negative here where the deployed gated version is positive. Only the *relative*
comparison and the correlation are informative.

## Disposition

- The GR-weighted variant is not a decorrelated third source. It could be re-examined later as a minor
  **L4 refinement** rather than an L5 candidate, but with +0.92 error correlation the expected gated
  full-scale gain is small, and the L4 grid already shows that line sitting on a broad plateau.
- The L5 objective itself remains open, and the data audit sharpens what would satisfy it: a computation
  over GR/geometry whose errors are genuinely decorrelated from DWT (feature regression), PF (typewell
  GR matching) and the structural field (cross-well geometry). Candidates that do **not** qualify, now
  on evidence: other-log forwards (no such channel at test), formation-top/stratigraphic state (train-only
  labels, line already closed), and GR-reweighted geometry (this smoke, +0.92 correlated).

## Step 4 — second mechanism tested and closed: GR difference as a level correction

The structural field assumes a mate's `r = TVT + Z` transfers directly at matched XY; it never checks
whether the two wells are actually at the same structural level. If the local GR-vs-TVT gradient (from
the typewell, test-available) converted a GR difference into a TVT difference, that would be a usable
correction the field currently ignores — and a genuinely different computation.

Tested on TRAIN pairs where both true TVTs are known (`scripts/l5_gr_offset_probe.py`):

```
pairs sampled: 4508 matched points
  true dTVT      std=220.06 ft   mean=-48.11
  GR diff        std=30.06       |dGR/dTVT| median=0.703 /ft
  predicted dTVT std=60.04 ft

  corr(predicted dTVT, true dTVT) = +0.0197
  corr(raw GR diff,   true dTVT)  = -0.0872
  best scalar a=0.0832 -> residual std 220.02 vs baseline 220.06, variance explained 0.0%
```

**The mechanism does not exist.** A pointwise GR difference carries essentially no information about the
TVT difference between two wells. The reason is structural: the typewell GR profile oscillates with
depth and is not monotonic, so a given GR value is consistent with many depths and a GR *difference* is
ambiguous about a depth *difference*. This is precisely the ambiguity the PF resolves by sequential
filtering along a whole trajectory rather than by pointwise inversion — which is why the PF works and
this does not.

## L5 status after two mini-smokes

Both GR-based routes to a decorrelated cross-well computation are now closed on evidence:

| route | result |
|---|---|
| GR-weighted IDW (point similarity) | +0.0395 over geometry-only, but **corr(err) = +0.9194** — a re-weighting, not a new source |
| GR-difference level correction | **0.0% variance explained**, corr +0.0197 — mechanism absent |

What survives as the remaining L5 shape: a computation that uses GR **as a sequence along the
trajectory** (the property that makes the PF work) but referenced against **neighbouring horizontal
wells** rather than the vertical typewell. That is the one combination not yet occupied by an existing
component. It is also substantially more expensive than either smoke above, so it should only be started
against a concrete headroom estimate rather than on plausibility.
