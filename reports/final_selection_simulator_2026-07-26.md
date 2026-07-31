# G3.4 — robust final-selection simulator (2026-07-26)

No submission, no GPU. Tool: `scripts/final_selection_simulator.py`. Final score = **best of the 2
selected submissions** on the private set, so the object to optimise is the **pair**, not the individual
candidate.

## Estimation rules (stated, not hidden)

- **H-visible** (private = held-out rows of the same 3 visible wells): private ≈ public. Justified by
  within-well residual autocorrelation +0.9998 — the two row halves track each other.
- **H-hidden** (private = novel wells, no train duplicate): retrieval contributions go inert, so a
  candidate degrades by its **measured** retrieval dependence. Measured value: **0.080**
  (= 6.643 overlap-OFF − 6.563 overlap-ON, from `54968060` vs `54922806`). No-retrieval candidates are
  unchanged. A novel-well penalty common to all candidates cancels in the ranking and is set to 0.
- **mixed**: half the retrieval penalty.

## Per-candidate estimates

```
candidate                      public  H-visible  H-hidden   mixed   provenance
54922806 frontier overlap-ON    6.563     6.563     6.643    6.603   teammate/public-derived
54968060 frontier overlap-OFF   6.643     6.643     6.643    6.643   ours/public-derived
54896975 frontier overlap-ON    6.669     6.669     6.749    6.709   teammate/public-derived
54923144 frontier GR-sigma      6.678     6.678     6.758    6.718   teammate/public-derived
54844628 honest                 7.891     7.891     7.891    7.891   fully owned
```

## Pair evaluation (best-of-2, min-regret)

```
pair                                            H-vis   H-hid   mixed   WORST    mean
54844628_honest      + 54922806_overlapON       6.563   6.643   6.603   6.643   6.603
54896975_overlapON   + 54922806_overlapON       6.563   6.643   6.603   6.643   6.603
54922806_overlapON   + 54923144_gr_sigma        6.563   6.643   6.603   6.643   6.603
54922806_overlapON   + 54968060_overlapOFF      6.563   6.643   6.603   6.643   6.603
54844628_honest      + 54968060_overlapOFF      6.643   6.643   6.643   6.643   6.643
```

**Four pairs tie at worst-case 6.643 / mean 6.603.** All four contain `54922806`; the tie arises because
under H-hidden `54922806` degrades exactly to 6.643, which is `54968060`'s constant.

## The tie-break — and a correction to the earlier slot-2 recommendation

The numeric objective cannot separate the top four pairs, so the tie must be broken on a criterion the
objective does not encode: **robustness to the estimation rules themselves being wrong.**

- `54922806 + 54968060` are the **same pipeline family** (prediction corr 0.99998). If the frontier
  approach has a systematic problem on the private set that my retrieval-penalty model does not capture
  — third-party artifacts not generalising, or a visible-well-specific fit beyond the measured overlap
  term — **both slots fail together**.
- `54922806 + 54844628` pairs the frontier with a **structurally independent** pipeline (DWT + PF +
  group-anchored structural field, fully owned, 760-well nested OOF + bootstrap). Its failure modes are
  uncorrelated with the frontier's.

Since both pairs show an **identical modelled worst case (6.643)**, the independent pair is preferable:
diversity is free here.

**This corrects the slot-2 recommendation carried since 2026-07-25.** That earlier recommendation
compared candidates *individually* (`54968060` 6.643 beats `54844628` 7.891, so prefer `54968060`). But
with best-of-2 scoring and slot 1 already holding the frontier line, a second frontier candidate is
**redundant**, while the honest slot is **insurance**. The individual comparison was the wrong unit of
analysis.

## Updated recommendation

- **Slot 1: `54922806` (6.563)** — best public; carries H-visible upside.
- **Slot 2: `54844628` (7.891)** — structurally independent, fully owned, OOF-validated. Costs nothing in
  the modelled worst case (6.643 either way) and insures against a family-wide frontier failure.

`54968060` remains a fully validated, high-quality candidate and is the natural **replacement for slot 1**
if the frontier line ever needs an our-account, no-retrieval representative. It is simply redundant as a
*second* slot alongside `54922806`.

## Sensitivity

The one input that could change this is the retrieval penalty (measured 0.080). If the true H-hidden
degradation of overlap-ON branches were much larger (say > 1.25), `54922806` would fall behind
`54844628` under H-hidden and the pair worst-case would be set by the honest slot — which strengthens,
not weakens, the recommendation to keep `54844628` in slot 2. The recommendation is therefore stable
across the plausible range of that parameter.
