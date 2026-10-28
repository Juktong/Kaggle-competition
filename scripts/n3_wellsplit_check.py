"""N3 follow-up: is the TWH=32 gain real, or an artifact of the random PAIR split?

G3.2's protocol (inherited here for comparability) splits PAIRS at random, so pairs from the same well
appear in both train and validation. This re-runs the key comparison with disjoint WELLS.
"""
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
tr_w, va_w = wids[:60], wids[60:100]          # disjoint wells; val wells are the G3.2 eval pool
raw = lambda p: M.atrous_haar(p)[0][0]

def fit_eval(twh, seed=0):
    Xtr, Ytr, _, _ = M.build_pairs(tr_w, raw, twh=twh)
    Xva, Yva, NCCva, LVLva = M.build_pairs(va_w, raw, twh=twh)
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
    return (roc_auc_score(Yva, pv), roc_auc_score(Yva, NCCva), roc_auc_score(Yva, LVLva), len(Yva))

print('train wells %d | validation wells %d (DISJOINT)' % (len(tr_w), len(va_w)))
print('%-6s %10s %10s %10s %10s' % ('TWH', 'window', 'LEARNED', 'NCC', 'level'))
out = {}
for twh in [1, 4, 8, 16, 32, 64]:
    a, n, l, npair = fit_eval(twh)
    out[twh] = a
    print('%-6d %9dft %10.4f %10.4f %10.4f   (val pairs %d)' % (twh, 2*twh+1, a, n, l, npair), flush=True)
print()
print('pair-split (leaky) said: TWH=8 -> 0.7160, TWH=32 -> 0.7476  (delta +0.0316)')
print('well-split says        : TWH=8 -> %.4f, TWH=32 -> %.4f  (delta %+.4f)'
      % (out[8], out[32], out[32] - out[8]))
# seed stability of the winner
seeds = [fit_eval(32, seed=s)[0] for s in range(3)]
print('TWH=32 well-split AUC across 3 seeds: %s  (std %.4f)'
      % (' '.join('%.4f' % s for s in seeds), float(np.std(seeds))))
