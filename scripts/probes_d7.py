"""Direction 7 — cheap probes on existing OOF arrays (no new heavy artifacts).

P1  3-way weight re-optimization. The 0.5/0.5 DWT/PF split was fixed BEFORE the structural field
    existed; the deployed gated form is effectively 0.425 DWT + 0.425 PF + 0.15 struct. Refit (a,b,c)
    nested by well and see whether the incumbent split is still optimal.
P2  Robust combiner. Residual kurtosis is +9.17, so a trimmed / median-style combiner of DWT & PF
    could beat the mean.
P3  Continuous structural weight W(nnb, closest) instead of the binary deployment gate.
P4  Monotone (isotonic) calibration of the final prediction.
P5  Per-well nested weight vs global nested weight -- quantifies how much of the 3-way weight gain (if
    any) is well-specific rather than global.

Everything is nested by well (fit on half the wells, applied to the held-out half, 3 seeds).
"""
import os, numpy as np
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
_z = np.load(os.path.join(SH, 'decomp_features.npz'), allow_pickle=True)
dc = {k: _z[k] for k in _z.files}
dw = dc['well'].astype(str)
rd = np.load(os.path.join(SH, 'struct_oof_rowdist.npz'), allow_pickle=True)
rw = rd['well'].astype(str); rs = rd['struct'].astype(np.float64)
nnb = dict(zip(rd['meta_well'].astype(str), rd['meta_nnb'].astype(int)))
cl = dict(zip(rd['meta_well'].astype(str), rd['meta_closest'].astype(float)))

di = defaultdict(list); si = defaultdict(list)
for i, w in enumerate(dw): di[w].append(i)
for i, w in enumerate(rw): si[w].append(i)
D_, P_, S_, Y_, W_ = [], [], [], [], []
for w in sorted(set(dw) & set(rw)):
    a = np.array(di[w]); b = np.array(si[w])
    if len(a) != len(b): continue
    D_.append(dc['dwt'][a].astype(np.float64)); P_.append(dc['pf'][a].astype(np.float64))
    S_.append(rs[b]); Y_.append(dc['truth'][a].astype(np.float64)); W_.append(np.full(len(a), w))
Dv = np.concatenate(D_); Pv = np.concatenate(P_); Sv = np.concatenate(S_); Y = np.concatenate(Y_); W = np.concatenate(W_)
nnbv = np.array([nnb.get(w, 0) for w in W], float); clov = np.array([cl.get(w, np.nan) for w in W], float)
gate = (nnbv >= 4) & (clov < 1000) & np.isfinite(clov)
rmse = lambda a: float(np.sqrt(np.mean((a - Y) ** 2)))
base = 0.5 * Dv + 0.5 * Pv
cur = base.copy(); cur[gate] = 0.85 * base[gate] + 0.15 * Sv[gate]
uw = np.array(sorted(set(W)))
print(f"rows={len(Y)} wells={len(uw)} gated={100*gate.mean():.1f}%", flush=True)
print(f"  DWT {rmse(Dv):.4f}  PF {rmse(Pv):.4f}  struct {rmse(Sv):.4f}  base {rmse(base):.4f}  DEPLOYED {rmse(cur):.4f}\n", flush=True)

