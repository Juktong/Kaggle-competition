# ROGII Kaggle Autopilot Context for Codex

Last updated: 2026-07-31.

This file is the handoff context for using Codex after Claude Code auth expired. Treat this file, `standing_rules.md`, `templates/task_wrapper.md`, the selected prompt, `queue.jsonl`, and current reports as the source of truth.

## Operating Rules

- Continue the same project context through files. Do not depend on a hidden chat history.
- Use Codex with `model_reasoning_effort="high"` unless the owner changes it.
- Use neutral technical language. Avoid "gamble", "bet", "dead", "give up", "ceiling", and Chinese equivalents such as "赌".
- Before long work, live refresh repo state, Kaggle submissions, daily quota, active kernels/processes, and recent reports.
- Smoke/preflight before every long Kaggle run or submission.
- Submit only if the candidate passes gates and has clear public-score, private-risk, final-slot, or non-homogeneity information value.
- Do not submit smoke, dummy, plain rerun, or near-duplicate outputs.
- Commit and push completed work to branch `codex/autonomous-queue-2026-07-15`.

## Current Environment

- Repo: `/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue`
- Remote: `juktong=https://github.com/Juktong/Kaggle-competition.git`
- Upstream/teammate repo: `origin=https://github.com/Marc0823/Kaggle-competition.git`
- PR: `https://github.com/Juktong/Kaggle-competition/pull/3`
- Kaggle CLI: `/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle`
- Competition: `rogii-wellbore-geology-prediction`
- Claude auth is expired as of 2026-07-30. Codex auth is configured and usable.

## Scoreboard Anchors

- Best public: `54922806 = 6.563`, teammate `leemarc223`.
- Our best frontier: `54968060 = 6.643`, our account `joezzzzz`.
- SP45-only: `54990075 = 6.690`.
- Hedge-off: `55064411 = 6.695`.
- Honest decorrelated line: `54844628 = 7.891`.
- The final score is best-of-2 selected submissions, so slot diversity matters.

## Final Slot State

Current recommendation remains:

- Score-first / diversity-first / provenance-first: `54922806 + 54844628`.
- Our-account-first: `54968060 + 54844628`.

The slot-1 choice between `54922806` and `54968060` is an owner judgement, not something further public submissions are likely to settle. The public gap is 0.080, while Q44/Q45 recorded that the measurement/generalization structure makes this effectively tied for final-slot reasoning. Slot 2 is settled at `54844628` because it is the decorrelated member.

Final selection is a separate Kaggle UI action. It costs no submission quota. Do not assume Kaggle defaults will choose `54844628`; Q47 says doing nothing likely discards the recommended pair. Recommended final selection action by 2026-08-04 12:00 UTC / 20:00 Beijing. Hard competition deadline: 2026-08-05 23:59 UTC.

## Teammate / Mark Provenance

Q38 corrected an earlier gap: the Kaggle API exposed exact teammate kernel slugs and `scriptVersionId`s, and kernels were pullable from this account.

Key distinction:

- Mark/origin public-6.626 repro package:
  - Submission `54896975`, public `6.669`.
  - Kernel `leemarc223/rogii-kaiwalya-public-tvt-6-626-repro`.
  - `scriptVersionId=337097140`.
  - 9 datasets.
  - In `origin/main@a589fa8`.
- Current best `54922806`, public `6.563`:
  - Kernel `leemarc223/rogii-public-pf-frontier-rerun-20260723`.
  - `scriptVersionId=337355891`.
  - 7 datasets.
  - Same Kaiwalya frontier family, but with one-token GR sigma `*1.3` change.
  - Not the same run as Mark/origin's 6.626 repro package.

Q46 found that `api.kernels_output()` returns latest kernel output, not necessarily submitted-version output. The exact submitted output for `54922806` was not retrievable by API and should be downloaded from Kaggle UI version history if it is selected.

## Closed Technical Lines

- Emission/AUC lever is closed: Q17 measured that emission AUC is decoupled from DP trajectory quality.
- PF path hard selection and soft combination are closed: Q11 and Q21 found the deployed PF path is already a softmax-like combiner near optimum.
- Alignment DP transition/decoder/state-space tuning is closed:
  - Q40/N1/Q54 closed soft penalties and hard corridors.
  - Q55 showed exact Viterbi reduces objective cost but worsens RMSE; the approximate beam is protective.
  - Q57 showed dip-state augmentation can move the path but moves it in the wrong direction.
  - The remaining missing ingredient is directional content, not more transition flexibility.
- GR sigma inside the honest blend failed the 3-well gate in Q36.
- Submission ensemble is closed by Q48: best-of-2 acts like a variance option; averaging reduces option value unless it becomes a strictly better single artifact, which current evidence does not show.

## Recent Results to Preserve

- Q53 corrected the simulator: old retrieval penalty and GR-sigma transfer assumptions were canceling. The conclusion survived: slot-1 remains an ownership judgement.
- Q54 hard DP corridors failed. The DP was over-damped, not under-constrained.
- Q55 beam/soft-min decoder failed gates; exact objective optimization made RMSE worse.
- Q56 had a broad +0.2541 but failed 3-well condition.
- Q57 dip-state augmentation failed; extra mobility amplified wrong-direction emission error.
- Q58 producer completed 760 wells / 3,721,471 rows and wrote `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/q58_pf_smoothed_preds.npz`. Manual evaluator on 2026-07-31 found:
  - full-table smoother can improve apparent RMSE;
  - nested selected `8.9595` vs deployed `8.8626`, gain `-0.0969`;
  - 3-well bootstrap 5th `-1.4233`, `P(>0)=0.5684`;
  - gate fails, no submission.

## Current Queue Problem

Claude auth expired and the runner marked these as blocked with detail `Login expired`:

- `q28_measurement_traps_ledger`
- `q49_transition_prior_smoke_from_research`
- `q50_ownership_first_candidate_search`
- `q51_owner_message_pack`
- `q52_next_queue_builder_after_q38_q51`

When Codex takes over, re-queue these rows only after the Codex runner is working. Preserve their original `queue_reason`, and add `requeued_after="claude_login_expired_codex_takeover_2026-07-31"`.

## What Codex Should Do First

1. Read this file fully.
2. Read `standing_rules.md`, `templates/task_wrapper.md`, and the selected prompt.
3. Live refresh state.
4. Execute the selected task, not just plan.
5. Write a report, update `queue.jsonl`, commit, and push.
6. If a task is blocked, record the blocker and move on.
