# CNN/Siamese GR local scorer — root-cause diagnosis and GPU decision (2026-07-21)

**Direction 5** of the continuous optimization queue.
Status: **Kaggle GPU deliberately NOT spent this round.** The pre-registered gate is not met, and the
reason is now quantified rather than guessed. Script: `scripts/siamese_v2.py`.

## What the previous round left open

`reports/cnn_siamese_gr_scorer_smoke_2026-07-20.md` reported val_auc 0.605 → **0.657** and
pre-registered two criteria for continuing: a GPU run reaching **val_auc ≳ 0.75**, or a mini-DP result
showing the learned cost beats the NCC cost.

That round had a gap: **it never measured NCC on the same pairs.** An AUC of 0.657 is uninterpretable
without the incumbent's number — it could be far above or far below the cost the PF already uses.

## What was added

`scripts/siamese_v2.py` scores four things on **identical validation pairs**:

0. **NCC baseline** — the incumbent hand-coded emission cost, no learning
1. Siamese + avgpool — the 2026-07-20 architecture (reproduction)
2. Siamese + flatten — same encoder, **position-preserving** pooling
3. Joint 2-channel CNN — both windows as input channels, so local differences are computable in layer 1

Variants 2 and 3 test a specific hypothesis: `AdaptiveAvgPool1d(1)` makes the encoder
translation-**invariant**, which would be antithetical to a task whose entire signal is a translation
offset.

## Result (80 wells, 6 epochs, 40 k pairs, CPU, 85 s)

```
NCC (incumbent)        0.524
siam_avg  (old arch)   0.636   +0.112 vs NCC
siam_flat (pos-keep)   0.636   +0.112 vs NCC
joint_2ch              0.647   +0.123 vs NCC
```

Per-epoch, all three architectures **plateau at epoch 3–4 while training loss keeps falling**
(e.g. joint_2ch: 0.686 → 0.637 loss, val_auc 0.595 → 0.647 → 0.631). That is overfitting against an
information ceiling, not underfitting.

**The translation-invariance hypothesis is refuted.** Position-preserving pooling scored *identically*
to average pooling (0.636 vs 0.636), and the joint 2-channel model added only +0.011. Architecture is
not the binding constraint. Recording this explicitly because it was my stated reason for building
variants 2 and 3.

## Root cause — quantified

The pairing itself is mis-specified by roughly **34×** in vertical scale:

| | TVT span of section covered |
|---|---|
| horizontal 64-row MD window | **median 0.95 ft** (p10 0.18, p90 40.5) |
| typewell window it is paired against | 64 × 0.5 ft = **32.0 ft** |

**71.3%** of horizontal windows span **< 2 ft** of TVT; **82.9%** span < 5 ft. This is the expected
geometry: a horizontal well runs nearly parallel to bedding, so a local MD window barely moves through
section. The "positive pair" therefore compares roughly one foot of section against thirty-two feet of
it. There is almost no vertical GR *shape* in the horizontal window to match — which is exactly why NCC
sits at chance.

A second, compounding flaw: **per-window z-scoring destroys the one cue that survives.** On raw
(un-normalized) windows:

```
shape match (NCC on z-scored windows)      AUC 0.509   <- the incumbent formulation
LEVEL match  -|mean(GR_h) - mean(GR_tw)|   AUC 0.578   <- destroyed by z-scoring
spread match -|std(GR_h)  - std(GR_tw)|    AUC 0.531
learned CNN (free to combine cues)         AUC 0.647
```

Absolute GR level is the stronger hand-coded cue, and normalization removes it before either the NCC
baseline or the Siamese encoder can see it. The learned scorer beats every individual hand-coded cue,
so there **is** real signal being extracted — but the formulation caps how much exists to extract.

## Decision

**Do not spend Kaggle GPU on this formulation.** Justification against the pre-registered criteria:

- The gate was val_auc ≳ 0.75. Three structurally different architectures converge to 0.64.
- The failure mode is overfitting (train loss ↓, val AUC flat), so more capacity or more epochs — the
  things GPU buys — would move it the wrong way. More *pairs* might add a little, but not +0.11.
- The honest repair (compare at matched TVT extent, using GR level rather than z-scored shape) is
  precisely what the **PF emission model already implements**, and the PF already yields OOF 10.9952
  standalone and is in the deployed blend. A rebuilt local scorer would converge toward an incumbent we
  already have rather than adding a decorrelated source.

This is a case where the tiny→medium protocol paid for itself: ~90 s of CPU plus two diagnostic
measurements replaced a multi-hour GPU run and produced an explanation instead of just a weak number.

## What would reopen this line

Not a bigger encoder. A **different formulation** with genuine vertical extent — e.g. scoring an entire
trajectory segment (hundreds of feet of TVT excursion) against the typewell, i.e. a learned DTW/DP cost
rather than a local window cost. That is a different model class from the one tested here and would need
its own OOF against the DWT+PF base before any GPU commitment.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
MAXW=20 EPOCHS=1 MAXPAIRS=8000  python3 scripts/siamese_v2.py   # tiny smoke, ~6 s
MAXW=80 EPOCHS=6 MAXPAIRS=40000 python3 scripts/siamese_v2.py   # medium, ~85 s
```
Artifacts: `siamese_v2.json`, `siamese_v2_med.json` in `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/`.
