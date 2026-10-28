# ROGII — S-A: decision-theoretic final-2 optimization (2026-07-15)

Quantitative optimization of the **two final submissions** under uncertainty about the private
set's composition. Extends `reports/final_submission_strategy.md` (which *characterized* the
honest/hedge pair) with an explicit scenario model that *optimizes* the pair. Analysis only — no
Kaggle submission. Script: `scripts/final2_decision_analysis.py`. Neutral technical language.

## 1. Model

Kaggle uses the **best of your 2 selected** submissions on the **private** leaderboard (standard
2-final rule; the strategy ledger already assumes it — worth a one-line manual confirmation on the
ROGII rules page, but it is the standard mechanism). So the pair's final score is

    final(pair, f) = min_{sub ∈ pair}  pooled_private_RMSE(sub, f)

with `f` = fraction of **private** rows that are train-duplicate ("overlap") wells (the exact-match
override reconstructs their TVT ≈ exactly); the remaining `1−f` are novel wells (override is a
no-op → the submission scores its honest base there). Pooled RMSE combines in quadrature:

    pooled(sub, f) = sqrt( f·r_overlap² + (1−f)·r_novel_eff² )

Candidate submissions:

| candidate | r_novel | r_overlap | note |
|---|---|---|---|
| **DWT** honest 9.519 (ref 54453597) | r_H ≈ 9.8 | r_H ≈ 9.8 | no override; honest on both |
| **HEDGE** Gate-Safe 7.212 (ref 54289934) | r_hedge_honest ≈ 12 (unmeasured, [10,14]) | r_ov ≈ 1.5 | weak base + guarded override |
| **HONEST2** 2nd honest model | r_H2 ≈ 10.4 | r_H2 ≈ 10.4 | blend-neutral, corr≈0.9 with DWT |
| **B4′** guarded honest+overlap on DWT base | r_H (+ FP penalty) | r_ov ≈ 1.5 | DWT on novel + override on detected duplicates |

Parameter sources: `r_H` — DWT public 9.519 / internal native-mask CV 10.40 (honest models: public
≈ private); `r_ov` — S4 measured hedge 1.46 on overlap wells; `r_hedge_honest` — unmeasured, the
7.212 forks collapse toward a base weaker than DWT (honest public samples span 8.1–12.0); B4′
false-positive rate `e` and per-FP error `r_fp` — governed by the guarded detector's precision.

## 2. Results

**pooled private RMSE by submission vs overlap fraction f**

| f | DWT | HEDGE | HONEST2 | B4′ |
|---|---|---|---|---|
| 0.00 | 9.80 | 12.00 | 10.40 | 10.42 |
| 0.05 | 9.80 | 11.70 | 10.40 | 10.17 |
| 0.15 | 9.80 | 11.08 | 10.40 | **9.63** |
| 0.30 | 9.80 | 10.07 | 10.40 | **8.76** |
| 0.50 | 9.80 | **8.55** | 10.40 | **7.45** |
| 1.00 | 9.80 | 1.50 | 10.40 | 1.50 |

**pair final = best-of-2 (lower is better)**

| f | DWT+HEDGE | DWT+HONEST2 | HEDGE+HEDGE | **B4′+DWT** |
|---|---|---|---|---|
| 0.00 | 9.80 | 9.80 | 12.00 | 9.80 |
| 0.05 | 9.80 | 9.80 | 11.70 | 9.80 |
| 0.15 | 9.80 | 9.80 | 11.08 | **9.63** |
| 0.30 | 9.80 | 9.80 | 10.07 | **8.76** |
| 0.50 | 8.55 | 9.80 | 8.55 | **7.45** |
| 1.00 | 1.50 | 9.80 | 1.50 | 1.50 |

**E[final] under priors on f** (lower is better)

| pair | novel-heavy Beta(1,9) E[f]=0.10 | mild Beta(2,6) E[f]=0.25 | uniform E[f]=0.50 | worst-case f=0 |
|---|---|---|---|---|
| DWT+HEDGE (available now) | 9.788 | 9.581 | 7.726 | 9.80 |
| DWT+HONEST2 | 9.800 | 9.800 | 9.800 | 9.80 |
| HEDGE+HEDGE | 11.379 | 10.368 | 8.111 | **12.00** |
| **B4′+DWT** | **9.638** | **8.968** | **7.037** | 9.80 |

