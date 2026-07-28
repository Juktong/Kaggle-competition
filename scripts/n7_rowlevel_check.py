"""N7 follow-up: ROW-level test. The public repo's -0.107 gain was tortuosity as a per-row FEATURE inside
a LightGBM predicting TVT, not a per-well summary. The well-level test can miss a row-level signal, so
this measures local tortuosity in a window around each toe row against that row's |residual| of the
deployed honest line."""
import os, sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, '/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue/scripts')
os.environ['STATION_FT'] = '30'
import n7_q3d_tortuosity as T

D = T.D; SH = T.SH
STATION = 30.0
WIN = 600.0          # ft of MD on each side for the local tortuosity window

z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
well = z['well'].astype(str); ridx = z['ridx'].astype(int)
err = np.abs(z['s_54844628'].astype(np.float64) - z['truth'].astype(np.float64))
res = pd.DataFrame(dict(well=well, ridx=ridx, aerr=err))

wids = sorted(set(well))[:120]
rows = []
for w in wids:
    d = pd.read_csv(f'{D}/{w}__horizontal_well.csv', usecols=['MD','X','Y','Z'])
    md = d['MD'].values.astype(float)
    grid = np.arange(md[0], md[-1], STATION)
    if len(grid) < 8: continue
    x, y, zz = (np.interp(grid, md, d[c].values.astype(float)) for c in ['X','Y','Z'])
    inc, azi, ds, md_s = T._angles(grid, x, y, zz)
    dls_local = np.abs(np.diff(inc)) + np.abs(np.diff(azi)) * np.sin(np.radians(inc[:-1]))
    md_d = md_s[1:]
    sub = res[res.well == w]
    if sub.empty: continue
    r_md = md[np.clip(sub.ridx.values, 0, len(md)-1)]
    # local tortuosity = mean angular change per 100 ft within +/-WIN of the row
    loc = np.empty(len(r_md))
    for i, m0 in enumerate(r_md):
        sel = np.abs(md_d - m0) <= WIN
        loc[i] = (100.0 * np.sum(dls_local[sel]) / max(STATION * sel.sum(), 1e-9)) if sel.any() else np.nan
    rows.append(pd.DataFrame(dict(well=w, aerr=sub.aerr.values, loc_tort=loc)))

A = pd.concat(rows).dropna()
print('rows %d over %d wells' % (len(A), A.well.nunique()))
print('local tortuosity (deg/100ft): p5 %.3f  p50 %.3f  p95 %.3f'
      % tuple(np.percentile(A.loc_tort, [5,50,95])))
print()
print('ROW-LEVEL pooled  pearson(loc_tort, |err|) = %.4f   spearman = %.4f'
      % (A.loc_tort.corr(A.aerr), A.loc_tort.corr(A.aerr, method='spearman')))
# within-well correlation removes the between-well confound
g = A.groupby('well').apply(lambda t: t.loc_tort.corr(t.aerr, method='spearman'), include_groups=False)
g = g.dropna()
print('WITHIN-WELL spearman: mean %+.4f  median %+.4f  std %.4f  frac|rho|>0.2 %.3f  (n=%d wells)'
      % (g.mean(), g.median(), g.std(), (g.abs() > 0.2).mean(), len(g)))
