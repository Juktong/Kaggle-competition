---
id: q19_external_solution_refresh
priority: 290
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q19 External Solution Refresh

Refresh public notebooks/repos/datasets for genuinely new strong solution ideas, but convert each find into
an executable smoke or close it.

Goal:

- Find new public methods since the last audit, including forks or repos not previously accessible.
- Prioritise methods that could beat or diversify the current frontier/honest pair.

Required execution:

1. Search Kaggle/GitHub/web if network is available.
2. For each candidate found:
   - provenance/license/rules;
   - public score if visible;
   - method family;
   - whether it is redundant with frontier/honest;
   - smallest smoke.
3. Queue only 1-3 executable follow-up prompts with clear evidence.
4. If a public method has a valid kernel path and clear score value, smoke before any full run.
5. Submit only if the gate passes and it is not a plain duplicate.

Write `reports/q19_external_solution_refresh_2026-07-29.md`.
