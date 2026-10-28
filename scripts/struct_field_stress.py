"""A2: stress scenarios for the group-anchored structural field candidate.
Uses the saved struct OOF (no re-run). Scenarios: novel/sparse-neighbour, dense-offset, guard sensitivity
(min_sep), weight sensitivity, singleton groups, and the overlap-like case."""
import os, numpy as np, pandas as pd
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
st = np.load(os.path.join(SH, 'struct_oof.npz'), allow_pickle=True)
sw = st['well'].astype(str); sr = st['ridx'].astype(int); ss = st['struct'].astype(np.float64)
mw = st['meta_well'].astype(str); mnb = st['meta_nnb'].astype(int); mcl = st['meta_closest'].astype(float)
nnb = dict(zip(mw, mnb)); closest = dict(zip(mw, mcl))

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dw = cs['well'][tM].astype(str); do = cs['oof'][tM].astype(np.float64); dy = cs['yt'][tM].astype(np.float64); dr = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(dw, dr, do, dy): dwt[w][r] = (o, y)
pf = np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz', allow_pickle=True)
pw = pf['well'].astype(str); pp = pf['pred'].astype(np.float64)
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'

# PF rows are in toe order per well -> map to ridx via the well's toe indices
pf_map = {}
for wid in np.unique(pw):
    try:
        hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['TVT_input'])
    except Exception: continue
    tidx = np.where(hw['TVT_input'].isna().values)[0]
    v = pp[pw == wid]
    if len(v) == len(tidx): pf_map[wid] = dict(zip(tidx.tolist(), v.tolist()))

sidx = defaultdict(dict)
for w, r, s in zip(sw, sr, ss): sidx[w][int(r)] = s

Ds, Ps, Ss, Ys, Ws = [], [], [], [], []
for w in sorted(set(sw)):
    if w not in dwt or w not in pf_map: continue
    for r, s in sidx[w].items():
        if r in dwt[w] and r in pf_map[w]:
            o, y = dwt[w][r]
            Ds.append(o); Ps.append(pf_map[w][r]); Ss.append(s); Ys.append(y); Ws.append(w)
D_ = np.array(Ds); P_ = np.array(Ps); S_ = np.array(Ss); Y_ = np.array(Ys); W_ = np.array(Ws)
base = 0.5 * D_ + 0.5 * P_
rmse = lambda a, m=None: float(np.sqrt(np.mean((a[m] - Y_[m]) ** 2))) if m is not None else float(np.sqrt(np.mean((a - Y_) ** 2)))
print(f"aligned: wells={len(set(W_))} rows={len(Y_)}")
print(f"base blend0.5={rmse(base):.4f}  struct={rmse(S_):.4f}  DWT={rmse(D_):.4f}  PF={rmse(P_):.4f}")

