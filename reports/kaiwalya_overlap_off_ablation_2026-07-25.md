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

## A2 full run + submission (COMPLETE)

`joezzzzz/rogii-kaiwalya-overlap-off-full` v1 COMPLETE (overlap OFF confirmed; 14151 rows in 64s).
Sanity: columns [id,tvt], 14151 rows, finite, no dup ids, id set+order == sample_submission,
range 11593.7–12239.2. Diffs (full fidelity):

```
A2 (overlap-OFF frontier) vs 54844628 (7.891) : rmse 2.537  corr 0.99997  78% rows >1ft
A2 (overlap-OFF)          vs overlap-ON base   : rmse 3.105  corr 0.99995   (materially different by construction)
per-well vs 54844628: 000d7d20 mean -1.32 / 00bbac68 +1.05 / 00e12e8b +2.98
```

**Submitted: ref `54968060`** (kernels-only code submission, kernel v1), description marks it an
overlap-OFF H-hidden diagnostic. Today 1/5 used. It is materially different from the 6.5 family (overlap
removed) and from our honest slot, and its purpose is to read the frontier's public score WITHOUT the
overlap lookup — quantifying how much of the 6.5 line is the visible-well overlap vs genuine modeling.
Score watcher running; result appended below.

Interpretation guide (pre-registered): if `54968060` scores near the 6.5 family → overlap contributes
little and the frontier's modeling is genuinely strong (favors H-visible robustness). If it scores
materially worse (toward ~7.x, near our honest slot) → the 6.5 line is largely overlap on visible wells,
confirming the H-hidden risk that the frontier reverts on novel wells and reinforcing `54844628` as the
H-hidden hedge.

## RESULT: `54968060` public = **6.643** — the "near 6.5" branch

```
54968060 overlap-OFF                       6.643
  vs its family reference (6.626 package)  +0.017
  vs best overlap-ON branch (54922806)     +0.080
  vs our honest 54844628 (7.891)           -1.248
A1 config-variance noise floor             ~0.115
```

**Removing the overlap lookup costs at most 0.080 on public — inside the noise floor.** `54968060` even
outscores two overlap-ON family members (`54896975` 6.669, `54923144` 6.678).

### This corrects the hypothesis stated earlier in this report

The FAST-smoke evidence (100% toe override on all 3 visible wells, ~3.2 ft rmse movement) made the
overlap mechanism look dominant, and this report concluded "the entire 6.5→7.9 public gap is the overlap
lookup on the visible wells." **The public result does not support that.** The mechanism is large in ft
but small in score: the override largely reproduces values the frontier's own model already predicts
well, so replacing them changes the RMSE little. The honest decomposition is:

```
7.891 -> 6.643  = 1.248   frontier MODELING without any overlap
6.643 -> 6.563  = 0.080   overlap + config differences, within noise
```

Consequence for the H-visible / H-hidden fork: the frontier family's advantage is **not** contingent on
the test wells being duplicated in train. On novel wells it would retain the modeling that produces
~6.64. This raises the frontier line's expected private value and makes `54968060` a live slot-2
candidate rather than a pure diagnostic — see
`reports/final_slot_package_corrected_gate_2026-07-25.md`.
