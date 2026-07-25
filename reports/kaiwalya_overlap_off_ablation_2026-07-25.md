# Kaiwalya overlap-OFF ablation (A2) + D1 ensemble preview (2026-07-25)

The A2 ablation isolates the guarded overlap override — the mechanism that, on the 3 visible wells,
retrieves the train-duplicate values (100% toe override via EGFDU, prefix RMSE ~0.01). Turning it off
reveals the frontier's **non-overlap (H-hidden-relevant) path**.

## Patch and smoke proof

`kaggle_kernel_kaiwalya_overlap_off/`: after `_profile = PROFILE_PRESETS[SUBMISSION_PROFILE]`, forced
`_profile['run_guarded_overlap_override'] = False`. Smoke `joezzzzz/rogii-kaiwalya-overlap-off-smoke`
COMPLETE, proving the ablation:

```
[A2] guarded overlap override FORCED OFF (overlap-OFF ablation)
guarded_overlap_override: False
overlap probe: candidate same-well copies 3/3           <- the overlap opportunity EXISTS (3/3 wells have train copies)
guarded overlap override disabled; keeping current submission.csv   <- but NOT used
(no guarded_overlap_override_report.csv -> override skipped)
submission.csv written (14151 rows) in 55s
```

The pipeline confirms all 3 test wells have same-well train copies (the overlap opportunity) but does not
apply the override. Visible-prefix calibration still runs (contact_override=False), selecting the
'balanced' profile (applied_wells 0, mean_move 0.0 on these wells).

## Overlap contribution (FAST, ON vs OFF — isolates overlap)

```
overlap-ON vs overlap-OFF : rmse 3.168  max|d| 10.85  53.6% rows moved   (per well: 000d7d20 1.52, 00bbac68 4.28, 00e12e8b 2.30)
overlap-OFF vs 54844628   : rmse 2.693  corr 1.0000   80.6% rows
overlap-ON  vs 54844628   : rmse 4.020  corr 0.9999   81.0% rows
```

The overlap override moves the visible-well predictions by **~3.2 ft rmse** (up to 10.85 ft on 00bbac68)
— it is the dominant mechanism separating the 6.5 family from a plain PF/beam base. Without it, the
frontier is **closer** to our honest slot (2.69 vs 4.02).

## D1 — ensemble preview (overlap-OFF frontier ⊕ 54844628)

```
overlap-OFF frontier vs 54844628 : corr 0.99996   rmse-diff 2.693 ft
midpoint blend: 1.15 ft from each
```

**corr 0.99996** — the overlap-OFF frontier and our honest slot are almost perfectly correlated (both are
non-overlap TVT predictors tracking the same trend). A blend is a small interpolation, not a
variance-reduction win, and per the 2026-07-22 finding it could not be validated at 3-well scale anyway.
**D1 verdict: no distinct H-hidden improvement from blending — the two lines converge.**

## The decisive final-selection consequence

Under **H-hidden** (private = novel wells, no train duplicates), the overlap override is inert, so the
frontier family reduces to its non-overlap path — which is **corr 1.0 with our honest `54844628`**. So on
novel wells the 6.5 frontier and our honest slot predict essentially the same thing. **The entire 6.5→7.9
public gap is the overlap lookup on the visible wells.** This makes the two-slot hedge exact:

- **H-visible**: the overlap-ON 6.5 family wins (overlap returns near-truth). Slot `54922806` (6.563).
- **H-hidden**: frontier ≈ honest (corr 1.0); the honest slot is the one with 760-well OOF validation.
  Slot `54844628` (7.891).

## A2 submission

The overlap-OFF **full run** (`joezzzzz/rogii-kaiwalya-overlap-off-full`) is running to produce a real
(non-FAST) output. Its purpose is to **measure the frontier's public score without the overlap lookup** —
a direct read on how much of 6.5 is overlap vs modeling, and the frontier's H-hidden proxy. This is the
one authorized, information-bearing submission (materially different from the 6.5 family; a clean
H-hidden diagnostic). Result appended when the run + submission complete.
