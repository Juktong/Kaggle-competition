# Q20 — usage-aware queue builder: Q10–Q19 consolidated, queue cut 16 → 5, prompt bloat fixed

Date: 2026-07-29
Task: `q20_usage_aware_queue_builder` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **management round completed. No submission (the task forbids one). Quota untouched at 0/5.**

## 1. Usage — a compounding prompt-bloat defect, found and fixed

`sent_log.jsonl` records the prompt size sent each round:

```
q16  15,919      q17  15,949      q18  49,212      q19  49,513      q20  49,806
```

A **3.1× jump in one round**. Cause: the runner's live-status block ran

```
ps -eo pid,ppid,stat,etime,cmd | egrep 'claude|kaggle|...' | head -30
```

with the `cmd` column **untruncated**. An autopilot Claude carries its *entire prompt* on its command
line, so each round's `ps` embedded the previous round's full prompt — which had itself embedded the one
before it. This compounds: once a 49 k-char process appears in `ps`, the next prompt would carry it again.

**Fixed** in `scripts/claude_autopilot.py` by adding `cut -c1-200` before `head`. Measured on the live
process table this round:

```
untruncated  34,940 bytes
truncated     2,373 bytes
saved        32,567 bytes per round
```

That accounts for essentially the whole 15.9 k → 49.8 k jump. Every process line remains identifiable at
200 chars. This is the single highest-leverage change available this round, because it applies to every
future round.

## 2. Tasks completed, Q10 → Q19

| task | outcome | submission |
|---|---|---|
| Q10 TWH=1 scorer as DP emission | first nested win over the flat anchor (12.170 vs 12.722), still ~37% worse than deployed | none |
| Q11 TWH=1 PF path ranker | every arm worse than the PF mean path; first reliably **negative** achievable margin | none |
| Q12 coverage-gated self template | closed | none |
| Q13 hybrid emission | pointwise clearly better, trajectory clearly **worse** — sign reverses through the DP | none |
| Q14 bimodal hedge weight scan | hedge manufactures +1.81 ft of bias on `00e12e8b` | **`55064411`** (PENDING) |
| Q15 frontier dependency replacement | not started — needs a frontier full run that must not overlap one in flight | none |
| Q16 residual router | **closed at prerequisite**: signed-residual CV R² **−0.0802** by well | none |
| Q17 tiny GPU training | **HOLD**: emission lever closed; AUC decoupled from DP quality | none |
| Q18 final-pair stress | the **0.080** deciding slot 1 is unresolvable at 3-well scale | none |
| Q19 external refresh | the public 6.213 kernel is our base **plus one token**; fails the 3-well gate | none |

**Ten rounds, one submission** (`55064411`, from Q14). Every other round closed on evidence without
spending a slot.

## 3. Submissions, quota, standing

| | |
|---|---|
| submissions used in Q10–Q19 | **1** (`55064411`) |
| `55064411` status | **PENDING ~6.5 h**; kernel `COMPLETE`, `failureMessage` null → Kaggle-side stall |
| quota today (2026-07-29 UTC) | **0 / 5 used, 5 remaining** |
| private-score visibility | **none**, for any submission |
| deadline | 2026-08-05 23:59 UTC → ~**35 slots** remain in total, **none allocated** |
| public standing | LB leader 4.679; 200th 6.389; our best 6.563 → outside the top 200 |

## 4. Retained signals — what still has a concrete smoke and a plausible gain

1. **GR-sigma widening** (Q19). One token, `gs * 1.5`. Nested **+2.3513** on the standalone PF with 1.5 a
   confirmed **interior** optimum. Fails the 3-well gate and is tail-driven (helps 41.7% of wells) — but
   the PF is only a **0.5-weight** blend component and Rule #1 says averaging damps tails. Concrete smoke
   exists (`scripts/q19_gr_sigma_multiplier_smoke.py`, `_GS_MULT` flag already merged, default 1.0).
   → **`q36_gr_sigma_in_blend_oof`**.
2. **Soft combination over the 96 stored PF paths.** Q11 closed path *ranking* — hard selection. Soft
   *averaging* is the class Rule #1 says transfers, and `topk96_paths/` already holds 773 wells × 96 paths
   with truth, so nothing needs regenerating. → **`q21_pf_path_soft_combiner`**.
