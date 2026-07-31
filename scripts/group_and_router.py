"""Directions 3 + 4 on the deployed honest slot 54844628 (OOF 8.8626).

D3 group-level correction (group identity was NOT used by the row-level residual model):
   a) per-typewell-group residual OFFSET (constant), nested
   b) per-group linear TREND in row_frac, nested
   c) per-group shrunk offset (James-Stein style shrinkage toward 0 by group size)
D4 multi-signal conservative ROUTER: choose per well/row among {base(DWT+PF), struct-blend, DWT-only}
   using several signals jointly (never a single previously-refuted variable), nested by well.

All fits nested GroupKFold by well; only test-available signals; tw_pressure excluded.
"""
import os, numpy as np, pandas as pd, glob
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
_z = np.load(os.path.join(SH, 'decomp_features.npz'), allow_pickle=True)
dc = {k: _z[k] for k in _z.files}
dw = dc['well'].astype(str)
rd = np.load(os.path.join(SH, 'struct_oof_rowdist.npz'), allow_pickle=True)
rw = rd['well'].astype(str); rs = rd['struct'].astype(np.float64); nn = rd['nn_dist'].astype(np.float64)
nnb = dict(zip(rd['meta_well'].astype(str), rd['meta_nnb'].astype(int)))
cl = dict(zip(rd['meta_well'].astype(str), rd['meta_closest'].astype(float)))
uz = np.load(os.path.join(SH, 'pf_unc.npz'), allow_pickle=True)
uw = uz['well'].astype(str); uu = uz['unc'].astype(np.float64)

gkey = {}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid = os.path.basename(f).split('__')[0]
    try: gkey[wid] = round(float(np.nanmax(pd.read_csv(f, usecols=['TVT'])['TVT'].values)), 1)
    except Exception: pass

di = defaultdict(list); si = defaultdict(list); ui = defaultdict(list)
for i, w in enumerate(dw): di[w].append(i)
for i, w in enumerate(rw): si[w].append(i)
for i, w in enumerate(uw): ui[w].append(i)

B, S, T, W, G, RF, NND, UNC, DWTv, PFv = [], [], [], [], [], [], [], [], [], []
for w in sorted(set(dw) & set(rw) & set(uw)):
    a = np.array(di[w]); b = np.array(si[w]); c = np.array(ui[w])
    if not (len(a) == len(b) == len(c)): continue
    B.append(dc['blend'][a].astype(np.float64)); T.append(dc['truth'][a].astype(np.float64))
    DWTv.append(dc['dwt'][a].astype(np.float64)); PFv.append(dc['pf'][a].astype(np.float64))
    RF.append(dc['row_frac'][a].astype(np.float64))
    S.append(rs[b]); NND.append(nn[b]); UNC.append(uu[c])
    W.append(np.full(len(a), w)); G.append(np.full(len(a), gkey.get(w, -1.0)))
base = np.concatenate(B); struct = np.concatenate(S); truth = np.concatenate(T)
well = np.concatenate(W); grp = np.concatenate(G); rf = np.concatenate(RF)
nnd = np.concatenate(NND); unc = np.concatenate(UNC); dwtv = np.concatenate(DWTv); pfv = np.concatenate(PFv)
nnbv = np.array([nnb.get(w, 0) for w in well], float); clov = np.array([cl.get(w, np.nan) for w in well], float)

gate = (nnbv >= 4) & (clov < 1000) & np.isfinite(clov)
cur = base.copy(); cur[gate] = 0.85 * base[gate] + 0.15 * struct[gate]
rmse = lambda a: float(np.sqrt(np.mean((a - truth) ** 2)))
resid = truth - cur
uwell = np.array(sorted(set(well)))
print(f"rows={len(truth)} wells={len(uwell)} groups={len(set(grp))}  deployed={rmse(cur):.4f}", flush=True)

