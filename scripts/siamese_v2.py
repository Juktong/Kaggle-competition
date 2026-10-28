"""Direction 5 (revised): is a LEARNED GR window scorer actually better than the hand-coded NCC cost?

The 2026-07-20 round reported val_auc 0.657 for a Siamese scorer but never measured the incumbent
(normalized cross-correlation) on the SAME pairs, so the number was uninterpretable. It also used
AdaptiveAvgPool1d(1), which makes the encoder translation-INVARIANT -- antithetical to a task whose
whole signal is a translation offset.

This script scores, on identical pairs:
  0) NCC baseline           -- the incumbent hand-coded emission cost (no learning)
  1) Siamese + avgpool      -- the 2026-07-20 architecture (reproduction)
  2) Siamese + flatten      -- same encoder, position-preserving pooling
  3) Joint 2-channel CNN    -- both windows as channels; can compute local differences directly

Env: MAXW, EPOCHS, WIN, NEG_MIN, BATCH, DEVICE, MAXPAIRS.
"""
import os, glob, time, json, numpy as np, pandas as pd
import torch, torch.nn as nn
from sklearn.metrics import roc_auc_score
torch.manual_seed(0); np.random.seed(0)

D = os.environ.get('DATA', '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train')
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MAXW = int(os.environ.get('MAXW', '80')); EPOCHS = int(os.environ.get('EPOCHS', '6'))
WIN = int(os.environ.get('WIN', '64')); NEG_MIN = float(os.environ.get('NEG_MIN', '10'))
BATCH = int(os.environ.get('BATCH', '256')); DEVICE = os.environ.get('DEVICE', 'cpu')
MAXPAIRS = int(os.environ.get('MAXPAIRS', '40000'))
OUT = os.environ.get('OUT', os.path.join(SH, 'siamese_v2.json'))
torch.set_num_threads(int(os.environ.get('THREADS', '1')))   # K=48 owns the cores

def tw_grid(tw, step=0.5):
    t = tw.sort_values('TVT'); tv = t['TVT'].values.astype(float)
    gr = t['GR'].fillna(t['GR'].mean()).values.astype(float)
    lo, hi = np.nanmin(tv), np.nanmax(tv)
    grid = np.arange(lo, hi, step)
    return grid, np.interp(grid, tv, gr), lo, hi, step

