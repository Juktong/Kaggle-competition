# G1.3 — frontier dependency and provenance audit (2026-07-28)

Autopilot task `g13_dependency_provenance_audit` (`requires_gpu=false`, `can_submit=false`).
**No submission, 0 quota used.** Static source analysis of the frontier notebook plus empirical evidence
from our own completed full run (`54968060`, overlap-OFF, public 6.643).

## Headline

The frontier stack attaches **9 public Kaggle datasets**, which has been carried in the final-slot
package as a broad provenance reservation. Measured against source and run logs, the surface is much
narrower:

| class | count | datasets |
|---|---|---|
| affects predictions, **shared with our own honest line** | 1 | `ravaghi/wellbore-geology-prediction-artifacts` |
| affects predictions, **frontier-specific** | **1** | `fleongg/rogii-claude-models-pub` |
| runtime environment only (offline pip wheels) | 1 | `phongnguyn23021656/koolbox-offline` |
| loaded but its contribution was **rejected by an internal guard** | 1 | `pilkwang/rogii-model-package` |
| **vestigial** — zero source references, zero log appearances | 5 | `nina2025/rogii-03`, `thbdh5765/rogii-v10-fresh-artifacts`, `thbdh5765/rogii-v11-fresh-artifacts`, `chesnikovleonid/rogii-v50-dwt-phaseb-modelonly`, `needless090/rogii-tabicl-mirror` |

**Exactly one third-party dataset both affects predictions and is not already part of our own stack.**

## Evidence per dependency

**1. `ravaghi/wellbore-geology-prediction-artifacts` — required, model artifact, affects predictions.**
`RIDGE_ARTIFACT_ROOT`; supplies the Ridge/SP45 anchor (`SP45_RIDGE_MODEL_WEIGHT = 0.30`).
**Also listed in our own honest kernels** (`kaggle_kernel_struct_field_blend` → `54844628`,
`kaggle_kernel_struct_aniso`, `kaggle_kernel_dwt_pf_blend`). It is a shared baseline dependency, so it
adds no provenance risk *relative to* our own line.

**2. `fleongg/rogii-claude-models-pub` — required, model artifact, affects predictions, frontier-specific.**
`LEARNED_MODEL_ROOTS`; the learned-trajectory model. Run log: `INFERENCE mode - loading models from
/kaggle/input/datasets/fleongg/rogii-claude-models-pub`. It enters the final output through the
SP45/learned blend at `w_sp45 = 0.60 / w_learned = 0.40`
(`wrote final submission.csv from submission_sp45_learned_w0.60.csv`).

**Its public contribution is measurable and small.** `54990075` (SP45-only) vs `54968060` (SP45/learned
blend) differ *only* in this component — the other post-SP45 stages were verified inert in that run
(prefix calibration applied `alpha = 0.0`, model package rejected, bimodal made no change):

```
54990075  SP45 only            6.690
54968060  SP45 + learned 0.40  6.643
difference                     0.047   <- the measured public value of this dependency
config-variance floor (A1)     ~0.115
```

So the one irreducible frontier-specific dependency is worth **≈0.047 on public, inside the
config-variance floor**. Dropping it would cost little in measured terms.

**3. `phongnguyn23021656/koolbox-offline` — required at runtime, environment only, no direct prediction effect.**
An offline pip wheel repository. Run log: `using koolbox dir: …/koolbox-offline`, then
`install …/alembic-1.17.2…`, `colorlog-6.10.1`, `joblib-1.5.2`, `koolbox-0.1.3` →
`Successfully installed koolbox-0.1.3`. This exists because the competition is internet-off; it supplies
packages, not data or models.

**4. `pilkwang/rogii-model-package` — optional, model artifact, did NOT affect the final output.**
`MODEL_PACKAGE_ROOTS`, with `MODEL_PACKAGE_REQUIRE = False`. In the `54968060` run its correction was
**rejected by an internal safety guard**:

```
log:    model package p95 diff 29.464 > 25.000
report: selected_for_submission_csv = False   for every gated weight (0.00425 … 0.02)
```

So although the dataset is attached and loaded, the model package contributed nothing to the submitted
prediction. (Consistent with the A3 ablation, which found it a bounded ±2 ft top-up.)

**5–9. Five vestigial datasets.** `nina2025/rogii-03`, `thbdh5765/rogii-v10-fresh-artifacts`,
`thbdh5765/rogii-v11-fresh-artifacts`, `chesnikovleonid/rogii-v50-dwt-phaseb-modelonly`,
`needless090/rogii-tabicl-mirror` have **zero references in the notebook source** (neither full path nor
slug) and **zero appearances in the run logs**. They are almost certainly inherited from forking and can
be detached without changing behaviour.

## Generic-scan guards (checked, because they could reach unnamed datasets)

