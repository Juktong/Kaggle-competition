# ROGII — DWT+PF private-risk stress test (Direction B, 2026-07-19)

Session `1a07ce3e`. Simulate private-composition scenarios from the 773-well honest OOF and check DWT+PF
robustness. `$JOB/tmp/bd_stress.py`. Neutral technical language.

## Method
Aligned honest OOF (DWT combo_state + PF pf_oof_full773 + truth), pooled toe RMSE per subset. Subsets are
train-OOF proxies for private composition. (Overlap-heavy cannot be simulated from the honest OOF — that is
the Gate-Safe/overlap-hedge scenario, handled in the final-2 by the 2nd slot.)

## Results (pooled RMSE; lower better)
| scenario (subset) | n | DWT | PF | blend@0.5 | blend@0.44 | winner |
|---|---|---|---|---|---|---|
| ALL (novel proxy) | 773 | 10.40 | 11.00 | 9.30 | 9.28 | **blend** |
| hard-well-heavy (top33% DWT-RMSE) | 256 | 16.18 | 15.21 | 13.95 | 14.04 | **blend** |
| easy-well-heavy (bot33%) | 255 | 3.43 | 6.81 | 4.16 | 3.92 | **DWT** |
| long-well-heavy (top33% toe count) | 256 | 11.45 | 10.87 | 9.74 | 9.80 | **blend** |
| short-well-heavy (bot33%) | 255 | 9.15 | 10.02 | 8.36 | 8.32 | **blend** |
| high-drift-heavy (top33%) | 256 | 11.32 | 11.14 | 9.55 | 9.59 | **blend** |
| low-drift-heavy (bot33%) | 255 | 8.69 | 9.53 | 7.93 | 7.89 | **blend** |
| high-zspan-heavy (top33%) | 256 | 11.57 | 11.89 | 10.30 | 10.30 | **blend** |

## Conclusion
- **The DWT+PF blend beats BOTH DWT and PF in 7 of 8 scenarios** (hard, long, short, high/low-drift, high-zspan,
  all). It is robust for any novel/mixed/hard private set → confirms it as the honest slot.
- **Single exception: easy-well-heavy** — where DWT is already very accurate (RMSE 3.43) the PF adds noise and
  DWT alone beats the blend (4.16). But (a) that "easy" is defined by DWT's own error (oracle), NOT detectable
  from test-available features (Direction C), so it cannot be routed; and (b) an all-easy private is unlikely
  and would have low absolute error regardless.
- No honest candidate is more robust than the blend across scenarios. DWT+PF stands.
