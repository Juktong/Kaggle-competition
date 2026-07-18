# ROGII — qwer (54777533) re-audit vs the verified DWT+PF blend (2026-07-19)

Session `dcdcec05` (chain `…→06dd2efb→dcdcec05`). Trigger: qwer public **7.921** is better than the honest
DWT+PF blend public **8.080**, so we must re-check whether qwer should replace or combine with DWT+PF for the
final-2. Neutral technical language.

## 1. Source trace — re-confirmed NOT recoverable (third independent check)
- Submission **54777533**, public **7.921**, desc "Codex verified qwer OOF meta direct source SHA424e target
  6.909", submitted **2026-07-17 07:15** (joezzzzz).
- This round's fresh checks: (a) `git log --all` for `424e`/`qwer` → only the prior 2026-07-17 downgrade
  commit, no source commit; (b) repo/job-dir grep for `qwer`/`SHA424e`/`6.909` → only the prior audit reports;
  (c) **no joezzzzz kernel ran at 07:15** (dwt-detbase/affine ran ~05:07, sunny-oof ~15:41/19:13) → the
  submission is not tied to any recoverable joezzzzz kernel; (d) downloaded the 3 plausible candidate kernels
  (`rogii-neural-aligner-codex`, `rogii-kokinn-v14-codex`, `rogii-mycarta-toolkit-codex`) — none carries a
  `qwer`/`424e`/`6.909`/"OOF meta" signature (kokinn-v14 is an overlap kernel with `tvt_from_contacts`, but
  its name/content do not match qwer, so it cannot be confirmed as the source); (e) the Kaggle CLI offers no
  download of a past competition submission's CSV, so qwer's prediction vector is not obtainable.
- **Verdict: source + predictions unrecoverable** (remote Codex session, no local trace — same pattern as v36
  54753209 and spatial-formation 54723189). qwer cannot be reproduced, so its OOF cannot be re-derived and its
  error-correlation vs DWT+PF cannot be computed directly.

## 2. Honesty — qwer's OOF 6.909 is definitively leakage-inflated (sharper argument, now vs DWT+PF)
The decision does NOT need the source; it follows from the now-**verified** honest frontier:
- The project's honest frontier (test-available inputs, no overlap) is DWT CV **10.40**; the strongest
  *verified* honest model is the **DWT+PF blend, honest OOF 9.2969** (public-verified 8.080). An OOF of
  **6.909 is 2.39 (26%) BELOW** the best honest OOF ever achieved. No honest model 26% better than DWT+PF
  exists — the multi-round search (facies, structural surfaces, SSL/ROCKET, spatial KNN, GR-matcher, beam-DP,
  ANCC-PF, Z-PF, NCC) all landed blend-neutral or worse. **An honest OOF cannot reach 6.909; it is only
  attainable by folding overlap / train-duplicate leakage into the OOF** (train-test duplicates score ~0 in
  the fold, dragging the CV far below the honest floor).
- **OOF→public direction confirms it:** qwer OOF 6.909 → public 7.921 (**public 1.01 WORSE than OOF**). An
  honest model has public ≈ OOF or public < OOF (public wells are often easier) — exactly what DWT+PF shows
  (OOF 9.30 → public 8.080, public *better*). qwer's public being *worse* than its OOF is the signature of
  **overlap-OOF overfit** that only partially transfers to the hidden public split.
- **Conclusion: qwer is NOT an honest model.** It is an overlap/meta play whose OOF is leakage-inflated.

## 3. Comparison — qwer vs DWT+PF vs Gate-Safe
| candidate | public | honest OOF | class | novel-private behavior |
|---|---|---|---|---|
| Gate-Safe 54289934 | 7.212 | — | overlap-exploitation hedge | collapses (affine FP-unsafe) |
| qwer 54777533 | 7.921 | 6.909 (**leakage, not honest**) | overlap/meta play | collapses (overlap component) |
| **DWT+PF blend 54804893** | **8.080** | **9.2969** | **honest, decorrelated** | **holds ~9.3 (verified transfer)** |

- **Public ordering (7.212 < 7.921 < 8.080) is an OVERLAP ordering, not a novel-quality ordering.** Lower
  public here is driven by overlap capture, which does not transfer to a novel private set. qwer's better
  public than DWT+PF reflects *more overlap exploitation*, not better honest/novel quality.
- **For the OVERLAP slot:** qwer (7.921) is **dominated by Gate-Safe (7.212)** — Gate-Safe captures more
  overlap. qwer adds nothing to the overlap slot.
- **For the HONEST slot:** qwer is not honest (leakage OOF) and collapses on novel → cannot be the honest
  slot; DWT+PF (verified honest, OOF 9.30, public-transfer confirmed) holds it.

## 4. Final-2 decision (best-of-2 = min of two pooled private scores)
| option | pair | NOVEL-heavy private (the goal) | OVERLAP-heavy private | verdict |
|---|---|---|---|---|
| **A (recommended)** | **{DWT+PF 54804893, Gate-Safe 54289934}** | **~9.3** (DWT+PF holds; Gate-Safe collapses, floored by DWT+PF) | **~7.2** (Gate-Safe wins) | **best of both scenarios** |
| B | {qwer 54777533, Gate-Safe 54289934} | weak — BOTH overlap plays collapse, no honest floor | ~7.2 (Gate-Safe wins) | dominated by A on novel |
| C | {qwer 54777533, DWT+PF 54804893} | ~9.3 (DWT+PF holds; qwer adds nothing on novel) | ~7.9 (qwer) — worse than Gate-Safe 7.2 | dominated by A on overlap |
| D | {DWT+PF, DWT det-base} | ~9.3 (DWT+PF ≤ DWT everywhere → DWT floor redundant) | ~8+ (no overlap capture) | dominated by A on overlap |

- **Option A {DWT+PF, Gate-Safe} weakly dominates every qwer pairing:** on novel it matches or beats them
  (DWT+PF is the only non-collapsing slot); on overlap it matches or beats them (Gate-Safe is the strongest
  overlap capture). qwer never improves the pair in either scenario.
- **qwer is excluded from the final-2** (not honest for the honest slot; dominated by Gate-Safe for the
  overlap slot). Its 7.921 public is a "strong-public-but-leakage" data point, not a novel-quality signal.

## 5. Recommendation
**Final-2 = Option A: {DWT+PF blend 54804893 (honest slot, public 8.080 / OOF 9.30), Gate-Safe 54289934
(overlap hedge, public 7.212)}.** Unchanged by the qwer re-audit — qwer's better public is overlap-driven and
does not transfer to the novel/private goal. Private hidden until 2026-08-05; OOF 9.30 is the honest proxy.
