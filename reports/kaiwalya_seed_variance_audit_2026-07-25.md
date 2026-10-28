# Kaiwalya/PF-frontier seed-variance audit (A1, 2026-07-25)

Purpose: size the family's run-to-run variability so we do not over-read a 0.03–0.08 public delta.
**No submission.** Two independent lines of evidence.

## 1. The frontier pipeline is DETERMINISTIC given its seed config (code-proven)

In the notebook, every stochastic PF step is preceded by `np.random.seed(seed_base + s)` inside the
per-seed loop (`_pf_lik_allseeds`, `lik_pf`), with `seed_base = 0` as a fixed default. A scan for
unseeded randomness (`np.random.randn/uniform/...` outside a seeded block, `default_rng()`) finds none —
all such calls are downstream of the per-seed `np.random.seed`. Therefore:

- **Re-running the identical notebook produces bit-identical output** (same-config variance = 0).
- The observed public spread **6.563 / 6.669 / 6.678** across `54922806` / `54896975` / `54923144` is
  **CONFIG variance** — those are different branches ("PF frontier rerun", "GR sigma 1.0 branch",
  "bimodal midpoint reproduction"), not repeated runs of one config. Range **0.115**, std ≈ 0.047.

**Actionable noise floor**: a public delta **< ~0.11** between two *different* frontier configs is within
the family's config-sensitivity; a delta between two *identical* configs is 0. So only a public move
larger than ~0.11 (or a change that is structurally motivated) should be treated as real signal.

## 2. Local PF seed-variance proxy (ft-scale, on the 3 test wells)

The frontier PF is deterministic given `seed_base`, but *how much* would output move if `seed_base`
changed? Measured with the local single-seed PF (`scripts/a1_pf_seedvar.py`, 4 seed bases 0/1000/2000/3000
— a proxy, not the frontier PF):

```
000d7d20: per-row seed std 0.230 ft  (p95 0.64, max 0.92)   pairwise seed-pair RMSE mean 0.469
00bbac68: per-row seed std 2.219 ft  (p95 7.64, max 8.32)   pairwise seed-pair RMSE mean 4.825
00e12e8b: per-row seed std 4.001 ft  (p95 5.91, max 8.01)   pairwise seed-pair RMSE mean 6.733
POOLED  : per-row seed std mean 2.222 ft, median 0.469, p95 7.395
```

Two of the three wells (00bbac68, 00e12e8b) are **highly seed-sensitive** at the single-seed level
(pairwise RMSE up to 6.7 ft). Three caveats make this an **upper bound** on the frontier's actual
seed sensitivity:

1. **The frontier uses 128-seed likelihood-weighted ENSEMBLES** (`n_seeds=128`), which average the
   per-seed noise down by ≈ 1/√128 ≈ 11×. So the frontier's `seed_base`-to-`seed_base` variance is far
   smaller than this single-seed proxy.
2. **On the visible wells the overlap override pins the output** to the train-duplicate values, so PF
   seed variance is irrelevant there (variance ≈ 0 on the scored visible wells under overlap-ON).
3. This is my local PF, architecturally similar but not the frontier's exact PF.

## Synthesis

- **Same-config reruns**: 0 variance (deterministic) — no reason to rerun the identical notebook.
- **Config-to-config**: ~0.11 public range across frontier branches — the interpretation floor.
- **Underlying PF seed sensitivity**: large per-well at single-seed (up to ~7 ft), but ensembled away by
  the 128-seed mean and moot on overlap-pinned visible wells.

**Consequence for the queue**: do not read a sub-0.11 public difference between frontier variants as
signal; and any variant's value must come from a *structural* difference (e.g. overlap-OFF changing the
H-hidden path), not from seed/config jitter. No submission from A1.
