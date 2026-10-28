# Kaggle ROGII Wellbore Geology Prediction

This repository contains our working code, reports, experiment trackers, and Kaggle notebook forks for the **ROGII Wellbore Geology Prediction** competition.

The goal is to collaborate on high-quality, reproducible Kaggle submissions while keeping large data files, generated artifacts, and private credentials out of Git.

## Competition Summary

- Competition: ROGII Wellbore Geology Prediction
- Task type: regression / sequence reconstruction
- Target: `tvt`
- Metric: RMSE, lower is better
- Current confirmed public best in our logs: `7.235`

The problem is not a simple row-wise tabular regression problem. Strong solutions reconstruct the hidden TVT trajectory for each well using:

- known `TVT_input` prefix anchors
- GR curve alignment against typewell
- particle filtering / beam search
- well-wise smoothing and physical constraints
- public high-score stack replication

## Repository Structure

```text
.
├── scripts/                         # Utility scripts and local surrogate scoring
├── reports/                         # Progress notes and decision reports
├── experiments/                     # Lightweight experiment trackers
├── goals/                           # Operating goals and submission strategy
├── kaggle_kernel_lucifer_wellbore_wizard_pf_stack/      # current 7.235 reference
├── kaggle_kernel_degnonguidi_7159_submit/                # 7.159 reproduction target
├── kaggle_kernel_baidalin7201_v2/                        # 7.201 reproduction target
├── kaggle_kernel_henry_v10_sunny80_blend/                # artifact/physical blend candidate
├── kaggle_kernel_david_v12_budget_guarded_clean_gpu/     # 7.263 backup reference
├── requirements.txt
├── .gitignore
└── README.md
```

Not included in Git:

- `data/`
- `artifacts/`
- model files such as `.pkl`, `.ckpt`, `.pth`
- Kaggle credentials
- generated submission files

Candidate outputs should still follow the local convention in
`reports/candidate_artifact_convention.md`. Initialize a new ignored candidate
folder with:

```bash
python3 scripts/init_candidate_artifact.py --candidate-id my_candidate_v1 --family projection_branch --source-path path/to/source.csv
```

## Operating Goal

The current optimization workflow is documented in:

```text
goals/rogii_iterative_submission_optimization.md
```

Use this as the working contract for iterative submission improvement:

1. Generate candidates with a clear hypothesis.
2. Run notebooks and download outputs without spending official submissions.
3. Audit format, hidden-test compatibility, shape, and known-submission distance.
4. Run train pseudo-test CV when the method supports it.
5. Submit only candidates that pass the gate and answer a specific experiment question.
6. Record every official result in `experiments/submission_ledger.csv`.
7. Record batch questions and option choices in `experiments/question_decision_log.csv`.
8. Keep the next concrete questions in `experiments/question_backlog.csv` so each batch begins with a decision, not a vague modeling tweak.

The control loop is:

```text
specific question -> multiple feasible options -> selected option with reasoning -> execution -> batch review -> next questions
```

For each top-priority question, compare a conservative option, a structural/high-upside option, and a cheap diagnostic option when possible. The selected option should maximize information value while passing audit and avoiding pure public-leaderboard overfit.

Kaggle kernel runs are cheap compared with official submissions. Official submissions are capped at five per team per UTC day; the operating target is to use 4-5 slots when enough audited, informative candidates exist, with every submission treated as a planned experiment.

## Data Setup

Each teammate should download the competition data from Kaggle and place it locally.

Recommended local path:

```text
D:\Codex\kaggle\rogii-wellbore\data
```

Expected structure:

```text
data/
├── train/
├── test/
└── sample_submission.csv
```

If you use another path, pass it explicitly to scripts with `--data-dir`.

## Environment Setup

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install and configure Kaggle API separately. Do not commit `kaggle.json` or any API token.

## Local Surrogate Scoring

Because Kaggle submissions are limited and scoring can be slow, we use a local surrogate checker before submitting.

Run:

```powershell
python scripts\local_surrogate_score.py --data-dir D:\Codex\kaggle\rogii-wellbore\data --root . --output-dir experiments
```

Outputs:

```text
experiments/local_surrogate_scores.csv
experiments/local_surrogate_pairwise_distance.csv
reports/local_surrogate_score_report.md
```

