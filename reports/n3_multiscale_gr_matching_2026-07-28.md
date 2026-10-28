# N3 — coarse-to-fine multi-scale GR matching (diagnostic), 2026-07-28

Autopilot task `n3_multiscale_gr_matching` (`requires_gpu=false`, `can_submit=false`,
`max_submit_cost=0`). Script: `scripts/n3_multiscale_gr_matching.py`. Logs:
`reports/logs/n3_{multiscale,wellsplit,seedcheck}_2026-07-28.log`. No submission; quota untouched at 0/5.

**Answer to the task's question: no decomposition level exceeds G3.2's 0.7242, and structure peaks at the
FINEST scale — multi-scale decomposition is not the remedy.** But the round is not empty: the diagnostic
located the actual lever, and it is a different one. Narrowing the *typewell window* from 17 ft to 3 ft
raises held-out-well AUC from 0.7300 to **0.7655** (+0.0355, 8.7× the seed-noise scale), and a
**no-training** level score reaches **0.7352** — above G3.2's trained 0.7242.

## 1. The scale mismatch is still present in G3.2

G3.2's docstring claims it fixed the ~34× mismatch ("MATCHED EXTENT") by making the horizontal side a
point feature. Measured on the same wells:

```
median TVT extent spanned by G3.2's 33-row horizontal window : 0.525 ft
G3.2's typewell window (TWH=8, STEP=1)                       : 17 ft     -> ~32x
```

The horizontal side sees half a foot of section while the typewell side is asked about seventeen. The
mismatch was moved, not removed — so the premise of this task holds.

## 2. Decomposition

`pywt` is not installed, so an **undecimated (à-trous) Haar** transform is implemented explicitly. It is
length-preserving, which is essential here: `tfeat` indexes the profile by state `s`, so a decimated DWT
would break the state grid.

```
A_{j+1}[n] = (A_j[n] + A_j[n - 2^j]) / 2      (edge-replicated)
D_{j+1}    = A_j - A_{j+1}
```

## 3. Phase A — AUC per level, under G3.2's exact protocol (HW=16, TWH=8)

```
band            scale        NCC      level    LEARNED
A0 (raw)           1ft     0.4971     0.6412     0.7160
A1 approx          2ft     0.5039     0.6437     0.7059
A2 approx          4ft     0.5111     0.6460     0.7030
A3 approx          8ft     0.5062     0.6439     0.6938
A4 approx         16ft     0.4975     0.6228     0.6573
D1 detail          2ft     0.4900     0.4883     0.6076
D2 detail          4ft     0.4978     0.4880     0.6327
D3 detail          8ft     0.5167     0.4863     0.6046
D4 detail         16ft     0.5074     0.4826     0.6080
G3.2 reference:                       0.6423     0.7242   (NCC 0.5010)
```

Three findings:

- **No level exceeds 0.7242.** The best is `A0` — the raw, undecomposed profile — at 0.7160, which is
  simply the G3.2 reproduction (the small gap is RNG seeding; G3.2 left its pair sampler unseeded).
- **AUC decreases monotonically as the approximation coarsens** (0.7160 → 0.6573). Smoothing destroys
  the cue rather than exposing it. Coarse-to-fine is the wrong direction here.
- **NCC sits at chance in every band** (0.490–0.517), approximation and detail alike. The shape-matching
  failure recorded in the closed scorer line is therefore **not a scale artefact** — decomposition cannot
  recover it at any scale. What carries signal is the level cue, exactly as the earlier audit found.

## 4. Phase B — the actual lever is the typewell window, not the wavelet scale

Sweeping `TWH` on the raw band. The first pass used G3.2's protocol (a random split of **pairs**), which
puts pairs from the same well on both sides; it ranked `TWH=32` best at 0.7476. Re-run with **disjoint
wells** (60 train / 40 validation) the ranking inverts:

```
TWH     window    LEARNED        NCC      level
 1         3ft     0.7632     0.5058     0.7352
 4         9ft     0.7433     0.4853     0.6652
 8        17ft     0.7331     0.4979     0.6450      <- G3.2's setting
16        33ft     0.7457     0.5394     0.6047
32        65ft     0.7482     0.4864     0.5815
64       129ft     0.7453     0.4856     0.5729
```

Seed stability (5 seeds, disjoint wells):

```
TWH=1  LEARNED  0.7632 0.7635 0.7678 0.7702 0.7628  ->  0.7655 +/- 0.0030   | level 0.7352 (no training)
TWH=8  LEARNED  0.7331 0.7258 0.7329 0.7298 0.7282  ->  0.7300 +/- 0.0028   | level 0.6450 (no training)
TWH=1 - TWH=8 = +0.0355   seed-noise scale 0.0041   ratio 8.7x
```

- **The narrowest window wins**, and the effect is 8.7× the seed-noise scale, so it is not a seed artefact.
- The **hand-coded level score** climbs from 0.6450 to **0.7352** as the window narrows — monotonically
  across all six widths. That number involves **no training at all** and still exceeds G3.2's trained
  0.7242.
- This **vindicates the extent-mismatch diagnosis and refutes the proposed remedy**: the fix is to shrink
  the typewell window to the ~0.5 ft of section the horizontal window actually spans, not to decompose
  into scales.

### Protocol warning worth carrying forward

G3.2's random **pair** split ranked the windows wrongly — it chose `TWH=32` (0.7476) where the well split
chooses `TWH=1` (0.7655), and it understated the absolute AUC (0.7160 vs 0.7331 at TWH=8). Pairs drawn
from the same well share a typewell and a GR baseline, so a pair split does not measure transfer to a new
well. **Every future scorer comparison in this line must split by well.**

## 5. Verdict and handoff

- Task question 3: **no level exceeds 0.7242**; structure peaks at the finest scale (`A0`, 1 ft), and
  every coarser approximation and every detail band is worse. Multi-scale decomposition is closed as a
  remedy for this line.
- The gate ("a level must exceed 0.7242 to be handed to N1") is **not met by any level**. It *is* met by
  the `TWH=1` window setting, but that is a window change, not a decomposition level.
- **Not reopening N1 on this basis.** N1 established the same day that the DP fails to beat the flat
  anchor under nested selection, and that the gap lies in the *transition model*, not the emission. A
  +0.036 AUC on the emission does not address that. `TWH=1` is recorded as a cheap, well-split-verified,
  seed-stable improvement available to any future alignment work, together with the fact that most of it
  is reachable with a **no-training** level score.
- Diagnostic only, as specified: no model was scaled up, no full run, no submission.
