# Corrected 3-well-scale validation gate (2026-07-22)

Infrastructure A. Replaces the 760-well bootstrap that let `54878409` pass and then lose on public.
Tool: `scripts/eval_three_well_gate.py` (reusable CLI + importable `three_well_gate()`).
Frame builder: `scripts/build_aligned_frame.py` → `aligned_preds.npz` (all candidates on one row order).

## Why this exists

The competition evaluates the whole test set = **3 wells / 14,151 rows**. A "stably positive bootstrap"
computed by resampling **760 wells** is the sampling distribution of a 760-well *mean* and does not
constrain a 3-well outcome. `54878409` passed that 760-well gate (5th +0.049, 99% positive) and scored
**worse** on public.

## The tool

Given any candidate + baseline per-row prediction (default baseline `s_54844628`, public 7.891):

- pooled OOF gain, per-well gain mean/median/std, helped/hurt fraction
- **3-well bootstrap**: percentiles 1/5/25/50/75/95, P(gain>0), best/worst named 3-well draw
- 760-well bootstrap — **reference only, never a gate**
- exact gain on the actual 3 test wells (`000d7d20, 00bbac68, 00e12e8b`) — OOF proxy only, since the
  train copies have a different heel/toe split than the test versions

## Corrected gate definition

- **Default pass:** 3-well bootstrap **5th percentile > 0**.
- **Conditional:** if 5th ≤ 0 but 25th > 0 — *not* an auto-pass. Requires a pre-public/test-available
  guard **and** row-split stability (`reports/row_split_stability_audit_2026-07-22.md`) before it can be
  considered for a slot.
- **Fail:** 5th ≤ 0 and 25th ≤ 0.

The 760-well bootstrap is retained in the output purely so the *gap* between the two scales is visible.

## Validation — it retro-flags `54878409`

```
candidate=s_54878409  baseline=s_54844628
  pooled OOF gain (760 wells) = +0.1802
  per-well gain: mean +0.0990 median +0.0000 std 1.3007 | helped 47.8% hurt 38.7%
  3-WELL bootstrap: 1st -2.7236 5th -1.2618 25th -0.2442 50th +0.0976 75th +0.5214 95th +1.5874
                    P(gain>0) 58.4%  worst3 -4.982 best3 +5.190
  760-well ref (NOT a gate): mean +0.1801 5th +0.0501 P>0 98.9%
  actual 3 test wells: gain +0.2906 (OOF proxy)
  CORRECTED GATE: FAIL (3-well 5th<=0 and 25th<=0)
```

Under the 760-well statistic the candidate reads as a near-certain improvement (5th +0.050, P>0 98.9%).
Under the corrected 3-well statistic it **fails** — 5th −1.26, and it only clears zero in 58.4% of
3-well draws. This matches the public outcome (−0.062) and is the discriminator that was missing.

The per-well median of exactly **0.000** is the crux: the pooled +0.18 comes entirely from an
asymmetric tail (helped 47.8%, hurt 38.7%), and a 3-well draw samples that tail with high variance.

## Usage

```bash
python3 scripts/eval_three_well_gate.py --candidate <col> [--baseline s_54844628] [--json out.json]
```
Frame columns: `dwt pf base s_54844628 s_54878409 s_a20_w25 base_k96 s_k96_aniso topk96_l75`.
Rebuild the frame with `python3 scripts/build_aligned_frame.py`.
