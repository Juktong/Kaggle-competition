# Multi-signal router / selector — validation result (2026-07-21)

**Direction 4** of the continuous optimization queue. Status: **no stable improvement observed; gate not met.**
This probe also quantifies *why* selection-type methods keep failing on this problem.

## Question

Earlier work refuted routing on a **single** variable (PF uncertainty). The open question was whether a
**multi-signal** router — one that sees neighbour geometry, PF dispersion, model disagreement and row
position jointly — can pick, per row, the best of several honest candidates.

Candidates routed among (all already honest and all test-available at inference):

| candidate | standalone OOF |
|---|---|
| `cur` — deployed 0.5·DWT+0.5·PF with gated 0.15 structural | **8.8626** |
| `base_noStruct` — 0.5·DWT+0.5·PF, structural term dropped | 9.2987 |
| `dwt_only` — DWT ensemble alone | 10.2891 |

Router features (7): per-row `nn_dist`, well `nnb`, well `closest`, PF `unc`, `row_frac`,
`|DWT − PF|`, `|struct − base|`. Model: `HistGradientBoostingClassifier` predicting which candidate has
the smallest absolute error, trained **nested by well** (fit on half the wells, applied to the other
half, both directions, 3 seeds), row-subsampled 1:4 for training.

## Result

```
oracle route mix: cur=38%, base_noStruct=31%, dwt_only=31%
ORACLE router (truth-selected upper bound) = 7.3763   gain +1.4863
NESTED multi-signal router                 = 9.4684   gain -0.6057

GATE (>= +0.10 with stably positive bootstrap): DOES NOT MEET
```

## Interpretation — the oracle gap is the finding

The oracle says routing is worth **+1.49** if you know the answer. The honest router loses **−0.61**.
A gap that large is not a modelling shortfall to be closed with a better classifier; the **near-uniform
oracle mix (38 / 31 / 31)** explains it directly.

If one candidate were genuinely better on an identifiable family of rows, the oracle mix would be
skewed and the winning family would be characterised by the features. Instead the per-row winner is
close to a three-way coin flip. `dwt_only` wins 31% of rows despite being **1.43 ft worse overall** —
it wins them because on those particular rows its noise happened to fall the right way, which is
information that does not exist in any feature and does not repeat on new wells.

The deeper mechanism, now confirmed four times:

> The deployed prediction is a **variance-reduced average**. Hard selection replaces the average with a
> single member, discarding the variance reduction and paying the full noise of the chosen member —
> plus the estimation error of the selector. The expected cost of selection is positive even when the
> selector is unbiased.

This is the same result found in direction D (top-K path ranker), where **shrinkage — not selection —
was the usable mechanism**, and it is consistent with directions 2 and 3, where post-hoc corrections
built on already-consumed signals failed to transfer.

An oracle number is therefore **not** evidence of an achievable gain, and should not be used to justify
building a selector. Recording it here so the gap itself is the documented artifact.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
python3 scripts/group_and_router.py        # D4 section prints the block above
```
Required artifacts: `decomp_features.npz`, `struct_oof_rowdist.npz`, `pf_unc.npz` in
`/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/`.

## Disposition

Direction 4 closed as a negative. Routing/selection is deprioritised as a class. Remaining effort moves
to directions that add **genuinely decorrelated information** rather than re-processing existing
predictions — see `reports/autonomous_backlog_status_2026-07-21.md`.
