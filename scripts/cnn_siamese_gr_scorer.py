"""E: CNN/Siamese GR local-window scorer (tiny smoke first; Kaggle GPU for medium/full).

Idea: replace the hand-written NCC/PF GR likelihood with a learned similarity between a horizontal-GR window
and a typewell-GR window, then use it as the emission cost in a DP/top-K global search.

Honest by construction: inputs are the horizontal well's GR window (test-available) and the typewell GR
profile (test-available). Labels come from TRAIN wells' TVT (ordinary supervised use), never from the target
well's toe truth at inference.

Sampling:
  positive = (hw GR window at row i, typewell GR window centred at the TRUE TVT of row i)
  negative = same hw window vs typewell window centred at TVT + offset (|offset| >= NEG_MIN ft)
Model: small 1D-CNN encoder shared by both branches (Siamese) + cosine/MLP head -> similarity logit.

Env: MAXW, EPOCHS, WIN, NEG_MIN, BATCH, DEVICE, OUT.
Runs on CPU at tiny scale; set DEVICE=cuda on a Kaggle GPU kernel for medium/full.
"""
import os, glob, time, numpy as np, pandas as pd

D = os.environ.get('DATA', '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train')
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MAXW = int(os.environ.get('MAXW', '20')); EPOCHS = int(os.environ.get('EPOCHS', '1'))
WIN = int(os.environ.get('WIN', '64')); NEG_MIN = float(os.environ.get('NEG_MIN', '10'))
BATCH = int(os.environ.get('BATCH', '256')); DEVICE = os.environ.get('DEVICE', 'cpu')
MAXPAIRS = int(os.environ.get('MAXPAIRS', '20000'))
OUT = os.environ.get('OUT', os.path.join(SH, 'cnn_scorer_smoke.json'))

import torch, torch.nn as nn
torch.manual_seed(0)

def tw_grid(tw, step=0.5):
    """typewell GR resampled on a uniform TVT grid -> lets us window by TVT offset."""
    t = tw.sort_values('TVT'); tv = t['TVT'].values.astype(float)
    gr = t['GR'].fillna(t['GR'].mean()).values.astype(float)
    lo, hi = np.nanmin(tv), np.nanmax(tv)
    grid = np.arange(lo, hi, step)
    return grid, np.interp(grid, tv, gr), lo, hi, step

def build_pairs(wids):
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
            hwin = gr[i - half:i + half]
            pos = tgr[c - half:c + half]
            off = float(np.random.choice([-1, 1]) * np.random.uniform(NEG_MIN, 4 * NEG_MIN))
            cn = int((tvt[i] + off - lo) / step)
            if cn - half < 0 or cn + half >= len(grid): continue
            neg = tgr[cn - half:cn + half]
            if len(hwin) != WIN or len(pos) != WIN or len(neg) != WIN: continue
            X1 += [hwin, hwin]; X2 += [pos, neg]; Y += [1.0, 0.0]
            if len(Y) >= MAXPAIRS: break
        if len(Y) >= MAXPAIRS: break
    def norm(a):
        a = np.asarray(a, np.float32)
        m = a.mean(1, keepdims=True); s = a.std(1, keepdims=True) + 1e-6
        return (a - m) / s
    return norm(X1), norm(X2), np.asarray(Y, np.float32)

class Enc(nn.Module):
    def __init__(s, c=32):
        super().__init__()
        s.net = nn.Sequential(nn.Conv1d(1, c, 7, padding=3), nn.ReLU(), nn.MaxPool1d(2),
                              nn.Conv1d(c, c, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
                              nn.Conv1d(c, c, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool1d(1))
    def forward(s, x): return s.net(x.unsqueeze(1)).squeeze(-1)

class Siam(nn.Module):
    def __init__(s, c=32):
        super().__init__(); s.enc = Enc(c); s.head = nn.Sequential(nn.Linear(3 * c, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(s, a, b):
        ea, eb = s.enc(a), s.enc(b)
        return s.head(torch.cat([ea, eb, (ea - eb).abs()], 1)).squeeze(-1)

if __name__ == '__main__':
    t0 = time.time()
    allw = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(3); rng.shuffle(allw)
    tr_w, te_w = allw[:MAXW], allw[MAXW:MAXW + max(4, MAXW // 4)]
    X1, X2, Y = build_pairs(tr_w)
    V1, V2, VY = build_pairs(te_w)
    print(f"pairs: train={len(Y)} val={len(VY)}  (win={WIN}, neg_min={NEG_MIN}ft)  build {time.time()-t0:.1f}s", flush=True)
    if len(Y) < 100 or len(VY) < 50:
        print("insufficient pairs -> smoke FAIL"); raise SystemExit(1)
    dev = torch.device(DEVICE)
    m = Siam().to(dev); opt = torch.optim.Adam(m.parameters(), 1e-3); lossf = nn.BCEWithLogitsLoss()
    Xt1 = torch.tensor(X1); Xt2 = torch.tensor(X2); Yt = torch.tensor(Y)
    for ep in range(EPOCHS):
        m.train(); perm = torch.randperm(len(Yt)); tot = 0.0
        for i in range(0, len(Yt), BATCH):
            b = perm[i:i + BATCH]
            opt.zero_grad()
            out = m(Xt1[b].to(dev), Xt2[b].to(dev))
            l = lossf(out, Yt[b].to(dev)); l.backward(); opt.step(); tot += float(l) * len(b)
        m.eval()
        with torch.no_grad():
            vp = m(torch.tensor(V1).to(dev), torch.tensor(V2).to(dev)).cpu().numpy()
        acc = float(np.mean((vp > 0) == (VY > 0.5)))
        from sklearn.metrics import roc_auc_score
        auc = float(roc_auc_score(VY, vp)) if len(set(VY.tolist())) > 1 else float('nan')
        print(f"  epoch {ep}: train_loss={tot/len(Yt):.4f} val_acc={acc:.3f} val_auc={auc:.3f}", flush=True)
    import json
    json.dump(dict(pairs_train=len(Y), pairs_val=len(VY), val_acc=acc, val_auc=auc,
                   win=WIN, neg_min=NEG_MIN, epochs=EPOCHS, device=DEVICE,
                   runtime_s=round(time.time() - t0, 1)), open(OUT, 'w'), indent=1)
    print(f"\nsmoke done in {time.time()-t0:.1f}s -> {OUT}")
    print("GATE: val_auc must be clearly > 0.5 for the learned scorer to be worth a DP/top-K integration.")
