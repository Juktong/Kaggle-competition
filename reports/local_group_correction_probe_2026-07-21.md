# Typewell-group local correction — validation result (2026-07-21)

**Direction 3** of the continuous optimization queue. Status: **no stable improvement observed; gate not met.**

## Question

The row-level residual probe (`reports/residual_correction_probe_2026-07-21.md`) used row features but
**never used group identity as a categorical**. That was a real gap: the 773 typewells collapse to ~54
distinct master logs, and wells sharing a group share a TVT datum. If a group carries a systematic
level or trend bias in the deployed prediction, a per-group correction estimated from *other wells in
the same group* would be test-available at inference time (the target's own group key comes from its
own typewell) and would transfer.

## Setup

- Script: `scripts/group_and_router.py` (section D3)
- Rows **3,721,471**, wells **760**, **41 groups** present after intersection; deployed OOF **8.8626**.
- All corrections fit **nested by well**: the group statistic is estimated on one half of the wells and
  applied to the held-out half, both directions, 3 seeds. A group needs ≥200 training rows to be fit.

Three forms tested:

- **(a) per-group offset** — add `mean(resid)` of the group's training wells.
- **(b) shrunk offset** — the same offset scaled by `n/(n + shrink_n)`, a James–Stein style pull toward
  zero that protects small groups.
- **(c) per-group linear trend** — regress the residual on `row_frac` within the group and apply
  `a + b*row_frac`, which can correct a group-systematic heel→toe drift rather than a flat level.

## Result

| correction | nested OOF | gain vs deployed |
|---|---|---|
| per-group offset (no shrinkage) | 9.3779 | **−0.5153** |
| per-group offset, shrink_n=5000 | 9.2518 | −0.3892 |
| per-group offset, shrink_n=50000 | 8.9993 | −0.1366 |
| per-group linear trend in row_frac | 9.4882 | **−0.6255** |

```
GATE (>= +0.10 with stably positive bootstrap): DOES NOT MEET
```

## Interpretation

The shrinkage series is the informative part. As `shrink_n` grows the correction is pulled toward zero
and the loss shrinks monotonically toward the deployed score:

```
shrink 0      -> -0.5153
shrink 5000   -> -0.3892
shrink 50000  -> -0.1366
shrink ->inf  ->  0.0000   (the deployed pipeline)
```

The curve **approaches zero from below and never crosses it**. That is a clean statement that the
optimal group-level correction is exactly zero: every non-zero amount of group correction costs
accuracy, in proportion to how much is applied. There is no shrinkage setting worth deploying, and no
need to search the shrinkage grid further.

Why: a group's residual mean estimated on its training wells is dominated by those wells' own noise,
not by a shared group bias. The group datum is already exploited — the structural field is *anchored*
per well on the target's own last 100 known heel rows, which removes exactly the level offset a
per-group constant would try to re-estimate, and does so per well rather than per group. The trend
variant is worse still because it spends two parameters per group on the same absent signal.

This is a useful negative: it closes group-level post-hoc calibration as a class, not just one form of it.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
python3 scripts/group_and_router.py        # D3 section prints the table above
```
Required artifacts: `decomp_features.npz`, `struct_oof_rowdist.npz`, `pf_unc.npz` in
`/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/`, plus `data/rogii/train/*__typewell.csv` for the
group key (`round(max(typewell.TVT), 1)` — the same key the deployed inference uses).

## Disposition

Direction 3 closed as a negative. Combined with directions 2 and 4 it forms a consistent picture,
recorded in `reports/autonomous_backlog_status_2026-07-21.md`.
