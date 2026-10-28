"""Probe 2 evaluation: does a per-ROW nearest-neighbour distance gate/weight beat the deployed per-WELL gate?

Deployed: gate = (well nnb>=4) AND (well closest<1000ft), then W=0.15 flat on gated rows.
Tested here (all nested by well, 3 seeds):
  A) deployed per-well gate + flat W                (reference)
  B) per-ROW distance gate: apply only where nn_dist < T, flat W
  C) per-ROW distance-decayed weight: W * f(nn_dist)
"""
import os, numpy as np
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
rd = np.load(os.path.join(SH, 'struct_oof_rowdist.npz'), allow_pickle=True)
rw = rd['well'].astype(str); rr = rd['ridx'].astype(int); rs = rd['struct'].astype(np.float64); nn = rd['nn_dist'].astype(np.float64)
nnb = dict(zip(rd['meta_well'].astype(str), rd['meta_nnb'].astype(int)))
cl = dict(zip(rd['meta_well'].astype(str), rd['meta_closest'].astype(float)))

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dw = cs['well'][tM].astype(str); do = cs['oof'][tM].astype(np.float64); dy = cs['yt'][tM].astype(np.float64); dr = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(dw, dr, do, dy): dwt[w][r] = (o, y)
del cs
import pandas as pd
pf = np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz', allow_pickle=True)
pw = pf['well'].astype(str); pp = pf['pred'].astype(np.float64)
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
pf_map = {}
for wid in np.unique(pw):
    try: hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['TVT_input'])
    except Exception: continue
    ti = np.where(hw['TVT_input'].isna().values)[0]; v = pp[pw == wid]
    if len(v) == len(ti): pf_map[wid] = dict(zip(ti.tolist(), v.tolist()))

byw = defaultdict(list)
for i, w in enumerate(rw): byw[w].append(i)
Ds, Ps, Ss, Ys, Ws, NN = [], [], [], [], [], []
for w, idxs in byw.items():
    if w not in dwt or w not in pf_map: continue
    for i in idxs:
        r = int(rr[i])
        if r in dwt[w] and r in pf_map[w]:
            o, y = dwt[w][r]
            Ds.append(o); Ps.append(pf_map[w][r]); Ss.append(rs[i]); Ys.append(y); Ws.append(w); NN.append(nn[i])
D_ = np.array(Ds); P_ = np.array(Ps); S_ = np.array(Ss); Y_ = np.array(Ys); W_ = np.array(Ws); NN = np.array(NN)
base = 0.5 * D_ + 0.5 * P_
rmse = lambda a: float(np.sqrt(np.mean((a - Y_) ** 2)))
wellgate = np.array([(nnb.get(w, 0) >= 4) and np.isfinite(cl.get(w, np.nan)) and cl.get(w, 1e9) < 1000 for w in W_])
uw = np.array(sorted(set(W_)))
print(f"rows={len(Y_)} wells={len(uw)}  base={rmse(base):.4f}  well-gated={100*wellgate.mean():.1f}%", flush=True)
print(f"per-row nn_dist: median={np.median(NN):.0f} p10={np.percentile(NN,10):.0f} p90={np.percentile(NN,90):.0f} ft", flush=True)
dep = base.copy(); dep[wellgate] = 0.85 * base[wellgate] + 0.15 * S_[wellgate]
print(f"  A) deployed per-well gate, flat W=0.15   = {rmse(dep):.4f}", flush=True)

def nested(mask, wvec, label):
    outs = []
    for seed in range(3):
        rg = np.random.RandomState(seed); sh = uw.copy(); rg.shuffle(sh)
        g0 = set(sh[:len(sh) // 2]); inA = np.array([w in g0 for w in W_])
        pred = base.copy()
        for tr, te in [(inA, ~inA), (~inA, inA)]:
            m = tr & mask
            if m.sum() < 500: continue
            d = (S_ - base) * wvec
            a = float(np.clip(np.dot(d[m], (Y_ - base)[m]) / max(np.dot(d[m], d[m]), 1e-9), 0, 3))
            ap = te & mask; pred[ap] = base[ap] + a * wvec[ap] * (S_[ap] - base[ap])
        outs.append(rmse(pred))
    print(f"     {label:52s} {np.mean(outs):.4f}", flush=True)
    return float(np.mean(outs))

print("  nested comparisons (scalar refit on each scheme):", flush=True)
ref = nested(wellgate, np.full(len(Y_), 0.15), 'A) per-well gate + flat (nested refit)')
for T in [400, 600, 800, 1200]:
    nested(wellgate & (NN < T), np.full(len(Y_), 0.15), f'B) per-ROW gate nn_dist<{T}ft (+ well gate)')
for tag, f in [('1/(1+nn/500)', 1.0 / (1.0 + NN / 500.0)), ('1/(1+nn/1000)', 1.0 / (1.0 + NN / 1000.0)),
               ('exp(-nn/800)', np.exp(-NN / 800.0))]:
    nested(wellgate, 0.15 * f / max(np.mean(f), 1e-9), f'C) per-ROW decayed weight {tag}')
print("\n=> a per-row scheme must beat A) materially to justify replacing the per-well gate.")
