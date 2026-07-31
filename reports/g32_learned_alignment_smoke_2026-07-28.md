# G3.2 — learned local alignment scorer + DP (2026-07-28)

Autopilot task `g32_learned_alignment_smoke` (`requires_gpu=true`, `can_submit=true`,
`max_submit_cost=1`). **Outcome: real signal found — the first positive result in this alignment line —
but far below the deployed pipeline, so no Kaggle run and no submission. 0 quota used.**
Tool: `scripts/g32_learned_alignment_smoke.py`. Local CPU (`torch 2.12.1+cpu`, no local GPU); per the
standing rules a Kaggle GPU run is only launched after a local smoke shows signal, and the masked split
below does not support one.

## Two prior results this task had to overcome

- **2026-07-21**: a CNN/Siamese GR-window scorer reached AUC 0.636–0.647 against an NCC baseline of
  0.524 (chance). Root causes identified then: the pairing was mis-specified by **~34×** in vertical
  extent (a 64-row horizontal MD window spans a median 0.95 ft of TVT, paired against a 32 ft typewell
  window), and per-window z-scoring destroyed the level cue (level AUC 0.578 > shape 0.509).
- **2026-07-26 (G3.1)**: a DP over a `|GR_h − GR_tw|` cost matrix converged to the flat-anchor baseline
  **from above** and never crossed it.

## Design changes

1. **Matched extent.** The horizontal side is *summarised* as local features at row `i` (it has almost no
   TVT extent); the typewell side supplies a short window around the candidate state `s`. The 34× mismatch
   is removed by construction.
2. **Level cue preserved.** Features are **not** per-window z-scored, so absolute GR level enters the
   model — it was the stronger hand-coded cue.
3. The scorer emits `cost[row, state]` directly, so it drops into **the same beam DP as G3.1** and is
   compared against the same flat-anchor baseline.

Model: tiny MLP (17 features → 64 → 32 → 1), 8 epochs, CPU.

## Result 1 — the scorer is materially better than every hand-coded cue

```
training: loss 0.6880 -> 0.6015      val_auc 0.6321 -> 0.6950 (run A) / 0.7242 (run B)

on IDENTICAL validation pairs (run B):
  NCC shape (z-scored)   AUC 0.5010     <- chance, as in 2026-07-20
  level  -|GRh - GRtw|   AUC 0.6423
  LEARNED scorer         AUC 0.7242     <- +0.223 vs NCC, +0.082 vs level
```

Loss decreases, validation is well above chance, and the learned scorer beats the best 2026-07-21
architecture (0.647). **The two design corrections were the operative change**, not extra capacity — this
is a 17-feature MLP, far smaller than the CNNs that plateaued at 0.647.

## Result 2 — the DP crosses the flat-anchor baseline, unlike G3.1

```
lam    DP (learned emission)   flat-anchor   verdict
   5          16.167             13.103      worse than flat
  20          12.885             13.103      BEATS flat
  60          12.527             13.103      BEATS flat   <- interior optimum
 150          12.912             13.103      BEATS flat
G3.1 |GR diff| emission: converged to flat from ABOVE, never crossed
```

The optimum is **interior** (best at lam=60, worse at both 5 and 150), which is the signature of a
genuinely informative emission rather than a degenerate one. This is the first time in this line that a
GR-derived emission has improved on simply holding the anchor flat.

## Why this is still not a candidate

```
DP with learned emission (best)    12.527 ft
flat-anchor baseline               13.103 ft
deployed honest pipeline OOF        ~8.86 ft
```

The DP is **~42% worse than the pipeline we already have**. It beats a trivial baseline, not a useful one.
Per the task's own rule — *"Do not launch full Kaggle unless smoke and masked split both support it"* —
the masked split does not support a full run, so none was launched and the submit gate was never reached.

**Caveat on stability:** training pairs are resampled per run (the negative-offset draw is unseeded), and
between two runs the val AUC moved 0.6950 → 0.7242 and NCC 0.5548 → 0.5010. The DP conclusion is robust to
this (flat is beaten at 3 of 4 lam values), but the exact AUC figures should be treated as ±0.03.

## Disposition

**Signal recorded; direction kept open as a component, not a standalone.** The honest reading is that a
learned emission carries real alignment information that hand-written NCC/DTW costs do not — which
retires the earlier conclusion that "GR-derived emission adds nothing" (G3.1) and replaces it with a
sharper one: *pointwise hand-coded* GR costs add nothing, but a *learned, level-aware, extent-matched*
scorer does.

It is far too weak to stand alone at 12.5 ft. The only way it could matter is as an **extra emission term
inside a stronger sequential model** (the PF already integrates GR along the trajectory with a motion
model and reaches ~11.0 ft standalone). That is a larger piece of work than this task's scope and would
need its own prompt.

No submission, no Kaggle run, 0 of today's 5 quota used. `54844628` and the slot recommendation are
unchanged.

---

## AMENDMENT (same day, from N1) — the "DP beats the flat anchor" claim does not survive nesting

This report recorded "its DP beats the flat-anchor baseline (12.527 vs 13.103, interior optimum at
lam=60)". That comparison selected `lam` on the same 12 eval wells it reported.

`reports/n1_geometry_bounded_alignment_2026-07-28.md` re-ran the same DP on **40 eval wells** (a strict
superset) with the `lam` choice **nested** — chosen on one half of the wells, scored on the disjoint half:

```
POOLED HELD-OUT: DP 13.644   flat-anchor 12.722   -> does NOT beat flat
per-well: DP beats flat on 37.5% of held-out wells (n=40)
```

**What stands:** the learned scorer carries real signal — AUC **0.7242** vs NCC **0.5010** on held-out
pairs is a clean comparison and is unaffected.

**What is withdrawn:** "the DP beats the flat anchor". Under nested hyper-parameter selection it does
not. The gap in this line is in the *transition model*, not the emission.
