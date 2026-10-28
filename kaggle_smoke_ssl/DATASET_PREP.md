# External GR Kaggle Dataset prep (FORCE-2020) — offline attachment for the smoke kernel

Goal: package public FORCE-2020 gamma-ray logs as a Kaggle Dataset so the smoke kernel can load it
offline (`enable_internet:false`). No secrets/tokens in these steps.

## Source & license (verified 2026-07-15)
- FORCE-2020 ML competition well logs. GR (gamma-ray) is a guaranteed field (only DEPT + GR are
  guaranteed present across wells). Data license **NLOD 2.0** (Norwegian Licence for Open Government
  Data); lithofacies labels **CC-BY-4.0**. Publicly redistributable **with citation**:
  "Lithofacies data was provided by the FORCE Machine Learning competition with well logs and seismic 2020".
- Mirrors: Zenodo record 4351156; GitHub `bolgebrygg/Force-2020-Machine-Learning-competition`.

## Steps (run on a machine WITH internet + kaggle CLI; NOT inside the offline kernel)
1. Download the training logs CSV (train.csv / *.las→csv) from the Zenodo/GitHub mirror.
2. Reduce to GR-only to keep the dataset small and domain-focused:
   `df[['WELL','DEPTH_MD','GR']].dropna(subset=['GR'])` → `force2020_gr.csv` (or per-well CSVs).
   (Optional facies branch: also keep `FORCE_2020_LITHOFACIES_LITHOLOGY` as labels.)
3. Create a Kaggle Dataset:
   ```
   mkdir force-2020-gr-windows && cp force2020_gr.csv force-2020-gr-windows/
   # dataset-metadata.json: {"title":"FORCE 2020 GR windows","id":"<owner>/force-2020-gr-windows",
   #   "licenses":[{"name":"other"}]}  # note NLOD-2.0 + CC-BY-4.0 in the description + citation
   kaggle datasets create -p force-2020-gr-windows
   ```
4. Put the resulting slug into `smoke_kernel-metadata.json` → `dataset_sources`.
5. Attribution: include the required FORCE citation in the dataset description AND the kernel.

## Compliance gate (must clear before any competition submission that USES external data)
- ROGII host-specific external-data clause must be manually confirmed on the (login-gated) rules
  page: External Data section + Winner's Obligations (disclosure). The Kaggle standard clause allows
  freely/publicly-available external data + pretrained models in code competitions unless the Host
  prohibits it — but the ROGII-specific text is unverified here. **Do not submit a competition
  prediction that depends on external data until this is confirmed.** Using external data for
  local/dev embeddings (no submission) is fine.