3. **`55064411`'s score**, with the reading **pre-registered** in Q19 §4 before the number lands.
   → **`q22_frontier_hedgeoff_score_response`**.

## 5. Closed directions — do not re-queue

Post-hoc residual correction on the deployed line (Q16: sign unpredictable, R² −0.0802, generalising the
older closure to the full test-available feature set) · emission/scorer improvement validated on AUC or
any pointwise metric (Q17: AUC decoupled from DP quality; subsumes the Q13 rule) · PF path **ranking**
(Q11) · coverage-gated self template (Q12) · hybrid emission (Q13) · `contact_gated_anchor` profile (Q19:
upstream records it as an underperforming ablation, and it is not what the 6.213 kernel runs) · per-well
hand-fitted shifts (Q19 Find B) · single-dip reparametrisation, images-as-input, exact typewell grouping,
per-well confidence gating, increment-target field, geometry band, multi-scale decomposition, azimuth
filtering, Q3D tortuosity, self-correlation (N-series).

**Still open and untested:** the **transition model** in the alignment line. Q17 says nothing against it;
Q10 and N1 both identify it as the remaining lever.

## 6. Queue rebuilt: 16 queued → 5 active

The task allows adding at most 5 prompts. **Zero new prompts were added** — the round instead pruned an
over-full queue against the evidence. The runner selects the lowest-priority row with `status == "queued"`,
so any other status is inert and safe.

| # | task | why it survives |
|---|---|---|
| 500 | `q33_controlled_submission_budget_plan` | cheap, and ~35 slots to the deadline are unallocated; **owns the endgame schedule** |
| 510 | `q36_gr_sigma_in_blend_oof` | strongest evidence-backed candidate; slot-2 (fully-owned) path |
| 520 | `q22_frontier_hedgeoff_score_response` | fires when `55064411` lands; reading pre-registered, so decisive |
| 530 | `q21_pf_path_soft_combiner` | averaging class; artifacts already exist |
| 540 | `q30_competition_rules_final_audit` | cheap and load-bearing before the final selection is locked |

`q37_frontier_gr_sigma_public_repro` stays **blocked** behind `q36`. **11 tasks deferred**, each with a
recorded reason in `queue.jsonl`; the substantive ones:

- `q26` / `q27` public research — Q19 established the published pool tops out at 7.06–8.86 and the ~200
  teams at 4.7–6.4 have **not** published, so further sweeps have low expected value;
- `q23` / `q24` frontier stage-localiser and variance control — both need frontier full runs to resolve
  differences Q18 showed the decision no longer depends on;
- `q31` teammate repo refresh — Q19 already audited `origin/main`'s `a589fa8` as redundant;
- `q34` — duplicate of this task;
- `q32` — **merged** into `q22` so two tasks do not poll the same submission.

### A deferral risk, handled explicitly

`q29_final_slot_candidate_packager` and `q35_status_summary_for_owner` are **deadline-critical** but were
deferred as premature (they depend on `55064411` and on `q36`). Deferred rows are never picked, so
`q33`'s prompt was amended to make **re-queueing them its explicit responsibility**, with the budget facts
stated inline. Flagging this because it is the one way this pruning could lose something that matters.

## 7. What was changed

- `scripts/claude_autopilot.py` — `cut -c1-200` on the process table (parses OK; 32,567 bytes/round).
- `.claude/autopilot/queue.jsonl` — 5 active, 11 deferred with reasons, 1 blocked.
- `.claude/autopilot/prompts/q33_...md` — endgame-scheduling duty + budget facts.
- `.claude/autopilot/prompts/q22_...md` — absorbs the score-watcher; pre-registered reading inlined.

## 8. Limits

- The prompt-size fix is verified by measurement on the current process table and by an `ast.parse` of the
  runner, **not** by a full round having run through it. The next round's `sent_log` entry is the real
  confirmation.
- Deferral is a judgement about expected value, not proof that those directions are unproductive. Each
  reason is recorded so any of them can be reinstated by editing one status field.
- Claude token usage is not directly observable here; `prompt_chars` from `sent_log.jsonl` is the proxy
  used, and it measures input size only.

## 9. Next

`q33_controlled_submission_budget_plan`.
