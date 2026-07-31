"""G3.5 — honest prefix-cut calibration smoke (local, no Kaggle, no submission).

The honest pipeline `54844628` already anchors the structural field on the target's own last 100 known
heel rows, so re-doing level anchoring adds nothing. The mechanism it does NOT have is the frontier's
**prefix-cut self-calibration**: cut the well's own known prefix, predict the held-out part of it, and
use that measured error to calibrate a bounded correction on the toe. That uses only test-available data
(the well's own known heel), so it is private-compatible.

Decisive prerequisite tested here, before building any correction:

    Does a well's error on a held-out part of its OWN known prefix predict its error on the toe?

If that correlation is ~0, no prefix-derived correction can work and the direction closes cheaply.

Method (per well, honest):
  known prefix K (TVT_input present). Cut at CUT: K_cal = K[:cut], K_hold = K[cut:].
  Re-run the PF forward with ONLY K_cal known -> predictions for K_hold and for the toe.
  signal  = PF error statistics on K_hold  (test-available at inference)
  target  = PF error statistics on the toe (what a correction would fix)
  Report correlation of bias and of drift-rate between the two, across wells.

Env: MAXW, CUT.
"""
import os, glob, numpy as np, pandas as pd

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MAXW = int(os.environ.get('MAXW', '30'))
CUT = float(os.environ.get('CUT', '0.70'))

code = open('/home/ubuntu/.claude/jobs/06dd2efb/tmp/SUNNY_CODE.py').read()
cut_i = code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
funcs = code[:cut_i].replace("INPUT_DIR = find_input_dir()",
                             "INPUT_DIR='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii'")
ns = {}; exec(funcs, ns)
run_pf = ns['run_particle_filter']

def slope(v):
    if len(v) < 5: return np.nan
    x = np.arange(len(v), dtype=float)
    return float(np.polyfit(x, v, 1)[0]) * len(v)      # total drift across the segment

rows = []
wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng = np.random.RandomState(7); rng.shuffle(wids)
done = 0
for wid in wids:
    if done >= MAXW: break
    try:
        hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv')
        tw = pd.read_csv(f'{D}/{wid}__typewell.csv')
    except Exception:
        continue
    kn = hw['TVT_input'].notna().values
    nk = int(kn.sum())
    if nk < 300 or (~kn).sum() < 300: continue
    ki = np.where(kn)[0]
    ncal = int(nk * CUT)
    if nk - ncal < 100: continue
    hold_idx = ki[ncal:]                      # held-out part of the KNOWN prefix
    toe_idx = np.where(~kn)[0]
    # truncate the known prefix: only K_cal is given to the PF
    hw2 = hw.copy()
    hw2.loc[hw2.index[hold_idx], 'TVT_input'] = np.nan
    try:
        pred, _ = run_pf(hw2, tw, seed=0)          # TRUNCATED prefix -> gives the inference-available signal
        pred_full, _ = run_pf(hw, tw, seed=0)      # FULL prefix -> the toe error we actually want to fix
    except Exception as e:
        print(f"  {wid}: PF failed {str(e)[:40]}"); continue
    tru = hw['TVT'].values.astype(float)
    e_hold = pred[hold_idx] - tru[hold_idx]        # signal: computable at inference
    e_toe_trunc = pred[toe_idx] - tru[toe_idx]     # same-run toe error (CONFOUNDED with the signal)
    e_toe = pred_full[toe_idx] - tru[toe_idx]      # deployment target: full-prefix toe error
    if not (np.isfinite(e_hold).all() and np.isfinite(e_toe).all()): continue
    rows.append(dict(wid=wid, n_hold=len(hold_idx), n_toe=len(toe_idx),
                     bias_hold=float(e_hold.mean()), bias_toe=float(e_toe.mean()),
                     bias_toe_trunc=float(e_toe_trunc.mean()),
                     drift_hold=slope(e_hold), drift_toe=slope(e_toe),
                     rmse_hold=float(np.sqrt(np.mean(e_hold**2))),
                     rmse_toe=float(np.sqrt(np.mean(e_toe**2)))))
    done += 1
    if done % 5 == 0: print(f"  [{done}/{MAXW}]", flush=True)

df = pd.DataFrame(rows)
print(f"\n=== G3.5 prefix-cut smoke: {len(df)} wells, CUT={CUT} ===")
print(f"  held-out prefix rows: median {df.n_hold.median():.0f} | toe rows: median {df.n_toe.median():.0f}")
print(f"  bias  on held-out prefix: mean {df.bias_hold.mean():+.3f} std {df.bias_hold.std():.3f}")
print(f"  bias  on toe            : mean {df.bias_toe.mean():+.3f} std {df.bias_toe.std():.3f}")
print(f"  rmse  hold {np.sqrt((df.rmse_hold**2).mean()):.3f} | toe {np.sqrt((df.rmse_toe**2).mean()):.3f}")
def cc(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() > 3 else np.nan
c_bias_conf = cc(df.bias_hold.values, df.bias_toe_trunc.values)
c_bias = cc(df.bias_hold.values, df.bias_toe.values)
print(f"\n  [CONFOUNDED] corr(bias_hold, bias_toe_SAME-truncated-run) = {c_bias_conf:+.4f}"
      f"  -> {100*c_bias_conf**2:.1f}% (shares the truncation degradation; NOT the deployment quantity)")
c_drift = cc(df.drift_hold.values, df.drift_toe.values)
print(f"\n  corr(bias_hold,  bias_toe)  = {c_bias:+.4f}   -> explains {100*c_bias**2:.1f}% of toe-bias variance")
print(f"  corr(drift_hold, drift_toe) = {c_drift:+.4f}   -> explains {100*c_drift**2:.1f}% of toe-drift variance")
# what would a bounded correction achieve, at best (oracle scalar, in-sample upper bound)?
m = np.isfinite(df.bias_hold) & np.isfinite(df.bias_toe)
a = float(np.dot(df.bias_hold[m], df.bias_toe[m]) / max(np.dot(df.bias_hold[m], df.bias_hold[m]), 1e-9))
resid = df.bias_toe[m] - a * df.bias_hold[m]
print(f"\n  best scalar a={a:.3f}: toe-bias std {df.bias_toe[m].std():.3f} -> residual std {resid.std():.3f}")
print(f"  variance of toe bias removed = {100*(1 - resid.var()/df.bias_toe[m].var()):.1f}% (IN-SAMPLE upper bound)")
print("\nGATE: the prefix-cut signal must explain a material share of toe bias for a bounded correction")
print("      to be worth building. Prior reference (2026-07-21): the raw heel level explained ~5% (100")
print("      rows) to ~17% (500 rows) of whole-well bias variance.")
df.to_csv('/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/g35_prefix_cut.csv', index=False)
