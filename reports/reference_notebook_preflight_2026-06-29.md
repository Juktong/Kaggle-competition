# Reference Notebook Preflight - 2026-06-29

This report records the first reference-notebook preflight batch after the goal protocol was tightened.

## Current State

Official submissions state:

| submission_id | candidate | status | public score |
| ---: | --- | --- | ---: |
| 54174876 | fleongg pretrained branch calibration | PENDING |  |
| 54174151 | active-account 7.235 baseline reproduction | PENDING |  |
| 54162612 | Henry TabICL/v10 hidden-compatible retry | COMPLETE | 13.453 |

Because the baseline and fleongg scores are pending, dependent calibration should wait. Henry's weak score is usable as negative artifact-stack calibration. Independent reference-notebook preflight can continue without consuming official submission slots.

## Batch Question

Which reference notebook should be prepared while official scores are still pending?

## Options

| option | lane | evidence | decision |
| --- | --- | --- | --- |
| Run Degnonguidi 7.159 no-submit kernel | structural / high-upside | source audit PASS; dynamic test discovery; final submission validation; gold overlay off by default | selected |
| Run Baidalin 7.201 no-submit kernel | structural / high-upside | source audit FAIL: hardcoded visible train well demo and unsafe train/test `TVT_input` row copy | hold |
| Wait for pending official scores only | operational | would avoid extra work but does not improve next-batch readiness | reject |
| Patch audit before any reference run | diagnostic | useful for Baidalin, but Degnonguidi already passed current audit | partial: apply to Baidalin only |

## Source Audit Results

Degnonguidi 7.159:

```text
notebook: kaggle_kernel_degnonguidi_7159_submit/public-score-rogii-lb-7-159.ipynb
status: PASS
failures: 0
warnings: 0
required_signals:
  sample_submission: true
  dynamic_horizontal_well_discovery: true
  test_split_reference: true
  submission_write: true
```

Baidalin 7.201:

```text
notebook: kaggle_kernel_baidalin7201_v2/rogii-lb-7-201.ipynb
original status: FAIL
patched status: PASS
failures: 0
warnings: 0
```

The Baidalin row copy finding is especially important:

```text
hw_te['TVT_input'] = hw_tr['TVT_input'].values
```

This is not safe for hidden rerun assumptions unless the code path is removed or proven unreachable.

Patch applied:

```text
removed hardcoded visible demo well
replaced fixed-width id slicing with rsplit('_', 1)
replaced train/test TVT_input row copy with MD-aligned interpolation
aligned physical-model predictions by MD and falls back to selector if unavailable
```

Baidalin active-account preflight:

```text
kernel: joezzzzz/rogii-baidalin-7-201-preflight-codex
version: 1
status: RUNNING
official submission: none
```

## Selected Action

Fork Degnonguidi 7.159 into the active account and run it as a no-submit Kaggle kernel preflight:

```text
kernel: joezzzzz/rogii-degnonguidi-7159-preflight-codex
version: 1
status: ERROR
official submission: none
```

This does not consume an official competition submission slot. The purpose is to test dependency/runtime/output sanity before deciding whether any official submission is justified.

## Version 1 Result

Version 1 failed before producing `submission.csv`.

Downloaded log:

```text
artifacts/degnonguidi_7159_preflight_joezzzzz_v1/rogii-degnonguidi-7159-preflight-codex.log
```

Failure:

```text
KeyError at X_test_A = test_df_A[features_A]
missing columns:
  beam_vcons_d, beam_vloose_d, beam_stiff_d,
  tda-80 ... tda80,
  tdbc-40 ... tdbc40,
  tdsc-30 ... tdsc30,
  tdpf-30 ... tdpf30
```

Interpretation:

- The notebook found the data and artifact mount.
- The replacement `CVTrainer` loaded successfully.
- The failure is a Pipeline A train/test feature-schema mismatch.
- This is a runtime fix issue, not a source-audit failure or an official submission failure.

## Version 2 Patch

Patched the ignored working copy before `X_test_A = test_df_A[features_A]`:

```python
missing_test_features_A = [c for c in features_A if c not in test_df_A.columns]
if missing_test_features_A:
    print("Pipeline A: filling missing test feature columns from train medians:", missing_test_features_A)
    for _col in missing_test_features_A:
        _fill = pd.to_numeric(train_df_A[_col], errors="coerce").median() if _col in train_df_A.columns else 0.0
        if not np.isfinite(_fill):
            _fill = 0.0
        test_df_A[_col] = float(_fill)
```

