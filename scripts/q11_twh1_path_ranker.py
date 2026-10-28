"""Q11 — rank stored PF candidate paths with TWH=1 alignment summaries, instead of generating paths.

Why this shape. Every pointwise-DP formulation tried so far (G3.1, G3.2, N1, Q10) generates a trajectory
from a per-row emission and lands far from the deployed honest line. Q11 keeps the PF motion model and its
path proposals and only *chooses among them*.

The headroom is real and, unusually, better than deployed (760 wells, pooled row-weighted RMSE on toe rows):

    PF mean path (the default)   10.9905
    median path of the 96        12.4375
    ORACLE best-of-96             7.1579     <- beats deployed honest 8.8626
    worst-of-96                  22.1407
    deployed honest 54844628      8.8626
    ORACLE headroom vs PF mean   +3.8326      worst-case risk -11.1502

The standing counter-evidence. The ledger records a prior top-K ranker over these same paths that reached
only **+0.1492** pooled — 3.9% of the oracle headroom — and was NOT submitted (5th percentile negative,
45.7% of wells hurt, no guard constructible). Its feature set (loglik, w, lik_rank, smooth, jumps,
total_move, dir_changes, seam, out_of_range, d_dwt, d_struct, d_mean, n_eval, heel_drift) contained **no
alignment-to-typewell score at all**. That is exactly what Q11 adds.

So the question is one-factor: do TWH=1 alignment summaries convert materially more of the +3.83 headroom
than the prior feature set did?

Efficiency note: the scorer emission C[row, state] is computed ONCE per well over all states, then each of
the 96 paths simply indexes into it — so scoring 96 paths costs no more than scoring one.

Arms: PF mean (default) | ranker on PRIOR features | ranker on TWH1 features | ranker on BOTH | oracle.
Splits are BY WELL. Env: MAXW_TRAIN, MAXW_EVAL, EPOCHS, TWH, SUB.
"""
import os
import glob

import numpy as np
import pandas as pd

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
EPOCHS = int(os.environ.get('EPOCHS', '8'))
TWH = int(os.environ.get('TWH', '1'))
SUB = int(os.environ.get('SUB', '10'))
STEP = 1.0
HW = 16

PRIOR_FEATS = ['loglik', 'w', 'lik_rank', 'smooth', 'jumps', 'total_move', 'dir_changes',
               'seam', 'out_of_range', 'd_dwt', 'd_struct', 'd_mean', 'n_eval', 'heel_drift']
TWH1_FEATS = ['al_mean', 'al_p10', 'al_p25', 'al_p75', 'al_std', 'al_worst',
              'al_prefix_gap', 'al_smooth', 'al_range_press', 'al_vs_meanpath']


