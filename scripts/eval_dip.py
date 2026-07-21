"""Probe 3 evaluation: does the group local DIP PLANE add over / replace the isotropic IDW structural field?

Compares, all nested by well on the deployed pipeline (base = 0.5*DWT + 0.5*PF, gated rows only):
  A) deployed: base + W*(struct_IDW - base)
  B) dip only: base + W*(dip - base)
  C) both:     base + a*(struct - base) + b*(dip - base)     [2-coefficient nested fit]
"""
import os, numpy as np, pandas as pd
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
st = np.load(os.path.join(SH, 'struct_oof.npz'), allow_pickle=True)
sw = st['well'].astype(str); sr = st['ridx'].astype(int); ss = st['struct'].astype(np.float64)
nnb = dict(zip(st['meta_well'].astype(str), st['meta_nnb'].astype(int)))
cl = dict(zip(st['meta_well'].astype(str), st['meta_closest'].astype(float)))
dp = np.load(os.path.join(SH, 'dip_oof.npz'), allow_pickle=True)
dw2 = dp['well'].astype(str); dr2 = dp['ridx'].astype(int); dv = dp['dip'].astype(np.float64)

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
cw = cs['well'][tM].astype(str); co = cs['oof'][tM].astype(np.float64); cy = cs['yt'][tM].astype(np.float64); cr = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(cw, cr, co, cy): dwt[w][r] = (o, y)
del cs
pf = np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz', allow_pickle=True)
pw = pf['well'].astype(str); pp = pf['pred'].astype(np.float64)
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
pf_map = {}
for wid in np.unique(pw):
    try: hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['TVT_input'])
    except Exception: continue
    ti = np.where(hw['TVT_input'].isna().values)[0]; v = pp[pw == wid]
    if len(v) == len(ti): pf_map[wid] = dict(zip(ti.tolist(), v.tolist()))

sidx = defaultdict(dict); didx = defaultdict(dict)
for w, r, s in zip(sw, sr, ss): sidx[w][int(r)] = s
for w, r, s in zip(dw2, dr2, dv): didx[w][int(r)] = s

Ds, Ps, Ss, Vs, Ys, Ws = [], [], [], [], [], []
for w in sorted(set(sidx) & set(didx)):
    if w not in dwt or w not in pf_map: continue
    for r, s in sidx[w].items():
        if r in dwt[w] and r in pf_map[w] and r in didx[w]:
            o, y = dwt[w][r]
            Ds.append(o); Ps.append(pf_map[w][r]); Ss.append(s); Vs.append(didx[w][r]); Ys.append(y); Ws.append(w)
D_ = np.array(Ds); P_ = np.array(Ps); S_ = np.array(Ss); V_ = np.array(Vs); Y_ = np.array(Ys); W_ = np.array(Ws)
base = 0.5 * D_ + 0.5 * P_
rmse = lambda a: float(np.sqrt(np.mean((a - Y_) ** 2)))
gate = np.array([(nnb.get(w, 0) >= 4) and np.isfinite(cl.get(w, np.nan)) and cl.get(w, 1e9) < 1000 for w in W_])
uw = np.array(sorted(set(W_)))
print(f"rows={len(Y_)} wells={len(uw)} gated={100*gate.mean():.1f}%  base={rmse(base):.4f}", flush=True)
print(f"  standalone: struct_IDW={rmse(S_):.3f}  dip_plane={rmse(V_):.3f}", flush=True)
eS = S_ - Y_; eV = V_ - Y_; eB = base - Y_
print(f"  corr(dip,struct)={np.corrcoef(eV,eS)[0,1]:+.3f}  corr(dip,base)={np.corrcoef(eV,eB)[0,1]:+.3f}  corr(struct,base)={np.corrcoef(eS,eB)[0,1]:+.3f}", flush=True)
dep = base.copy(); dep[gate] = 0.85 * base[gate] + 0.15 * S_[gate]
print(f"  A) deployed struct-only flat W=0.15 = {rmse(dep):.4f}", flush=True)

def nested(cols, label):
    outs = []
    for seed in range(3):
        rg = np.random.RandomState(seed); sh = uw.copy(); rg.shuffle(sh)
        g0 = set(sh[:len(sh) // 2]); inA = np.array([w in g0 for w in W_])
        pred = base.copy()
        for tr, te in [(inA, ~inA), (~inA, inA)]:
            m = tr & gate
            if m.sum() < 500: continue
            X = np.column_stack([c[m] - base[m] for c in cols]); r = (Y_ - base)[m]
            try: a, _, _, _ = np.linalg.lstsq(X, r, rcond=None)
            except Exception: a = np.zeros(len(cols))
            a = np.clip(a, 0, 1)
            ap = te & gate
            pred[ap] = base[ap] + sum(a[i] * (cols[i][ap] - base[ap]) for i in range(len(cols)))
        outs.append(rmse(pred))
    print(f"     {label:46s} {np.mean(outs):.4f}", flush=True)
    return float(np.mean(outs))

print("  nested (non-negative coefficients, fit on half the wells, applied to the other half):", flush=True)
a1 = nested([S_], 'A) struct_IDW only')
a2 = nested([V_], 'B) dip_plane only')
a3 = nested([S_, V_], 'C) struct + dip (2 coefficients)')
print(f"\n  dip adds vs struct-only: {a1-a3:+.4f}")
print("=> the dip plane must add materially over struct-only to justify a second field in inference.")