Source audit after patch:

```text
status: PASS
failures: 0
warnings: 0
```

Pushed:

```text
kernel: joezzzzz/rogii-degnonguidi-7159-preflight-codex
version: 2
status: ERROR
official submission: none
```

## Version 2 Result

Version 2 passed the first failure point:

```text
Pipeline A: filling missing test feature columns from train medians:
beam_vcons_d, beam_vloose_d, beam_stiff_d, and td*/tda*/tdbc*/tdsc*/tdpf* columns
Pipeline A features built in 329s | train rows=3783989 test rows=14151 features=195
```

Then it failed while loading pre-trained artifact trainers:

```text
ModuleNotFoundError: No module named 'koolbox'
```

Interpretation:

- The feature-schema guard worked.
- The next blocker is pickle compatibility: artifact trainer files reference `koolbox.Trainer`.
- This remains a no-submit runtime preflight issue, not an official submission issue.

## Version 3 Patch

Patched the ignored working notebook after the visible `CVTrainer` replacement is defined:

```python
import types as _codex_types
_koolbox_stub = _codex_types.ModuleType("koolbox")
_koolbox_stub.Trainer = CVTrainer
sys.modules.setdefault("koolbox", _koolbox_stub)
```

Rationale:

- The notebook already defines `CVTrainer` as a visible replacement for `koolbox.Trainer`.
- Registering it under the expected module/class name lets `joblib.load` unpickle artifact trainers without internet or private source access.

Source audit after patch:

```text
status: PASS
failures: 0
warnings: 0
```

Pushed:

```text
kernel: joezzzzz/rogii-degnonguidi-7159-preflight-codex
version: 3
status: ERROR
official submission: none
```

## Version 3 Result

Version 3 reached the same artifact trainer loading stage, then failed on a more specific pickle module path:

```text
ModuleNotFoundError: No module named 'koolbox.trainer'; 'koolbox' is not a package
```

Interpretation:

- The package-level `koolbox.Trainer` compatibility stub was recognized only for `koolbox`.
- The pickle references `koolbox.trainer`, so Python needs `koolbox` to behave like a package and the submodule to exist in `sys.modules`.
- This remains a narrow no-submit runtime fix, not a reason to spend an official submission or switch to an unsafe notebook.

Downloaded log:

```text
artifacts/degnonguidi_7159_preflight_joezzzzz_v3/rogii-degnonguidi-7159-preflight-codex.log
```

## Version 4 Patch

Patched the ignored working notebook after the visible `CVTrainer` replacement is defined:

```python
import types as _codex_types
_koolbox_stub = _codex_types.ModuleType("koolbox")
_koolbox_stub.__path__ = []
_koolbox_stub.Trainer = CVTrainer
_koolbox_trainer_stub = _codex_types.ModuleType("koolbox.trainer")
_koolbox_trainer_stub.Trainer = CVTrainer
_koolbox_trainer_stub.CVTrainer = CVTrainer
_koolbox_stub.trainer = _koolbox_trainer_stub
sys.modules.setdefault("koolbox", _koolbox_stub)
sys.modules.setdefault("koolbox.trainer", _koolbox_trainer_stub)
```

Source audit after patch:

```text
status: PASS
failures: 0
warnings: 0
```

Pushed:

```text
kernel: joezzzzz/rogii-degnonguidi-7159-preflight-codex
version: 4
status: ERROR
official submission: none
```

## Version 4 Result

Version 4 progressed one nested module deeper, then failed on:

```text
ModuleNotFoundError: No module named 'koolbox.trainer.trainer'; 'koolbox.trainer' is not a package
```

Interpretation:

- The pickle references `koolbox.trainer.trainer`.
- The v4 `koolbox.trainer` stub also needs to behave like a package.
- This remains a dependency compatibility issue before model inference finishes.

Downloaded log:

```text
artifacts/degnonguidi_7159_preflight_joezzzzz_v4/rogii-degnonguidi-7159-preflight-codex.log
```

## Version 5 Patch

Patched the ignored working notebook to register all observed nested paths:

