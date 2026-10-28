# Mark's public-6.626 Kaiwalya repro package — integration + static audit (2026-07-24)

Mark's `origin/main@a589fa8 "Add reproducible public 6.626 ROGII kernel"` adds
`kaggle_kernel_kaiwalya_public_tvt_6626_repro/`. This audits it for integration, compliance, and
reproducibility from our account.

## Integration (task 2)

- `git fetch origin --prune`; `origin/main@a589fa8`. A full merge would **delete** CLAUDE.md and our
  2026-07-2x reports/experiments (origin/main is a divergent line), so **no merge was done**.
- Targeted extract only: `git checkout origin/main -- kaggle_kernel_kaiwalya_public_tvt_6626_repro/`
  → 3 files committed to `juktong/codex/autonomous-queue-2026-07-15`. Our reports untouched.

## Identity — byte-identical to the public source (decisive)

```
integrated pkg notebook  sha256 = d61a88c454ffcf4d   (code-only hash 6e9840a8, 265913 chars)
public kaiwalyaatulraut/rogii-public-tvt-solution (pulled 2026-07-23) = IDENTICAL
```

The package **is** the public Kaiwalya notebook, unmodified. Its README states the same: a reproduction
of `kaiwalyaatulraut/rogii-public-tvt-solution`; `6.626` belongs to the public source version.

This is the same notebook family already submitted by the team **three times**:
`54896975` (6.669), `54922806` (6.563, current team best), `54923144` (6.678).

## Static reproduction facts (task 3)

