# L4 anisotropic variant grid — robustness of `54878409` (2026-07-21)

Purpose: decide whether the submitted configuration (`A=50, W=0.25, gate closest_surv < 1000 ft`) sits on
a **stable plateau** or is a lucky single point. Validation only — **no submission was made from this
grid**, per the pending-submission discipline.

Script: `scripts/l4_variant_grid.py`. Grid: `A ∈ {20, 50, 100}` × `W ∈ {0.20, 0.25, 0.30}` ×
`gate ∈ {800, 1000, 1200}` = 27 configurations, all nested by well, 400-sample well bootstrap each.
Reference: deployed `A=1, W=0.15` = **8.8626**.

## Result

```
   A     W  gate |      OOF     gain |  boot5th frac>0 |  cov%     vis   twin39
  20  0.20   800 |   8.7380  +0.1247 |  +0.0430    99% | 81.5  4.4962  -0.5204
  20  0.20  1000 |   8.7269  +0.1357 |  +0.0528   100% | 87.2  4.4962  -0.3546
  20  0.20  1200 |   8.7228  +0.1399 |  +0.0294    98% | 90.9  4.4962  -0.3577
  20  0.25   800 |   8.6844  +0.1782 |  +0.0498    99% | 81.5  4.4173  -0.6764
  20  0.25  1000 |   8.6790  +0.1837 |  +0.0530    98% | 87.2  4.4173  -0.5071
  20  0.25  1200 |   8.6882  +0.1745 |  +0.0168    97% | 90.9  4.4173  -0.5069
  20  0.30   800 |   8.6674  +0.1952 |  +0.0186    97% | 81.5  4.4047  -0.8707
  20  0.30  1000 |   8.6711  +0.1916 |  +0.0119    96% | 87.2  4.4047  -0.6989
  20  0.30  1200 |   8.6994  +0.1632 |  -0.0344    90% | 90.9  4.4047  -0.6954
  50  0.20   800 |   8.7433  +0.1194 |  +0.0388    99% | 81.5  4.5707  -0.4662
  50  0.20  1000 |   8.7370  +0.1257 |  +0.0493    99% | 87.2  4.5707  -0.3055
  50  0.20  1200 |   8.7340  +0.1287 |  +0.0236    97% | 90.9  4.5707  -0.3090
  50  0.25   800 |   8.6824  +0.1802 |  +0.0516    99% | 81.5  4.4655  -0.6129
  50  0.25  1000 |   8.6825  +0.1802 |  +0.0579    98% | 87.2  4.4655  -0.4443  <== 54878409
  50  0.25  1200 |   8.6935  +0.1692 |  +0.0179    96% | 90.9  4.4655  -0.4445
  50  0.30   800 |   8.6546  +0.2081 |  +0.0269    98% | 81.5  4.4064  -0.6222
  50  0.30  1000 |   8.6642  +0.1984 |  +0.0188    96% | 87.2  4.4064  -0.6222
  50  0.30  1200 |   8.6952  +0.1675 |  -0.0312    91% | 90.9  4.4064  -0.6192
 100  0.20   800 |   8.7671  +0.0956 |  +0.0016    95% | 81.5  4.7661  -0.4827
 100  0.20  1000 |   8.7673  +0.0953 |  +0.0072    96% | 87.2  4.7661  -0.4201
 100  0.20  1200 |   8.7676  +0.0950 |  -0.0146    92% | 90.9  4.7661  -0.4225
 100  0.25   800 |   8.7103  +0.1524 |  +0.0122    96% | 81.5  4.6861  -0.6335
 100  0.25  1000 |   8.7184  +0.1442 |  +0.0097    96% | 87.2  4.6861  -0.5877
 100  0.25  1200 |   8.7326  +0.1300 |  -0.0226    91% | 90.9  4.6861  -0.5865
 100  0.30   800 |   8.6855  +0.1771 |  -0.0084    95% | 81.5  4.6394  -0.8243
 100  0.30  1000 |   8.7049  +0.1578 |  -0.0224    92% | 87.2  4.6394  -0.7933
 100  0.30  1200 |   8.7385  +0.1242 |  -0.0821    82% | 90.9  4.6394  -0.7888

joint NESTED (A,W,gate) = 8.7358   gain +0.1268
  picks: (50,0.30,800)x5, (20,0.30,1000)x2, (20,0.20,1200)x2, (20,0.25,1000)x1
spread of gain across all 27 configs: +0.0950 .. +0.2081
deployed visible-well pooled RMSE (OOF-based) = 4.7561
```

## Findings

**1. It is a plateau, not a point. All 27 configurations are positive** (+0.0950 … +0.2081). The
submitted configuration is not balanced on a knife edge.

**2. `54878409` has the highest bootstrap 5th percentile in the entire grid (+0.0579).** It is not
merely a good point on the plateau — it is the most *stable* one. The best-OOF configuration
(`A=50, W=0.30, gate=800`, +0.2081) has less than half the stability margin (+0.0269).

**3. A ≈ 20–50 is a genuine optimum band; A=100 degrades.** At `W=0.25, gate=1000`: A=20 gives +0.1837
(boot5th +0.0530), A=50 gives +0.1802 (+0.0579), A=100 gives +0.1442 (+0.0097). A=20 and A=50 differ by
+0.0035 in OOF and −0.0049 in stability — within noise of each other, so no re-submission is warranted.
A=100 is clearly outside the band.

**4. Two independent confirmations of choices made before this grid existed:**

- **W = 0.30 degrades bootstrap stability at every A** (boot5th +0.0186, +0.0119, −0.0344, +0.0269,
  +0.0188, −0.0312, −0.0084, −0.0224, −0.0821). The W ≤ 0.25 cap — set from the 2026-07-20 stress test,
  before any of these numbers existed — is confirmed by an independent axis.
- **gate = 1200 degrades stability in every block**, and gate = 1000 is best or near-best throughout.

**5. The joint nested (A,W,gate) selection returns +0.1268**, below the +0.1606 obtained when W was
capped at 0.25. Allowing W = 0.30 into the search lets the selector pick aggressive configurations
(5 of 12 folds chose `W=0.30`) that do not transfer. This is a clean demonstration that **a wider
hyper-parameter search can produce a worse honest result** — the constraint is doing real work.

**6. The weak twin subgroup is a property of the field, not of the configuration.** The 39 wells whose
closest candidate mate is a dropped near-twin are negative in all 27 configurations (−0.31 … −0.87),
tracking W rather than A. Consistent with `reports/submission_anisotropic_field_2026-07-21.md`, it is
recorded rather than guarded.

## Decision

**No submission.** No variant is clearly stronger than `54878409` on both axes, and the one with a
better point estimate is materially less stable. The grid's value is that it converts the submitted
configuration from "a candidate that passed the gate" into "the most stable point of a broad positive
plateau", which is the stronger statement for a private-ranking decision.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
MAXW=10000 ANISOS=20,100 MIN_SEP=150 OUT=$SH/struct_aniso_surv2.npz python3 scripts/struct_aniso_produce.py
python3 scripts/l4_variant_grid.py
```
with `SH=/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp`. Log: `reports/logs/l4_grid_2026-07-21.log`.

Note: the visible-well column here is **OOF-based** (the 3 test wells are also train wells), so it is a
relative proxy only and is not comparable to the inference-based 3.677 → 3.496 in the submission report.
