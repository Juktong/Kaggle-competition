"""Seed-stability of the N3 headline: TWH=1 vs TWH=8 (G3.2's value) on DISJOINT wells."""
import os, sys, glob
import numpy as np
sys.path.insert(0, '/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue/scripts')
os.environ.setdefault('MAXW_TRAIN', '60')
import n3_multiscale_gr_matching as M
from sklearn.metrics import roc_auc_score
import torch, torch.nn as nn

D = M.D
wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng = np.random.RandomState(11); rng.shuffle(wids)
tr_w, va_w = wids[:60], wids[60:100]
raw = lambda p: M.atrous_haar(p)[0][0]

cache = {}
def data(twh):
    if twh not in cache:
        cache[twh] = (M.build_pairs(tr_w, raw, twh=twh), M.build_pairs(va_w, raw, twh=twh))
    return cache[twh]

def fit(twh, seed):
    (Xtr, Ytr, _, _), (Xva, Yva, _, LVLva) = data(twh)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    torch.manual_seed(seed); torch.set_num_threads(2)
    net = nn.Sequential(nn.Linear(Xtr.shape[1], 64), nn.ReLU(),
                        nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
    opt = torch.optim.Adam(net.parameters(), 1e-3); lf = nn.BCEWithLogitsLoss()
    Xt, Yt = torch.tensor((Xtr - mu) / sd), torch.tensor(Ytr)
    for _ in range(8):
        net.train(); p = torch.randperm(len(Yt))
        for k in range(0, len(Yt), 512):
            b = p[k:k + 512]
            opt.zero_grad(); lf(net(Xt[b]).squeeze(-1), Yt[b]).backward(); opt.step()
    net.eval()
    with torch.no_grad():
        pv = net(torch.tensor(((Xva - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
    return roc_auc_score(Yva, pv), roc_auc_score(Yva, LVLva)

print('%-6s %-10s %s' % ('TWH', 'metric', 'seeds 0..4 -> mean +/- std'))
res = {}
for twh in [1, 8]:
    a = [fit(twh, s)[0] for s in range(5)]
    lv = fit(twh, 0)[1]
    res[twh] = (np.mean(a), np.std(a), lv)
    print('%-6d %-10s %s  ->  %.4f +/- %.4f' % (twh, 'LEARNED', ' '.join('%.4f' % v for v in a),
                                                np.mean(a), np.std(a)))
    print('%-6d %-10s %.4f  (no training)' % (twh, 'level', lv))
d = res[1][0] - res[8][0]
pooled = np.hypot(res[1][1], res[8][1])
print('\nTWH=1 minus TWH=8 (G3.2 value): %+.4f   seed-noise scale %.4f   ratio %.1fx'
      % (d, pooled, d / max(pooled, 1e-9)))
print('G3.2 recorded LEARNED 0.7242 on a random PAIR split of the same 60 wells.')
