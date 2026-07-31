# ROGII Status & Strategy — 2026-07-02

Snapshot of where the effort stands, what has been tried, and an honest read on
what is and isn't achievable. Written after a multi-day push on the from-scratch
router track and public-notebook reproductions.

## 1. Current Standing

- Team: `lee Marc223` (accounts `joezzzzz`, `leemarc223`).
- Best confirmed public score: **7.182** (active-account baseline reproduction),
  rank **164 / 4092** on the 2026-07-02 03:46 UTC API snapshot (top ~4.0%).
- First place: **5.262**. Gap from 7.182 = **−1.920 RMSE ≈ 46.3% MSE reduction**.
- Leaderboard cutoffs: #10 = 6.300, #50 = 6.954, #100 = 7.157.

The leaderboard has a huge **plateau at 7.10–7.30** — hundreds of teams forking
the same public stacks. We are near the front of that plateau. Below 7.10
(ranks ~20–75, 6.3–7.1) and the top-20 (5.26–6.54) use methods that are **not in
the public notebooks**.

## 2. Submission Budget

- Official limit: **5 per team per UTC day**, shared across all team members.
- Resets at 00:00 UTC. As of 2026-07-02 03:46 UTC: **0/5 used today (5 fresh).**
- On 2026-07-01 the teammate used 4/5 (see §4).

## 3. What Has Been Tried

### 3a. From-scratch candidate-router track (committed `4c58317`)
- Built a full-data pseudo-hidden CV harness (773 wells, 1546 splits, 6.33M rows).
- Prototyped a typewell segment-NCC **alignment** candidate: real signal on
  high-drift wells but naive warping runs away; a regularized version is
  0-catastrophic but only break-even; the prefix hold-out does **not** predict
  hidden-suffix wins, so simple gating cannot lift it.
- Built a minimal **typewell particle filter** (OU mean-reversion to anchor,
  prefix-calibrated σ_gr/dip). On the full 773 wells: always-on PF **14.7336** vs
  last_value **14.6844** (slightly worse); the unconditional-prior router rejects
  it. A move-magnitude-gated OOF router recovers **14.6782** (−0.0062) — the first
  full-data router improvement, but tiny.
- **Honest verdict:** this track is methodologically sound but a **leaderboard
  dead end** — it improves a *naive last_value* baseline by hundredths, while our
  7.182 already comes from a far more complete public PF+beam+NCC+ML stack.

### 3b. Tuning the existing 7.182 stack — ruled out (for now)
- The 7.182 fork (`wellbore-wizard-physics-pf-stack`) is a full PF (500×128×4) +
  beam + NCC + CatBoost/LightGBM ensemble with a per-bin selector and learned
  blend, GPU + pretrained-artifact dependent.
- Cannot be run/validated **locally** (no GPU; numba/lightgbm/catboost absent; the
  pretrained artifacts are Kaggle-only). Its cheapest knob (SP45/Fleongg blend
  weight) was already explored and flagged not worth a slot.
- Tuning it means blind ~9h Kaggle GPU runs — low-EV, hard to supervise.

### 3c. Public 7.159 / 7.153 reproductions — fragile, not landed
- Degnonguidi 7.159 fork (`joezzzzz/rogii-degnonguidi-7159-preflight-codex`):
  **7 consecutive failures.** Latest run (v7) errored after **~11 hours**
  (`DeadKernelError` in the heavy PF/beam stage); the partial `submission_A.csv`
  was **garbage** (TVT from −27561 to +12230, should be ~11000–12000). **Not
  submitted.**
- Best public score seen is **~7.153** (`rikuter67/...7153-reproduction`); it and
  the CPU repro (`takuyaando11/rogii-lb7159-public-repro`) both trip our source
  audit on `unsafe_train_test_tvtinput_row_copy` + a hardcoded well. Those authors
  scored 7.159, so the patterns are likely **safe-in-context**; the blocker has
  been getting these heavy/fragile notebooks to *run cleanly in our fork*.
- **Tooling blocker:** the current API token can push **updates to existing**
  kernels but **cannot create new** kernels (403 on new-slug push). So forking a
  clean repro into a new slug is blocked until we fix credentials (proper
  `kaggle.json`) or reuse an existing owned slug.

### 3d. Teammate's work (2026-07-01) — "affine overlay" line
Four submissions, none beat 7.182:
- 7.278 — hidden-compatible well-combo affine overlay (pred6.824)
- 7.294 — hidden-compatible strict affine overlay (pred6.994)
- 2 more probes ("high-upside", "controlled sub7") — COMPLETE but **blank score**
  (likely no valid hidden score).

## 4. Honest Strategic Assessment

- **Beating #1 (5.262) is not realistic via any approach available to us.** Public
  material tops out ~7.10–7.15; the top tier uses a fundamentally stronger
  signal/architecture not shared publicly. 7.18 → 5.26 is a different class, not a
  tuning/fork/ensemble result.
- **Realistic gain:** incremental, 7.18 → ~7.10–7.15 (up ~50–70 ranks) by landing
  a working 7.153/7.159 and/or ensembling with 7.182. Modest.
- **A dramatic leap would require original research** — e.g., a top-quality
  GR↔typewell alignment + sequence reconstruction (the PF prototype proved the
  signal exists but our implementation is too weak), or a data-structure insight
  others missed. Multi-week, uncertain, low probability of reaching the top.

## 5. Two Paths (decide before spending more effort/slots)

1. **Pragmatic (name/prize realism):** land a clean, running 7.153/7.159, ensemble
   with 7.182, aim for ~7.1. Stop grinding public-stack variants once there.
2. **Moonshot (chase the top):** stop forking plateau solutions; invest in a
   genuine best-in-class alignment/sequence model with rigorous full-data
   validation. High effort, uncertain payoff.

## 6. Coordination

The team (user, teammate, this agent) share one 5/day pool. Recent days show all
three drifting around 7.2 on separate lines (from-scratch router / 7.159 forks /
affine overlay) — **none beating 7.182**. Aligning on one target and dividing work
would stop wasting slots on parallel sub-7.18 probes.

## 7. Immediate Next Options (no slot spent yet today)

- Fix credentials (proper `kaggle.json`) or reuse an existing owned kernel slug so
  a **CPU** 7.159 repro can be run (CPU sidesteps the GPU 9h death that killed the
  Degnonguidi fork).
- Or hold at 7.182 and align with the teammate on target/division before spending
  the fresh 5 slots.

_No official submission has been made by this agent. Board score remains 7.182._