- **Structure**: 45 code cells, 265,913 chars. Papermill metadata: `exception=None`, `duration=849s`
  (the teammate's successful run).
- **Profile**: `SUBMISSION_PROFILE = 'vp_balanced_modelpkg_005'` (balanced visible-prefix profile,
  `sp45_blend_weight=0.60`, `run_guarded_overlap_override=True`, `run_visible_prefix_calibration=True`,
  `run_model_package_correction=True`, `model_package_gated_max_weight=0.00425`, `scale=6.0`).
- **Inputs**: competition data `/kaggle/input/competitions/rogii-wellbore-geology-prediction`; reads
  `sample_submission.csv` from `CFG.DATA`; artifact roots from the 9 datasets (Ridge/SP45 anchor,
  model package, koolbox, claude-models-pub, tabicl mirror, v10/v11/v50 artifacts).
- **Stochastic sections (seeded)**: `CV_SEED=0`, `SEED=42`, PF seed-ensemble `np.random.seed(seed_base+s)`,
  GBM `random_state` 0/29/7/123. Deterministic given seeds; README notes hidden-well output can differ
  slightly because parts of the PF pipeline are stochastic across seeds/particles.
- **Submission generation**: a multi-stage `/kaggle/working/submission.csv` pipeline, each stage
  refining the previous — base PF/beam → SP45 projection → learned-trajectory → guarded overlap override
  (skippable) → visible-prefix calibration (skippable) → model-package correction → PF bimodality hedge
  → final audit copy. Final columns `['id','tvt']`.
- **Schema audit**: `assert set(['id','tvt']).issubset(...)`; id built as `well[:8]` + `row_idx`, merged
  onto `sample_submission[['id']]` so row set/order match the template.
- **GPU**: LightGBM `device_type="gpu"`, CatBoost `task_type="GPU", devices="0"`; a torch TCN runs on
  CPU. `USE_GPU=os.environ.get("USE_GPU","auto")` → defaults to GPU. Genuinely GPU-dependent for the GBM
  stages (falls back to CPU only if forced).
- **"hidden-runtime" clarified**: `is_known = isfinite(TVT); is_hidden = ~is_known; first_hidden; known_prefix`
  — this is the standard **known-heel / hidden-toe** split on TVT finiteness, **not** an
  environment-detection trick. The submission-description phrase "hidden-runtime" refers to handling the
  hidden (toe) rows via the known prefix.
- **External data / compliance**: 9 **public** Kaggle datasets; `enable_internet=false`; **no** pip
  install / URL / requests / socket. All 9 verified accessible from our account (`joezzzzz`). Kernels-only
  (competition_sources set). Compliant; the only note is the standard dependency on other competitors'
  public shared artifacts.

## Metadata / ownership

- `kernel-metadata.json` id = `leemarc223/rogii-kaiwalya-public-tvt-6626-repro` (teammate). Our CLI
  cannot access that private kernel (`Permission kernels.get denied`).
- To run from our account the id must be changed to a `joezzzzz/...` slug. All 9 dataset_sources are
  public and attach from our account, so an our-account copy is runnable (GPU permitting).

## Reproducibility verdict

- **Substance-reproducible from our account**: yes — identical public notebook + 9 public datasets, all
  accessible; the teammate ran this exact notebook to COMPLETE 3×.
- **Bit-exact submission**: not guaranteed — the PF seed-ensemble/particle sampling is stochastic across
  runs; `6.626`/`6.563`/`6.669`/`6.678` are the observed spread of the same pipeline.

## Submit implication (feeds task 6)

A direct our-account rerun would be **highly homogeneous** with the already-submitted `54922806` (6.563)
/ `54896975` (6.669) — same notebook, only PF stochasticity differs. Per the standing rule ("do not
spend quota on a direct reproduction of the public 6.626 line that is homogeneous with 6.563/6.669"),
**no submission of a plain rerun is warranted**. Value, if any, is in *variants* (task 7), not in
re-running the identical notebook. A FAST smoke from our account is run only to confirm our-side
runnability, not to submit.

## FAST smoke result (task 4/5) — our-account reproducibility CONFIRMED

`joezzzzz/rogii-kaiwalya-6626-smoke` (same notebook + 9 datasets + GPU; prepended cell set
`FAST=1, N_TRAIN_WELLS=40, ROGII_GOLD_MAX_WELLS=40`) → **COMPLETE**.

```
[SMOKE] FAST=1 N_TRAIN_WELLS=40 ROGII_GOLD_MAX_WELLS=40
submission.csv written (14151 rows) in 48s
final submission.csv: columns [id,tvt], 14151 rows, all finite, range 11589-12240
id set AND order identical to sample_submission / 54844628
```

Our account runs the full pipeline end-to-end (imports, all 9 datasets attach, LightGBM/CatBoost GPU,
PF + model-package + prefix-calibration + overlap + bimodal stages, schema-valid write). **Reproducible
from our side.** (FAST/40-well mode → the *values* are reduced-fidelity, not the real 6.6 output; this
smoke validates runnability and schema, not the score.)

### The overlap mechanism, made explicit by the smoke's own report

`guarded_overlap_override_report.csv` for the three visible test wells:

```
well      status    ref_col  known_prefix_rmse  rows_overridden / rows_total
000d7d20  override  EGFDU    0.0101             3836 / 3836   (100%)
00bbac68  override  EGFDU    0.0090             6014 / 6014   (100%)
00e12e8b  override  EGFDU    ~0.01              4301 / 4301   (100%)
```

For all three visible wells the pipeline **overrides 100% of the toe rows** by matching each test well to
its train duplicate (via `EGFDU`, a train-only structural-surface column available precisely because
these test wells have train copies) at a near-zero known-prefix RMSE (~0.01 ft = same well). In effect
the frontier family **retrieves the train copy's toe TVT for the visible wells**. This is the concrete
source of the 6.5 public line, and it is LB-legal (uses provided data) but overlap-based.

### Direct private-risk consequence (H-visible vs H-hidden, now concrete)

- **H-visible** (private = same 3 visible wells): the override returns near-truth → the 6.5 line carries.
- **H-hidden** (private = novel wells): novel wells have no train duplicate → `status != override` →
  the pipeline falls back to base PF/beam → the line reverts toward ~7.x. **The overlap advantage does
  not transfer to novel wells.**

Structural diff (FAST smoke, indicative): 6626-line vs `54844628` rmse-diff 4.02 ft, corr 0.9999, 81% of
rows differ by >1 ft — the two lines agree on the trend but the frontier's per-row values are dominated
by the override on the visible wells.

## Final decision (tasks 5/6) — HOLD, no submission

- Reproducibility: **confirmed** from our account.
- Homogeneity: the package is byte-identical to the public source and to the already-submitted
  `54922806`/`54896975`; a rerun adds nothing.
- **No submission.** Quota preserved (0/5 today). The frontier line is teammate-owned and already
  represented on the board at 6.563.
- **Added intelligence for final selection**: the 6.5 line is substantially an overlap lookup on the
  visible wells (100% override via EGFDU), so its private value is conditional on H-visible. Our honest
  slot `54844628` (no overlap, 760-well-OOF-validated) is the H-hidden-robust hedge — the two-slot
  package in `reports/final_slot_package_corrected_gate_2026-07-23.md` covers both hypotheses.
