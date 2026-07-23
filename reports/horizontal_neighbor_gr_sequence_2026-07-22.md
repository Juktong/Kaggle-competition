# Horizontal-neighbour GR sequence alignment (2026-07-22)

Direction 5. The remaining L5 shape: use GR **as a sequence** referenced against neighbouring
**horizontal** wells (not the vertical typewell), to see whether it picks a better TVT than the
geometry-only structural field and whether its error decorrelates. Tool: `scripts/hneighbor_gr_smoke.py`.

## Method (smoke)

For each target toe row: take surviving group-mates (same MIN_SEP=150 ft duplicate guard); for the
geometrically-nearest mate point, slide a GR window (NCC) along the mate's trajectory to find the best
local GR match; transfer that matched point's `r = TVT + Z`. Compare to the geometry-nearest transfer.
Crude global anchor for the smoke (the deployed per-well heel anchor is used in the full field).

## Context that bounds the expectation

Two prior results bound this direction before it runs:
- **Pointwise GR difference → TVT difference: 0.0% variance explained** (2026-07-21). A GR value is
  consistent with many depths because the typewell GR profile is non-monotonic.
- **Learned GR window scorer (CNN/Siamese): AUC 0.66**, and the incumbent NCC baseline is 0.52 (chance)
  — local GR shape is a weak discriminator (2026-07-20).

A horizontal-neighbour sequence match inherits the same GR-shape weakness, so the smoke is expected to
show at most a small, correlated effect. It is run to confirm rather than assume.

## Result

**No result was produced.** The full O(rows × mates × window) smoke was too slow and was killed at
0/40 wells; the strided fast variant was relaunched but its process did not survive the session teardown
and produced no output file (`hnbr2.out` absent). The stale "smoke running" status and its background
waiter were cleaned up on 2026-07-23.

**Status: stale waiter killed; no active smoke process found; result unavailable — needs rerun.**

Priority note: given the medium-scale PF-variant outcome (standalone signal vanished at 60 wells) and
the direction-C transfer threshold, this direction's expected value is bounded by the same prior GR-shape
weakness (pointwise 0.0% variance, CNN AUC 0.66). A rerun is queued behind any direction with a concrete
transfer argument, not ahead of it.
