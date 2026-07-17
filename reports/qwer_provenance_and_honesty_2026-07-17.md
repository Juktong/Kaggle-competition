# ROGII — qwer (54777533) provenance + honesty (2026-07-17)

Task 1 of the relaxed-submission round. Neutral technical language.

## 1. Provenance trace — NOT locally recoverable
- **Submission:** ref **54777533**, public **7.921**, description "Codex verified qwer OOF meta direct
  source SHA424e target 6.909", submitted **2026-07-17 07:15** under joezzzzz.
- **Trace performed:** searched the local repo + all worktrees, all Claude job dirs, all Codex session
  rollouts (`~/.codex/sessions`), `~/.claude` JSONL, and `/home`+`/tmp` for `qwer`, `SHA424e`, `424e`,
  `6.909`, `54777533`; checked `git log --all` for a `424e` commit; enumerated all `joezzzzz` kernels.
  **Result: no source.** No git commit / kernel / Codex session matches `SHA424e` or "qwer" (the only
  "qwer"/"424e" hits are random hash substrings and router-matrix floats). Codex's local sessions end
  **07-14**; qwer was submitted 07-17 by a **remote Codex session** with no local trace (same pattern as
  v36 54753209 and spatial-formation 54723189). `SHA424e` does not resolve to any local artifact.
- **Verdict: source unrecoverable → "strong public but UNVERIFIABLE".** Cannot recompute its OOF, error
  correlation vs DWT/Sunny, or audit for leakage. Per the task rule, qwer **cannot be a robust final
  slot**; it can only be an upside-only candidate — and even that is weak (see §2).

## 2. Classification from metadata + score (the parts that ARE verifiable)
- **"OOF meta ... target 6.909".** An OOF/CV of **6.909** is **below the overlap plateau (~7.2)** and far
  below the honest frontier (DWT CV 10.40; the strongest shared honest public models are ~8.1). **An
  honest OOF cannot reach 6.909** — that CV is only attainable by folding **overlap / train-duplicate
  leakage into the OOF** (the meta blends overlap-exploiting predictions, whose OOF is inflated by the
  train-test duplication the competition contains). So qwer's "6.909" is a **leakage-inflated OOF, not an
  honest CV**; it is not evidence of honest quality.
- **Public 7.921.** This is **worse than Gate-Safe (7.212) and v36 (7.482)** — i.e. qwer is the *weakest*
  of the overlap/public plays on the board, and there is a large OOF→public gap (6.909→7.921, +1.01)
  consistent with overlap-OOF overfit that only partially transfers to the hidden public split.
- **Read:** qwer is a **mixed overlap/meta candidate** whose strong OOF is leakage-driven; on a novel
  private set its overlap component collapses (like all overlap plays, cf. the affine FP analysis), and
  its honest floor is unknown/unverifiable. It is **dominated by Gate-Safe** for the overlap slot
  (7.212 < 7.921) and provides **no verifiable honest value** for the honest slot.

## 3. Decision
- **qwer is NOT recommended for any robust final slot.** As an upside-only overlap candidate it is
  dominated by Gate-Safe (better public, same class). As an honest candidate it is unverifiable and its
  6.909 OOF is leakage-inflated (not honest). **Downgraded; excluded from the final-2 pool** except as a
  documented "strong-public-but-unverifiable" data point.
- Ledger + final-2 matrix updated accordingly (`submission_ledger_2026-07-17.md`,
  `final2_decision_update_2026-07-17.md`).
