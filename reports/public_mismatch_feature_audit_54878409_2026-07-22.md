# Public mismatch feature audit — `54878409` (2026-07-22)

Direction C. A diagnostic of the validation system, not post-public tuning. The central finding is a
**scoring-space boundary**: local truth-space gains do not transfer to the leaderboard at our candidates'
effect scale.

## The 3 test wells: fully characterised

The whole test set is **3 wells / 14,151 toe rows** (submission row count = exactly these wells' toe
rows; no hidden wells). All three are **duplicated in train** — `train/{w}` and `test/{w}` are the same
well (identical GR, XYZ, TVT_input; `train.TVT == test.TVT_input` on heel rows to 0.0000), and the train
copy carries full TVT. So at inference the models predict wells whose truth they were trained on.

Test-available slice vs the 760-well population:

| well | nnb (pop pctile) | closest_surv (pctile) | GR cov | heel known | toe predicted |
|---|---|---|---|---|---|
| 000d7d20 | 13 (20th) | 292 ft (18th) | 57.2% | 27.3% | 72.7% |
| 00bbac68 | 40 (79th) | 344 ft (32nd) | 87.5% | 20.4% | 79.6% |
| 00e12e8b | 13 (20th) | 355 ft (39th) | 90.9% | 32.6% | 67.4% |

- All 3 pass the deployment gate legitimately (nnb ≥ 4, closest_surv < 1000 ft).
- **None is in the weak twin subgroup** (closest_surv 292–355 ft, all > 150 ft). The smoke's
  `closest_all = 0 ft` was the inference-side train copy dropped by MIN_SEP.
- Two of the three sit in the low-neighbour-count fifth of the population (nnb ~13, 20th pctile), so the
  structural field has thinner support on them than on a typical well — a pre-public, test-available
  observation.

## The scoring-space boundary (the key finding)

Computing RMSE against the train-copy TVT (which equals the test truth on heel to 0.0000):

```
                 train-truth RMSE (all 14151 toe rows)     public
naive last-value        11.5393                            (very high, known)
54844628                 3.6772                            7.891
54878409                 3.4961                            7.953
```

Two facts that must be held together:

1. **In train-truth space, `54878409` is BETTER than `54844628`** over the full visible set (3.4961 vs
   3.6772, +0.181 — matching the OOF gain almost exactly).
2. **On public, `54878409` is WORSE** (7.953 vs 7.891).

So **rank is not preserved between the local truth space and the leaderboard** at this effect scale. And
no row subset reconstructs the public scale: splitting by toe fraction or by distance-from-heel, the
hardest slice (far toe, frac ≥ 0.7) reaches only RMSE 4.57, nowhere near 7.891. The competition scoring
space is therefore **not reconstructible from the data available to us.**

The relationship that *does* hold is coarse-scale monotonicity: naive (11.5) ≫ DWT-family ≫ struct-family
locally, matching public 9.519 → 8.080 → 7.891. The leaderboard separates **large** steps but not the
**~0.1–0.2** local differences our remaining candidates live in — exactly where `54878409` landed.

## Row-split behaviour (from direction 3)

- Random row split: `corr(publicHalf, privateHalf) = 0.999` (within-well autocorrelation 0.9998).
- Contiguous block split: `corr = 0.10–0.15` — near-independent halves.

Combined with the scoring-space boundary, this means public gives strong information about private **only
under a random split and only in the local truth space**; neither assumption is safe here.

## Pre-public / test-available observations (usable) vs public-defined slices (recorded only)

**Usable (test-available), recorded for future gating:**
- 2 of 3 test wells have low neighbour count (nnb ~13). Structural-field candidates have thinner support
  and higher variance on low-nnb wells.
- All 3 have closest_surv in 290–355 ft — inside the gate but not the safest tier.

**Public-defined (NOT usable for selection, recorded only):**
- Per-well public/train-truth mismatch cannot be attributed to a test-available feature without using
  the public outcome, which would be leakage. No such attribution is made.

## Conclusion

The audit finds **no test-available feature that flags `54878409` as unsafe on these specific wells** —
it passes every pre-public check. The failure is not a fixable feature bug; it is that **local
truth-space accuracy does not determine leaderboard accuracy at the 0.1-scale**. The operational
consequence is in `reports/submission_policy_after_54878409_2026-07-22.md`: small-margin candidates
cannot be validated locally, so the leaderboard itself (with 5/day) is the only test, and it should be
spent only on candidates that are *large* in local space or *structurally distinct*.
