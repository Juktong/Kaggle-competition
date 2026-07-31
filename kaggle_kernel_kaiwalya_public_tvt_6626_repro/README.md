# ROGII Kaiwalya Public TVT 6.626 Reproduction

This folder contains the minimal reproducible Kaggle kernel package for the
public notebook `kaiwalyaatulraut/rogii-public-tvt-solution`.

## Contents

- `rogii-public-tvt-solution.ipynb`: complete Code Competition notebook.
- `kernel-metadata.json`: required Kaggle datasets, GPU setting, and kernel ID.

## Method

The notebook combines the public Ridge/SP45 anchor, multi-scale particle
filter and beam reconstruction, learned trajectory artifacts, guarded
same-well contact checks, visible-prefix calibration, model-package gating,
and a bounded PF bimodality hedge.

## Score And Provenance

- Public reference score: `6.626` RMSE.
- Public source: <https://www.kaggle.com/code/kaiwalyaatulraut/rogii-public-tvt-solution>
- Team reproduction kernel: `leemarc223/rogii-kaiwalya-public-tvt-6626-repro`

The `6.626` score is attributed to the public source version. A private fork
can differ slightly on hidden wells because parts of the PF pipeline are
stochastic. Do not label a team run as `6.626` until its own Kaggle submission
has completed.

## Run On Kaggle

From a machine with the Kaggle API configured:

```powershell
kaggle kernels push -p kaggle_kernel_kaiwalya_public_tvt_6626_repro
kaggle kernels status leemarc223/rogii-kaiwalya-public-tvt-6626-repro
```

After the kernel is complete, submit its `submission.csv` through the Kaggle
Code Competition output interface or the competition submission command.

Competition data, generated CSV files, model artifacts, and credentials are
intentionally excluded from Git.