**Sensitivities.**
- **Hedge crossover** `f*` (min overlap for the hedge to beat DWT): 0.04 (r_hedge=10) → 0.34
  (r_hedge=12) → 0.52 (r_hedge=14). So the weaker the hedge's honest base, the more private overlap
  is required before it helps — but under best-of-2 it **never hurts** (DWT floors the pair at r_H).
- **B4′ false-positive rate** `e` (novel-heavy prior): worst-case stays **9.80 at every e** (the DWT
  safety slot absorbs mis-detections), while E[final] rises from 9.297 (e=0) to ≈9.80 (e=0.02). B4′
  keeps a strict edge over DWT-alone as long as its detector precision is high (e ≲ 0.005).
- **Dominance:** `B4′+DWT ≤ DWT+HEDGE` at **every** f (max advantage **1.28 RMSE** at intermediate f).

## 3. Interpretation

1. **Under best-of-2 a hedge is a free option** — adding it to DWT can only lower the pair's final.
   `{DWT, Gate-Safe hedge}` therefore weakly dominates `{DWT, HONEST2}` and `{DWT alone}`: it equals
   DWT for f < f* and improves for f > f*. A **2nd honest model is not worth a slot** (blend-neutral,
   corr≈0.9 → HONEST2 pair is flat at r_H; consistent with the V4/blend-neutral evidence). Two overlap
   plays `{HEDGE, HEDGE}` are worst-case worse (both collapse to weak bases at f=0) and share the same
   private-collapse risk.
2. **B4′ (guarded honest+overlap, built on the DWT base) is the strongest single submission.** It
   keeps DWT's strong honest base on novel wells *and* wins the overlap wells, so it dominates the
   separate weak-base hedge at every f. Pairing it with pure DWT makes the DWT slot a **safety net**
   that absorbs B4′'s false-positive risk (best-of-2 floors the pair at r_H). `{B4′, DWT}` weakly
   dominates the current `{DWT, HEDGE}` pair pointwise.

## 4. Recommendation

- **No new work before the deadline → keep the current pair:** DWT 9.519 (ref 54453597, honest
  primary) + Plane Top2 Gate-Safe 7.212 (ref 54289934, bounded overlap hedge). It is
  **robust-optimal among already-submitted refs**: best-of-2 hedges the two private-composition
  scenarios, and the hedge carries no downside. Both refs are banked and selectable now.
- **Worth the notebook work (gated) → build B4′ and switch slot-2 to `{B4′, DWT}`.** B4′ = a single
  submission that is DWT-honest by default and applies the exact-match override ONLY on hidden wells
  detected as high-confidence train duplicates. It weakly dominates the current pair at every overlap
  fraction, with DWT as the false-positive safety net.
  - **Gate to realize B4′:**
    (a) **Compliance** — confirm on the ROGII rules page that reconstructing test-from-train duplicate
        wells (a within-competition-data override, already the mechanism behind the public 7.2 plateau)
        is not prohibited. No external data needed → a lower gate than S-B.
    (b) **V5 audit** — the 3 visible test wells ARE train duplicates; require the override to
        reconstruct them near-exactly AND fall back to DWT elsewhere (`scripts/visible_well_audit.py`).
    (c) **Detector precision** — validate the guarded duplicate-detector's false-positive rate ≈ 0 on
        train NON-duplicate wells before trusting it (e ≲ 0.005 keeps a strict edge; higher e is still
        safe because the DWT slot floors the pair, but erodes the upside).
  - **Notebook work:** on the DWT honest notebook, add (i) a hidden-well ↔ train-well duplicate
    detector (GR/trajectory fingerprint match, high-confidence threshold), (ii) TVT reconstruction
    from the matched train twin on detected duplicates, (iii) DWT prediction everywhere else. Keep the
    override bounded ("Gate Safe") to protect partial-overlap wells.

## 5. Assumptions / risk points
- **Best-of-2 private rule** is the linchpin; if the ROGII rule differed (e.g. only the last
  submission counts) the free-option argument weakens — confirm on the rules page.
- `r_hedge_honest` is unmeasured; the recommendation is insensitive to it (the hedge never hurts
  under best-of-2, and B4′ sidesteps it by using the DWT base).
- The novel-well framing suggests a **low** private overlap fraction (small f), which favours DWT as
  the anchor — exactly why DWT is held in both recommended pairs.
