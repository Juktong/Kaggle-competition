# Rotation submission decisions — 2026-07-26

Every submit/HOLD decision with its reason. Submit gate: quota>0 · HARD sanity pass · not a
near-duplicate (rmse ≥ 0.50 vs every scored reference) · clear public or final-slot information value ·
stated justification · accurate description.

| round | candidate | decision | reason |
|---|---|---|---|
| 1 | G1.2 frontier component validation | **no submit (by design)** | Diagnostic only; produces no new submission artifact. Delivered the round's main findings. |
| 1 | G1.1 full-fidelity overlap-OFF ownership run | **HOLD** | Already satisfied by `54968060` (our account, our kernel, patch tracked in repo). A rerun would be homogeneous with a scored submission. |
| 1 | A3/A4/A5 frontier intermediates | **HOLD** (carried from 07-25) | Homogeneous intermediates of an already-submitted family. |
| 1 | G2.1 **SP45-projection-only** | **queued for round 2** | Passes homogeneity (rmse 1.809 vs `54968060`) and HARD sanity; best proxy RMSE (2.581). Needs its own kernel (smoke → full) before the gate can be applied. |

## Standing constraints

- Never submit a smoke/dummy output.
- Never resubmit a homogeneous plain rerun of the Kaiwalya notebook.
- A small public difference on 3 wells is not by itself a reason to submit (config-variance floor ≈0.115).
- The train-copy proxy **saturates** (near-exact retrieval buys only ~0.080 public), so a proxy gain is
  supporting evidence, never sufficient evidence.
