# Kaiwalya/PF-frontier safe-variant queue (2026-07-24)

Task 7. The 6.626 package is byte-identical to the public Kaiwalya notebook and to the family the team
already submitted 3× (6.563/6.669/6.678). A plain rerun has no incremental value. Value, if any, is in
**ablations that produce different information** — each smoked first, each judged on non-homogeneity +
information value + private-risk, not on chasing public.

## Control knobs (from `PROFILE_PRESETS` + `ROGII_GOLD_*` env)

`sp45_blend_weight` (0.55–0.60) · `run_guarded_overlap_override` · `run_visible_prefix_calibration` ·
`run_model_package_correction` + `model_package_gated_max_weight` · `run_bimodal_detector` /
`run_vp_bimodal_guard` / `ROGII_GOLD_SKIP_BIMODAL` · `visible_prefix_cut_fracs` ·
`ROGII_GOLD_{CAL,FINAL}_SEEDS` / `ROGII_GOLD_PARTICLES` · `ROGII_GOLD_CONTACT_OVERRIDE`.

## The one question that dominates variant value: H-visible vs H-hidden

- **H-visible** (public/private = row splits of the 3 visible wells): overlap + prefix-calibration are
  legitimate and the frontier family's public advantage carries to private.
- **H-hidden** (rerun scores novel wells): overlap goes inert (no train duplicate), prefix-calibration
  still applies (any well has a known heel), and the family reverts toward its base PF/beam quality.

The variant queue is designed to *probe* this without needing organizer confirmation.

## Queue — each: smoke (FAST) → full → judge

| # | variant | env change | what it reveals | submit criterion |
|---|---|---|---|---|
| V1 | **overlap-OFF ablation** | `run_guarded_overlap_override=False` | how much of the 6.5 public is overlap-driven. Public drop = overlap's public contribution; under H-hidden this is the more honest private estimate | submit only if it is a *distinct* private-safer candidate (materially different from 6.563 output) AND team wants an H-hidden hedge on the frontier line |
| V2 | **model-package-OFF ablation** | `run_model_package_correction=False` | isolates the third-party model-package contribution (dependency risk) | informational; submit only if it changes the output non-trivially and improves robustness |
| V3 | **prefix-calibration-OFF** | `run_visible_prefix_calibration=False` | how much depends on self-calibrating on the test wells' known prefix | informational; likely worse public |
| V4 | **bimodal-hedge-OFF** | `ROGII_GOLD_SKIP_BIMODAL=1` | the bimodal midpoint hedge's contribution (this is a genuine RMSE mechanism, likely helps) | do not submit an ablation that removes a genuine mechanism unless it decorrelates |
| V5 | **seed-variance audit** | vary `ROGII_GOLD_{CAL,FINAL}_SEEDS` / particles across N runs, LOCAL only | quantifies the family's run-to-run public spread (6.563↔6.678 already spans 0.115) | never submitted; sizes the noise floor so we don't over-read a 0.05 public move |

## Priority and discipline

- **V5 (seed-variance) first, local/smoke only** — it costs no submission and tells us the family's
  intrinsic public noise (the 6.563/6.669/6.678 spread suggests ≈ ±0.06, i.e. the same non-resolving
  scale our own 54878409 hit). This directly bounds how much any V1–V4 public delta can be trusted.
- **V1 (overlap-OFF) is the only ablation with a clear decision use**: it is the H-hidden hedge. But it
  is teammate-line territory (the frontier family is `leemarc223`'s), so per standing directive we do
  not submit it unilaterally; we prepare + smoke it and hand the evidence to the final-selection owner.
- V2–V4 are informational; they do not warrant a submission on their own.

## Our-line stance

None of these displaces our fully-owned honest slot `54844628` (7.891) as the H-hidden-robust,
760-well-OOF-validated candidate. The frontier variants are hedges on the *teammate* line, not our-line
submissions. No our-line quota is spent on them.
