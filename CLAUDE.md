# ROGII Wellbore Geology Prediction — working directives for AI agents

These are long-term working instructions for any agent (Claude Code or otherwise) contributing
to this competition. Read them before starting work. They are set by the project owner (Joe) and
take precedence over an agent's default habits. Detailed domain knowledge, tested candidates, and
the reproduction recipe live in `reports/lessons_and_strategy_2026-07-08.md` — read that too.

Competition goal: the **final/private ranking** (novel wells), not the public leaderboard. Our
banked honest base is the DWT fork — public **9.519**, internal native-mask CV **10.40**
(submission ref 54453597). New candidates are measured against that base, not against the naive
`last_value` CV baseline.

## Directive 1 — keep searching, systematically

- The objective is **not** to stop at "no method found" and **not** a one-shot attempt. It is a
  continuous, systematic loop: propose candidate directions -> validate honestly -> record the
  evidence -> drop unsupported hypotheses -> **expand the search space and keep going**.
- Prefer **low-cost, honest, reproducible** validation first. Use train masked-CV / out-of-fold
  (OOF) as the private-ranking proxy. When a small-scale result looks promising, **scale the
  validation up before drawing a conclusion** — do not generalize from one small sample, and do
  not treat an oracle (truth-selected) result as an achievable gain.
- Keep an evidence ledger of what was tried and what was observed (in the strategy/lessons doc and
  in agent memory), so future rounds build on prior evidence instead of repeating it.
- **Submission authority:** if a candidate shows a clear, reproducible honest improvement in local
  validation (stable OOF/masked-CV gain vs the DWT base, or a stable gain on a clearly-defined
  well-family via a guarded router) **and** passes the pre-submit audit, you may submit to Kaggle
  under the established conditions **without** waiting for confirmation. Pre-submit audit:
  (a) inputs are only test-available — no train-only fields (structural surfaces, Geology) and no
  hidden-label leakage; (b) format / row order / all-finite / value range / sane diff-vs-baseline
  / notebook-source risk all pass. After submitting, **record**: submission id, public score, the
  matching commit / notebook / source, and any gap between local validation and public. Watch the
  remaining daily slots; do not spend them on clearly-weak or merely-exploratory candidates.

## Directive 2 — neutral technical language

- Do **not** use emotional or strongly-directive words in reports or docs: avoid "gamble / bet"
  ("赌"), "dead" ("死了"), "give up" ("认输"), "ceiling" ("天花板"), and similar.
- Prefer neutral technical phrasing: *candidate direction*, *validation result*, *no stable
  improvement observed*, *insufficient current evidence*, *next search space*, *submittable
  conditions*, *risk points*, *locally applicable*, *needs further validation*.
- The purpose is to support rational technical decisions. Report a negative as "candidate X: no
  stable OOF improvement vs the DWT base observed (evidence ...); moving to the next search space",
  not as "X is dead / we hit the ceiling". Wording should not imply a direction must be abandoned
  when the evidence only shows it did not improve on this attempt.

## Directive 4 — Notebook preflight / smoke test before any long Kaggle run

Set after a Sunny-OOF fork ran ~60 min on a GPU and then failed at the OOF-consolidation cell because
`oof_preds` was empty (the per-model training flags were left at 0) — a configuration error that a
5-minute smoke would have surfaced immediately. **Never launch a multi-hour Kaggle notebook / GPU / CPU
run (or a submission) before a smoke passes.** For every such run:

1. **Preflight checks (fast, before the real run):**
   - imports / file paths / packages / secrets / dataset+kernel_sources availability all resolve;
   - the notebook executes **end-to-end to the key output cell**, either fully on a tiny input or via a
     `SMOKE_RUN`/`FAST_MODE` toggle (small `TEST_SIZE`/few wells, single or 2 folds, few epochs, `nrows`).
     Confirm the *actual* output-producing cells run — not just setup (the Sunny failure passed setup and
     died at consolidation because the model cells never populated `oof_preds`).
   - for Kaggle-only pipelines: push a **short smoke kernel** (or set `SMOKE_RUN=True` in the notebook)
     and read the completed log **before** switching to full parameters.
2. **Output-format validation on the smoke output:** the submission/OOF file exists; columns correct;
   row count correct; all values finite; id set & order unchanged vs `sample_submission`; value range sane.
   (Reuse `scripts/presubmit_gate.py` / `scripts/visible_well_audit.py` where applicable.)
3. **Record** the preflight command(s), wall-time, result, and the commit / notebook ref in the round
   report or ledger.
4. **Gate:** do **not** start the full long run — and do **not** consume a competition submission —
   until the smoke passes and the output format validates. If preflight must be skipped (e.g. the smoke
   path is not representative), **write the specific reason and the risk** in the report before running.
5. **When forking a heavy public notebook,** verify the flag combination actually activates the intended
   code path on a tiny run first (model-training flags, mode flags, dataset attachments), since a fork's
   default flags rarely match the mode you want.
