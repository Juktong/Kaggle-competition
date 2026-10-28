"""Q12 — coverage-gated self-correlation: is there a WELL-LEVEL coverage band where self wins?

What N9 already settled (do not re-derive):
  - self template AUC 0.7174 on prefix-COVERED states vs 0.4548 on uncovered -> interpolation is harmful;
  - but even restricted to covered states, self (0.7174) still trails the typewell (0.7710);
  - and `both` (typewell + self features) reaches 0.7680 on covered states, still below typewell alone.

So the state-level coverage gate was already measured by N9 and does not rescue the self template. What
N9 did NOT measure is a WELL-LEVEL gate: coverage is pooled across wells in N9, so a subpopulation of
high-coverage wells could still favour self without showing up in the pooled figure. That is the only
open form of the idea, and it is what Q12 tests.

The gate is test-available: per-well prefix coverage is the fraction of candidate TVT states that the
well's own known prefix visits, computable from `TVT_input` alone with no truth.

Design: identical to N9 (same grid, sampling, features, MLP, TWH=1, toe rows only, splits BY WELL). The
only addition is that AUC is computed PER WELL and stratified by that well's coverage.

Env: MAXW_TRAIN, MAXW_EVAL, EPOCHS, TWH.
"""
import os
import sys
import glob

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import n9_self_correlation as N9  # noqa: E402

D = N9.D
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '60'))
EPOCHS = int(os.environ.get('EPOCHS', '8'))
TWH = N9.TWH
STEP = N9.STEP
HW = N9.HW


def build_one(wid, arm):
    """N9's pair construction for a single well, plus that well's coverage fraction."""
    try:
        hw, gr, grid, prof_tw, prof_self, covered, kn = N9.load_full(wid)
    except Exception:
        return None
    X, Y = [], []
    rs = np.random.RandomState(7)
    tvt = hw['TVT'].values.astype(float)
    n = len(gr)
    toe = ~kn
    for i in np.arange(HW, n - HW, max(1, (n - 2 * HW) // 40)):
        if not np.isfinite(tvt[i]) or not toe[i]:
            continue
        s_true = int((tvt[i] - grid[0]) / STEP)
        if s_true < TWH or s_true >= len(grid) - TWH:
            continue
        fh = N9.N3.hfeat(gr, i, HW)
        s_neg = s_true + int(rs.choice([-1, 1]) * rs.randint(8, 60))
        if s_neg < TWH or s_neg >= len(grid) - TWH:
            continue
        for s, y in ((s_true, 1.0), (s_neg, 0.0)):
            f_tw = N9.N3.pairfeat(fh, N9.N3.tfeat(prof_tw, s, TWH))
            f_se = N9.N3.pairfeat(fh, N9.N3.tfeat(prof_self, s, TWH))
            X.append({'typewell': f_tw, 'self': f_se,
                      'both': np.concatenate([f_tw, f_se])}[arm])
            Y.append(y)
    if len(Y) < 20 or len(set(Y)) < 2:
        return None
    return np.array(X, np.float32), np.array(Y, np.float32), float(covered.mean())


def main():
    from sklearn.metrics import roc_auc_score
    import torch
    import torch.nn as nn

    wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print(f'train wells {len(tr_w)} | eval wells {len(ev_w)} (DISJOINT)  TWH={TWH}', flush=True)

    rows = []
    for arm in ['typewell', 'self', 'both']:
        Xtr, Ytr, _, _ = N9.build(tr_w, arm)
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
        torch.manual_seed(0)
        torch.set_num_threads(2)
        net = nn.Sequential(nn.Linear(Xtr.shape[1], 64), nn.ReLU(),
                            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        lf = nn.BCEWithLogitsLoss()
        Xt, Yt = torch.tensor((Xtr - mu) / sd), torch.tensor(Ytr)
        for _ in range(EPOCHS):
            net.train()
            p = torch.randperm(len(Yt))
            for k in range(0, len(Yt), 512):
                b = p[k:k + 512]
                opt.zero_grad()
                lf(net(Xt[b]).squeeze(-1), Yt[b]).backward()
                opt.step()
        net.eval()
        print(f'  {arm}: scorer trained', flush=True)
        for wid in ev_w:
            r = build_one(wid, arm)
            if r is None:
                continue
            Xv, Yv, cov = r
            with torch.no_grad():
                pv = net(torch.tensor(((Xv - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
            rows.append(dict(well=wid, arm=arm, auc=float(roc_auc_score(Yv, pv)),
                             cov=cov, npairs=len(Yv)))
    A = pd.DataFrame(rows)
    P = A.pivot(index='well', columns='arm', values='auc').dropna()
    P['cov'] = A.groupby('well')['cov'].first().reindex(P.index)
    print(f'\nper-well AUC table: {len(P)} eval wells')
    print('\n=== pooled over wells (mean of per-well AUC) ===')
    for a in ['typewell', 'self', 'both']:
        print('  %-10s %.4f' % (a, P[a].mean()))

    print('\n=== stratified by the well-level prefix-coverage gate (test-available) ===')
    print('%-16s %6s %10s %10s %10s %14s %12s' % ('coverage band', 'n', 'typewell', 'self', 'both',
                                                  'self-typewell', 'both-typewell'))
    P['band'] = pd.qcut(P['cov'], 5, duplicates='drop')
    for b, g in P.groupby('band', observed=True):
        print('%-16s %6d %10.4f %10.4f %10.4f %14.4f %12.4f'
              % (f'{b.left:.2f}-{b.right:.2f}', len(g), g['typewell'].mean(), g['self'].mean(),
                 g['both'].mean(), (g['self'] - g['typewell']).mean(), (g['both'] - g['typewell']).mean()))

    print('\n=== is there ANY coverage threshold where self or both wins? ===')
    print('%-10s %6s %14s %14s' % ('cov >=', 'wells', 'self-typewell', 'both-typewell'))
    for thr in [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        g = P[P['cov'] >= thr]
        if len(g) < 5:
            continue
        print('%-10.2f %6d %14.4f %14.4f'
              % (thr, len(g), (g['self'] - g['typewell']).mean(), (g['both'] - g['typewell']).mean()))
    print('\n  wells where self beats typewell: %.1f%%   both beats typewell: %.1f%%'
          % (100 * (P['self'] > P['typewell']).mean(), 100 * (P['both'] > P['typewell']).mean()))
    print('  corr(coverage, self-typewell) = %.4f' % P['cov'].corr(P['self'] - P['typewell']))
    print('  corr(coverage, both-typewell) = %.4f' % P['cov'].corr(P['both'] - P['typewell']))
    P.to_csv('/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/q12_per_well_auc.csv')
    print('\nGATE: a coverage band must show self or both beating typewell to justify a gated candidate.')


if __name__ == '__main__':
    main()
