"""Direction 2: residual correction on top of the deployed honest slot 54844628.

Target: truth - current_best_pred, where current_best_pred is EXACTLY the deployed pipeline
    base = 0.5*DWT + 0.5*PF ; out = base, with (1-0.15)*base + 0.15*struct on gated rows
    gate = (well nnb>=4) AND (well closest<1000ft)

Features are TEST-AVAILABLE ONLY. Explicitly EXCLUDED: tw_pressure (truth-derived, diagnostic only).
Included: row_frac, toe_dist_md, gr_rough, curvature, gbm_disagree, heel_drift, n_eval, gr_missing,
tw_range, z_span, per-row nn_dist, well nnb / closest, PF uncertainty (unc, likdisp), and model-disagreement
signals (struct-base, dwt-pf, |dwt-pf|).

All fitting is nested GroupKFold by well; the applied correction is additionally shrunk by a nested scalar.
Env: FOLDS, SUB (row subsample stride for training), MODEL.
"""
import os, numpy as np, pandas as pd
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
FOLDS = int(os.environ.get('FOLDS', '5')); SUB = int(os.environ.get('SUB', '4'))
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'

_dcz = np.load(os.path.join(SH, 'decomp_features.npz'), allow_pickle=True)
dc = {k: _dcz[k] for k in _dcz.files}          # materialize ONCE
dw = dc['well'].astype(str)
rd = np.load(os.path.join(SH, 'struct_oof_rowdist.npz'), allow_pickle=True)
rw = rd['well'].astype(str); rr = rd['ridx'].astype(int); rs = rd['struct'].astype(np.float64); nn = rd['nn_dist'].astype(np.float64)
nnb = dict(zip(rd['meta_well'].astype(str), rd['meta_nnb'].astype(int)))
cl = dict(zip(rd['meta_well'].astype(str), rd['meta_closest'].astype(float)))
uz = np.load(os.path.join(SH, 'pf_unc.npz'), allow_pickle=True)
uw = uz['well'].astype(str); uu = uz['unc'].astype(np.float64); ul = uz['likdisp'].astype(np.float64)

# decomp rows are per-well in toe order; rowdist carries explicit ridx in the same order; pf_unc likewise
di = defaultdict(list); si = defaultdict(list); ui = defaultdict(list)
for i, w in enumerate(dw): di[w].append(i)
for i, w in enumerate(rw): si[w].append(i)
for i, w in enumerate(uw): ui[w].append(i)

FEATS = ['row_frac', 'toe_dist_md', 'gr_rough', 'curvature', 'gbm_disagree', 'heel_drift',
         'n_eval', 'gr_missing', 'tw_range', 'z_span']
cols = {c: [] for c in FEATS}
BASE, STRUCT, TRUTH, WELL, NND, NNB, CLO, UNC, LIK, DWTv, PFv = [], [], [], [], [], [], [], [], [], [], []
for w in sorted(set(dw) & set(rw) & set(uw)):
    a = np.array(di[w]); b = np.array(si[w]); c = np.array(ui[w])
    if not (len(a) == len(b) == len(c)): continue
    for f in FEATS: cols[f].append(dc[f][a].astype(np.float64))
    BASE.append(dc['blend'][a].astype(np.float64)); TRUTH.append(dc['truth'][a].astype(np.float64))
    DWTv.append(dc['dwt'][a].astype(np.float64)); PFv.append(dc['pf'][a].astype(np.float64))
    STRUCT.append(rs[b]); NND.append(nn[b]); UNC.append(uu[c]); LIK.append(ul[c])
    NNB.append(np.full(len(a), nnb.get(w, 0), float)); CLO.append(np.full(len(a), cl.get(w, np.nan), float))
    WELL.append(np.full(len(a), w))
X = {f: np.concatenate(v) for f, v in cols.items()}
base = np.concatenate(BASE); struct = np.concatenate(STRUCT); truth = np.concatenate(TRUTH)
well = np.concatenate(WELL); nnd = np.concatenate(NND); nnbv = np.concatenate(NNB); clov = np.concatenate(CLO)
unc = np.concatenate(UNC); lik = np.concatenate(LIK); dwtv = np.concatenate(DWTv); pfv = np.concatenate(PFv)

gate = (nnbv >= 4) & (clov < 1000) & np.isfinite(clov)
cur = base.copy(); cur[gate] = 0.85 * base[gate] + 0.15 * struct[gate]
resid = truth - cur
rmse = lambda a: float(np.sqrt(np.mean((a - truth) ** 2)))
print(f"rows={len(truth)} wells={len(set(well))} gated={100*gate.mean():.1f}%", flush=True)
print(f"  deployed 54844628 pipeline OOF = {rmse(cur):.4f}   (reference 8.8626)", flush=True)
print(f"  residual: mean={resid.mean():+.3f} std={resid.std():.3f}", flush=True)

