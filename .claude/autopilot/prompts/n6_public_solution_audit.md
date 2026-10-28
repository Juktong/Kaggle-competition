---
id: n6_public_solution_audit
priority: 150
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# N6 Audit of a second public solution

Survey `aaryan2203/rogii-wellbore-geology-prediction-argon` for formulations not present in our evidence
ledger.

Context:

- We already integrated and audited one public solution (Kaiwalya; the `54896975` / `54968060` family).
  A second independent public solution is a cheap source of formulations and an independent check on
  which of our closed lines others also found unproductive.

Constraint carried explicitly:

- **Methods and code only.** No external training data and no public dataset is to be used before the
  competition rules are confirmed and the rule basis is written down in the report.

Required execution:

1. Read the repository's method description and source.
2. Produce a table of {its component -> our evidence status}: already deployed, closed on evidence with
   the reference, or not yet tried.
3. For anything in the third category, state the smallest smoke and whether it is worth queueing.
4. No code execution from the repository and no data import.

Write:

- `reports/n6_public_solution_audit_2026-07-28.md`
- New prompt files only for items that clear the "not yet tried and cheap" bar.
