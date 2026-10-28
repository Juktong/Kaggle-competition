"""Mainline C: structural-field variant sweep, computed in ONE pass over wells.
Variants: k in {8,12,20} x IDW power {1,2} x anchor rows {50,100,200}. The k=20 neighbour query subsumes
k=8/12, and anchor/power variants are cheap re-weightings, so all 18 combos cost ~one full run.
Evaluated with the DEPLOYED gate (nnb>=4 & closest<1000ft) at the deployed weight W=0.15 and nested."""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MIN_SEP = float(os.environ.get('MIN_SEP', '150')); KS = [8, 12, 20]; POWS = [1.0, 2.0]; ANCHORS = [50, 100, 200]
MAXW = int(os.environ.get('MAXW', '10000'))

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dwv = cs['well'][tM].astype(str); dov = cs['oof'][tM].astype(np.float64); dyv = cs['yt'][tM].astype(np.float64); drv = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(dwv, drv, dov, dyv): dwt[w][r] = (o, y)
pf = np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz', allow_pickle=True)
pw = pf['well'].astype(str); pp = pf['pred'].astype(np.float64)
pf_by = {w: pp[pw == w] for w in np.unique(pw)}

gkey = {}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid = os.path.basename(f).split('__')[0]
    try: gkey[wid] = round(float(np.nanmax(pd.read_csv(f, usecols=['TVT'])['TVT'].values)), 1)
    except Exception: pass
groups = defaultdict(list)
for w, k in gkey.items(): groups[k].append(w)

cache = {}
def get(w):
    if w not in cache: cache[w] = pd.read_csv(f'{D}/{w}__horizontal_well.csv', usecols=['X', 'Y', 'Z', 'TVT', 'TVT_input'])
    return cache[w]
_t = {}
def tree_of(w):
    if w not in _t:
        h = get(w); _t[w] = cKDTree(np.column_stack([h['X'].values, h['Y'].values]))
    return _t[w]

keys = [(k, p, a) for k in KS for p in POWS for a in ANCHORS]
acc = {kk: {'S': [], 'D': [], 'P': [], 'Y': [], 'W': [], 'NB': [], 'CL': []} for kk in keys}
targets = sorted(set(pw) & set(dwt))[:MAXW]
for n, wid in enumerate(targets):
    if n % 50 == 0: print(f'  [{n}/{len(targets)}]', flush=True)
    if wid not in gkey: continue
    try: hw = get(wid)
    except Exception: continue
    kn = hw['TVT_input'].notna().values
    if kn.sum() < max(ANCHORS): continue
    tidx = np.where(~kn)[0]
    prf = pf_by.get(wid)
    if prf is None or len(prf) != len(tidx): continue
    keep = [(j, i) for j, i in enumerate(tidx) if i in dwt[wid]]
    if len(keep) < 10: continue
    kj = np.array([j for j, _ in keep]); ki = np.array([i for _, i in keep])
    Dv = np.array([dwt[wid][i][0] for i in ki]); Yv = np.array([dwt[wid][i][1] for i in ki]); Pv = prf[kj]
    X = hw['X'].values; Y = hw['Y'].values; Z = hw['Z'].values; txy = np.column_stack([X, Y])
    px, py, pr, seps = [], [], [], []
    for m in groups.get(gkey[wid], []):
        if m == wid: continue
        try: mh = get(m)
        except Exception: continue
        if len(mh) < 5: continue
        d, _ = tree_of(m).query(txy[::10], k=1); sep = float(np.median(d)); seps.append(sep)
        if sep < MIN_SEP: continue
        rr = mh['TVT'].values + mh['Z'].values; ok = np.isfinite(rr)
        px.append(mh['X'].values[ok][::4]); py.append(mh['Y'].values[ok][::4]); pr.append(rr[ok][::4])
    if not px: continue
    nnb = len(px); closest = float(min(seps)) if seps else np.nan
    PX = np.concatenate(px); PY = np.concatenate(py); PR = np.concatenate(pr)
    kmax = min(max(KS), len(PR))
    dd, ii = cKDTree(np.column_stack([PX, PY])).query(txy, k=kmax)
    if dd.ndim == 1: dd = dd[:, None]; ii = ii[:, None]
    for k in KS:
        kk = min(k, kmax); dsub = dd[:, :kk]; isub = ii[:, :kk]
        for p in POWS:
            wg = 1.0 / (dsub + 1.0) ** p
            r_pred = (wg * PR[isub]).sum(1) / wg.sum(1)
            for a in ANCHORS:
                kidx = np.where(kn)[0][-a:]
                anc = float(np.nanmean(hw['TVT_input'].values[kidx] + Z[kidx] - r_pred[kidx]))
                S = (r_pred + anc - Z)[ki]
                t = acc[(k, p, a)]
                t['S'].append(S); t['D'].append(Dv); t['P'].append(Pv); t['Y'].append(Yv)
                t['W'].append(np.full(len(S), wid)); t['NB'].append(np.full(len(S), nnb)); t['CL'].append(np.full(len(S), closest))

print(f"\n{'k':>3} {'pow':>4} {'anch':>5} | {'gated RMSE@0.15':>15} {'nested':>8} {'gain':>7} {'rows%':>6}")
best = None
for kk in keys:
    t = acc[kk]
    if not t['S']: continue
    S = np.concatenate(t['S']); Dv = np.concatenate(t['D']); Pv = np.concatenate(t['P']); Yv = np.concatenate(t['Y'])
    Wv = np.concatenate(t['W']); NB = np.concatenate(t['NB']); CL = np.concatenate(t['CL'])
    base = 0.5 * Dv + 0.5 * Pv
    G = (NB >= 4) & (CL < 1000) & np.isfinite(CL)
    p15 = base.copy(); p15[G] = 0.85 * base[G] + 0.15 * S[G]
    r15 = float(np.sqrt(np.mean((p15 - Yv) ** 2)))
    uw = np.array(sorted(set(Wv))); outs = []
    for seed in range(3):
        rng = np.random.RandomState(seed); sh = uw.copy(); rng.shuffle(sh)
        g0 = set(sh[:len(sh) // 2]); inA = np.array([w in g0 for w in Wv])
        def fitw(m):
            m = m & G
            if m.sum() < 200: return 0.0
            d = S[m] - base[m]; r = Yv[m] - base[m]
            return float(np.clip(np.dot(d, r) / max(np.dot(d, d), 1e-9), 0, 1))
        pred = base.copy(); w0 = fitw(inA); w1 = fitw(~inA)
        ap = (~inA) & G; pred[ap] = base[ap] + w0 * (S[ap] - base[ap])
        ap = inA & G; pred[ap] = base[ap] + w1 * (S[ap] - base[ap])
        outs.append(float(np.sqrt(np.mean((pred - Yv) ** 2))))
    nst = float(np.mean(outs)); bl = float(np.sqrt(np.mean((base - Yv) ** 2)))
    print(f"{kk[0]:>3} {kk[1]:>4.0f} {kk[2]:>5} | {r15:>15.4f} {nst:>8.4f} {bl-nst:>+7.4f} {100*G.mean():>5.1f}%")
    if best is None or nst < best[1]: best = (kk, nst)
print(f"\nbest variant: k={best[0][0]} power={best[0][1]:.0f} anchor={best[0][2]} -> nested {best[1]:.4f}")
print("(deployed config is k=12 power=1 anchor=100; a variant must beat it materially to justify a change)")
