# ROGII — Lucifer PF-stack honest OOF plan (2026-07-18)

Session `06dd2efb`. Secondary line while the DWT+PF blend submission (`54804893`) reruns. Goal: determine
whether Lucifer `wellbore-wizard-physics-pf-stack` provides honest forward signal BEYOND the plain PF already
in the DWT+PF blend (OOF 9.30) — i.e. does adding beam-DP / ANCC-PF / Z-PF / NCC / a scale-ensemble further
decorrelate from DWT (and from the plain PF)? Neutral technical language.

## 1. Honest forward inventory (extracted + verified)
Clean extract: `scripts/lucifer_honest_forward.py` (imports clean; every forward run end-to-end on real test
data; numba absent locally → pure-Python `@njit` no-op fallback, slower but correct). Distinct honest forwards
beyond Sunny's plain `run_pf_lik_ensemble`:

| function | what | signature | honest inputs | return |
|---|---|---|---|---|
| `run_beam_ensemble` | beam-search DP GR↔typewell alignment, 14 configs averaged | `(hw, tw)` | hw TVT_input,GR ; tw TVT,GR | full-len array |
| `run_pf_ancc` | **anchored** rate-random-walk PF (anchored on last-known TVT+Z; NOT the ANCC surface) | `(hw, tw_tvt, tw_gr, N)` | hw TVT_input,Z,MD,GR | `(pts_eval, std)` |
| `run_pf_z` | Z-velocity-coupled PF (TVT-rate ~ fitted Z-gradient + smoothed-GR channel) | `(hw, tw_tvt, tw_gr, N)` | hw TVT_input,Z,MD,GR | `(pts_eval, std)` |
| `multi_scale_ncc` | multi-scale normalized-cross-correlation template matcher (3 scales, softmax) | `(kgr, ktvt, hgr, hws, stride)` | arrays from GR/TVT_input | array |
| `run_pf_lik_ensemble_scales` | multi-scale variant of the plain lik-PF; one 128-seed run → {pf_scale_3/5/8/12, pf_mean} | `(hw, tw, scales, n_particles, n_seeds)` | hw TVT_input,Z,MD,GR ; tw TVT,GR | dict |
| `selector_well_code` + `apply_selector_variant` | router: bins on n_eval (thr 4840) & z_span (thr 136.73/185.51) → blend-variant of {pf_scale, beam, hold} | `(hw)` / `(name, pf_by_scale, tvt_beam, last_known)` | hw TVT_input,Z | code/array |

**Return-shape note (important for the harness):** plain-PF / scales-`pf_mean` / beam return **full-length**
arrays (index by hw row); `run_pf_ancc` / `run_pf_z` return `(pts, std)` where `pts` is **eval-rows-only**
(scatter to full length via `out[toe]=pts`).

## 2. Honesty / leakage (verified vs real schema)
- Test hw = MD,X,Y,Z,GR,TVT_input ; test tw = TVT,GR (no Geology in test typewells). All forwards above read
  ONLY those. `run_pf_ancc` is anchored-PF, never reads `hw['ANCC']` (name is misleading but body is honest).
- **Leakage confined to overlap-only, EXCLUDED from the extract:** `tvt_from_contacts` (cell 16) &
  `tvt_from_contacts_arr` (cell 28) use `hw_tr['TVT']` (toe truth) + `hw_tr[EGFDU/…]` (structural surface) +
  tw Geology; `guarded_contact_override` (cell 28) gated `if wid not in train_wells: continue` (skips novel
  wells entirely). Same pattern as Sunny → the Lucifer submission's public strength on overlap is leakage,
  not novel strength; the honest forwards are the novel-well component.

## 3. Compute profile & smoke
- Pure CPU. numba `@njit` kernels (`_beam_jit`, `_pf_ancc`, `_pf_z`, `_pf_lik_allseeds`) — fast WITH numba;
  without it, pure-Python fallback. Local timing (no numba): `run_beam_ensemble` ≈ 15 s/well (14 configs);
  `run_pf_lik_ensemble_scales` ≈ 0.3 s/well at tiny params. Beam is the bottleneck (~1.6 h for 773 wells on
  2 cores without numba). Defaults: lik-PF n_seeds=128/n_particles=500/scales=(3,5,8,12); ancc/z N=600; beam
  14 configs (bs∈{8..30}).
- **Decorrelation smoke (6 wells, NS=8, `scripts`→`$JOB/tmp/lucifer_smoke.py`): <SMOKE_RESULT>**

## 4. Decision gate (before any full OOF or submission)
Run the full honest OOF (773 wells) for a Lucifer forward ONLY if the smoke shows it is (a) comparably strong
to DWT/PF and (b) decorrelated from BOTH DWT and the plain PF (else it adds nothing beyond the banked DWT+PF
blend). If a full OOF confirms an additional decorrelated positive-weight component, test a
DWT+PF+<lucifer> multi-model blend; submit ONLY if it clears an honest OOF gate + pre-submit audit (same bar
as the DWT+PF blend). **Resource rule:** do not launch the full (slow, no-numba) Lucifer OOF while it would
contend with an active critical run; install numba first if a full run is warranted. **No Lucifer submission
without honest OOF + blend gate + audit.**

## 5. Status
- Extract + honesty verified; decorrelation smoke: <SMOKE_STATUS>. Full OOF: not started (gated on smoke).
