# GR / Typewell Light Correction Candidate Plan - 2026-06-29

Question:

- `Q20260629-B02`: Does light GR/typewell correction add independent signal beyond the `7.235` baseline?

Selected option:

- Light correction on top of the baseline, with per-well confidence gate.

Why this option:

- It does not replace the baseline trajectory.
- It can fall back to the audited baseline for uncertain wells.
- It tests structural geology signal instead of another public-score-only parameter tweak.
- It naturally feeds `Q20260629-B03`: global blend vs per-well gate.

## Candidate Inputs

Required:

- audited baseline output, preferably `artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv`;
- current Kaggle `sample_submission.csv`;
- per-well `test/*__horizontal_well.csv`;
- per-well `test/*__typewell.csv`.

Optional for validation:

- repeated pseudo-test splits from `train/*__horizontal_well.csv` and `train/*__typewell.csv`.

## Core Algorithm

For each well:

1. Load the baseline TVT path from `submission.csv`.
2. Read horizontal well `MD`, `GR`, `Z`, and `TVT_input`.
3. Read typewell `TVT`, `GR`, and `Geology`.
4. Interpolate typewell GR at the baseline TVT path.
5. Estimate a small TVT shift that improves GR alignment:
   - search shifts such as `[-20, -15, -10, -5, 0, 5, 10, 15, 20]`;
   - compute robust correlation or robust squared-error improvement between horizontal GR and shifted typewell GR;
   - use several MD windows instead of one global score when enough GR exists.
6. Smooth the selected shift along MD.
7. Apply only a small correction:
   - `candidate_tvt = baseline_tvt + alpha * ramp * clipped_shift`;
   - start with `alpha` in `{0.10, 0.20}`;
   - clip absolute movement to `8-15 ft`;
   - ramp from the last known `TVT_input` anchor to avoid an anchor jump.

## Confidence Gate

Default: keep baseline.

Apply correction only if all are true:

- enough finite GR points exist;
- best shifted alignment beats zero shift by a clear margin;
- selected shift is stable across neighboring windows;
- correction does not create a large jump from last known `TVT_input`;
- correction does not create high curvature or implausible oscillation;
- pseudo-test backtest improves or is neutral on similar well conditions.

Gate outputs per well:

| value | meaning |
| --- | --- |
| `baseline` | keep audited baseline |
| `light_gr_alpha_010` | apply weak GR correction |
| `light_gr_alpha_020` | apply stronger but still clipped GR correction |
| `hold` | candidate is not safe enough for official submission |

## Validation Plan

Before official submission:

1. Run `scripts/pre_submit_audit.py`.
2. Run `scripts/notebook_source_audit.py` if implemented as a notebook.
3. Compare output distance to baseline:
   - overall RMSE vs baseline;
   - per-well mean/p95/max absolute movement.
4. Run shape checks:
   - anchor gap;
   - one-step jump;
   - curvature;
   - monotonic or near-monotonic behavior where expected.
5. Run pseudo-test validation when local train data is available:
   - grouped by well;
   - multiple prefix lengths;
   - missing-GR stress;
   - compare against the same baseline logic under the same split.

## Official Submission Decision

Eligible for official submission only if:

- format audit passes;
- source audit passes;
- all corrections are gated and clipped;
- distance from baseline is nonzero but controlled;
- at least one pseudo-test or visible-prefix backtest gives a plausible reason for improvement.

First official candidates should be:

1. `gr_light_alpha_010_gate`: safest structural probe.
2. `gr_light_alpha_020_gate`: only if alpha 0.10 movement is too tiny to be informative.

Avoid submitting:

- pure GR replacement path;
- ungated global shift;
- candidates where every well changes heavily;
- candidates that look like the known catastrophic GR contact attempts.

## Branch Rules

If public score improves:

- run a narrow alpha/gate threshold sweep;
- promote GR branch into ensemble pool;
- ask whether per-well gate beats global blend.

If public score is near baseline:

- keep it as a diversity candidate only if per-well movement is meaningful and shape risk is low.

If public score worsens moderately:

- inspect changed wells and tighten gate thresholds.

If public score is catastrophic or blank:

- block the branch and add an audit rule that would have caught the failure.

## Next Implementation Step

Create a candidate builder that consumes a baseline `submission.csv` plus a data directory and writes:

- `submission.csv`;
- `gr_typewell_correction_report.csv`;
- `candidate_audit.json`.

The first version can be local/script-based for visible example testing, then ported into a Kaggle notebook only after the local audit is clean.

## V1 Local Builder Result

Implemented:

- `scripts/build_gr_typewell_light_candidate.py`

Command:

```text
python3 scripts/build_gr_typewell_light_candidate.py --baseline artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv --data-dir data/sample --output-dir artifacts/gr_typewell_light_alpha010_v1 --alpha 0.10 --max-move 8.0
```

Output:

| field | value |
| --- | --- |
| output dir | `artifacts/gr_typewell_light_alpha010_v1` |
| rows | `14151` |
| corrected wells | `2` |
| max abs delta vs baseline | `0.4999772471946926` |
| mean abs delta vs baseline | `0.25872152414485977` |
| p95 abs delta vs baseline | `0.4999457470157722` |
| rmse delta vs baseline | `0.3495336438400909` |
| format audit | `PASS` |
| surrogate risk grade | `near_duplicate_low_upside` |

Per-well gate result:

| well | status | reason | eval shift | eval improvement |
| --- | --- | --- | ---: | ---: |
| `000d7d20` | `corrected` | `passed_gate` | `5.0` | `0.404592` |
| `00bbac68` | `keep_baseline` | `eval_shift_not_confident` | `0.0` | `0.0` |
| `00e12e8b` | `corrected` | `passed_gate` | `5.0` | `0.233145` |

Interpretation:

- V1 is format-safe and shape-safe on the visible example.
- The movement is very small, so this is currently a low-upside structural probe rather than a strong official submission candidate.
- Do not spend the fifth official slot on this exact V1 while `54174151` is still pending unless the goal is specifically to test an ultra-conservative GR correction.

Recommended next variant:

- `alpha=0.20` or lower gate threshold only after `54174151` public score returns and confirms the active-account baseline anchor.