uw = np.array(sorted(set(W_)))
def nested_gain(mask, seeds=5):
    """nested weight fit on well-splits within `mask`; returns (base, blended, gain, weights)"""
    ws = uw[np.isin(uw, np.unique(W_[mask]))]
    if len(ws) < 6: return None
    outs = []
    for seed in range(seeds):
        rng = np.random.RandomState(seed); sh = ws.copy(); rng.shuffle(sh)
        g0 = set(sh[:len(sh) // 2])
        m0 = mask & np.array([w in g0 for w in W_]); m1 = mask & ~np.array([w in g0 for w in W_])
        if m0.sum() < 100 or m1.sum() < 100: continue
        def fitw(m):
            d = S_[m] - base[m]; r = Y_[m] - base[m]
            return float(np.clip(np.dot(d, r) / max(np.dot(d, d), 1e-9), 0, 1))
        pred = base.copy(); w0, w1 = fitw(m0), fitw(m1)
        pred[m1] = base[m1] + w0 * (S_[m1] - base[m1]); pred[m0] = base[m0] + w1 * (S_[m0] - base[m0])
        outs.append((rmse(base, mask), rmse(pred, mask), w0, w1))
    if not outs: return None
    A = np.array([[o[0], o[1]] for o in outs])
    return A[:, 0].mean(), A[:, 1].mean(), A[:, 0].mean() - A[:, 1].mean(), [round(o[2], 3) for o in outs]

print("\n=== S1. WEIGHT SENSITIVITY (fixed weights, full set) ===")
for w in [0.0, 0.03, 0.05, 0.07, 0.09, 0.12, 0.15, 0.20]:
    print(f"  W={w:.2f}: {rmse((1-w)*base + w*S_):.4f}")
r = nested_gain(np.ones(len(Y_), bool))
if r: print(f"  NESTED (full): base {r[0]:.4f} -> {r[1]:.4f}  gain {r[2]:+.4f}  w={r[3]}")

print("\n=== S2. NEIGHBOUR-COUNT SEGMENTS (novel/sparse vs dense-offset) ===")
nb_arr = np.array([nnb.get(w, 0) for w in W_])
cl_arr = np.array([closest.get(w, np.nan) for w in W_])
for lo, hi, lab in [(0, 3, 'very sparse (<=3 mates)'), (4, 10, 'sparse 4-10'), (11, 30, 'mid 11-30'), (31, 10**6, 'dense >30')]:
    m = (nb_arr >= lo) & (nb_arr <= hi)
    if m.sum() < 500: print(f"  {lab:24s} n={m.sum()} (too few)"); continue
    rr = nested_gain(m)
    g = f"gain {rr[2]:+.4f} w={rr[3]}" if rr else "n/a"
    print(f"  {lab:24s} n={m.sum():>8d} wells={len(set(W_[m])):3d} base={rmse(base,m):.3f} struct={rmse(S_,m):.3f} w0.07={rmse((1-0.07)*base+0.07*S_, m):.3f}  {g}")

print("\n=== S3. CLOSEST-MATE DISTANCE SEGMENTS (the signal's range dependence) ===")
for lo, hi, lab in [(0, 300, '<300ft'), (300, 500, '300-500ft'), (500, 1000, '500-1000ft'), (1000, 1e9, '>1000ft')]:
    m = np.isfinite(cl_arr) & (cl_arr >= lo) & (cl_arr < hi)
    if m.sum() < 500: print(f"  {lab:14s} n={m.sum()} (too few)"); continue
    rr = nested_gain(m)
    g = f"gain {rr[2]:+.4f}" if rr else "n/a"
    print(f"  {lab:14s} n={m.sum():>8d} wells={len(set(W_[m])):3d} base={rmse(base,m):.3f} struct={rmse(S_,m):.3f} w0.07={rmse((1-0.07)*base+0.07*S_, m):.3f}  {g}")

print("\n=== S4. FALLBACK CHECK (wells with no struct row = 0 surviving neighbours) ===")
no_struct = [w for w in mw if nnb.get(w, 0) == 0]
print(f"  wells with 0 surviving neighbours: {len(no_struct)}/{len(mw)} -> struct contribution disabled, prediction = DWT+PF blend unchanged")

print("\n=== S5. PER-WELL RISK (does W=0.07 ever materially hurt a well?) ===")
per = []
for w in sorted(set(W_)):
    m = W_ == w
    b = rmse(base, m); n = rmse((1-0.07)*base + 0.07*S_, m)
    per.append((w, b, n, n - b, nnb.get(w, 0), closest.get(w, np.nan)))
pdf = pd.DataFrame(per, columns=['well', 'base', 'w007', 'delta', 'nnb', 'closest'])
print(f"  wells improved: {int((pdf.delta<0).sum())}/{len(pdf)}   worsened: {int((pdf.delta>0).sum())}")
print(f"  delta: mean={pdf.delta.mean():+.3f} p95={pdf.delta.quantile(.95):+.3f} worst={pdf.delta.max():+.3f} (well {pdf.loc[pdf.delta.idxmax(),'well']})")
print("  worst 5 wells:"); print(pdf.nlargest(5, 'delta')[['well','base','w007','delta','nnb','closest']].to_string(index=False))
pdf.to_csv(os.path.join(SH, 'struct_per_well_stress.csv'), index=False)
