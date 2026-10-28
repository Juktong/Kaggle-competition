"""Direction F/G: group-anchored cross-well structural field — HONESTY GATE (min_sep A/B) + nested weight.

Finding to test: typewells cluster into ~54 master logs; group-mates share a TVT datum so r = TVT+Z is
comparable within a group. Predict the target's toe r by IDW over group-mates' (X,Y,r), anchor the level on
the target's OWN known heel rows, then TVT = r_pred + anchor - Z.

CRITICAL GATE: if a group-mate is a near-duplicate (twin) of the target well, its r at the same coordinates is
the target's own truth -> duplicate reconstruction (overlap leakage), NOT honest. So we A/B the minimum
trajectory separation `min_sep`: if the positive-weight gain collapses once near neighbours are excluded, the
signal was duplicate-driven and the line closes.

Also: weight is selected NESTED (by well group-split), never in-sample.
Env: MAXW (wells cap), MINSEPS (comma list), K, ANCHOR.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
K = int(os.environ.get('K', '12')); ANCHOR = int(os.environ.get('ANCHOR', '100'))
MAXW = int(os.environ.get('MAXW', '200'))
MINSEPS = [float(x) for x in os.environ.get('MINSEPS', '0,150,300').split(',')]

# ---- reference models on identical rows ----
cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dw = cs['well'][tM].astype(str); do = cs['oof'][tM].astype(np.float64); dy = cs['yt'][tM].astype(np.float64); dr = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(dw, dr, do, dy): dwt[w][r] = (o, y)
pf = np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz', allow_pickle=True)
pw = pf['well'].astype(str); pp = pf['pred'].astype(np.float64)
pf_by = {}
for wid in np.unique(pw): pf_by[wid] = pp[pw == wid]

# ---- typewell groups (group key = rounded max TVT of the master log) ----
print('building typewell groups...', flush=True)
gkey = {}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid = os.path.basename(f).split('__')[0]
    try:
        t = pd.read_csv(f, usecols=['TVT'])
        gkey[wid] = round(float(np.nanmax(t['TVT'].values)), 1)
    except Exception: pass
groups = defaultdict(list)
for wid, k in gkey.items(): groups[k].append(wid)
sizes = sorted(((len(v), k) for k, v in groups.items()), reverse=True)
print(f'  {len(groups)} groups; top sizes {[s for s,_ in sizes[:6]]}', flush=True)

# ---- load well geometry once (X,Y,Z,TVT,TVT_input) ----
def load(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['MD', 'X', 'Y', 'Z', 'TVT', 'TVT_input'])
    return hw

NG=int(os.environ.get('NGROUPS','3'))
top_groups = [k for _, k in sizes[:NG]]
targets = []
for gk in top_groups: targets += groups[gk]
targets = [w for w in targets if w in dwt and w in pf_by][:MAXW]
print(f'targets={len(targets)} from {len(top_groups)} groups', flush=True)

cache = {}
def get(wid):
    if wid not in cache: cache[wid] = load(wid)
    return cache[wid]

_trees = {}
def tree_of(wid):
    if wid not in _trees:
        mh = get(wid); _trees[wid] = cKDTree(np.column_stack([mh['X'].values, mh['Y'].values]))
    return _trees[wid]

res = {ms: [] for ms in MINSEPS}
meta = []
SEPSTATS = []
for n, wid in enumerate(targets):
    if n % 20 == 0: print(f'  [{n}/{len(targets)}]', flush=True)
    try:
        hw = get(wid)
    except Exception: continue
    kn_mask = hw['TVT_input'].notna().values
    toe_mask = ~kn_mask
    if kn_mask.sum() < ANCHOR or toe_mask.sum() < 10: continue
    tidx = np.where(toe_mask)[0]
    keep = [(j, ii) for j, ii in enumerate(tidx) if ii in dwt[wid]]
    if len(keep) < 10: continue
    kj = np.array([j for j, _ in keep]); ki = np.array([ii for _, ii in keep])
    Dv = np.array([dwt[wid][ii][0] for ii in ki]); Yv = np.array([dwt[wid][ii][1] for ii in ki])
    prf = pf_by[wid]
    if len(prf) != len(tidx): continue
    Pv = prf[kj]
    X = hw['X'].values; Y = hw['Y'].values; Z = hw['Z'].values
    tgt_xy = np.column_stack([X, Y])
    gk = gkey.get(wid)
    mates = [m for m in groups.get(gk, []) if m != wid]
    if not mates: continue
    # anchor rows: last ANCHOR known rows
    kn_idx = np.where(kn_mask)[0][-ANCHOR:]
    r_true_anchor = hw['TVT_input'].values[kn_idx] + Z[kn_idx]
    # --- compute each mate's median trajectory separation ONCE (was O(n^2) per min_sep) ---
    mate_info = []
    for m in mates:
        try: mh = get(m)
        except Exception: continue
        mxy = np.column_stack([mh['X'].values, mh['Y'].values])
        if len(mxy) < 5: continue
        d, _ = tree_of(m).query(tgt_xy[::10], k=1)
        rr = mh['TVT'].values + mh['Z'].values
        ok = np.isfinite(rr)
        mate_info.append((float(np.median(d)), mh['X'].values[ok][::4], mh['Y'].values[ok][::4], rr[ok][::4]))
    if mate_info:
        _seps = sorted(mi[0] for mi in mate_info)
        SEPSTATS.append((wid, _seps[0], _seps[len(_seps)//2], len(_seps)))
    for ms in MINSEPS:
        px, py, pr = [], [], []
        used = 0
        for sep, mx, my, mr in mate_info:
            if sep < ms: continue     # duplicate/near-twin guard
            px.append(mx); py.append(my); pr.append(mr); used += 1
        if used == 0:
            res[ms].append(None); continue
        PX = np.concatenate(px); PY = np.concatenate(py); PR = np.concatenate(pr)
        tree = cKDTree(np.column_stack([PX, PY]))
        dd, ii2 = tree.query(tgt_xy, k=min(K, len(PR)))
        if dd.ndim == 1: dd = dd[:, None]; ii2 = ii2[:, None]
        wgt = 1.0 / (dd + 1.0)
        r_pred = (wgt * PR[ii2]).sum(1) / wgt.sum(1)
        anchor = float(np.nanmean(r_true_anchor - r_pred[kn_idx]))
        pred_full = r_pred + anchor - Z
        Sv = pred_full[ki]
        res[ms].append((wid, Dv, Pv, Sv, Yv, used))
    meta.append(wid)

print(f'\nwells scored={len(meta)}')
if SEPSTATS:
    mins=np.array([s0 for _,s0,_,_ in SEPSTATS]); meds=np.array([m for _,_,m,_ in SEPSTATS])
    print(f"MATE SEPARATION (median trajectory distance to each group-mate):")
    print(f"  closest mate per target: min={mins.min():.0f} p05={np.percentile(mins,5):.0f} median={np.median(mins):.0f} max={mins.max():.0f} ft")
    print(f"  targets with a mate <150ft: {int((mins<150).sum())}/{len(mins)}   <300ft: {int((mins<300).sum())}   <500ft: {int((mins<500).sum())}")
    print(f"  median-mate distance: median={np.median(meds):.0f} ft", flush=True)
def pooled(vals, f):
    D_ = np.concatenate([v[1] for v in vals]); P_ = np.concatenate([v[2] for v in vals])
    S_ = np.concatenate([v[3] for v in vals]); Y_ = np.concatenate([v[4] for v in vals])
    return f(D_, P_, S_, Y_)
rmse = lambda a, y: float(np.sqrt(np.mean((a - y) ** 2)))

for ms in MINSEPS:
    vals = [v for v in res[ms] if v is not None]
    if not vals: print(f'min_sep={ms}: no wells with surviving neighbours'); continue
    D_ = np.concatenate([v[1] for v in vals]); P_ = np.concatenate([v[2] for v in vals])
    S_ = np.concatenate([v[3] for v in vals]); Y_ = np.concatenate([v[4] for v in vals])
    W_ = np.concatenate([np.full(len(v[1]), v[0]) for v in vals])
    nb = np.mean([v[5] for v in vals])
    base = 0.5 * D_ + 0.5 * P_
    print(f"\n=== min_sep={ms:.0f} ft | wells={len(vals)} rows={len(Y_)} mean_neighbours={nb:.1f} ===")
    print(f"  struct RMSE={rmse(S_,Y_):.3f}  DWT={rmse(D_,Y_):.3f}  PF={rmse(P_,Y_):.3f}  blend0.5={rmse(base,Y_):.3f}")
    eS, eD, eP = S_ - Y_, D_ - Y_, P_ - Y_
    print(f"  corr(struct,DWT)={np.corrcoef(eS,eD)[0,1]:+.3f}  corr(struct,PF)={np.corrcoef(eS,eP)[0,1]:+.3f}")
    # in-sample weight sweep (diagnostic)
    sw = {w: rmse((1 - w) * base + w * S_, Y_) for w in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]}
    print("  in-sample w sweep:", {k: round(v, 3) for k, v in sw.items()})
    # NESTED weight by well split (5 seeds)
    uw = np.array(sorted(set(W_))); gains = []
    for seed in range(5):
        rng = np.random.RandomState(seed); sh = uw.copy(); rng.shuffle(sh)
        g0 = set(sh[:len(sh) // 2]); m0 = np.array([w in g0 for w in W_]); m1 = ~m0
        def fitw(m):
            d = S_[m] - base[m]; r = Y_[m] - base[m]
            return float(np.clip(np.dot(d, r) / max(np.dot(d, d), 1e-9), 0, 1))
        pred = np.empty(len(Y_))
        w0, w1 = fitw(m0), fitw(m1)
        pred[m1] = base[m1] + w0 * (S_[m1] - base[m1]); pred[m0] = base[m0] + w1 * (S_[m0] - base[m0])
        gains.append((rmse(base, Y_), rmse(pred, Y_), w0, w1))
    G = np.array([[g[0], g[1]] for g in gains])
    print(f"  NESTED: blend0.5={G[:,0].mean():.4f} -> +struct={G[:,1].mean():.4f}  gain={G[:,0].mean()-G[:,1].mean():+.4f}"
          f"  (fitted w per fold: {[round(g[2],3) for g in gains]})")
print("\nGATE: if the nested gain collapses from min_sep=0 to min_sep>=150, the signal was duplicate-driven.")
