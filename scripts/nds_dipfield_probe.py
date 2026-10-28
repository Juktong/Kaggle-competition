"""Probe: neighbour-well DIP-field (drift) vs the deployed LEVEL-field, anchored at the known heel.

Honest by construction: neighbour set excludes the target well and any near-duplicate (min_sep guard);
the anchor is the last row where TVT_input is known; only X/Y/Z/MD/GR/TVT_input are used from the target.
"""
import glob, os, numpy as np, pandas as pd
from scipy.spatial import cKDTree

ws = sorted(set(os.path.basename(p).split('__')[0] for p in glob.glob('train/*__horizontal_well.csv')))
W = {}
for w in ws:
    d = pd.read_csv(f'train/{w}__horizontal_well.csv',
                    usecols=['MD', 'X', 'Y', 'Z', 'TVT', 'TVT_input'])
    if d['TVT'].isna().any():
        continue
    W[w] = d
keys = list(W)
cen = np.array([[W[w].X.mean(), W[w].Y.mean()] for w in keys])
tree = cKDTree(cen)
MIN_SEP = 150.0      # duplicate guard, same value as the deployed field
K = 12
RAD = 8000.0

rows = []
for ti, w in enumerate(keys):
    d = W[w]
    known = d.TVT_input.notna().values
    toe = ~known
    if known.sum() < 30 or toe.sum() < 30:
        continue
    x, y, tvt = d.X.values, d.Y.values, d.TVT.values
    ai = np.where(known)[0][-1]                      # anchor = last known row
    # neighbour wells: nearest centroids, excluding self and near-duplicates
    cand = tree.query_ball_point(cen[ti], RAD)
    nb = []
    for j in cand:
        if j == ti:
            continue
        oj = W[keys[j]]
        if np.hypot(oj.X.mean() - x.mean(), oj.Y.mean() - y.mean()) < MIN_SEP:
            continue                                  # duplicate guard
        nb.append(j)
        if len(nb) >= K:
            break
    if len(nb) < 4:
        continue
    px = np.concatenate([W[keys[j]].X.values for j in nb])
    py = np.concatenate([W[keys[j]].Y.values for j in nb])
    pt = np.concatenate([W[keys[j]].TVT.values for j in nb])
    # local plane fit around the target well footprint
    A = np.c_[px - x[ai], py - y[ai], np.ones(len(px))]
    coef, *_ = np.linalg.lstsq(A, pt, rcond=None)
    a, b, c = coef
    dx, dy = x - x[ai], y - y[ai]
    lvl = a * dx + b * dy + c                        # LEVEL field (deployed style)
    drift = a * dx + b * dy                          # DIP field: increment only
    pred_flat = np.full(len(d), tvt[ai])
    pred_lvl = lvl
    pred_dip = tvt[ai] + drift
    f = lambda p: float(np.sqrt(np.mean((p[toe] - tvt[toe]) ** 2)))
    # blended forms at the deployed weight and a stronger one
    rows.append(dict(w=w, n_toe=int(toe.sum()), nb=len(nb),
                     flat=f(pred_flat), lvl=f(pred_lvl), dip=f(pred_dip),
                     dip15=f(0.85 * pred_flat + 0.15 * pred_dip),
                     dip50=f(0.50 * pred_flat + 0.50 * pred_dip),
                     lvl15=f(0.85 * pred_flat + 0.15 * pred_lvl)))
df = pd.DataFrame(rows)
tot = lambda k: float(np.sqrt(np.average(df[k] ** 2, weights=df.n_toe)))
print('wells evaluated', len(df), ' median neighbours', int(df.nb.median()))
print('\nrow-weighted RMSE on hidden toe rows (lower better)')
for k, lab in [('flat', 'flat anchor (carry last known TVT)'),
               ('lvl', 'neighbour LEVEL field, standalone'),
               ('dip', 'neighbour DIP field (anchor + drift)'),
               ('lvl15', 'flat + 0.15*LEVEL'),
               ('dip15', 'flat + 0.15*DIP'),
               ('dip50', 'flat + 0.50*DIP')]:
    print('  %-38s %8.4f   delta_vs_flat %+8.4f' % (lab, tot(k), tot('flat') - tot(k)))
print('\nper-well: DIP beats flat on %.1f%%; DIP15 beats flat on %.1f%%; LEVEL beats flat on %.1f%%'
      % (100 * (df.dip < df.flat).mean(), 100 * (df.dip15 < df.flat).mean(), 100 * (df.lvl < df.flat).mean()))
g = df.flat - df.dip15
print('per-well gain of DIP15 vs flat: mean %+.4f median %+.4f std %.4f  frac>0 %.3f'
      % (g.mean(), g.median(), g.std(), (g > 0).mean()))
b = np.array([np.average(g.sample(len(g), replace=True, random_state=s)) for s in range(400)])
print('760-well bootstrap of the mean gain: 5th %+.4f 50th %+.4f 95th %+.4f' % tuple(np.percentile(b, [5, 50, 95])))
b3 = np.array([g.sample(3, replace=True, random_state=s).mean() for s in range(2000)])
print('3-WELL bootstrap (the scored scale): 5th %+.4f 50th %+.4f 95th %+.4f  P(gain>0) %.3f'
      % (*np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
df.to_csv('/home/ubuntu/.claude/jobs/dca65f44/tmp/dipfield_probe.csv', index=False)
