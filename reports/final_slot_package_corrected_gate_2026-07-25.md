# Final-slot package — 2026-07-25

Deadline **2026-08-05 23:59 UTC** (≈11.7 days out); kernels-only; 5/day; final-2 selected via the UI.
Supersedes 2026-07-23. Final selection is best-of-2 across the team's submissions.

## Current board

| ref | public | side | role |
|---|---|---|---|
| `54922806` | **6.563** | teammate | **team best-public** (PF frontier, overlap-ON) |
| `54896975` | 6.669 | teammate | Kaiwalya repro (same family) |
| `54923144` | 6.678 | teammate | frontier GR-sigma branch |
| **`54968060`** | **6.643** | **ours** | **overlap-OFF frontier** — 2nd best on the board; live slot-2 candidate (H-hidden proxy) |
| `54878409` | 7.953 | ours | excluded (regression) |
| **`54844628`** | **7.891** | ours | **honest slot** (fully-owned, no overlap, 760-well-OOF-validated) |

## What this session established about the 6.5 line (REVISED by the 6.643 result)

The overlap override is mechanically large on the visible wells: it overrides 100% of toe rows with
train-duplicate values (matched via EGFDU, prefix RMSE ~0.01), moving predictions by ~3.2 ft rmse.
**But its measurable public contribution is small.** With overlap fully OFF, `54968060` still scores
**6.643** — only +0.017 vs its own family reference (6.626) and +0.080 vs the best overlap-ON branch
(6.563), both at/below the ~0.115 config-variance floor established in A1.

**Correction to the earlier hypothesis.** The framing "the entire 6.5→7.9 gap is the overlap lookup" is
**not supported by the public result**. The decomposition is:

```
7.891 (our honest) -> 6.643 (frontier, overlap OFF) = 1.248   <- frontier MODELING (PF/beam/SP45/prefix)
6.643 -> 6.563 (best overlap-ON branch)             = 0.080   <- overlap + config, within noise
```

`54968060` also **outscores two overlap-ON family members** (6.669, 6.678), which is only possible if the
modeling, not the lookup, carries the score. The prediction-space corr 0.99997 vs `54844628` reflects a
shared TVT trend, not equal accuracy: in error space they are only 0.765-correlated and the frontier is
the stronger model (D3: 3.259 vs 3.677 locally, now confirmed directionally on public).

## Two-slot recommendation (min-regret across H-visible / H-hidden)

- **Slot 1 — team best-public: `54922806` (6.563)** (or a better frontier ref if one appears).
  Wins decisively under **H-visible** (private = the same 3 visible wells; overlap returns near-truth).
- **Slot 2 — now a live choice between `54968060` (6.643) and `54844628` (7.891):**

  | | `54968060` overlap-OFF frontier | `54844628` our honest slot |
  |---|---|---|
  | public | **6.643** (2nd best on board) | 7.891 |
  | H-hidden proxy | **direct** — it *is* the frontier with the visible-well lookup removed, i.e. the closest available measurement of novel-well behaviour | indirect — no overlap by construction |
  | local (3 wells, train-copy TVT) | **RMSE 3.259** | RMSE 3.677 |
  | validation depth | public + local diff only | **760-well nested OOF**, bootstrap, full audit trail |
  | provenance | derived from the public Kaiwalya notebook + **9 third-party public datasets**; run from our account, not fully-owned lineage | **fully owned**, every component built and audited in this repo |
  | reproducibility | reproducible from our account (verified), but depends on third-party datasets staying available | fully self-contained |

  **On score and on H-hidden proxy quality, `54968060` is the stronger slot-2 candidate.** It is better
  on public by 1.248, better locally, and it directly measures the no-overlap path. The counterweight is
  **lineage/provenance**: it is a derivative of a public notebook with third-party dataset dependencies
  and no 760-well OOF validation, whereas `54844628` is fully owned and OOF-validated.

  **Recommendation:** unless the final-selection owner specifically weights fully-owned provenance and
  OOF-backed validation above measured score, **`54968060` is the better slot-2 pick**; `54844628`
  remains the fully-owned honest fallback and would be the choice under a provenance-first policy.

This pairing still hedges both hypotheses: slot 1 captures H-visible upside; slot 2 (either option)
covers the novel-well path, with `54968060` now offering a materially better measured level there.

## `54968060` (overlap-OFF) — resolved: **6.643**

The pre-registered reading was: *near 6.5 → frontier modeling is strong, not just overlap; toward ~7.x →
6.5 is largely overlap.* The result is **6.643 — clearly the "near 6.5" branch.**

Consequences:
1. **Frontier modeling is strong on its own.** Overlap contributes ≤0.080 on public (≤0.017 vs its own
   family reference), inside the noise floor. The H-hidden risk of the frontier family is therefore
   **materially lower than the overlap mechanism suggested** — on novel wells it retains the modeling
   that produces ~6.64, rather than reverting toward ~7.9.
2. **`54968060` is a live slot-2 candidate**, not merely a diagnostic. Earlier this report called it
   "not a final-slot candidate"; that judgement was based on the assumption that removing overlap would
   cost a lot of score. It did not. The remaining reservation is lineage/provenance, not performance.
3. Slot 1 (`54922806`, 6.563) is unchanged as the best measured public.

## Standing

Our-side quota today: 1/5 used (`54968060`). Honest slot `54844628` unchanged; `54878409` excluded.
Frontier line is teammate-owned; slot-1 final say belongs to the final-selection owner. No further
our-side submission is warranted until a candidate is non-homogeneous, 3-well-gate-consistent, and
H-hidden-defensible — none exists beyond the diagnostic just submitted.
