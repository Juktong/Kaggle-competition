# Rotation submission decisions — 2026-07-26

Every submit/HOLD decision with its reason. Submit gate: quota>0 · HARD sanity pass · not a
near-duplicate (rmse ≥ 0.50 vs every scored reference) · clear public or final-slot information value ·
stated justification · accurate description.

| round | candidate | decision | reason |
|---|---|---|---|
| 1 | G1.2 frontier component validation | **no submit (by design)** | Diagnostic only; produces no new submission artifact. Delivered the round's main findings. |
| 1 | G1.1 full-fidelity overlap-OFF ownership run | **HOLD** | Already satisfied by `54968060` (our account, our kernel, patch tracked in repo). A rerun would be homogeneous with a scored submission. |
| 1 | A3/A4/A5 frontier intermediates | **HOLD** (carried from 07-25) | Homogeneous intermediates of an already-submitted family. |
| 2 | G2.1 **SP45-projection-only** | **SUBMITTED `54990075` → 6.690** | Passed all six gate conditions (quota, HARD sanity, non-homogeneous rmse 1.640 vs `54968060`, clear decision value, documented, accurate description). Result settled the post-SP45 question: the stages earn their place; the proxy pointed the wrong way. |
| 2 | H final-selection simulator upgrade | **no submit (by design)** | Analysis only. Now emits score-first / diversity-first / provenance-first separately; all three converge on `54922806 + 54844628`. |

## Standing constraints

- Never submit a smoke/dummy output.
- Never resubmit a homogeneous plain rerun of the Kaiwalya notebook.
- A small public difference on 3 wells is not by itself a reason to submit (config-variance floor ≈0.115).
- The train-copy proxy **saturates** (near-exact retrieval buys only ~0.080 public), so a proxy gain is
  supporting evidence, never sufficient evidence.

| 5 | G3.5 honest prefix calibration | **no submit (closed on evidence)** | Local smoke prerequisite failed: the deployment-honest prefix-cut signal explains only 3.5%/0.5% of toe-bias variance (in-sample upper bound); the apparent 43.4% was a same-run confound. Submit gate never reached — nothing was carried past the smoke. 0 quota used. |

| 6 | G1.3 dependency/provenance audit | **no submit (by design, `can_submit=false`)** | Analysis only. Narrowed the frontier provenance reservation from "9 third-party datasets" to one quantified dependency (≈0.047 public). Slot recommendation unchanged. 0 quota used. |

