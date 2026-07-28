

## Round 14 — 2026-07-28 13:03 UTC (autopilot `n3_multiscale_gr_matching`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.

**Task question answered negatively; the diagnostic then located the real lever.**

First, the premise checks out: G3.2's docstring claims it fixed the ~34x extent mismatch, but measured on
the same wells its 33-row horizontal window spans **0.525 ft** of TVT against a **17 ft** typewell window
— still ~32x. The mismatch was moved, not removed.

`pywt` is absent, so an undecimated (a-trous) Haar transform was implemented explicitly — length-preserving,
which matters because `tfeat` indexes the profile by state.

**Phase A (AUC per level, G3.2 protocol).** No level exceeds 0.7242. Best is `A0` (raw, 1 ft) at 0.7160
— the G3.2 reproduction — and AUC falls monotonically as the approximation coarsens (0.7160 -> 0.6573 at
16 ft); detail bands sit at 0.605-0.633. **NCC is at chance in all nine bands (0.490-0.517)**, so the
shape-matching failure is NOT a scale artefact and decomposition cannot recover it. Coarse-to-fine is
closed as a remedy for this line.

**Phase B — the lever is the typewell WINDOW, not the wavelet scale.** On disjoint wells (60 train / 40
val), narrowing TWH from 8 (17 ft) to 1 (3 ft) raises AUC 0.7300 -> **0.7655** (5 seeds, +/-0.0030 vs
+/-0.0028; delta +0.0355 = **8.7x the seed-noise scale**). The **no-training** level score rises
0.6450 -> **0.7352**, monotonically across all six widths — above G3.2's trained 0.7242. This vindicates
the extent-mismatch diagnosis while refuting the proposed remedy: match the window to the ~0.5 ft the
horizontal side actually spans, rather than decomposing into scales.

**Protocol warning carried forward:** G3.2's random PAIR split mis-ranks the windows (it picks TWH=32 at
0.7476 where the well split picks TWH=1) and understates absolute AUC. Pairs from one well share a
typewell and GR baseline, so a pair split does not measure transfer. **Every future scorer comparison in
this line must split by well.**

**Not reopening N1.** N1 showed the same day that the DP fails to beat the flat anchor under nested
selection and that the gap is in the transition model, not the emission; +0.036 AUC on the emission does
not address that. TWH=1 is banked as a verified, seed-stable scorer improvement for future use.

Report: `reports/n3_multiscale_gr_matching_2026-07-28.md`. Next queued: `n6_public_solution_audit` (150).