def halves(seed):
    rg = np.random.RandomState(seed); sh = uwell.copy(); rg.shuffle(sh)
    g0 = set(sh[:len(sh)//2]); inA = np.array([w in g0 for w in well])
    return inA, ~inA

# ---------------- D3: group-level corrections ----------------
print("\n=== D3 group-level corrections (nested by well, 3 seeds) ===", flush=True)
def d3(kind, shrink_n=0.0):
    outs = []
    for seed in range(3):
        A, Bm = halves(seed)
        p = cur.copy()
        for tr, te in [(A, Bm), (Bm, A)]:
            for g in np.unique(grp):
                mtr = tr & (grp == g); mte = te & (grp == g)
                if mte.sum() == 0: continue
                if mtr.sum() < 200: continue
                if kind == 'offset':
                    n = mtr.sum(); off = resid[mtr].mean()
                    if shrink_n > 0: off *= n / (n + shrink_n)      # shrink small groups toward 0
                    p[mte] = cur[mte] + off
                else:  # linear trend in row_frac
                    Xtr = np.column_stack([np.ones(mtr.sum()), rf[mtr]])
                    try: co, _, _, _ = np.linalg.lstsq(Xtr, resid[mtr], rcond=None)
                    except Exception: continue
                    p[mte] = cur[mte] + co[0] + co[1] * rf[mte]
        outs.append(rmse(p))
    r = float(np.mean(outs))
    print(f"  {kind:26s} shrink_n={shrink_n:<7.0f} -> {r:.4f}   gain {rmse(cur)-r:+.4f}", flush=True)
    return r
d3('offset', 0)
d3('offset', 5000)
d3('offset', 50000)
d3('trend_rowfrac', 0)

# ---------------- D4: multi-signal conservative router ----------------
print("\n=== D4 multi-signal router (nested by well, 3 seeds) ===", flush=True)
alt_dwt = dwtv                       # fall back to DWT only
alt_base = base                      # drop the structural term
cands = {'cur': cur, 'base_noStruct': alt_base, 'dwt_only': alt_dwt}
for nm, v in cands.items():
    print(f"  candidate {nm:14s} standalone = {rmse(v):.4f}", flush=True)

FEATS = np.column_stack([nnd, nnbv, np.nan_to_num(clov, nan=1e4), unc, rf,
                         np.abs(dwtv - pfv), np.abs(struct - base)])
try:
    from sklearn.ensemble import HistGradientBoostingClassifier
    HAVE = True
except Exception:
    HAVE = False
print(f"  classifier available: {HAVE}", flush=True)
if HAVE:
    err = np.column_stack([np.abs(v - truth) for v in cands.values()])
    best_idx = np.argmin(err, 1)
    print(f"  oracle route mix: " + ", ".join(f"{n}={100*np.mean(best_idx==i):.0f}%" for i, n in enumerate(cands)), flush=True)
    oracle = np.choose(best_idx, [v for v in cands.values()])
    print(f"  ORACLE router (upper bound)  = {rmse(oracle):.4f}", flush=True)
    outs = []
    for seed in range(3):
        A, Bm = halves(seed)
        p = cur.copy()
        for tr, te in [(A, Bm), (Bm, A)]:
            idx = np.where(tr)[0][::4]
            try:
                clf = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.08, max_depth=6,
                                                     min_samples_leaf=200).fit(FEATS[idx], best_idx[idx])
                pr = clf.predict(FEATS[te])
                stacked = np.column_stack([v[te] for v in cands.values()])
                p[te] = stacked[np.arange(te.sum()), pr]
            except Exception as e:
                print('   router fold failed:', str(e)[:60], flush=True)
        outs.append(rmse(p))
    r = float(np.mean(outs))
    print(f"  NESTED multi-signal router   = {r:.4f}   gain {rmse(cur)-r:+.4f}", flush=True)
print("\nGATE for both: >= +0.10 vs deployed with stably positive bootstrap.", flush=True)
