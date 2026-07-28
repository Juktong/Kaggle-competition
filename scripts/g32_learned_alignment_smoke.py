"""G3.2 — learned local alignment scorer + DP (local smoke, no Kaggle, no submission).

Two prior results bound this task and are addressed by the design:
  2026-07-21: a CNN/Siamese GR-window scorer reached AUC 0.636-0.647 vs an NCC baseline of 0.524
              (chance). Root causes: the pairing was mis-specified by ~34x in vertical extent
              (a 64-row horizontal MD window spans a median 0.95 ft of TVT, paired against a 32 ft
              typewell window), and per-window z-scoring destroyed the level cue
              (level match AUC 0.578 > shape match 0.509).
  2026-07-26: G3.1 ran a DP over a |GR_h - GR_tw| cost matrix; it converges to the flat-anchor
              baseline FROM ABOVE and never crosses it.

Design changes here:
  1. MATCHED EXTENT. The horizontal side is summarised as local features at row i (it has almost no
     TVT extent); the typewell side supplies a short window around the candidate state s. No 34x
     mismatch.
  2. LEVEL CUE KEPT. Features are NOT per-window z-scored; absolute GR level enters the model, since
     level was the stronger hand-coded cue.
  3. The scorer directly produces cost[row, state], so it drops into the same beam DP as G3.1 and is
     compared against the flat-anchor baseline that G3.1 could not beat.

Env: MAXW_TRAIN, MAXW_EVAL, EPOCHS.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '12'))
EPOCHS = int(os.environ.get('EPOCHS', '8'))
STEP = 1.0          # TVT state grid (ft)
HW = 16             # horizontal half-window in rows
TWH = 8             # typewell half-window in grid cells


def load(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['MD', 'Z', 'GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR']).sort_values('TVT')
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tv = tw['TVT'].values.astype(float); tg = tw['GR'].fillna(tw['GR'].mean()).values.astype(float)
    grid = np.arange(np.nanmin(tv), np.nanmax(tv), STEP)
    prof = np.interp(grid, tv, tg)
    return hw, gr, grid, prof


def hfeat(gr, i):
    """horizontal-side local features at row i (level cue preserved)."""
    a, b = max(0, i - HW), min(len(gr), i + HW + 1)
    w = gr[a:b]
    return np.array([w.mean(), w.std(), gr[i], w.max() - w.min(),
                     (w[len(w)//2:].mean() - w[:len(w)//2].mean())], float)


def tfeat(prof, s):
    """typewell-side features at state s (level cue preserved)."""
    a, b = max(0, s - TWH), min(len(prof), s + TWH + 1)
    w = prof[a:b]
    if len(w) < 3: w = prof[max(0, s-1):s+2]
    g = np.gradient(w) if len(w) > 2 else np.zeros(len(w))
    return np.array([w.mean(), w.std(), prof[min(s, len(prof)-1)], w.max() - w.min(), g.mean()], float)


def pairfeat(fh, ft):
    """combine: both sides + differences + ratios. Level difference is explicit."""
    d = fh - ft
    return np.concatenate([fh, ft, d, [abs(d[0]), abs(d[2])]])


# ---------------- build training pairs ----------------
wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng = np.random.RandomState(11); rng.shuffle(wids)
train_w, eval_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]

X, Y, NCC, LVL = [], [], [], []
for wid in train_w:
    try: hw, gr, grid, prof = load(wid)
    except Exception: continue
    tvt = hw['TVT'].values.astype(float)
    n = len(gr)
    idx = np.arange(HW, n - HW, max(1, (n - 2*HW)//40))
    for i in idx:
        if not np.isfinite(tvt[i]): continue
        s_true = int((tvt[i] - grid[0]) / STEP)
        if s_true < TWH or s_true >= len(grid) - TWH: continue
        fh = hfeat(gr, i)
        off = int(np.random.choice([-1, 1]) * np.random.randint(8, 60))
        s_neg = s_true + off
        if s_neg < TWH or s_neg >= len(grid) - TWH: continue
        for s, y in ((s_true, 1.0), (s_neg, 0.0)):
            ft = tfeat(prof, s)
            X.append(pairfeat(fh, ft)); Y.append(y)
            # hand-coded baselines on the SAME pairs
            a, b = max(0, i-HW), min(len(gr), i+HW+1)
            wh = gr[a:b]; wt = prof[max(0, s-TWH):s+TWH+1]
            m = min(len(wh), len(wt))
            zh = (wh[:m]-wh[:m].mean())/(wh[:m].std()+1e-6); zt = (wt[:m]-wt[:m].mean())/(wt[:m].std()+1e-6)
            NCC.append(float(np.mean(zh*zt)))                       # shape (z-scored)
            LVL.append(-abs(float(wh.mean()) - float(wt.mean())))   # level
X = np.array(X, np.float32); Y = np.array(Y, np.float32)
NCC = np.array(NCC); LVL = np.array(LVL)
print(f"pairs={len(Y)} (pos {int(Y.sum())})  feat_dim={X.shape[1]}  train_wells={len(train_w)}", flush=True)

from sklearn.metrics import roc_auc_score
mu, sd = X.mean(0), X.std(0) + 1e-6
Xn = (X - mu) / sd
ntr = int(0.8 * len(Y))
perm = np.random.RandomState(0).permutation(len(Y))
tr, va = perm[:ntr], perm[ntr:]

import torch, torch.nn as nn
torch.manual_seed(0); torch.set_num_threads(2)
model = nn.Sequential(nn.Linear(X.shape[1], 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
opt = torch.optim.Adam(model.parameters(), 1e-3); lossf = nn.BCEWithLogitsLoss()
Xt = torch.tensor(Xn); Yt = torch.tensor(Y)
print("\n=== training (CPU, tiny MLP) ===", flush=True)
for ep in range(EPOCHS):
    model.train(); p = torch.randperm(len(tr)); tot = 0.0
    for k in range(0, len(tr), 512):
        b = torch.tensor(tr)[p[k:k+512]]
        opt.zero_grad(); l = lossf(model(Xt[b]).squeeze(-1), Yt[b]); l.backward(); opt.step()
        tot += float(l) * len(b)
    model.eval()
    with torch.no_grad(): vp = model(Xt[torch.tensor(va)]).squeeze(-1).numpy()
    auc = roc_auc_score(Y[va], vp)
    print(f"  ep{ep}: loss={tot/len(tr):.4f}  val_auc={auc:.4f}", flush=True)

print("\n=== baselines on the IDENTICAL validation pairs ===")
print(f"  NCC shape (z-scored)     AUC = {roc_auc_score(Y[va], NCC[va]):.4f}")
print(f"  level  -|GRh - GRtw|     AUC = {roc_auc_score(Y[va], LVL[va]):.4f}")
print(f"  LEARNED scorer           AUC = {auc:.4f}")

# ---------------- plug into the same beam DP as G3.1 ----------------
print("\n=== DP with the learned emission vs flat-anchor (masked-toe eval wells) ===", flush=True)
def dp_eval(wid, lam=20.0, K=6, band=60, sub=10):
    hw, gr, grid, prof = load(wid)
    kn = hw['TVT_input'].notna().values
    if kn.sum() < 100 or (~kn).sum() < 200: return None
    toe = np.where(~kn)[0][::sub]
    if len(toe) < 20: return None
    tru = hw['TVT'].values.astype(float)[toe]
    anchor = float(hw['TVT_input'].values[kn][-1])
    S = len(grid)
    TF = np.stack([tfeat(prof, s) for s in range(S)])
    C = np.empty((len(toe), S), float)
    with torch.no_grad():
        for j, i in enumerate(toe):
            fh = hfeat(gr, i)
            F = np.concatenate([np.repeat(fh[None], S, 0), TF, fh[None]-TF,
                                np.abs(fh[0]-TF[:, 0])[:, None], np.abs(fh[2]-TF[:, 2])[:, None]], 1)
            sc = model(torch.tensor(((F-mu)/sd).astype(np.float32))).squeeze(-1).numpy()
            C[j] = -sc                                   # cost = -score
            C[j] = (C[j] - C[j].mean()) / (C[j].std() + 1e-9)
    s0 = int(np.clip((anchor - grid[0]) / STEP, 0, S - 1))
    beams = [([s0], 0.0)]
    for j in range(len(toe)):
        cand = []
        for path, cost in beams:
            s = path[-1]; lo, hi = max(0, s-band), min(S, s+band+1)
            step = C[j, lo:hi] + lam * np.abs(np.arange(lo, hi) - s) / max(band, 1)
            for t in np.argsort(step)[:K]: cand.append((path + [lo+int(t)], cost + float(step[t])))
        cand.sort(key=lambda x: x[1]); seen = set(); beams = []
        for p_, c_ in cand:
            if p_[-1] in seen: continue
            seen.add(p_[-1]); beams.append((p_, c_))
            if len(beams) >= K: break
    top1 = grid[np.array(beams[0][0][1:])]
    return (float(np.sqrt(np.mean((top1-tru)**2))), float(np.sqrt(np.mean((anchor-tru)**2))))

LAMS = [float(x) for x in os.environ.get('LAMS', '5,20,60,150').split(',')]
flat_ref = None
for lam in LAMS:
    rs = [r for r in (dp_eval(w, lam=lam) for w in eval_w) if r is not None]
    if not rs: continue
    dpv = np.array([r[0] for r in rs]); fl = np.array([r[1] for r in rs]); flat_ref = np.sqrt((fl**2).mean())
    print(f"  lam={lam:6.1f}  DP(learned emission) = {np.sqrt((dpv**2).mean()):7.3f}   flat-anchor = {flat_ref:7.3f}"
          f"   {'BEATS flat' if np.sqrt((dpv**2).mean()) < flat_ref else 'worse than flat'}", flush=True)
print(f"  G3.1 reference (|GR diff| emission): converged to flat from ABOVE, never crossed")
print("\nGATE: the learned scorer must beat NCC materially AND its DP must beat the flat-anchor baseline.")
