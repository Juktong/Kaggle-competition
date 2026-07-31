# Kaggle API Workflow

This document describes how this project uses Kaggle API access without committing local credentials, virtual environments, downloaded data, generated submissions, or Kaggle output artifacts.

## Repository Roles

The public GitHub repository should contain:

- reproducible project code in `scripts/`;
- selected Kaggle notebook source folders that are safe to share;
- planning records in `goals/`, `experiments/`, and `reports/`;
- documentation such as this file.

The local Kaggle API workbench should stay outside the repository:

```text
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/
```

That folder is for local authentication, API smoke tests, kernel pushes, kernel status polling, output downloads, and submission commands. It may contain a virtual environment, temporary outputs, and local-only configuration, so it should not be merged into this public repo.

## Never Commit

Do not commit any of the following:

- `kaggle.json`, API tokens, `.env`, access tokens, or credential text files;
- `.venv/`, `venv/`, or other Python environments;
- Kaggle competition data, downloaded notebook outputs, model binaries, and generated `submission.csv` files;
- smoke test outputs or temporary Kaggle API downloads.

The repository `.gitignore` is configured to keep these out, but always check `git status` before committing.

## Local API Environment

Use the local workbench virtual environment for Kaggle CLI commands:

```bash
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle --version
```

Recommended credential handling:

1. Create an API token from Kaggle account settings.
2. Store credentials only in a local Kaggle-supported location such as `~/.kaggle/kaggle.json`, or a local-only workbench path.
3. Ensure credential files have restrictive permissions when using legacy `kaggle.json`.
4. Never copy credential files into this repository.

## Common Commands

Check recent competition submissions:

```bash
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle competitions submissions rogii-wellbore-geology-prediction --csv --page-size 8
```

Push a prepared Kaggle notebook folder:

```bash
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle kernels push -p working/<kernel_folder>
```

Check kernel status:

```bash
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle kernels status <owner>/<kernel-slug>
```

Download kernel output for local audit:

```bash
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle kernels output <owner>/<kernel-slug> -p artifacts/kernel_outputs/<kernel_slug>_vN
```

Submit only an audited Kaggle notebook output:

```bash
/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle competitions submit rogii-wellbore-geology-prediction -k <owner>/<kernel-slug> -v <version> -f submission.csv -m "<message>"
```

For this competition, official submissions should come from Kaggle Notebook outputs, not from arbitrary local CSV uploads.

## Safe Submission Loop

The intended loop is:

1. Prepare or fork a Kaggle notebook under `working/`.
2. Confirm the notebook is hidden-test compatible:
   - no hardcoded visible test well IDs;
   - no fixed row-count assumption;
   - no static visible-test `submission.csv` replay;
   - dynamic test file discovery;
   - final output named exactly `submission.csv`.
3. Push the notebook to Kaggle under the active account.
4. Wait for the kernel to finish.
5. Download the Kaggle-generated output into ignored `artifacts/`.
6. Run local source/output audits.
7. Submit only if audits pass and the current release gate permits the slot.
8. Poll for public score.
9. Update `experiments/` ledgers and `reports/` before the next official submission.

## Polling Cadence

Kaggle polling is a lightweight API read. It does not consume official submissions and does not rerun notebooks.

- During the first hour after a submission, poll every 10-15 minutes if the result controls the next decision.
- After one hour, slow down to every 30-60 minutes unless the UTC day is close to ending.
- Do not regenerate all reports on every poll unless a status, score, kernel state, or tracked planning artifact changes.

## Public Repository Safety

Both configured GitHub remotes are public:

- `https://github.com/Juktong/Kaggle-competition`
- `https://github.com/Marc0823/Kaggle-competition`

Because the repository is public, keep Kaggle API credentials and local workbench state out of Git. Commit only reusable code, safe notebook sources, planning records, and human-readable reports.
