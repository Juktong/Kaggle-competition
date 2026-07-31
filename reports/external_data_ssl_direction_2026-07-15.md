# ROGII — Direction F: external public well-log data / SSL-facies encoder (2026-07-15)

Question: can external public well-log data or a pretrained well-log encoder become a Kaggle-GPU
candidate that improves the honest base (DWT 9.519 / internal CV ~10.40, ref 54453597)? Neutral
technical language; public-hedge kept separate; honest OOF as the private proxy.

## 1. Rules & compliance verification

- **Standard Kaggle framework (verified across several competition rules pages):** "You may use
  External Data … provided it is publicly available and equally accessible to all Participants at
  no cost, or meets the Reasonableness standard." For **code competitions**, freely & publicly
  available external data **and pretrained models** are allowed **unless specifically prohibited by
  the Host**.
- **ROGII-specific clause — NEEDS MANUAL CONFIRMATION.** The competition rules page is JS/auth-gated
  and not machine-readable here (WebFetch returns only the page shell). Do **not** assume the
  standard clause applies. Before any external-data work, a logged-in human must read on
  `https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/rules`:
  (a) the **External Data** section (allowed / prohibited / Reasonableness);
  (b) **Pre-trained Models** allowance;
  (c) **Winner's Obligations** (disclosure of all external data/code/weights if we finish in the money).
  A Host-specific prohibition would void this direction.
- **Offline-runtime constraint (verified from our own kernel metadata):** the submission notebook
  runs with `enable_internet:false`. Therefore any external data or pretrained weights **must be
  attached as a public Kaggle Dataset** and loaded offline — never fetched at runtime. If used, it
  must be publicly shared (dataset) so all participants have equal access.

## 2. Public resource screening

| resource | GR? | license | Kaggle-Dataset / redistributable? | domain gap vs ROGII | worth a smoke? |
|---|---|---|---|---|---|
| **FORCE-2020 lithofacies** (Zenodo 4351156, GitHub bolgebrygg) | **yes** (DEPT+GR guaranteed) | data **NLOD 2.0**, labels **CC-BY-4.0** (open, cite required) | **yes** — already public; re-hostable with citation | vertical North Sea wells + lithofacies labels; different basin/tools than ROGII horizontal laterals + typewell; GR-shape *may* transfer | primary candidate |
| Volve / Equinor logs | yes | **CC-BY-NC-SA** (non-open: NC + no resale, redistribution-restricted) | **risky** — NC clause vs a $50k comp; re-hosting = redistribution | same North Sea vertical | not without legal clearance |
| WLFM foundation model (arXiv 2509.18152; GR+SP+AC, 1200 wells) | yes | **weight release + license UNCONFIRMED** | unknown | cross-basin pretrain | only if weights are openly released + license permits offline use — manual check |
| 60M ViT-MAE well-log model (1.1M North-American logs) | yes | **weight/license UNCONFIRMED** | unknown | North-American (possibly closer to ROGII) | same caveat as WLFM |

Read: FORCE-2020 is the one clean, licensable, GR-bearing, offline-packageable corpus. Its use would
be to **train our own** GR encoder/facies model (avoiding pretrained-weight licensing risk).

## 3. Local preflight (decides whether GPU is warranted)  `scratchpad_probes/ssl_gr_encoder_preflight.py`

- **Design:** train a small **self-supervised contrastive GR encoder** (SimCLR/TS2Vec-lite: 1D-CNN,
  InfoNCE with jitter/scale/mask augmentations) on ROGII GR windows (test-available); extract
  per-toe-row 32-d embeddings; fit a residual LightGBM (drift target); honest 5-fold well-OOF; check
  nested blend-weight **sign** vs DWT. This is the smoke test's own local-acceptance criterion
  applied to a ROGII-trained encoder — the cheapest fair proxy for the external-SSL branch.
- **Result:** InfoNCE converged (3.55→2.18). DWT=10.395, SSL-residual RMSE **15.95**, corr(err,DWT)
  **0.723**, mean nested blend weight **−0.096 (negative)** → drift-amplification (λ-disguise) artifact.
- **Key comparison:** essentially identical to the untrained ROCKET random-conv probe (15.96 / 0.721
  / −0.093). **Representation quality (random vs learned contrastive) does not change the outcome** —
  any GR-window representation yields a weak, 0.72-correlated, negative-blend-weight residual. The
  limitation is **informational** (GR is one channel DWT already saturates), not representational.

