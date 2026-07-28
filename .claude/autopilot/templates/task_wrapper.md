# Autopilot Task Wrapper

For each autopilot task:

1. Read `.claude/autopilot/standing_rules.md`.
2. Read the specific task prompt selected from `.claude/autopilot/prompts/`.
3. Live refresh state:
   - Kaggle submissions and daily quota.
   - Active Kaggle kernels.
   - Active local processes/watchers.
   - Git status, fetch `origin`, fetch `juktong`.
   - Mark/Marc `origin/main` changes.
   - New teammate/public kernels or submissions.
4. Execute the task, not only a plan.
5. Smoke before any long/full run.
6. Apply the submit gate before any Kaggle submission.
7. Update reports, queue state, commit, and push.
8. If the task is blocked, record the blocker and move to the next queued task.
9. Final response must be concise Chinese status including:
   - whether the job is still running;
   - active candidate;
   - Kaggle GPU/kernel status;
   - daily quota used/remaining;
   - changed files;
   - latest commit;
   - new submission and score if any;
   - slot1/slot2 recommendation by score-first, diversity-first, provenance-first;
   - next queued task.