M = np.column_stack([X[f] for f in FEATS] + [nnd, nnbv, clov, unc, lik,
                                             struct - base, dwtv - pfv, np.abs(dwtv - pfv)])
NAMES = FEATS + ['nn_dist', 'nnb', 'closest', 'pf_unc', 'lik_disp', 'struct_minus_base', 'dwt_minus_pf', 'abs_dwt_pf']
M = np.nan_to_num(M, nan=0.0, posinf=0.0, neginf=0.0)
print(f"  feature matrix: {M.shape} ({len(NAMES)} features, tw_pressure EXCLUDED as truth-derived)", flush=True)

uwell = np.array(sorted(set(well))); rng = np.random.RandomState(0)
fold_of = {w: i % FOLDS for i, w in enumerate(rng.permutation(uwell))}
foldv = np.array([fold_of[w] for w in well])

from sklearn.linear_model import Ridge, HuberRegressor
try:
    from sklearn.ensemble import HistGradientBoostingRegressor; HAVE_H = True
except Exception: HAVE_H = False

def run(name):
    pred_res = np.zeros(len(truth))
    for f in range(FOLDS):
        tr = (foldv != f); te = (foldv == f)
        idx = np.where(tr)[0][::SUB]
        Xtr, ytr = M[idx], resid[idx]
        if name == 'ridge':
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
            m = Ridge(alpha=10.0).fit((Xtr - mu) / sd, ytr)
            pred_res[te] = m.predict((M[te] - mu) / sd)
        elif name == 'huber':
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
            m = HuberRegressor(alpha=1e-3, max_iter=200).fit((Xtr - mu) / sd, ytr)
            pred_res[te] = m.predict((M[te] - mu) / sd)
        else:
            m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.06, max_depth=6,
                                              min_samples_leaf=200, l2_regularization=1.0).fit(Xtr, ytr)
            pred_res[te] = m.predict(M[te])
    print(f"\n  [{name}] corr(pred_resid, resid) = {np.corrcoef(pred_res, resid)[0,1]:+.4f}", flush=True)
    for lam in [0.25, 0.5, 0.75, 1.0]:
        print(f"      lam={lam:.2f}: {rmse(cur + lam*pred_res):.4f}  gain {rmse(cur)-rmse(cur+lam*pred_res):+.4f}", flush=True)
    # nested shrinkage scalar
    outs = []
    for seed in range(3):
        rg = np.random.RandomState(seed); sh = uwell.copy(); rg.shuffle(sh)
        g0 = set(sh[:len(sh)//2]); inA = np.array([w in g0 for w in well])
        p = cur.copy()
        for tr, te in [(inA, ~inA), (~inA, inA)]:
            d = pred_res[tr]; r = resid[tr]
            a = float(np.clip(np.dot(d, r) / max(np.dot(d, d), 1e-9), 0, 2))
            p[te] = cur[te] + a * pred_res[te]
        outs.append(rmse(p))
    nested = float(np.mean(outs))
    print(f"      NESTED shrinkage        : {nested:.4f}  gain {rmse(cur)-nested:+.4f}", flush=True)
    return nested, pred_res

best = None
for nm in (['ridge', 'huber'] + (['hgb'] if HAVE_H else [])):
    try:
        r, pr = run(nm)
        if best is None or r < best[0]: best = (r, nm, pr)
    except Exception as e:
        print(f"  [{nm}] failed: {str(e)[:70]}", flush=True)

if best:
    r, nm, pr = best
    print(f"\n  BEST: {nm} -> {r:.4f} (gain {rmse(cur)-r:+.4f} vs deployed {rmse(cur):.4f})", flush=True)
    # bootstrap over wells at the nested-best
    outs = []
    rg = np.random.RandomState(7); sh = uwell.copy(); rg.shuffle(sh)
    g0 = set(sh[:len(sh)//2]); inA = np.array([w in g0 for w in well])
    p = cur.copy()
    for tr, te in [(inA, ~inA), (~inA, inA)]:
        d = pr[tr]; rr2 = resid[tr]
        a = float(np.clip(np.dot(d, rr2) / max(np.dot(d, d), 1e-9), 0, 2))
        p[te] = cur[te] + a * pr[te]
    idxw = {w: np.where(well == w)[0] for w in uwell}
    gains = []
    for _ in range(200):
        samp = uwell[rg.randint(0, len(uwell), len(uwell))]
        rows = np.concatenate([idxw[w] for w in samp])
        gains.append(np.sqrt(np.mean((cur[rows]-truth[rows])**2)) - np.sqrt(np.mean((p[rows]-truth[rows])**2)))
    g = np.array(gains)
    print(f"  bootstrap(200 wells): mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} frac>0={100*np.mean(g>0):.0f}%", flush=True)
    print(f"\n  GATE (>= +0.10 with stably positive bootstrap): {'MEETS' if (rmse(cur)-r)>=0.10 and np.percentile(g,5)>0 else 'DOES NOT MEET'}")