Important: this does **not** know hidden labels and cannot exactly predict Public LB. It is mainly used to reject obviously bad or duplicated candidates before spending submissions.

Build a next-batch readiness report from surrogate scores, pending submissions, running kernels, and local validation:

```powershell
python scripts\next_batch_readiness_report.py
```

Outputs:

```text
experiments/next_batch_readiness.csv
reports/next_batch_readiness_report.md
```

Run the safe polling and refresh pass:

```powershell
python scripts\poll_and_refresh_state.py
```

This checks Kaggle kernel/submission status in dry-run mode by default, then refreshes readiness, audit summary, and the conditional submission batch plan.

Outputs:

```text
experiments/poll_refresh_summary.csv
reports/poll_refresh_report.md
```

Summarize audit evidence for the current readiness candidates:

```powershell
python scripts\candidate_audit_summary.py
```

Outputs:

```text
experiments/candidate_audit_summary.csv
reports/candidate_audit_summary_report.md
```

Build a conditional 4-5 slot submission batch plan from the audited candidate pool:

```powershell
python scripts\next_submission_batch_plan.py
```

Outputs:

```text
experiments/next_submission_batch_plan.csv
reports/next_submission_batch_plan.md
```

Check whether planned official submission slots may be released:

```powershell
python scripts\submission_release_gate.py
```

Outputs:

```text
experiments/submission_release_gate.csv
reports/submission_release_gate_report.md
```

Validate planning state consistency before any official submission:

```powershell
python scripts\validate_planning_state.py
```

Outputs:

```text
experiments/planning_state_validation.csv
reports/planning_state_validation_report.md
```

Build the result-branch matrix for pending public scores and reference kernels:

```powershell
python scripts\result_branch_matrix.py
```

Outputs:

```text
experiments/result_branch_matrix.csv
reports/result_branch_matrix.md
```

Run pseudo-test CV on training wells by hiding known-TVT suffixes:

```powershell
python scripts\pseudo_test_cv.py --data-dir data\sample --output-dir experiments --report reports\pseudo_test_cv_report.md
```

This evaluates method families, not completed `submission.csv` files. Use it to decide whether a structural idea can beat a simple visible-prefix baseline before turning that idea into a Kaggle notebook candidate.

Run the multi-hypothesis router CV harness after the 2026-07-01 architecture pivot:

```powershell
python scripts\multi_hypothesis_router_cv.py --data-dir data\sample
```

Outputs:

```text
experiments/multi_hypothesis_router_cv_scores.csv
experiments/multi_hypothesis_router_cv_summary.csv
experiments/multi_hypothesis_router_cv_decisions.csv
reports/multi_hypothesis_router_cv_report.md
```

This compares candidate TVT paths and records a naive prefix-holdout router, a guarded router, and a confidence-guarded router that can use high-confidence self-correlation evidence visible in evaluation GR. The confidence-guarded router is the current validation entry point for future geosteering-router candidates; official submissions stay blocked until this class of candidate improves pseudo-hidden validation and passes the normal audits.

Sweep nearby plateau recent-quantile parameters on the same pseudo-test splits:

```powershell
python scripts\plateau_quantile_sweep.py --data-dir data\sample
```

Use this to check whether a plateau candidate is robust across nearby windows, quantiles, and movement thresholds before spending an official information slot.

## Pre-Submit Format Audit

Before spending an official submission slot, audit the generated `submission.csv` against the current sample file:

```powershell
python scripts\pre_submit_audit.py artifacts\candidate_folder\submission.csv --sample data\sample\sample_submission.csv
```

This checks columns, row count, ID order, duplicate IDs, finite predictions, summary stats, and sha256. It does not replace hidden-compatibility source review or pseudo-test validation.

For future candidates, first create a standard ignored artifact folder:

```powershell
python scripts\init_candidate_artifact.py --candidate-id candidate_folder --family projection_branch
```

The required local files and release checklist are documented in `reports/candidate_artifact_convention.md`.

Check planned-slot manifests before release:

```powershell
python scripts\candidate_artifact_manifest_summary.py
```

Inspect final local package readiness before any official submission:

```powershell
python scripts\final_submission_package.py
```