## 4. Kaggle GPU smoke-test design (documented for readiness; currently GATED — see verdict)

Only meaningful if the local-acceptance criterion (positive-weight blend) can be met. Design:
- **Environment:** Kaggle notebook, `enable_gpu:true` (T4), `enable_internet:false`. Confirm the comp
  allows GPU kernels (manual check).
- **Datasets (offline mounts):** a public FORCE-2020 Kaggle Dataset + the ROGII competition data.
- **Encoder (smoke = tiny):** contrastive or MAE GR encoder trained on FORCE GR (+ optionally ROGII
  GR), 1–2 epochs on a well subset, just to confirm the offline GPU pipeline (load → train → export).
- **Output:** ROGII per-well / per-window embeddings written to `/kaggle/working`.
- **Local acceptance (the gate):** download embeddings, fit an embedding-residual model, check the
  nested blend weight vs our cached DWT OOF. **PASS = positive weight + directional honest-OOF
  improvement**; FAIL = negative/near-zero (as the §3 preflight already shows).
- **Full-run condition:** only if smoke PASSES → scale encoder (full FORCE+ROGII, more epochs, larger
  model) on GPU, re-validate on full OOF + spatial-blocked worst-group.
- **Submit condition:** only if the full run gives a **stable positive-weight honest OOF improvement
  vs DWT 9.519** that survives the spatial-worst-group screen and a pre-submit audit (format / row
  order / all-finite / range / no train-only fields / no hidden-label leakage). Then build the
  hidden-compatible notebook, submit, and record submission id / public score / commit / source /
  local gap.
- **Kernel skeleton (metadata template, ready to instantiate):**
  ```json
  {"id":"joezzzzz/rogii-ssl-gr-encoder-smoke","title":"ROGII SSL GR Encoder (smoke)",
   "code_file":"ssl_gr_encoder_smoke.ipynb","language":"python","kernel_type":"notebook",
   "is_private":true,"enable_gpu":true,"enable_tpu":false,"enable_internet":false,
   "dataset_sources":["<owner>/force-2020-well-logs"],
   "competition_sources":["rogii-wellbore-geology-prediction"],"kernel_sources":[],"model_sources":[]}
  ```
  Notebook stages: load FORCE GR (offline) → build windows → train encoder (GPU) → embed ROGII
  train/test wells → save embeddings.parquet. (Not instantiated as a runnable notebook because the
  preflight fails the acceptance gate — see verdict.)

## 5. Verdict & next

- **Compliance:** the standard Kaggle framework would allow FORCE-2020 (public, open, offline-mountable),
  but the **ROGII-specific external-data clause must be manually confirmed** before use.
- **Is F worth Kaggle GPU now? No.** The local preflight — which is exactly the smoke's local-acceptance
  criterion applied to a ROGII-trained SSL encoder — produces a **negative blend weight** and is
  indistinguishable from the untrained ROCKET result. External data only improves the encoder's
  representation/diversity, but the preflight shows representation quality is not the bottleneck (random
  = learned). So a Kaggle-GPU external-data encoder is predicted to fail the same acceptance gate; running
  it would spend GPU without clearing the submittable bar. **No stable improvement observed; not warranted.**
- **The facies branch** (supervised GR→facies from external labels) is also low-prior: Direction C
  (unsupervised facies-token alignment) already only tied DWT's oracle, and FORCE lithofacies are a
  different basin than ROGII formations (domain gap on top of the same GR-channel saturation).
- **Recommended next search space:** stop investing in GR-representation residual/blend variants (random,
  learned, external — all land on the blend-neutral frontier / negative weight). A genuinely new
  information channel or a fundamentally stronger single model would be required; none has been found in
  the current test-available input set. Honest final base unchanged = DWT 9.519 (ref 54453597); final-2
  strategy in `reports/final_submission_strategy.md`.
- **GPU/compute labeling:** §3 preflight = CPU probe (done). §4 smoke = Kaggle GPU candidate, **gated**
  (do not run until the acceptance criterion can plausibly be met, e.g. a genuinely different signal or a
  foundation-model whose weights are confirmed open + offline-loadable).

Sources: FORCE-2020 — Zenodo 4351156, github.com/bolgebrygg/Force-2020-Machine-Learning-competition;
Volve — equinor.com/energy/volve-data-sharing (CC-BY-NC-SA); WLFM — arXiv:2509.18152; Kaggle external-data
framework — kaggle.com/docs/competitions + standard competition rules pages.
