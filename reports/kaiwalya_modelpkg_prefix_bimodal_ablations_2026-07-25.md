# Kaiwalya frontier — model-package / prefix / bimodal ablations (A3/A4/A5, 2026-07-25)

Efficiency note: the frontier notebook writes its **staged intermediate submissions** to
`/kaggle/working/`, so A3/A4/A5 are obtained from the intermediates of a single run — no extra GPU
kernels needed. These are read from the completed baseline FAST smoke
(`joezzzzz/rogii-kaiwalya-6626-smoke`). **FAST/40-well fidelity**: absolute values are degraded, but the
ablation *diffs* are test-side operations on the 3 visible wells, largely independent of GBM training
scale, so they are indicative. All three are **HOLD (no submission)** — they are intermediate states of
the same overlap-driven family, homogeneous with the already-submitted 6.563/6.669/6.678.

## A3 — model-package-OFF (`submission_before_model_package.csv`)

```
mpkg-OFF vs final(6.5 family) : rmse 1.103  max|d| 2.00  p95 2.00  corr 1.0000  30.4% rows moved
mpkg-OFF vs 54844628 (ours)   : rmse 3.678  max|d| 11.32 p95 8.18  corr 0.9999  78.9% rows
gate-weight sweep vs final    : w004 1.109 · w005 1.110 · w010 1.117 · w020 1.131  (monotone)
```

The third-party model-package correction is the **last ~1.1 ft adjustment**, capped (max 2.0 ft), moving
30% of rows, scaling monotonically with the gate weight. It is a bounded refinement on top of the
overlap-driven base, and it is the stage that carries the external-dataset dependency risk. Removing it
leaves the pipeline essentially at the overlap+prefix+PF state.

## A5 — bimodal-hedge-OFF (`submission_before_branch_hedge.csv`)

```
before_branch_hedge  vs  before_model_package : rmse 0.000  (IDENTICAL)
```

**On the 3 visible test wells the bimodal branch hedge makes no change** — `before_branch_hedge` equals
`before_model_package` exactly. There are no bimodal-active wells among the three, so the bimodal midpoint
mechanism contributes **zero** to these wells' score. (It is a genuine RMSE mechanism in principle, but
inactive here.) Removing it changes nothing on the scored wells.

## A4 — prefix-calibration variants (`submission_gold_prefix_{conservative,balanced,aggressive}.csv`)

```
prefix_conservative / balanced / aggressive  vs final : all rmse 1.103 (IDENTICAL to each other)
```

The three prefix-aggressiveness variants produce the **same** output on the visible wells (before the
model-package stage). The prefix-calibration effect is folded into the 3.678 gap vs `54844628`, but the
*choice* of prefix aggressiveness does not move these three wells — consistent with the overlap override
already pinning them to the train-duplicate values, leaving little for prefix calibration to adjust.

## Decomposition of the 6.5-family output vs our honest slot (FAST, indicative)

```
final(6.5 family) vs 54844628 total gap ≈ 4.02 ft, of which:
  model-package (last stage)           ≈ 1.10
  everything before model-package      ≈ 3.68   (dominated by the 100% overlap override on visible wells)
  bimodal hedge                        =  0.00   (inactive on these wells)
  prefix-aggressiveness choice         =  0.00   (pinned by overlap)
```

## Disposition

A3/A4/A5 are **informational, HOLD**. They confirm the 6.5 family's visible-well output is dominated by
the overlap override; the model-package correction is a small bounded top-up; bimodal and
prefix-aggressiveness are inert on the scored wells. The one ablation that reveals the H-hidden-relevant
(non-overlap) behavior is **A2 overlap-OFF**, which requires its own run (no "before overlap" intermediate
exists) — smoke in progress. None of A3/A4/A5 is submittable: each is a homogeneous intermediate of the
already-submitted family.

---

## CORRECTION (2026-07-28) — the A5 bimodal conclusion was wrong

A5 above states the bimodal hedge "makes no change" because `before_branch_hedge` equals
`before_model_package`. Those two files are indeed identical, **but both are upstream of the hedge**, so
that comparison cannot detect it. The correct comparison is `final` vs `before_branch_hedge`:

```
final - before_branch_hedge:  00e12e8b  4301/4301 rows changed, mean +2.0000 ft
                              000d7d20  0 rows,  00bbac68  0 rows
pf_seed_branch_hedge_report:  00e12e8b applied, separation 29.439 ft, shift 2.0, moved_rows 4301
```

**The bimodal hedge applies +2.0 ft to all 4,301 rows of `00e12e8b`** and is the largest single post-SP45
effect in the deployed configuration (rmse 1.103 vs final, 30.4% of rows). See
`reports/frontier_variant_matrix_lite_2026-07-28.md`.

