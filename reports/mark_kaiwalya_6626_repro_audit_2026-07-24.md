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