This command does not submit to Kaggle. When release gates clear, use `--prepare --planned-slot N` only after final review to copy the exact selected output into the ignored candidate artifact folder and rerun the deep audit.

After every poll, inspect the result application plan:

```powershell
python scripts\result_application_plan.py
```

This translates pending scores, kernel state, ledger dry-run updates, release gates, and final-package gates into the next concrete action. It does not edit ledgers or submit to Kaggle.

Review per-well impact of the current planned candidates:

```powershell
python scripts\planned_candidate_well_impact.py
```

This shows whether a candidate is broad, concentrated, sparse, or single-well dominated relative to the active-account baseline.

Review pairwise diversity between planned candidates:

```powershell
python scripts\planned_candidate_diversity.py
```

This flags near-duplicate or highly redundant planned slots so blend sweeps remain deliberate calibration experiments rather than accidental duplicate submissions.

Review planned official slots with all gate and evidence signals combined:

```powershell
python scripts\planned_slot_review.py
```

This joins release gates, final-package state, per-well impact, and pairwise diversity into one slot-level review. Use it as the final planning view before packaging or submitting any slot.

Build contingency rules for planned slots after pending scores or kernels resolve:

```powershell
python scripts\planned_slot_contingency.py
```

This records which slots to keep, replace, or drop if the baseline anchor fails, Fleongg is weak/competitive, Degnonguidi completes cleanly, or the blend sweep is no longer an explicit experiment.

Build the replacement-candidate queue for redundant or weak planned slots:

```powershell
python scripts\replacement_candidate_queue.py
```

This turns contingency replacement needs into concrete build, audit, and design tasks. It is also where newly built local replacements such as GR/typewell alpha variants are tracked before they can enter readiness review.

Audit the notebook source for common hidden-test risks:

```powershell
python scripts\notebook_source_audit.py kaggle_kernel_lucifer_wellbore_wizard_pf_stack\wellbore-wizard-physics-pf-stack.ipynb
```

This source scan flags hardcoded visible wells, fixed visible row counts, static replay patterns, and unsafe train/test row-alignment copies. It is a guardrail, not a proof of model quality.

Run a deeper pre-submit audit with anchor continuity, jump/curvature checks, typewell range checks, and distance to reference submissions:

```powershell
python scripts\pre_submit_audit.py artifacts\candidate_folder\submission.csv --data-dir data\sample --reference current_best=artifacts\lucifer_baseline_repro_joezzzzz_v1\submission.csv --json-out artifacts\candidate_folder\deep_pre_submit_audit.json
```

This still cannot see hidden labels, but it helps block physically implausible outputs, near-duplicates, and candidates that drift far from known references before spending an official slot.

Use the standard reference registry for repeatable distance checks:

```powershell
python scripts\pre_submit_audit.py artifacts\candidate_folder\submission.csv --data-dir data\sample --reference-registry experiments\reference_submission_registry.csv --json-out artifacts\candidate_folder\deep_pre_submit_audit.json
```

The registry includes known-good, pending, and known-bad reference paths. Missing local artifacts are skipped as warnings so the same command can run on lean clones and fuller workspaces.

Build the first local GR/typewell structural probe from an audited baseline:

```powershell
python scripts\build_gr_typewell_light_candidate.py --baseline artifacts\lucifer_baseline_repro_joezzzzz_v1\submission.csv --data-dir data\sample --output-dir artifacts\gr_typewell_light_alpha010_v1 --alpha 0.10 --max-move 8.0
```

Generate a compact candidate decision table from local surrogate scores:

```powershell
python scripts\candidate_decision_report.py
```

Build the plateau recent-quantile probe from an audited baseline:

```powershell
python scripts\build_plateau_recent_quantile_candidate.py --baseline artifacts\lucifer_baseline_repro_joezzzzz_v1\submission.csv --data-dir data\sample --output-dir artifacts\plateau_recent_quantile_v1
```

## Submission Ledger

Official submission outcomes should be recorded in:

```text
experiments/submission_ledger.csv
```

This file tracks the candidate ID, kernel slug/version, public score, audit status, decision, and notes. Keep it lightweight and avoid adding generated outputs or private artifacts.

