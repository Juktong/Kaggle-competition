# Final-slot package — 2026-07-25

Deadline **2026-08-05 23:59 UTC** (≈11.7 days out); kernels-only; 5/day; final-2 selected via the UI.
Supersedes 2026-07-23. Final selection is best-of-2 across the team's submissions.

## Current board

| ref | public | side | role |
|---|---|---|---|
| `54922806` | **6.563** | teammate | **team best-public** (PF frontier, overlap-ON) |
| `54896975` | 6.669 | teammate | Kaiwalya repro (same family) |
| `54923144` | 6.678 | teammate | frontier GR-sigma branch |
| **`54968060`** | **PENDING** | ours (this session) | **overlap-OFF diagnostic** — frontier without the visible-well lookup (H-hidden proxy) |
| `54878409` | 7.953 | ours | excluded (regression) |
| **`54844628`** | **7.891** | ours | **honest slot** (fully-owned, no overlap, 760-well-OOF-validated) |

## What this session established about the 6.5 line

The frontier's 6.5 public is **dominated by the guarded overlap override**: on all 3 visible test wells it
overrides 100% of toe rows with the train-duplicate values (matched via EGFDU, prefix RMSE ~0.01). Turning
it off (A2, `54968060`) moves predictions by ~3.2 ft rmse. Critically, with overlap OFF the frontier is
**corr 0.99997 with our honest `54844628`** — so on novel wells (no duplicates) the frontier and our
honest slot predict essentially the same thing. **The entire 6.5→7.9 public gap is the overlap lookup on
the visible wells.**

## Two-slot recommendation (min-regret across H-visible / H-hidden)

- **Slot 1 — team best-public: `54922806` (6.563)** (or a better frontier ref if one appears).
  Wins decisively under **H-visible** (private = the same 3 visible wells; overlap returns near-truth).
- **Slot 2 — our honest `54844628` (7.891).** Under **H-hidden** (private = novel wells) the frontier's
  overlap goes inert and it reverts to a line corr 1.0 with our honest slot — but ours is the one with
  760-well OOF validation and no visible-set-specific construction. It is the min-regret hedge.

This pairing is the min-regret final-2: it captures the H-visible upside (slot 1) while bounding the
H-hidden downside (slot 2). No single-hypothesis pair dominates it.

## `54968060` (overlap-OFF) — how its score updates this package

Pending. Pre-registered reading:
- **near 6.5** → the frontier's *modeling* (not just overlap) is strong; H-visible robustness is higher
  than feared, and slot 1's private value rises.
- **toward ~7.x (near our honest slot)** → 6.5 is largely the visible-well overlap; the frontier reverts
  on novel wells, confirming the H-hidden risk and reinforcing slot 2 (`54844628`) as the essential
  hedge. (This is the outcome the corr-1.0 finding predicts.)

Either way `54968060` is a **diagnostic, not a final-slot candidate** — it deliberately removes a
public-beneficial mechanism, so it will not be selected as a final submission; it informs the weighting
between slots 1 and 2.

## Standing

Our-side quota today: 1/5 used (`54968060`). Honest slot `54844628` unchanged; `54878409` excluded.
Frontier line is teammate-owned; slot-1 final say belongs to the final-selection owner. No further
our-side submission is warranted until a candidate is non-homogeneous, 3-well-gate-consistent, and
H-hidden-defensible — none exists beyond the diagnostic just submitted.
