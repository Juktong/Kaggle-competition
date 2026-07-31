---
id: new_direction_search
priority: 90
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# New Direction Search

Expand the search space only after the current queued implementation tasks are done or blocked.

Scope:

- Search beyond the direct competition: well-log alignment, geosteering, stratigraphic correlation, trajectory inversion, sequence alignment, uncertainty modeling, and industrial drilling workflows.
- Prefer sources that can become a concrete smoke test in this repo.
- Do not include directions already closed by evidence unless there is a materially different formulation.

Output:

- At least five new candidate directions.
- For each direction:
  - why it could apply to this competition;
  - how it differs from tried methods;
  - smallest smoke test;
  - expected cost;
  - submit relevance;
  - reason to queue or not queue.
- Add only queued directions that can become executable prompts.

Write:

- `reports/new_direction_search_2026-07-28.md`
- New prompt files under `.claude/autopilot/prompts/` for queued directions.
- Updated `.claude/autopilot/queue.jsonl`.
