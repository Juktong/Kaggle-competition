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

*(Smoke running — the full O(rows × mates × window) version was too slow; a strided fast variant
[toe stride 8, 3 mates, window step 6, 25 wells] is running. Result and error-correlation with the
geometry field appended on completion. Disposition will follow the pre-registered gate: the sequence
match must both beat geometry AND decorrelate to be a candidate.)*
