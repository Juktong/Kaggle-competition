# L6 multi-seed DWT averaging — already implemented (2026-07-21)

Task 3 of the parallel queue. Status: **closed by source inspection; no experiment run and none needed.**

## Question

Averaging/shrinkage is the one mechanism that has repeatedly transferred in this project. L6 proposed
applying it to the DWT component: train DWT under several seeds and average.

## Finding

Reading the deployed kernel's training cell, the DWT ensemble **already does exactly this**:

```python
lgb: dict(learning_rate=0.025, n_estimators=8000, seed=42,  **lgb_params_base)
     dict(learning_rate=0.020, n_estimators=8000, seed=7,   **lgb_params_base)
     dict(learning_rate=0.030, n_estimators=8000, seed=123, **lgb_params_base)
cat: dict(learning_rate=0.025, random_seed=42,  **cb_params_base)
     dict(learning_rate=0.020, random_seed=7,   **cb_params_base)
     dict(learning_rate=0.030, random_seed=123, **cb_params_base)
...
return np.mean(preds, axis=0)
```

Six models across **three seeds × two libraries** (LightGBM + CatBoost), with three learning rates,
combined by a plain mean. That is multi-seed averaging plus two further diversity axes.

## Why the marginal extension is low-value

- Variance reduction scales like ~1/√N; going from 3 seeds to 6 inside an already-6-model ensemble moves
  little.
- Seed is the *weakest* of the three diversity axes present. Library (LightGBM vs CatBoost) and learning
  rate already contribute more decorrelation than reseeding the same learner.
- Cost is real: six models at `n_estimators=8000` already dominate kernel runtime; doubling the pool
  would roughly double it for a sub-noise expected gain.

## Disposition

L6 is closed as **already implemented**. This was settled by reading the source rather than by running a
smoke, which is the correct order of operations — the proposal was written before the ensemble's
internals had been inspected. No diversity/correlation experiment was run because there is no decision
it could change: the mechanism is present, and the only open variant (more seeds) is bounded above by
1/√N on the weakest diversity axis.
