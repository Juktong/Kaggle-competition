"""Probe 3: typewell-group LOCAL DIP PLANE field (vs the deployed isotropic IDW).

The deployed structural field is an isotropic IDW over group-mates' r = TVT + Z, which ignores the dip
DIRECTION. Here we fit, per toe row, a local plane  r ~ a + b*x + c*y  by ridge regression over nearby
group-mate points, and integrate only the gradient (b, c) from the target's own heel anchor:

    r_pred(i) = r0 + b*(x_i - x0) + c*(y_i - y0)      ->   TVT = r_pred - Z

r0/(x0,y0) come from the target's OWN last ANCHOR known rows (test-available). Same duplicate guard
(min_sep) and the same group key from the target's own typewell. Saves per-row dip predictions plus the
plane residual RMS and neighbour count as confidence proxies.
Env: MIN_SEP, RADIUS, MIN_PTS, ANCHOR, MAXW, OUT.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MIN_SEP = float(os.environ.get('MIN_SEP', '150')); RADIUS = float(os.environ.get('RADIUS', '1500'))
MIN_PTS = int(os.environ.get('MIN_PTS', '200')); ANCHOR = int(os.environ.get('ANCHOR', '100'))
MAXW = int(os.environ.get('MAXW', '10000')); RIDGE = 1e-3
OUT = os.environ.get('OUT', os.path.join(SH, 'dip_oof.npz'))
STRIDE = int(os.environ.get('STRIDE', '25'))     # fit a plane every STRIDE toe rows, interpolate between

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dwell = cs['well'][tM].astype(str); dr = cs['ridx'][tM].astype(int)
toe_rows = defaultdict(set)
for w, r in zip(dwell, dr): toe_rows[w].add(int(r))
del cs

gkey = {}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid = os.path.basename(f).split('__')[0]
    try: gkey[wid] = round(float(np.nanmax(pd.read_csv(f, usecols=['TVT'])['TVT'].values)), 1)
    except Exception: pass
groups = defaultdict(list)
for w, k in gkey.items(): groups[k].append(w)
print(f'{len(groups)} groups', flush=True)

cache = {}
def get(w):
    if w not in cache:
        cache[w] = pd.read_csv(f'{D}/{w}__horizontal_well.csv', usecols=['X', 'Y', 'Z', 'TVT', 'TVT_input'])
    return cache[w]
_t = {}
def tree_of(w):
    if w not in _t:
        h = get(w); _t[w] = cKDTree(np.column_stack([h['X'].values, h['Y'].values]))
    return _t[w]

targets = sorted(toe_rows.keys())[:MAXW]
OW, OR, OD, ORES, ONB = [], [], [], [], []
for n, wid in enumerate(targets):
    if n % 50 == 0: print(f'  [{n}/{len(targets)}]', flush=True)
    if wid not in gkey: continue
    try: hw = get(wid)
    except Exception: continue
    kn = hw['TVT_input'].notna().values
    if kn.sum() < ANCHOR: continue
    ridx = np.array(sorted(toe_rows[wid]))
    if len(ridx) < 10: continue
    X = hw['X'].values; Y = hw['Y'].values; Z = hw['Z'].values
    txy = np.column_stack([X, Y])
    px, py, pr = [], [], []
    for m in groups.get(gkey[wid], []):
        if m == wid: continue
        try: mh = get(m)
        except Exception: continue
        if len(mh) < 5: continue
        d, _ = tree_of(m).query(txy[::10], k=1)
        if float(np.median(d)) < MIN_SEP: continue        # duplicate guard
        rr = mh['TVT'].values + mh['Z'].values; ok = np.isfinite(rr)
        px.append(mh['X'].values[ok][::4]); py.append(mh['Y'].values[ok][::4]); pr.append(rr[ok][::4])
    if not px: continue
    PX = np.concatenate(px); PY = np.concatenate(py); PR = np.concatenate(pr)
    tree = cKDTree(np.column_stack([PX, PY]))
    kn_idx = np.where(kn)[0][-ANCHOR:]
    r0 = float(np.nanmean(hw['TVT_input'].values[kn_idx] + Z[kn_idx]))
    x0 = float(np.nanmean(X[kn_idx])); y0 = float(np.nanmean(Y[kn_idx]))
    # fit planes on a strided subset of the toe, then interpolate the gradient along the trajectory
    fit_at = ridx[::STRIDE]
    if len(fit_at) < 2: fit_at = ridx[:2]
    bs, csx, res = [], [], []
    for i in fit_at:
        idx = tree.query_ball_point([X[i], Y[i]], RADIUS)
        if len(idx) < MIN_PTS:
            d, idx = tree.query([X[i], Y[i]], k=min(MIN_PTS, len(PR))); idx = np.atleast_1d(idx)
        idx = np.asarray(idx)
        A = np.column_stack([np.ones(len(idx)), PX[idx] - X[i], PY[idx] - Y[i]])
        yv = PR[idx]
        try:
            coef = np.linalg.solve(A.T @ A + RIDGE * np.eye(3), A.T @ yv)
            rr = yv - A @ coef
            bs.append(coef[1]); csx.append(coef[2]); res.append(float(np.sqrt(np.mean(rr ** 2))))
        except Exception:
            bs.append(0.0); csx.append(0.0); res.append(np.nan)
    b_i = np.interp(ridx, fit_at, bs); c_i = np.interp(ridx, fit_at, csx)
    res_i = np.interp(ridx, fit_at, np.nan_to_num(res, nan=float(np.nanmean(res)) if np.isfinite(res).any() else 0.0))
    r_pred = r0 + b_i * (X[ridx] - x0) + c_i * (Y[ridx] - y0)
    pred = r_pred - Z[ridx]
    if not np.isfinite(pred).all(): continue
    OW.append(np.full(len(ridx), wid)); OR.append(ridx); OD.append(pred.astype(np.float32))
    ORES.append(res_i.astype(np.float32)); ONB.append(np.full(len(ridx), len(px), np.int32))

np.savez_compressed(OUT, well=np.concatenate(OW).astype(str), ridx=np.concatenate(OR).astype(np.int32),
                    dip=np.concatenate(OD), plane_res=np.concatenate(ORES), nnb=np.concatenate(ONB))
print(f"saved {OUT}: wells={len(OW)} rows={sum(len(x) for x in OR)}")
