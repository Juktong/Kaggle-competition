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

- kernel `joezzzzz/rogii-frontier-sp45-only-smoke` v1 — **smoke_passed** (FAST=1, 40 wells, 47 s).
  Patch proof in the log: `[G2.1] FINAL submission.csv <- sp45_projection_submission.csv rows=14151
  mean=11903.637`. Audit: HARD PASS; proxy RMSE **1.958**; rmse **2.520 vs `54968060`** → non-homogeneous.
- kernel `joezzzzz/rogii-frontier-sp45-only-full` v1 — **full_running**.
- Note: Kaggle resolved the slug from the title (`...sp45-only-smoke`, not `...sp45only-smoke`);
  `kernel-metadata.json` was corrected to match so later pushes stay on one slug.
- On smoke pass → full run → `scripts/rotation_candidate_audit.py` → submit gate.
- Pre-registered read: if it scores **below 6.643**, the frontier's post-SP45 stages are net-negative on
  the leaderboard and SP45-only becomes the stronger slot-2 candidate; if **above**, those stages earn
  their place and `54968060` stays. Either way the result is decision-relevant, which is what justifies
  the slot under the gate.

## Round 3 — 2026-07-26 15:09 UTC

**Live refresh:** today 1/5 used (4 remaining); `54990075` COMPLETE **6.690**; no local processes or
Kaggle kernels running; git clean; `origin/main` unchanged at `a589fa8`; no new teammate submission.

| item | result |
|---|---|
| **A** final-slot contradiction | **fixed** — three criteria stated separately; all converge on `54922806 + 54844628` |
| **H** simulator upgrade | **done** — adds `54990075`, family/provenance/OOF flags, measured prediction correlations; emits score-first / diversity-first / provenance-first. Fixed a tiebreak flaw treating an unmeasurable correlation as worst-case |
| **G2.1** result | `54990075` = **6.690** → the `> 6.678` branch: post-SP45 stages **earn their place**; the local proxy pointed the wrong way |
| **B / G2.2** well-level selector | **closed** — oracle margin **+0.0000**; and the proxy **inverts** the within-family ranking |
| **C / G3.1** heatmap + top-K path search | **closed** — DP converges to the flat-anchor baseline from above and never crosses it; emission adds no information |

**Submissions this round: 0** (the round's one submission, `54990075`, was made in round 2 and scored
this round). Quota 1/5 used today.

### Methodological result carried forward

Two independent findings this round converge on the same rule: **the train-copy proxy must not be used
to rank candidates that are close together.** `54990075` (proxy-best) scored worst of the frontier pair
on public, and the G2.2 table shows the proxy inverting the within-family ordering while ranking across
families correctly. Only a structural argument or a leaderboard result can separate close candidates.

## Round 4 — 2026-07-28 05:33 UTC (autopilot `live_refresh_and_decision`)

Live-refresh task only (`can_submit=false`, no heavy run). **Material state changes since round 3**, so
this status file is updated:

| item | round 3 (07-26) | round 4 (07-28) |
|---|---|---|
| daily quota | 1/5 used | **0/5 used, 5 remaining** (new day) |
| days to deadline | ~10.4 | **8.77** (2026-08-05 23:59 UTC) |
| Kaggle kernels running | 0 | 0 (`sp45-only-full`, `overlap-off-full` both COMPLETE) |
| new submissions | — | **none** since `54990075` (6.690, 07-26) |
| `origin/main` | `a589fa8` | `a589fa8` — **no new Mark/Marc commits** |
| branch vs `juktong` | in sync | in sync (0 unpushed) |
| execution model | manual rounds | **autopilot runner active** (`scripts/claude_autopilot.py --loop --sleep 900`, commits `01f2294`, `1e372e1`) |

An idle gap of ~2 days occurred between rounds 3 and 4; no work was lost and no process was left
running. The board is unchanged, so no candidate re-ranking is warranted and the final-slot package
stands as written.

### Queue decision

Next runnable task by priority: **`g35_honest_prefix_calibration`** (priority 10, `requires_gpu=false`,
`can_submit=true`, `max_submit_cost=1`). It is the correct next step: all three selection criteria place
the fully-owned honest line (`54844628`) in slot 2, so improving it has direct final-slot value, and it
needs no GPU.

**Design constraint carried into that task** (so the boundary is not rediscovered): the 2026-07-21
per-well bias analysis measured how much of a well's whole-toe bias is visible from its known heel —

```
corr(first-100-row bias, whole-well bias) = +0.213  ->  ~5% of variance
corr(first-500-row bias, whole-well bias) = +0.415  ->  ~17% of variance
```

so a prefix-derived correction can address at most a small share of the per-well bias. G3.5 should
therefore be scoped as a **bounded** correction validated by honest masked split / OOF / bootstrap, with
a modest expected effect, and must not use train-copy lookup. Sub-0.1 local gains cannot be ranked by
the train-copy proxy (retired as a ranking tool in round 3).

Following tasks in queue order: `g13_dependency_provenance_audit` (no GPU, no submit),
`g32_learned_alignment_smoke`, `g33_multi_hypothesis_smoke`, `frontier_variant_matrix_lite`,
`new_direction_search`, `status_summary_for_user`.