```python
_koolbox_stub = _codex_types.ModuleType("koolbox")
_koolbox_stub.__path__ = []
_koolbox_stub.Trainer = CVTrainer
_koolbox_trainer_stub = _codex_types.ModuleType("koolbox.trainer")
_koolbox_trainer_stub.__path__ = []
_koolbox_trainer_stub.Trainer = CVTrainer
_koolbox_trainer_stub.CVTrainer = CVTrainer
_koolbox_trainer_trainer_stub = _codex_types.ModuleType("koolbox.trainer.trainer")
_koolbox_trainer_trainer_stub.Trainer = CVTrainer
_koolbox_trainer_trainer_stub.CVTrainer = CVTrainer
_koolbox_stub.trainer = _koolbox_trainer_stub
_koolbox_trainer_stub.trainer = _koolbox_trainer_trainer_stub
sys.modules.setdefault("koolbox", _koolbox_stub)
sys.modules.setdefault("koolbox.trainer", _koolbox_trainer_stub)
sys.modules.setdefault("koolbox.trainer.trainer", _koolbox_trainer_trainer_stub)
```

Source audit after patch:

```text
status: PASS
failures: 0
warnings: 0
```

Pushed:

```text
kernel: joezzzzz/rogii-degnonguidi-7159-preflight-codex
version: 5
status: ERROR
official submission: none
```

## Version 5 Result

Version 5 fixed the nested module path issue and successfully loaded the first artifact trainer:

```text
Loading lightgbm-1 from artifacts...
  loaded with overall RMSE: 10.7668
```

Then prediction failed because the unpickled object did not have the visible replacement's expected model-list attribute:

```text
AttributeError: 'CVTrainer' object has no attribute 'models_'
```

Interpretation:

- The module-path pickle compatibility layer is now sufficient for at least one artifact.
- The next issue is loaded-object contract compatibility.
- This is a higher-risk patch than module aliasing, so one compatibility attempt is justified; another unrelated contract failure should trigger an inference-core port/block decision.

Downloaded log:

```text
artifacts/degnonguidi_7159_preflight_joezzzzz_v5/rogii-degnonguidi-7159-preflight-codex.log
```

## Version 6 Patch

Patched `CVTrainer.predict` in the ignored working notebook to use common model-list aliases:

```text
models_
models
estimators_
estimators
fold_models
fold_models_
trained_models
trained_models_
```

If no compatible attribute exists, the patched method raises an error with the available loaded attributes.

Source audit after patch:

```text
status: PASS
failures: 0
warnings: 0
```

Pushed:

```text
kernel: joezzzzz/rogii-degnonguidi-7159-preflight-codex
version: 6
status: RUNNING
official submission: none
```

## Metadata Notes

Degnonguidi metadata:

```text
enable_gpu: true
enable_internet: false
competition_sources:
  - rogii-wellbore-geology-prediction
dataset_sources:
  - phongnguyn23021656/koolbox-offline
  - nina2025/rogii-03
  - thbdh5765/rogii-v10-fresh-artifacts
  - fleongg/rogii-claude-models-pub
  - needless090/rogii-tabicl-mirror
  - ravaghi/wellbore-geology-prediction-artifacts
kernel_sources:
  - packagemanager/pm-119045926-at-06-21-2026-22-50-51
```

The original `leemarc223/rogii-degnonguidi-7159-submit` kernel is private/inaccessible from the active account, so active-account preflight is required.

## Next Branch Rules

| result | next action |
| --- | --- |
| kernel COMPLETE and output audit PASS | download output, run deep pre-submit audit with `experiments/reference_submission_registry.csv`, compare distance to `7.235`, decide whether it is a future submission candidate |
| kernel COMPLETE but audit FAIL | block official submission and add the failure to audit rules |
| kernel FAILED due dependency/schema | record missing source; choose between another minimal patch, inference-core port, or blocking this reference |
| output is near-duplicate of current best | hold as low-upside reference |
| output differs materially with low shape risk | consider one official slot after baseline score resolves |
| official scores appear while kernel runs | update ledger first, then re-rank next batch using new public scores |

## Current Decision

Proceed with Degnonguidi no-submit preflight v6 and Baidalin no-submit preflight v1. Do not make an official submission from either reference unless its completed output passes deep pre-submit and reference-distance audit.
