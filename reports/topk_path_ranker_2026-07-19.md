# ROGII — top-K path search + ranker: oracle-gap test (Direction C, 2026-07-19)

Sprint session `3f11942e`→`4d6cd351`. Cheap-first design: before building a path ranker, measure whether the
PF's own seed-paths contain materially better paths than their likelihood-weighted average, and whether any
deployable signal can pick them. Script `scripts/topk_path_oracle_gap.py`. Neutral technical language.

## Method
The PF already produces K=NS independent seed paths per well; the shipped prediction is their
likelihood-weighted average. For 15 randomly-shuffled train wells (NS=24, 500 particles), on the aligned toe
rows, compare: the weighted average · the ORACLE best seed (truth-selected, upper bound for any ranker) ·
the **max-likelihood** seed (the deployable single-path pick) · the worst seed · and the same at the
DWT+PF blend level.

## Results (15 wells, row-count-weighted pooled RMSE)
| method | pooled RMSE | note |
|---|---|---|
| PF weighted-average | 6.7290 | current shipped PF |
| **PF ORACLE best-seed** | **5.6383** | upper bound for a perfect path ranker (−1.09, −16 %) |
| PF max-likelihood seed | **7.1477** | deployable pick — **worse than averaging (+0.42)** |
| PF worst seed | 9.9756 | spread across seeds is large |
| DWT+PF blend (avg PF) | 5.6278 | current honest slot mechanism |
| **DWT+PF blend (ORACLE seed)** | **4.9350** | upper bound at blend level (−0.69, −12 %) |
| mean corr(seed loglik, −seed RMSE) | **0.343** | likelihood vs path quality |

## Findings
1. **Real headroom exists in principle.** The seed ensemble contains paths materially better than their
   average: −1.09 ft at PF level, **−0.69 ft at blend level (5.628 → 4.935)**. So multi-path selection is not
   an empty direction — if a ranker could identify good paths, the prize is meaningful.
2. **The natural ranking signal is too weak to realise it.** The seed log-likelihood correlates with path
   quality only at **r = 0.343**, and picking the max-likelihood path is **worse than averaging**
   (7.148 vs 6.729). Averaging is itself a variance-reduction mechanism; a single-path pick discards it, so a
   ranker must be substantially more precise than "better than random" merely to break even.
3. **Consistent with Direction A.** A's full-power screen found no test-available feature predicting which
   *model* is better (|corr| ≤ 0.061); here the PF's own internal confidence predicts which *path* is better
   only at 0.343. Both point the same way: the information needed to select is largely not observable from
   test-available quantities.

## Status and what would change it
**Recorded as a quantified partial-negative — not closed.** The oracle gap (−0.69 at blend level) is the one
place in this sprint where a non-trivial upper bound was demonstrated. A learned ranker using more than the
likelihood (path smoothness, jump magnitude, anchor consistency at the heel, typewell range pressure,
agreement with the DWT prior) remains the open question; it would need to beat plain averaging, i.e. clear
+0.42 ft over the likelihood pick just to reach parity with the current average.

**Cost note:** building it requires re-running the PF while retaining all K seed paths (the shipped harness
keeps only the weighted mean), plus a nested per-well ranker. That is a multi-hour CPU job on this 2-core box
and was not started in this sprint; it is the highest-value remaining item in the backlog if the sprint
continues.

**Submission impact: none** — no candidate produced; the honest slot 54804893 is unchanged.
