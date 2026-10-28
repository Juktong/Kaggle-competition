"""Direction A (memory-efficient rewrite): DWT+PF error decomposition -> feature table for the selector (B).
v1 died at 750/773 wells building a list of 3.78M dicts -> DataFrame (multi-GB peak, killed).
v2 accumulates per-well numpy arrays (float32) and concatenates once, saving .npz."""
import numpy as np, pandas as pd, os, glob
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
OUT = os.environ.get('OUT', os.path.join(SH, 'decomp_features.npz'))

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dw = cs['well'][tM].astype(str); do = cs['oof'][tM].astype(np.float64); dy = cs['yt'][tM].astype(np.float64); dr = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(dw, dr, do, dy): dwt[w][r] = (o, y)
del cs, dw, do, dy, dr

pf = np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz', allow_pickle=True)
pw = pf['well'].astype(str); pp = pf['pred'].astype(np.float64)

sn = np.load('/home/ubuntu/.claude/jobs/276bd506/tmp/smk/sunny_oof.npz', allow_pickle=True)
sw = sn['well'].astype(str); spm = sn['per_model'].astype(np.float32)
gdis = {}
_idx = defaultdict(list)
for i, w in enumerate(sw): _idx[w].append(i)
for w, ii in _idx.items(): gdis[w] = np.std(spm[np.array(ii)], axis=1).astype(np.float32)
del sn, sw, spm, _idx

cols = ['dwt', 'pf', 'blend', 'truth', 'row_frac', 'toe_dist_md', 'gr_rough', 'curvature',
        'gbm_disagree', 'heel_drift', 'n_eval', 'gr_missing', 'tw_range', 'tw_pressure', 'z_span']
acc = {c: [] for c in cols}; wells_acc = []
wl = list(np.unique(pw))[:int(os.environ.get('MAXW', 10**9))]
for i, wid in enumerate(wl):
    if i % 100 == 0: print(f'  [A2] {i}/{len(wl)}', flush=True)
    if wid not in dwt: continue
    try:
        hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv'); tw = pd.read_csv(f'{D}/{wid}__typewell.csv')
    except Exception: continue
    toe = hw['TVT_input'].isna().values; tidx = np.where(toe)[0]
    m = pw == wid; pr = pp[m]
    if len(pr) != len(tidx): continue
    keep_j = []; keep_i = []
    for j, ii in enumerate(tidx):
        if ii in dwt[wid]: keep_j.append(j); keep_i.append(ii)
    if len(keep_i) < 10: continue
    keep_j = np.array(keep_j); keep_i = np.array(keep_i)
    o = np.array([dwt[wid][ii][0] for ii in keep_i], dtype=np.float32)
    y = np.array([dwt[wid][ii][1] for ii in keep_i], dtype=np.float32)
    p = pr[keep_j].astype(np.float32)
    kn = hw[hw['TVT_input'].notna()]
    gr = hw['GR'].values.astype(float); z = hw['Z'].values.astype(float); md = hw['MD'].values.astype(float)
    grough = pd.Series(gr).rolling(15, center=True, min_periods=1).std().values
    curv = np.abs(np.gradient(np.gradient(z, md), md))
    tw_tvt = tw['TVT'].values.astype(float); tw_lo, tw_hi = np.nanmin(tw_tvt), np.nanmax(tw_tvt)
    last_md = float(kn['MD'].iloc[-1])
    tail = kn.tail(30); dt = np.diff(tail['TVT_input'].values); dm = np.diff(tail['MD'].values); mm = dm > 0
    hd = float(np.median(np.abs(dt[mm] / dm[mm]))) if mm.sum() >= 3 else 0.0
    n = len(keep_i)
    gd = gdis.get(wid)
    gdv = np.full(n, np.nan, np.float32)
    if gd is not None:
        k = min(n, len(gd)); gdv[:k] = gd[:k]
    acc['dwt'].append(o); acc['pf'].append(p); acc['blend'].append((0.5 * o + 0.5 * p).astype(np.float32))
    acc['truth'].append(y)
    acc['row_frac'].append((np.arange(n) / n).astype(np.float32))
    acc['toe_dist_md'].append((md[keep_i] - last_md).astype(np.float32))
    acc['gr_rough'].append(np.nan_to_num(grough[keep_i]).astype(np.float32))
    acc['curvature'].append(np.nan_to_num(curv[keep_i]).astype(np.float32))
    acc['gbm_disagree'].append(gdv)
    acc['heel_drift'].append(np.full(n, hd, np.float32))
    acc['n_eval'].append(np.full(n, n, np.float32))
    acc['gr_missing'].append(np.full(n, float(np.mean(~np.isfinite(gr))), np.float32))
    acc['tw_range'].append(np.full(n, float(tw_hi - tw_lo), np.float32))
    acc['tw_pressure'].append(np.minimum(np.abs(y - tw_lo), np.abs(tw_hi - y)).astype(np.float32))
    acc['z_span'].append(np.full(n, float(np.nanmax(z[toe]) - np.nanmin(z[toe])), np.float32))
    wells_acc.append(np.full(n, wid))

arrs = {c: np.concatenate(acc[c]) for c in cols}
arrs['well'] = np.concatenate(wells_acc).astype(str)
np.savez_compressed(OUT, **arrs)
print(f"\nrows={len(arrs['truth'])} wells={len(np.unique(arrs['well']))} -> {OUT}")

Dv, Pv, Bv, Yv = arrs['dwt'].astype(np.float64), arrs['pf'].astype(np.float64), arrs['blend'].astype(np.float64), arrs['truth'].astype(np.float64)
eD, eP, eB = np.abs(Dv - Yv), np.abs(Pv - Yv), np.abs(Bv - Yv)
print("\n=== pooled RMSE ===")
for nm, v in [('DWT', Dv), ('PF', Pv), ('BLEND0.5', Bv)]:
    print(f"  {nm:9s} {np.sqrt(np.mean((v-Yv)**2)):.4f}")
win = np.where((eD < eP) & (eD < eB), 0, np.where((eP < eD) & (eP < eB), 1, 2))
print(f"\n=== per-row winner === DWT={100*np.mean(win==0):.1f}%  PF={100*np.mean(win==1):.1f}%  BLEND={100*np.mean(win==2):.1f}%")
print(f"both_fail (both>10ft): {100*np.mean(np.minimum(eD,eP)>10):.1f}% of rows")
print("\n=== error by toe-distance quartile ===")
tq = np.digitize(arrs['toe_dist_md'], np.quantile(arrs['toe_dist_md'], [.25, .5, .75]))
for k in range(4):
    m = tq == k
    print(f"  Q{k+1}: n={m.sum():>8d} DWT={np.sqrt(np.mean(eD[m]**2)):6.2f} PF={np.sqrt(np.mean(eP[m]**2)):6.2f} BLEND={np.sqrt(np.mean(eB[m]**2)):6.2f} PFwin={100*np.mean(eP[m]<eD[m]):4.1f}%")
print("\n=== DIRECTIONAL feature screen: corr with (eD-eP) [+ => PF better] ===")
diff = eD - eP
for f in ['gbm_disagree', 'gr_rough', 'curvature', 'tw_pressure', 'toe_dist_md', 'heel_drift', 'gr_missing', 'tw_range', 'row_frac', 'z_span', 'n_eval']:
    s = arrs[f].astype(np.float64); ok = np.isfinite(s) & np.isfinite(diff)
    if ok.sum() > 1000:
        print(f"  {f:14s} corr={np.corrcoef(s[ok],diff[ok])[0,1]:+.4f}  (n={ok.sum()})")