Two constructs scan `/kaggle/input` generically; both are guarded, so the vestigial datasets cannot leak
in:

- `glob('/kaggle/input/**/train/*__horizontal_well.csv')` runs **only as a fallback** if the competition
  path is not found (`if _DATA is None`). The competition dataset is attached, so the direct path
  resolves first and the glob never fires.
- The model-package auto-search over `input_root.glob('**/metadata/model_package_manifest.json')` is
  behind `MODEL_PACKAGE_ALLOW_AUTO_SEARCH`, which is set to **`False`**.

`enable_internet: false`; no `pip install` from the network, no URL/`requests`/socket calls (verified
2026-07-23). All dependencies are public Kaggle datasets — the standard sharing channel documented in
`reports/pf_frontier_submission_source_audit_2026-07-23.md`. **No private or undocumented rule is assumed
here**; this audit only records what the repo and the run logs show.

## Risk table

| # | dependency | runtime | type | affects predictions | replaceable | risk |
|---|---|---|---|---|---|---|
| 1 | `ravaghi/…artifacts` | required | model artifact | yes (SP45 ridge, w 0.30) | already ours | **low** — shared with our honest line |
| 2 | `fleongg/rogii-claude-models-pub` | required | model artifact | yes (learned traj, w 0.40) | reproducible in principle; measured worth ≈0.047 | **low–moderate** — the only frontier-specific prediction dependency |
| 3 | `phongnguyn…/koolbox-offline` | required | pip wheels | no | vendorable | **low** — environment only |
| 4 | `pilkwang/rogii-model-package` | optional | model artifact | **no** (guard-rejected in our run) | droppable | **low** |
| 5–9 | five vestigial datasets | not used | — | no | droppable | **negligible** |

Cross-cutting risk: all five prediction-relevant or runtime datasets are third-party **public** datasets
that could in principle be deleted or altered by their owners before the deadline. That is an
availability risk, not a correctness one, and it applies to `ravaghi/…` for our own honest line too.

## Mitigation queue (ordered by value / cost)

1. **Detach the 5 vestigial datasets** from our own frontier kernel metadata. Reduces the declared
   dependency surface 9 → 4 at zero expected prediction cost. Verify with one FAST smoke that the output
   is byte-identical. *No quota cost.*
2. **Drop `pilkwang/rogii-model-package`** from our frontier kernel: its correction was guard-rejected, so
   removing it should also be output-neutral. Same FAST-smoke verification. *No quota cost.*
3. **Vendor the koolbox wheels** (or test whether the notebook runs without `koolbox`) to convert a
   third-party runtime dependency into a repo-owned one. Moderate cost, no prediction effect.
4. **`fleongg/rogii-claude-models-pub`**: accept and document. Reproducing an equivalent learned-trajectory
   model is expensive and the measured public value is ≈0.047, inside the noise floor. If the dataset ever
   becomes unavailable, the fallback is exactly `54990075` (SP45-only, 6.690).

## Final-slot risk language — update

The earlier package described the frontier's provenance reservation as "derives from the public Kaiwalya
notebook plus **9 third-party public datasets**". That is accurate but overstates the exposure. Corrected
wording, now used in `reports/final_slot_package_corrected_gate_2026-07-26.md`:

> Frontier candidates depend on **one** third-party public dataset that is not already part of our own
> stack (`fleongg/rogii-claude-models-pub`, measured public value ≈0.047, within the config-variance
> floor). One further dataset supplies offline pip wheels, one was guard-rejected at runtime, five are
> vestigial, and the remaining one (`ravaghi/…artifacts`) is shared with our own honest line.

This **does not change** the slot recommendation — all three criteria still converge on
`54922806 + 54844628` — but it narrows the provenance argument to a single, quantified dependency rather
than a nine-dataset surface. Provenance-first still prefers `54844628` in slot 2 because it is the only
fully-owned, 760-well-OOF-validated candidate, which is a separate property from dependency count.

---

## CORRECTION (same day) — the ≈0.047 attribution spans two stages, not one

This report stated that `54990075` (SP45-only) and `54968060` "differ *only* in this component
[the learned-trajectory blend]", because the other post-SP45 stages were taken to be inert. That was
based on the A5 bimodal claim, which has since been shown incorrect: the **PF bimodal branch hedge
applies +2.0 ft to all 4,301 rows of `00e12e8b`** (see
`reports/frontier_variant_matrix_lite_2026-07-28.md`).

The two submissions therefore differ across **two** active stages — the learned-trajectory blend *and*
the bimodal hedge. **≈0.047 is a joint upper bound for both, not a clean measurement of
`fleongg/rogii-claude-models-pub` alone.** The dependency classification in the risk table is unaffected
(one prediction-affecting third-party dataset not already in our stack); only the size attributed to it
changes, and it can only be smaller than 0.047.

