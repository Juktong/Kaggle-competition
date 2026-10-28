"""Direction 6 headroom diagnostic: does the deployed prediction leave SEQUENCE structure unexploited?

A sequence / MTP / MDN model can only help if the residual of the current prediction is structured
along the trajectory. Three cheap, decisive measurements before building any such model:

  1) residual autocorrelation along the toe row index (lag 1 .. 2000)
  2) does NESTED-FIT smoothing of the deployed prediction along MD reduce RMSE?
     (bandwidth chosen on held-out wells; if the honest optimum is ~0, sequence smoothing has no headroom)
  3) is the residual multi-modal / heavy-tailed enough for a mixture head to pay off?

All on the deployed honest slot 54844628 (OOF 8.8626). Rows are stored per-well in toe order.
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

wells = []
for w in sorted(set(dw) & set(rw)):
    a = np.array(di[w]); b = np.array(si[w])
    if len(a) != len(b): continue
    base = dc['blend'][a].astype(np.float64); truth = dc['truth'][a].astype(np.float64)
    st = rs[b]
    g = (nnb.get(w, 0) >= 4) and np.isfinite(cl.get(w, np.nan)) and cl.get(w, 1e9) < 1000
    cur = 0.85 * base + 0.15 * st if g else base
    wells.append((w, cur, truth))
print(f"wells={len(wells)} rows={sum(len(c) for _, c, _ in wells)}", flush=True)
allcur = np.concatenate([c for _, c, _ in wells]); alltru = np.concatenate([t for _, _, t in wells])
rmse_all = float(np.sqrt(np.mean((allcur - alltru) ** 2)))
print(f"deployed OOF = {rmse_all:.4f}\n", flush=True)

# ---- 1) residual autocorrelation along the trajectory ----
print("=== 1) residual autocorrelation along toe row index ===", flush=True)
for lag in [1, 5, 20, 100, 500, 2000]:
    num = den = 0.0
    for _, c, t in wells:
        r = t - c
        if len(r) <= lag + 5: continue
        a, b = r[:-lag], r[lag:]
        a = a - a.mean(); b = b - b.mean()
        num += float(np.dot(a, b)); den += float(np.sqrt(np.dot(a, a) * np.dot(b, b)) + 1e-12)
    print(f"  lag {lag:5d}: autocorr = {num/max(den,1e-12):+.4f}", flush=True)

# ---- 2) nested-fit smoothing of the prediction along MD ----
print("\n=== 2) nested-fit smoothing along MD (bandwidth chosen on held-out wells) ===", flush=True)
def smooth(x, k):
    if k <= 1: return x
    ker = np.ones(k) / k
    pad = k // 2
    return np.convolve(np.pad(x, (pad, pad), mode='edge'), ker, mode='same')[pad:pad + len(x)]

KS = [1, 5, 15, 51, 151, 501, 1501]
per_k = {}
for k in KS:
    sq = {}
    for w, c, t in wells:
        sq[w] = float(np.sum((smooth(c, k) - t) ** 2)), len(c)
    per_k[k] = sq
    tot = sum(v[0] for v in sq.values()); n = sum(v[1] for v in sq.values())
    print(f"  k={k:5d}: full-data RMSE = {np.sqrt(tot/n):.4f}  gain {rmse_all-np.sqrt(tot/n):+.4f}", flush=True)

uw = np.array([w for w, _, _ in wells])
outs = []
for seed in range(3):
    rg = np.random.RandomState(seed); sh = uw.copy(); rg.shuffle(sh)
    half = set(sh[:len(sh) // 2])
    tot = n = 0.0
    for tr_set in [half, set(uw) - half]:
        te_set = set(uw) - tr_set
        bestk, bestv = 1, np.inf
        for k in KS:
            s = sum(per_k[k][w][0] for w in tr_set); m = sum(per_k[k][w][1] for w in tr_set)
            if s / m < bestv: bestv, bestk = s / m, k
        tot += sum(per_k[bestk][w][0] for w in te_set); n += sum(per_k[bestk][w][1] for w in te_set)
    outs.append(np.sqrt(tot / n))
nested = float(np.mean(outs))
print(f"  NESTED bandwidth selection: {nested:.4f}   gain {rmse_all-nested:+.4f}", flush=True)

# ---- 3) residual shape ----
print("\n=== 3) residual distribution shape ===", flush=True)
r = alltru - allcur
from scipy import stats
print(f"  mean={r.mean():+.3f} std={r.std():.3f} skew={stats.skew(r):+.3f} kurtosis={stats.kurtosis(r):+.3f}", flush=True)
print(f"  |r|<1ft {100*np.mean(np.abs(r)<1):.1f}%   |r|>10ft {100*np.mean(np.abs(r)>10):.1f}%   |r|>25ft {100*np.mean(np.abs(r)>25):.1f}%", flush=True)
try:
    from sklearn.mixture import GaussianMixture
    samp = r[np.random.RandomState(0).choice(len(r), 200000, replace=False)].reshape(-1, 1)
    for nc in [1, 2, 3]:
        gm = GaussianMixture(nc, random_state=0, max_iter=60).fit(samp)
        print(f"  GMM k={nc}: BIC={gm.bic(samp):.0f}  means={np.round(gm.means_.ravel(),2)}  weights={np.round(gm.weights_,3)}", flush=True)
except Exception as e:
    print("  GMM skipped:", str(e)[:60], flush=True)
print("\nGATE: sequence/MTP/MDN work is justified only if residual autocorrelation is materially")
print("      non-zero at usable lags AND nested smoothing shows a real gain.")