Sync the ledger from Kaggle's official submission list:

```powershell
python scripts\update_submission_ledger.py --page-size 50 --append-missing
```

Use `--dry-run` first when checking a new environment or when you only want to inspect pending score changes.

Batch-level questions and option choices should be recorded in:

```text
experiments/question_decision_log.csv
```

Use it to capture the concrete question, candidate options, selected option, evidence needed, result, and next question for each experiment batch.

Open strategic questions should be maintained in:

```text
experiments/question_backlog.csv
```

Use this file as the live queue of what to decide next. Each row includes the question type, decision effect, options, selected path, dependencies, and review trigger.

Kaggle kernel runs that do not necessarily become official submissions should be tracked in:

```text
experiments/kernel_run_ledger.csv
```

Use it for kernel slug, version, status, output artifact location, audit status, and next action.

Poll running kernel rows from Kaggle without editing the ledger:

```powershell
python scripts\sync_kernel_ledger.py --kaggle-bin kaggle
```

Apply terminal status updates only after reviewing the dry-run output:

```powershell
python scripts\sync_kernel_ledger.py --kaggle-bin kaggle --apply
```

## Current Public LB Notes

Confirmed useful references from our tracker:

- `7.235`: Wellbore wizard physics PF stack, current best in our logs
- `7.263`: David v12 budget guarded clean GPU
- `7.588` to `7.606`: Ricardo/Fleongg-style blends
- `7.703`: David bimodal model package branch

Rejected or risky:

- naive train TVT lookup scored extremely badly and is not a safe route
- static replay notebooks failed hidden rerun formatting
- large artifact-only transfers can fail if alignment is wrong

## Current High-Priority Directions

1. Poll and audit `Degnonguidi 7.159` preflight v6 under `joezzzzz`.
2. Poll and audit `Baidalin 7.201` preflight v1 under `joezzzzz`; source audit is now PASS after removing hardcoded demo wells, fixed-width ID parsing, and unsafe train/test `TVT_input` row copy.
3. Monitor active-account baseline and fleongg branch official submissions; treat Henry TabICL score `13.453` as negative artifact-stack calibration.
4. Use local surrogate scoring before deciding whether a generated output is worth submitting.

## Why This Repo Is Lean

The local workspace contains many pulled public notebooks and generated artifacts, but the GitHub repo intentionally keeps only the files teammates need immediately:

- core scripts
- lightweight reports and trackers
- five important Kaggle kernel forks
- setup instructions

Large outputs, pulled reference notebooks, and generated submissions are excluded to keep cloning fast and avoid accidentally publishing data or model artifacts.

## Suggested Collaboration Split

Person A: data and diagnostics

- maintain reports
- inspect bad wells and trajectory failures
- run local surrogate scoring
- verify submission sanity

Person B: modeling and Kaggle kernels

- push/run Kaggle kernels
- download outputs
- submit only audited candidates
- maintain experiment tracker

## Useful Commands

Check Kaggle submissions:

```powershell
kaggle competitions submissions -c rogii-wellbore-geology-prediction --csv
```

Sync Kaggle submissions into the local ledger:

```powershell
python scripts\update_submission_ledger.py --page-size 50 --append-missing
```

Check a kernel:

```powershell
kaggle kernels status leemarc223/<kernel-slug>
```

Download kernel output:

```powershell
kaggle kernels output leemarc223/<kernel-slug> -p artifacts\<output-folder>
```

Download or audit a completed kernel output through the project guardrails:

```powershell
python scripts\audit_kernel_output.py --kernel joezzzzz/<kernel-slug> --output-dir artifacts\<output-folder> --kaggle-bin kaggle --data-dir data\sample --reference-registry experiments\reference_submission_registry.csv
```

For an already downloaded folder, add `--skip-download`.

Submit a code-competition notebook output:

```powershell
kaggle competitions submit -c rogii-wellbore-geology-prediction -k leemarc223/<kernel-slug> -v 1 -f submission.csv -m "message"
```

## Team Notes

Use GitHub for code, reports, and experiment coordination. Use Kaggle or local storage for large data and generated outputs.

Do not commit:

- Kaggle API credentials
- competition data
- downloaded artifacts
- generated submission CSVs
- large model files