def build_pairs(wids, maxp):
    X1, X2, Y = [], [], []
    for wid in wids:
        try:
            hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['GR', 'TVT', 'TVT_input'])
            tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR'])
        except Exception: continue
        gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(np.float32)
        tvt = hw['TVT'].values.astype(float)
        grid, tgr, lo, hi, step = tw_grid(tw)
        if len(grid) < WIN + 4 or len(gr) < WIN + 4: continue
        half = WIN // 2
        idx = np.arange(half, len(gr) - half, max(1, (len(gr) - WIN) // 60))
        for i in idx:
            if not np.isfinite(tvt[i]): continue
            c = int((tvt[i] - lo) / step)
            if c - half < 0 or c + half >= len(grid): continue
            hwin = gr[i - half:i + half]; pos = tgr[c - half:c + half]
            off = float(np.random.choice([-1, 1]) * np.random.uniform(NEG_MIN, 4 * NEG_MIN))
            cn = int((tvt[i] + off - lo) / step)
            if cn - half < 0 or cn + half >= len(grid): continue
            neg = tgr[cn - half:cn + half]
            if len(hwin) != WIN or len(pos) != WIN or len(neg) != WIN: continue
            X1 += [hwin, hwin]; X2 += [pos, neg]; Y += [1.0, 0.0]
            if len(Y) >= maxp: break
        if len(Y) >= maxp: break
    def norm(a):
        a = np.asarray(a, np.float32)
        m = a.mean(1, keepdims=True); s = a.std(1, keepdims=True) + 1e-6
        return (a - m) / s
    return norm(X1), norm(X2), np.asarray(Y, np.float32)

class Enc(nn.Module):
    def __init__(s, c=32, pool='avg', win=64):
        super().__init__(); s.pool = pool
        s.body = nn.Sequential(nn.Conv1d(1, c, 7, padding=3), nn.ReLU(), nn.MaxPool1d(2),
                               nn.Conv1d(c, c, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
                               nn.Conv1d(c, c, 3, padding=1), nn.ReLU())
        s.out_dim = c if pool == 'avg' else c * (win // 4)
    def forward(s, x):
        h = s.body(x.unsqueeze(1))
        return h.mean(-1) if s.pool == 'avg' else h.flatten(1)

class Siam(nn.Module):
    def __init__(s, c=32, pool='avg', win=64):
        super().__init__(); s.enc = Enc(c, pool, win); d = s.enc.out_dim
        s.head = nn.Sequential(nn.Linear(3 * d, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(s, a, b):
        ea, eb = s.enc(a), s.enc(b)
        return s.head(torch.cat([ea, eb, (ea - eb).abs()], 1)).squeeze(-1)

class Joint(nn.Module):
    """both windows as 2 input channels -> local differences are computable in layer 1."""
    def __init__(s, c=32, win=64):
        super().__init__()
        s.body = nn.Sequential(nn.Conv1d(2, c, 7, padding=3), nn.ReLU(), nn.MaxPool1d(2),
                               nn.Conv1d(c, c, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
                               nn.Conv1d(c, c, 3, padding=1), nn.ReLU())
        s.head = nn.Sequential(nn.Linear(c * (win // 4), 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(s, a, b):
        return s.head(s.body(torch.stack([a, b], 1)).flatten(1)).squeeze(-1)

t0 = time.time()
allw = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng = np.random.RandomState(3); rng.shuffle(allw)
tr_w, te_w = allw[:MAXW], allw[MAXW:MAXW + max(4, MAXW // 4)]
X1, X2, Y = build_pairs(tr_w, MAXPAIRS)
V1, V2, VY = build_pairs(te_w, MAXPAIRS // 4)
print(f"pairs: train={len(Y)} val={len(VY)}  win={WIN} neg_min={NEG_MIN}ft  build {time.time()-t0:.1f}s", flush=True)
if len(Y) < 100 or len(VY) < 50: print("insufficient pairs"); raise SystemExit(1)

# ---- 0) NCC baseline: the incumbent hand-coded cost, on the identical val pairs ----
ncc = np.mean(V1 * V2, axis=1)          # both already z-scored per window -> this IS normalized xcorr
auc_ncc = float(roc_auc_score(VY, ncc))
acc_ncc = float(np.mean((ncc > np.median(ncc)) == (VY > 0.5)))
print(f"\n  [0] NCC baseline (no learning) : val_auc={auc_ncc:.3f}  acc@median={acc_ncc:.3f}", flush=True)

dev = torch.device(DEVICE)
Xt1 = torch.tensor(X1); Xt2 = torch.tensor(X2); Yt = torch.tensor(Y)
Vt1 = torch.tensor(V1).to(dev); Vt2 = torch.tensor(V2).to(dev)

def train(model, name):
    m = model.to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); lossf = nn.BCEWithLogitsLoss()
    best = 0.0
    for ep in range(EPOCHS):
        m.train(); perm = torch.randperm(len(Yt)); tot = 0.0
        for i in range(0, len(Yt), BATCH):
            b = perm[i:i + BATCH]; opt.zero_grad()
            l = lossf(m(Xt1[b].to(dev), Xt2[b].to(dev)), Yt[b].to(dev))
            l.backward(); opt.step(); tot += float(l) * len(b)
        m.eval()
        with torch.no_grad(): vp = m(Vt1, Vt2).cpu().numpy()
        auc = float(roc_auc_score(VY, vp)); best = max(best, auc)
        print(f"      ep{ep}: loss={tot/len(Yt):.4f} val_auc={auc:.3f}", flush=True)
    print(f"  [{name}] best val_auc={best:.3f}   vs NCC {auc_ncc:.3f}  -> {best-auc_ncc:+.3f}", flush=True)
    return best

print("\n  [1] Siamese avgpool (2026-07-20 reproduction)", flush=True)
a1 = train(Siam(32, 'avg', WIN), '1 siam_avg')
print("\n  [2] Siamese flatten (position-preserving)", flush=True)
a2 = train(Siam(32, 'flat', WIN), '2 siam_flat')
print("\n  [3] Joint 2-channel CNN", flush=True)
a3 = train(Joint(32, WIN), '3 joint_2ch')

json.dump(dict(auc_ncc=auc_ncc, auc_siam_avg=a1, auc_siam_flat=a2, auc_joint=a3,
               pairs_train=len(Y), pairs_val=len(VY), win=WIN, neg_min=NEG_MIN,
               epochs=EPOCHS, maxw=MAXW, runtime_s=round(time.time()-t0, 1)), open(OUT, 'w'), indent=1)
print(f"\n=== SUMMARY (identical val pairs) ===")
print(f"  NCC (incumbent)        {auc_ncc:.3f}")
print(f"  siam_avg  (old arch)   {a1:.3f}   {a1-auc_ncc:+.3f} vs NCC")
print(f"  siam_flat (pos-keep)   {a2:.3f}   {a2-auc_ncc:+.3f} vs NCC")
print(f"  joint_2ch              {a3:.3f}   {a3-auc_ncc:+.3f} vs NCC")
print(f"\nGATE: a learned scorer must BEAT NCC materially to justify DP/top-K integration + GPU time.")
print(f"done in {time.time()-t0:.1f}s -> {OUT}")