def load(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR']).sort_values('TVT')
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tv = tw['TVT'].values.astype(float)
    tg = tw['GR'].fillna(tw['GR'].mean()).values.astype(float)
    grid = np.arange(np.nanmin(tv), np.nanmax(tv), STEP)
    return hw, gr, grid, np.interp(grid, tv, tg)


def hfeat(gr, i):
    a, b = max(0, i - HW), min(len(gr), i + HW + 1)
    w = gr[a:b]
    return np.array([w.mean(), w.std(), gr[i], w.max() - w.min(),
                     (w[len(w) // 2:].mean() - w[:len(w) // 2].mean())], float)


def tfeat(prof, s, twh=TWH):
    a, b = max(0, s - twh), min(len(prof), s + twh + 1)
    w = prof[a:b]
    if len(w) < 3:
        w = prof[max(0, s - 1):s + 2]
    g = np.gradient(w) if len(w) > 2 else np.zeros(len(w))
    return np.array([w.mean(), w.std(), prof[min(s, len(prof) - 1)], w.max() - w.min(), g.mean()], float)


def pairfeat(fh, ft):
    d = fh - ft
    return np.concatenate([fh, ft, d, [abs(d[0]), abs(d[2])]])


def train_scorer(wells, seed=0):
    import torch
    import torch.nn as nn
    X, Y = [], []
    rs = np.random.RandomState(7)
    for wid in wells:
        try:
            hw, gr, grid, prof = load(wid)
        except Exception:
            continue
        tvt = hw['TVT'].values.astype(float)
        n = len(gr)
        for i in np.arange(HW, n - HW, max(1, (n - 2 * HW) // 40)):
            if not np.isfinite(tvt[i]):
                continue
            s_true = int((tvt[i] - grid[0]) / STEP)
            if s_true < TWH or s_true >= len(grid) - TWH:
                continue
            fh = hfeat(gr, i)
            s_neg = s_true + int(rs.choice([-1, 1]) * rs.randint(8, 60))
            if s_neg < TWH or s_neg >= len(grid) - TWH:
                continue
            for s, y in ((s_true, 1.0), (s_neg, 0.0)):
                X.append(pairfeat(fh, tfeat(prof, s)))
                Y.append(y)
    X = np.array(X, np.float32)
    Y = np.array(Y, np.float32)
    mu, sd = X.mean(0), X.std(0) + 1e-6
    torch.manual_seed(seed)
    torch.set_num_threads(2)
    net = nn.Sequential(nn.Linear(X.shape[1], 64), nn.ReLU(),
                        nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    lf = nn.BCEWithLogitsLoss()
    Xt, Yt = torch.tensor((X - mu) / sd), torch.tensor(Y)
    for _ in range(EPOCHS):
        net.train()
        p = torch.randperm(len(Yt))
        for k in range(0, len(Yt), 512):
            b = p[k:k + 512]
            opt.zero_grad()
            lf(net(Xt[b]).squeeze(-1), Yt[b]).backward()
            opt.step()
    net.eval()
    return net, mu, sd


def path_features(wid, net, mu, sd):
    """TWH=1 alignment summaries for each stored PF path of one well."""
    import torch
    p = f'{SH}/topk96_paths/{wid}.npz'
    if not os.path.exists(p):
        return None
    z = np.load(p)
    ridx = z['ridx'].astype(int)
    paths = z['paths'].astype(np.float64)          # (96, n_toe)
    meanp = z['mean'].astype(np.float64)
    truth = z['truth'].astype(np.float64)
    try:
        hw, gr, grid, prof = load(wid)
    except Exception:
        return None
    kn = hw['TVT_input'].notna().values
    if kn.sum() < 50:
        return None
    anchor = float(hw['TVT_input'].values[kn][-1])
    sel = np.arange(0, len(ridx), SUB)
    rows = ridx[sel]
    S = len(grid)
    # emission computed ONCE over all states; every path just indexes into it
    TF = np.stack([tfeat(prof, s) for s in range(S)])
    C = np.empty((len(sel), S), float)
    with torch.no_grad():
        for j, i in enumerate(rows):
            fh = hfeat(gr, min(i, len(gr) - 1))
            F = np.concatenate([np.repeat(fh[None], S, 0), TF, fh[None] - TF,
                                np.abs(fh[0] - TF[:, 0])[:, None],
                                np.abs(fh[2] - TF[:, 2])[:, None]], 1)
            sc = net(torch.tensor(((F - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
            C[j] = (sc - sc.mean()) / (sc.std() + 1e-9)     # higher = better match

    def summarise(tvt_path):
        st = np.round((tvt_path[sel] - grid[0]) / STEP).astype(int)
        clipped = (st < 0) | (st >= S)
        st = np.clip(st, 0, S - 1)
        v = C[np.arange(len(sel)), st]
        d = np.diff(tvt_path[sel])
        return dict(al_mean=v.mean(), al_p10=np.percentile(v, 10), al_p25=np.percentile(v, 25),
                    al_p75=np.percentile(v, 75), al_std=v.std(), al_worst=v.min(),
                    al_prefix_gap=abs(tvt_path[0] - anchor),
                    al_smooth=float(np.mean(np.abs(d))),
                    al_range_press=float(clipped.mean()),
                    al_vs_meanpath=float(np.mean(np.abs(tvt_path[sel] - meanp[sel]))))

    rows_out = []
    for k in range(paths.shape[0]):
        f = summarise(paths[k])
        f.update(well=wid, seed=k,
                 path_rmse=float(np.sqrt(np.mean((paths[k] - truth) ** 2))))
        rows_out.append(f)
    mf = summarise(meanp)
    return (pd.DataFrame(rows_out),
            dict(well=wid, n=len(ridx),
                 mean_rmse=float(np.sqrt(np.mean((meanp - truth) ** 2))),
                 mean_al=mf['al_mean']))


def main():
    from sklearn.ensemble import GradientBoostingRegressor
    wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print(f'train wells {len(tr_w)} | eval wells {len(ev_w)} (DISJOINT)  TWH={TWH} SUB={SUB}', flush=True)

    net, mu, sd = train_scorer(tr_w)
    print('scorer trained', flush=True)

    PRIOR = pd.read_csv(f'{SH}/topk96_feat.csv')
    PRIOR = PRIOR[PRIOR.seed >= 0]

    frames, meta = [], []
    for n, wid in enumerate(tr_w + ev_w):
        if n % 20 == 0:
            print(f'  [{n}/{len(tr_w) + len(ev_w)}]', flush=True)
        r = path_features(wid, net, mu, sd)
        if r is None:
            continue
        frames.append(r[0])
        meta.append(r[1])
    A = pd.concat(frames, ignore_index=True)
    M = pd.DataFrame(meta).set_index('well')
    A = A.merge(PRIOR[['well', 'seed'] + PRIOR_FEATS], on=['well', 'seed'], how='inner')
    print(f'\npath rows {len(A)} over {A.well.nunique()} wells', flush=True)

    # per-well standardised target: lower path_rmse is better
    A['tgt'] = A.groupby('well').path_rmse.transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))
    tr = A[A.well.isin(tr_w)]
    ev = A[A.well.isin(ev_w)]
    ev_wells = sorted(ev.well.unique())
    nr = M.loc[ev_wells, 'n'].values.astype(float)

    def pooled(per_well):
        return float(np.sqrt(np.average(np.asarray(per_well) ** 2, weights=nr)))

    ref_mean = pooled(M.loc[ev_wells, 'mean_rmse'].values)
    ref_best = pooled([ev[ev.well == w].path_rmse.min() for w in ev_wells])
    ref_worst = pooled([ev[ev.well == w].path_rmse.max() for w in ev_wells])
    print('\n=== eval-well references (pooled row-weighted) ===')
    print('  PF mean path (default) %8.4f | ORACLE best %8.4f | worst %8.4f'
          % (ref_mean, ref_best, ref_worst))
    print('  deployed honest 8.8626 | flat-anchor is not defined for these path sets')

    print('\n=== ranker arms, selection on HELD-OUT wells ===')
    print('%-22s %10s %12s %14s %12s' % ('feature set', 'pooled', 'vs PF mean', 'headroom used', 'wells helped'))
    res = {}
    for name, feats in [('prior (14)', PRIOR_FEATS),
                        ('TWH1 (10)', TWH1_FEATS),
                        ('both (24)', PRIOR_FEATS + TWH1_FEATS)]:
        Xtr = tr[feats].replace([np.inf, -np.inf], np.nan).fillna(0).values
        g = GradientBoostingRegressor(random_state=0, n_estimators=300, max_depth=3,
                                      learning_rate=0.05).fit(Xtr, tr.tgt.values)
        Xev = ev[feats].replace([np.inf, -np.inf], np.nan).fillna(0).values
        ev = ev.assign(pred=g.predict(Xev))
        pick = ev.loc[ev.groupby('well').pred.idxmin()]
        pick = pick.set_index('well').loc[ev_wells]
        sel_rmse = pick.path_rmse.values
        p = pooled(sel_rmse)
        helped = float(np.mean(sel_rmse < M.loc[ev_wells, 'mean_rmse'].values))
        res[name] = (p, sel_rmse)
        print('%-22s %10.4f %12.4f %13.1f%% %11.1f%%'
              % (name, p, ref_mean - p, 100 * (ref_mean - p) / max(ref_mean - ref_best, 1e-9), 100 * helped))
    print('\nprior ledger: the earlier top-K ranker reached +0.1492 pooled and still failed the gate')
    print('              (5th pct negative, 45.7%% of wells hurt, no guard constructible)')

    # 3-well gate on the best arm vs the PF mean default
    best = min(res, key=lambda k: res[k][0])
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from eval_three_well_gate import three_well_gate
    gains = M.loc[ev_wells, 'mean_rmse'].values - res[best][1]
    print(f'\n=== per-well gain of the best arm ({best}) vs the PF mean default ===')
    print('  mean %+.4f median %+.4f std %.4f | helped %.1f%% hurt %.1f%%'
          % (gains.mean(), np.median(gains), gains.std(),
             100 * np.mean(gains > 0), 100 * np.mean(gains < 0)))
    rs = np.random.RandomState(7)
    b3 = np.array([np.average(gains[rs.randint(0, len(gains), 3)]) for _ in range(20000)])
    print('  3-WELL bootstrap of the mean gain: 5th %+.4f 50th %+.4f 95th %+.4f  P(gain>0) %.4f'
          % (*np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
    print('\nGATE: must convert materially more headroom than the prior +0.1492 AND survive the 3-well scale.')


if __name__ == '__main__':
    main()
