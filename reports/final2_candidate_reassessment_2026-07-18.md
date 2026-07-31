# ROGII — consolidated final-2 candidate ledger + reassessment (2026-07-18)

Session chain `16baec36 → dacc2829 → b2229931 → 99fff121 → 276bd506`. Goal = private/final rank on NOVEL
wells. Best-of-2 = min of two pooled private scores. Neutral technical language.

## Decision ledger

| candidate | ref | public | source / provenance | classification | reproducible? | private-risk (novel) | usable in final-2? | evidence that would change it |
|---|---|---|---|---|---|---|---|---|
| **det-base DWT** | 54775625 | **9.487** | `joezzzzz/rogii-dwt-detbase-codex` (this branch, `n_jobs=1`) | **honest** GBM ensemble | **YES** | low — safe ~9.5 | **YES — honest floor (slot-1)** | a verified honest model with lower CV |
| old DWT | 54453597 | 9.519 | banked DWT notebook (`n_jobs=-1`) | honest | no (non-det) | low — ≡ det-base | yes (equiv fallback) | — |
| **Sunny PF90** | 54710185 | **8.864** | `henry_v10_sunny80_blend` (leemarc223, v34) | **honest** (leakage audit PASSED) | via fork (OOF being re-run) | **honest upside — likely < DWT** | **YES — honest 2nd slot** | its OOF CV: <10.40 confirms slot; ≈/>10.40 downgrades to public-favorable |
| Gate-Safe | 54289934 | 7.212 | Plane Top2 (banked); mechanism ≈ david_v12 `_fast_exact_recovery` | overlap hedge (affine overlay) | overlay reproducible (david_v12) but banked ref is frozen | collapses on novel (affine FP-unsafe) | fallback slot-2 (overlap scenario only) | proof private has overlap wells |
| v36 | 54753209 | 7.482 | remote Codex, source unrecoverable | overlap/spatial hedge | NO | collapses on novel | no (dominated by Gate-Safe) | recovering a reproducible source + a novel-robust mechanism |
| qwer | 54777533 | 7.921 | remote, `SHA424e` unresolved | overlap OOF-meta (leakage-inflated OOF 6.909) | NO | collapses on novel | no (excluded) | a reproducible honest OOF, not leakage |
| spatial-formation | 54723189 | 9.150 | remote Codex, no source | structural-surface guard (partial overlap) | NO | reverts to ~honest base on novel | no (unverifiable) | reproducible source + honest classification |
| B4′ exact | 54727655 | 9.864 | this branch | DWT + exact override | yes | ~= det-base (no capture) | no (dominated) | — |
| DWT+affine | 54775626 | 9.823 | this branch | DWT + affine override | yes | net-negative (+0.336) | no (FP-unsafe) | — |

## Reassessment notes (secondary objectives 1–2)
- **v36 (54753209):** source remains **not locally recoverable** (re-confirmed: no git/kernel/Codex-session
  match for `SHA424e`/"qwer"/v36; remote sessions leave no local trace). It is an overlap/spatial hedge
  weaker than Gate-Safe (7.482 vs 7.212) → **not preferred**; no reproducible variant to build.
- **Gate-Safe reproducibility:** a reproducible overlay mechanism *does* exist locally —
  `kaggle_kernel_david_v12_budget_guarded_clean_gpu` has `_fast_exact_recovery` + affine-overlay. BUT the
  prior affine analysis (2026-07-17) showed affine/exact overlays are **FP-unsafe and net-negative on novel**
  (DWT+affine scored +0.336 worse; the heel↔toe wall). Gate-Safe (banked 7.212) is the proven overlay and
  is **selectable as-is** for the overlap slot → **building a new overlay variant is low-value** (dominated
  by the banked ref; would not be submitted).
- **Stronger honest public pipelines:** the local forks (baidalin, degnonguidi, david_v12, lucifer) are all
  **koolbox-dependent and/or overlap-heavy** (non-portable per lessons §3 — 11 h feature builds, DeadKernel,
  whack-a-mole). The one honest, materially-different pipeline is **Sunny (henry v34)** — GBM ensemble +
  NCC/beam geosteering forward + Climber, leakage-clean — which is exactly the candidate under validation.
  No additional honest-different pipeline is worth a heavy run beyond Sunny.

## Current final-2 recommendation (unchanged pending Sunny CV)
- **novel / mixed (the goal): `{det-base DWT 54775625, Sunny PF90 54710185}`**
- **overlap-heavy: `{det-base DWT 54775625, Gate-Safe 54289934}`**

The one open lever is Sunny's numeric OOF CV vs DWT 10.40, being obtained via the smoke→formal fork
(`joezzzzz/rogii-sunny-oof-smoke`, then a partial formal run). See
`sunny_oof_smoke_and_fullrun_2026-07-18.md`.