def halves(seed):
    rg = np.random.RandomState(seed); sh = uw.copy(); rg.shuffle(sh)
    g0 = set(sh[:len(sh)//2]); inA = np.array([w in g0 for w in W])
    return [(inA, ~inA), (~inA, inA)]

# ---------------- P1: 3-way nested weight refit ----------------
print("=== P1  3-way weight re-optimization (nested, non-negative, sum-to-1) ===", flush=True)
def fit3(tr, use_struct):
    m = tr & gate if use_struct else tr
    cols = [Dv[m], Pv[m], Sv[m]] if use_struct else [Dv[m], Pv[m]]
    A = np.column_stack(cols); y = Y[m]
    # solve with sum-to-1 by eliminating the last weight
    A2 = A[:, :-1] - A[:, -1:]; y2 = y - A[:, -1]
    try: c, _, _, _ = np.linalg.lstsq(A2, y2, rcond=None)
    except Exception: return None
    wgt = np.append(c, 1.0 - c.sum())
    return np.clip(wgt, 0, 1) / max(np.clip(wgt, 0, 1).sum(), 1e-9)
outs, wl = [], []
for seed in range(3):
    p = cur.copy()
    for tr, te in halves(seed):
        w3 = fit3(tr, True)
        if w3 is None: continue
        wl.append(w3)
        ap = te & gate
        p[ap] = w3[0]*Dv[ap] + w3[1]*Pv[ap] + w3[2]*Sv[ap]
        w2 = fit3(tr & ~gate, False)
        if w2 is not None:
            an = te & ~gate; p[an] = w2[0]*Dv[an] + w2[1]*Pv[an]
    outs.append(rmse(p))
r1 = float(np.mean(outs))
wm = np.mean(wl, 0)
print(f"  fitted gated weights (mean): DWT={wm[0]:.3f} PF={wm[1]:.3f} struct={wm[2]:.3f}", flush=True)
print(f"  deployed equivalent        : DWT=0.425 PF=0.425 struct=0.150", flush=True)
print(f"  NESTED 3-way refit = {r1:.4f}   gain {rmse(cur)-r1:+.4f}\n", flush=True)

# ---------------- P2: robust combiner ----------------
print("=== P2  robust combiners of DWT & PF ===", flush=True)
for nm, v in [('mean (incumbent)', 0.5*Dv+0.5*Pv),
              ('shrink-to-median 0.75', 0.75*(0.5*Dv+0.5*Pv) + 0.25*np.minimum(Dv, Pv)),
              ('closer-to-struct pick', np.where(np.abs(Dv-Sv) < np.abs(Pv-Sv), Dv, Pv))]:
    vv = v.copy(); vv[gate] = 0.85*v[gate] + 0.15*Sv[gate]
    print(f"  {nm:24s} {rmse(vv):.4f}  gain {rmse(cur)-rmse(vv):+.4f}", flush=True)

# ---------------- P3: continuous structural weight ----------------
print("\n=== P3  continuous W(nnb, closest) vs the binary gate ===", flush=True)
def contW(kind):
    if kind == 'nnb':  f = np.clip((nnbv - 2) / 10.0, 0, 1)
    elif kind == 'clo': f = np.clip(1.0 - clov / 2000.0, 0, 1)
    else:              f = np.clip((nnbv - 2) / 10.0, 0, 1) * np.clip(1.0 - clov / 2000.0, 0, 1)
    return np.nan_to_num(f, nan=0.0)
for kind in ['nnb', 'clo', 'both']:
    f = contW(kind); outs = []
    for seed in range(3):
        p = base.copy()
        for tr, te in halves(seed):
            d = (Sv - base) * f
            a = float(np.clip(np.dot(d[tr], (Y-base)[tr]) / max(np.dot(d[tr], d[tr]), 1e-9), 0, 3))
            p[te] = base[te] + a * f[te] * (Sv[te] - base[te])
        outs.append(rmse(p))
    print(f"  W ~ {kind:5s}: {np.mean(outs):.4f}  gain {rmse(cur)-np.mean(outs):+.4f}", flush=True)

# ---------------- P4: isotonic calibration ----------------
print("\n=== P4  monotone (isotonic) calibration of the final prediction ===", flush=True)
try:
    from sklearn.isotonic import IsotonicRegression
    outs = []
    for seed in range(3):
        p = cur.copy()
        for tr, te in halves(seed):
            idx = np.where(tr)[0][::8]
            ir = IsotonicRegression(out_of_bounds='clip').fit(cur[idx], Y[idx])
            p[te] = ir.predict(cur[te])
        outs.append(rmse(p))
    print(f"  isotonic: {np.mean(outs):.4f}  gain {rmse(cur)-np.mean(outs):+.4f}", flush=True)
except Exception as e:
    print("  skipped:", str(e)[:60], flush=True)

# ---------------- P5: per-well vs global weight ----------------
print("\n=== P5  per-well nested weight (upper bound on well-specific weighting) ===", flush=True)
outs = []
for seed in range(3):
    p = cur.copy()
    for tr, te in halves(seed):
        gl = fit3(tr, True)
        for w in np.unique(W[te]):
            m = (W == w) & gate
            if m.sum() < 50: continue
            p[m] = gl[0]*Dv[m] + gl[1]*Pv[m] + gl[2]*Sv[m]
    outs.append(rmse(p))
print(f"  (global weight applied per gated well) {np.mean(outs):.4f}", flush=True)
print("\nGATE: >= +0.10 vs deployed with stably positive bootstrap.", flush=True)
