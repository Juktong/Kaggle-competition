# ROGII rotation pipeline — status (2026-07-26)

A repeating loop around the Kaiwalya/frontier line. Each round: live refresh → candidate pool update →
priority scoring → smoke → full → output audit → local/proxy evaluation → submit/HOLD → ledger update →
commit/push → next round. Stops only on a hard blocker or exhausted round budget.

## Fixed rules

**A. Live refresh (every round):** Kaggle submissions, today's UTC quota, active kernels, local
processes/watchers, `git status`, `origin`/`juktong` fetch, and whether `origin/main` has new commits.
New teammate/public kernels are recorded (source + result) before the pool is adjusted. A dirty worktree
is understood before anything is written.

**Smoke:** every Kaggle kernel gets a FAST/tiny smoke first, checking imports, dataset availability, GPU,
output path, submission schema, id order, finiteness, and **that the intended patch actually applied**.
Max 3 automatic repair attempts; then `blocked` and move to the next candidate.

**Full:** only from `smoke_passed`. Output downloaded and audited via
`scripts/rotation_candidate_audit.py` (rows=14151, columns, id order, finite, distribution, per-well
trajectory slope/jump, diff vs every scored reference, sha256, homogeneity flag). Full output is never
auto-submitted.

**Submit gate (all must hold):** quota remaining > 0; HARD sanity pass; not a plain rerun / near-duplicate
(rmse-diff ≥ 0.50 vs every scored reference); clear public or final-slot information value; report states
why the slot is worth spending; description accurate and not overstated. On submit: record ref, poll to
COMPLETE (or leave a ref-matched watcher), then update ledger / final-slot / queue.

**Never:** submit a smoke or dummy; resubmit a homogeneous plain rerun; submit on a small 3-well public
difference alone; overwrite unread changes; use emotive framing.

**State fields:** `not_started · static_audited · smoke_prepared · smoke_running · smoke_passed ·
smoke_failed · full_running · full_passed · audited · submitted · hold · blocked`.

## Round 1 — 2026-07-26 02:30 UTC

**Live refresh result:** today's quota **0/5**; no Kaggle kernel running; no local process/watcher; git
clean at `e923cd7`; `origin/main` unchanged at `a589fa8`; no new teammate kernel or submission since
`54968060`.

| ref | public | side |
|---|---|---|
| `54922806` | **6.563** | teammate (frontier overlap-ON) |
| `54968060` | **6.643** | ours (frontier overlap-OFF) |
| `54896975` | 6.669 | teammate |
| `54923144` | 6.678 | teammate |
| `54844628` | 7.891 | ours (fully-owned honest) |
| `54878409` | 7.953 | ours (excluded) |

**Executed this round:** infrastructure (`scripts/rotation_candidate_audit.py`, 5 management reports) +
**G1.2 frontier component validation** — completed from the frontier's own masked-split reports without
spending a Kaggle run. See `reports/frontier_oof_component_validation_2026-07-26.md`.

**Submissions this round: 0.** Nothing reached the submit gate; the round's output is diagnostic.

## Infrastructure

- `scripts/rotation_candidate_audit.py` — unified sanity/diff/score/homogeneity table (self-tested on
  `54968060`: HARD PASS, distinct from all scored references).
- `reports/rotation_candidate_queue_2026-07-26.md` — pool + priority scores + state fields.
- `reports/rotation_submission_decisions_2026-07-26.md` — every submit/HOLD decision with reasons.
- `reports/submission_ledger_2026-07-26.md` — daily quota and board.
- `reports/final_slot_package_corrected_gate_2026-07-26.md` — current final-2 recommendation.

## Round 2 — 2026-07-26 02:36 UTC (in progress)

**Candidate: G2.1 SP45-projection-only.** Built from the overlap-OFF notebook (retrieval stays off) with
a final cell that writes `sp45_projection_submission.csv` as the submission, and asserts row count and
finiteness so the patch cannot silently no-op.

- kernel `joezzzzz/rogii-frontier-sp45-only-smoke` v1 — **smoke_running** (FAST=1, 40 wells).
- Note: Kaggle resolved the slug from the title (`...sp45-only-smoke`, not `...sp45only-smoke`);
  `kernel-metadata.json` was corrected to match so later pushes stay on one slug.
- On smoke pass → full run → `scripts/rotation_candidate_audit.py` → submit gate.
- Pre-registered read: if it scores **below 6.643**, the frontier's post-SP45 stages are net-negative on
  the leaderboard and SP45-only becomes the stronger slot-2 candidate; if **above**, those stages earn
  their place and `54968060` stays. Either way the result is decision-relevant, which is what justifies
  the slot under the gate.
