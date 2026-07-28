# ROGII Claude Autopilot Standing Rules

These rules apply to every autopilot task in this repository.

## Session and execution

- Continue the same ROGII Claude context by using `claude --resume`; do not start unrelated research sessions.
- Use `--effort max` and `--model opus` unless the owner changes this rule.
- Before starting work, live refresh current state instead of trusting stale reports.
- If a background Claude job or Kaggle kernel is already running, do not launch a duplicate full run.

## Language

- Use neutral technical language.
- Avoid emotional or directive wording such as "gamble", "bet", "dead", "give up", "ceiling", and Chinese equivalents like "赌".

## Kaggle run gates

- Every long Kaggle run must pass a representative smoke/preflight first.
- Smoke must check imports, dataset availability, GPU availability when needed, intended patch activation, output path, schema, row count, id order, finite values, and sane value range.
- Full runs are allowed only after smoke passes.
- Never submit smoke, dummy, plain rerun, or near-duplicate outputs.
- A candidate may be submitted without additional user confirmation only if it passes the submit gate and has clear leaderboard or final-slot information value.

## Submit gate

All conditions must hold:

- Daily submission quota remains.
- Output audit is a hard pass.
- The output is not a smoke/dummy/plain rerun/near duplicate.
- The result has clear public-score, private-risk, final-slot, or non-homogeneity information value.
- The report states why the submit is worth one quota slot.
- The Kaggle description accurately states the purpose and does not overstate expected gain.

If submitted, record submission ref, score, commit, kernel slug/version, output hash, reason, and quota usage.

## Documentation

After each task stage, update relevant reports and the autopilot queue.
At minimum, consider:

- `reports/rotation_pipeline_status_2026-07-26.md`
- `reports/rotation_candidate_queue_2026-07-26.md`
- `reports/rotation_submission_decisions_2026-07-26.md`
- `reports/submission_ledger_2026-07-26.md`
- `reports/final_slot_package_corrected_gate_2026-07-26.md`

Commit and push completed work to the existing PR branch. Do not open a new PR unless explicitly required.

## Current anchor facts

- Best public: `54922806 = 6.563`.
- Our best frontier overlap-OFF: `54968060 = 6.643`.
- SP45-only: `54990075 = 6.690`, so post-SP45 frontier stages are useful on public.
- Fully-owned honest hedge: `54844628 = 7.891`.
- Current final-slot package separates score-first, diversity-first, and provenance-first criteria.
