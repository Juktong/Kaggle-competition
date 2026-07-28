"""Q10 — turn N3's TWH=1 scorer gain into an actual TVT candidate via a DP, or show that it does not.

The open signal (N3): narrowing the typewell window from TWH=8 (17 ft) to TWH=1 (3 ft) raised held-out-WELL
scorer AUC from 0.7300 +/- 0.0028 to 0.7655 +/- 0.0030. That is an EMISSION improvement.

The standing counter-evidence (N1): with a TWH=8 emission the beam DP does NOT beat the flat anchor once
the transition hyper-parameter is chosen nested — pooled held-out DP 13.644 vs flat-anchor 12.722 on 40
wells, beating flat on only 37.5% of them. N1 concluded the gap is in the TRANSITION model, not the
emission, and withdrew G3.2's "DP beats flat" claim.

Q10 is therefore a direct one-factor test of N1's conclusion: hold the DP, the wells, the protocol and the
nesting fixed, and change ONLY the emission's TWH. If N1 is right, a +0.036 AUC emission should not rescue
the DP.

Protocol, fixed by the standing rules established this round:
  - splits BY WELL, never by pair (N3: a pair split mis-ranks configurations and understates AUC);
  - >= 40 eval wells (N1: a 12-well eval set manufactured a 25% apparent gain that vanished at 40);
  - every transition hyper-parameter chosen NESTED — selected on one half of the eval wells, scored on the
    disjoint half, both ways (project rule: a parameter sweep is not a validation).

Env: MAXW_TRAIN, MAXW_EVAL, EPOCHS, TWHS, LAMS.
"""
import os
import glob
from collections import defaultdict

import numpy as np
import pandas as pd

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
EPOCHS = int(os.environ.get('EPOCHS', '8'))
TWHS = [int(x) for x in os.environ.get('TWHS', '1,8').split(',')]
LAMS = [float(x) for x in os.environ.get('LAMS', '1,2,5,10,20,60').split(',')]
STEP = 1.0
HW = 16
BAND = 60
K = 6
SUB = 10

np.random.seed(11)


def load(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv',
                     usecols=['MD', 'X', 'Y', 'Z', 'GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR']).sort_values('TVT')
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tv = tw['TVT'].values.astype(float)
    tg = tw['GR'].fillna(tw['GR'].mean()).values.astype(float)
    grid = np.arange(np.nanmin(tv), np.nanmax(tv), STEP)
    return hw, gr, grid, np.interp(grid, tv, tg), round(float(np.nanmax(tv)), 1)


def hfeat(gr, i):
    a, b = max(0, i - HW), min(len(gr), i + HW + 1)
    w = gr[a:b]
    return np.array([w.mean(), w.std(), gr[i], w.max() - w.min(),
                     (w[len(w) // 2:].mean() - w[:len(w) // 2].mean())], float)


def tfeat(prof, s, twh):
    a, b = max(0, s - twh), min(len(prof), s + twh + 1)
    w = prof[a:b]
    if len(w) < 3:
        w = prof[max(0, s - 1):s + 2]
    g = np.gradient(w) if len(w) > 2 else np.zeros(len(w))
    return np.array([w.mean(), w.std(), prof[min(s, len(prof) - 1)], w.max() - w.min(), g.mean()], float)


def pairfeat(fh, ft):
    d = fh - ft
    return np.concatenate([fh, ft, d, [abs(d[0]), abs(d[2])]])


def train_scorer(wells, twh, epochs=EPOCHS, seed=0):
    import torch
    import torch.nn as nn
    from sklearn.metrics import roc_auc_score
    X, Y = [], []
    rs = np.random.RandomState(7)
    for wid in wells:
        try:
            hw, gr, grid, prof, _ = load(wid)
        except Exception:
            continue
        tvt = hw['TVT'].values.astype(float)
        n = len(gr)
        for i in np.arange(HW, n - HW, max(1, (n - 2 * HW) // 40)):
            if not np.isfinite(tvt[i]):
                continue
            s_true = int((tvt[i] - grid[0]) / STEP)
            if s_true < twh or s_true >= len(grid) - twh:
                continue
            fh = hfeat(gr, i)
            s_neg = s_true + int(rs.choice([-1, 1]) * rs.randint(8, 60))
            if s_neg < twh or s_neg >= len(grid) - twh:
                continue
            for s, y in ((s_true, 1.0), (s_neg, 0.0)):
                X.append(pairfeat(fh, tfeat(prof, s, twh)))
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
    for _ in range(epochs):
        net.train()
        p = torch.randperm(len(Yt))
        for k in range(0, len(Yt), 512):
            b = p[k:k + 512]
            opt.zero_grad()
            lf(net(Xt[b]).squeeze(-1), Yt[b]).backward()
            opt.step()
    net.eval()
    return net, mu, sd


def scorer_auc(net, mu, sd, wells, twh):
    """Held-out-WELL AUC on disjoint wells."""
    import torch
    from sklearn.metrics import roc_auc_score
    X, Y = [], []
    rs = np.random.RandomState(7)
    for wid in wells:
        try:
            hw, gr, grid, prof, _ = load(wid)
        except Exception:
            continue
        tvt = hw['TVT'].values.astype(float)
        n = len(gr)
        for i in np.arange(HW, n - HW, max(1, (n - 2 * HW) // 40)):
            if not np.isfinite(tvt[i]):
                continue
            s_true = int((tvt[i] - grid[0]) / STEP)
            if s_true < twh or s_true >= len(grid) - twh:
                continue
            fh = hfeat(gr, i)
            s_neg = s_true + int(rs.choice([-1, 1]) * rs.randint(8, 60))
            if s_neg < twh or s_neg >= len(grid) - twh:
                continue
            for s, y in ((s_true, 1.0), (s_neg, 0.0)):
                X.append(pairfeat(fh, tfeat(prof, s, twh)))
                Y.append(y)
    X = np.array(X, np.float32)
    Y = np.array(Y, np.float32)
    with torch.no_grad():
        p = net(torch.tensor(((X - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
    return float(roc_auc_score(Y, p))


def prep(wid, net, mu, sd, twh):
    import torch
    hw, gr, grid, prof, gkey = load(wid)
    kn = hw['TVT_input'].notna().values
    if kn.sum() < 100 or (~kn).sum() < 200:
        return None
    toe = np.where(~kn)[0][::SUB]
    if len(toe) < 20:
        return None
    tru = hw['TVT'].values.astype(float)[toe]
    anchor = float(hw['TVT_input'].values[kn][-1])
    S = len(grid)
    TF = np.stack([tfeat(prof, s, twh) for s in range(S)])
    C = np.empty((len(toe), S), float)
    with torch.no_grad():
        for j, i in enumerate(toe):
            fh = hfeat(gr, i)
            F = np.concatenate([np.repeat(fh[None], S, 0), TF, fh[None] - TF,
                                np.abs(fh[0] - TF[:, 0])[:, None],
                                np.abs(fh[2] - TF[:, 2])[:, None]], 1)
            c = -net(torch.tensor(((F - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
            C[j] = (c - c.mean()) / (c.std() + 1e-9)
    return dict(wid=wid, gkey=gkey, grid=grid, C=C, tru=tru, anchor=anchor, S=S,
                flat=float(np.sqrt(np.mean((anchor - tru) ** 2))))


def run_dp(P, lam):
    """G3.2's beam DP: emission + lam*|state change| / BAND, symmetric +/-BAND search."""
    C, S, grid = P['C'], P['S'], P['grid']
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    beams = [([s0], 0.0)]
    for j in range(len(C)):
        cand = []
        for path, cost in beams:
            s = path[-1]
            lo, hi = max(0, s - BAND), min(S, s + BAND + 1)
            step = C[j, lo:hi] + lam * np.abs(np.arange(lo, hi) - s) / BAND
            for t in np.argsort(step)[:K]:
                cand.append((path + [lo + int(t)], cost + float(step[t])))
        cand.sort(key=lambda v: v[1])
        seen, beams = set(), []
        for p_, c_ in cand:
            if p_[-1] in seen:
                continue
            seen.add(p_[-1])
            beams.append((p_, c_))
            if len(beams) >= K:
                break
    top1 = grid[np.clip(np.array(beams[0][0][1:]), 0, S - 1)]
    return float(np.sqrt(np.mean((top1 - P['tru']) ** 2)))


def main():
    wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print(f'train wells {len(tr_w)} | eval wells {len(ev_w)} (DISJOINT)  TWHS={TWHS}  LAMS={LAMS}',
          flush=True)

    out = {}
    for twh in TWHS:
        net, mu, sd = train_scorer(tr_w, twh)
        auc = scorer_auc(net, mu, sd, ev_w, twh)
        print(f'\n=== TWH={twh}: held-out-WELL scorer AUC = {auc:.4f} ===', flush=True)
        P = [p for p in (prep(w, net, mu, sd, twh) for w in ev_w) if p is not None]
        flat = np.sqrt(np.mean([p['flat'] ** 2 for p in P]))
        per = {lam: np.array([run_dp(p, lam) for p in P]) for lam in LAMS}
        print('  %-8s %s' % ('lam', ''.join('%9.3f' % np.sqrt(np.mean(per[l] ** 2)) for l in LAMS)))
        print('  %-8s %s' % ('', ''.join('%9s' % ('lam=%g' % l) for l in LAMS)))
        print('  flat-anchor on these %d wells: %.3f' % (len(P), flat))
        # ---- nested 2-fold: lam chosen on one half, scored on the disjoint half ----
        n = len(P)
        idx = np.arange(n)
        folds = [(idx[:n // 2], idx[n // 2:]), (idx[n // 2:], idx[:n // 2])]
        held, held_flat, picks = [], [], []
        fl_pw = np.array([p['flat'] for p in P])
        for sel, rep in folds:
            best = min(LAMS, key=lambda l: np.sqrt(np.mean(per[l][sel] ** 2)))
            picks.append(best)
            held.append(per[best][rep])
            held_flat.append(fl_pw[rep])
            print('    select on %2d -> lam=%-5g | held-out %2d: DP %7.3f  flat %7.3f'
                  % (len(sel), best, len(rep), np.sqrt(np.mean(per[best][rep] ** 2)),
                     np.sqrt(np.mean(fl_pw[rep] ** 2))))
        hd = np.sqrt(np.mean(np.concatenate(held) ** 2))
        hf = np.sqrt(np.mean(np.concatenate(held_flat) ** 2))
        beats = float(np.mean(np.concatenate(held) < np.concatenate(held_flat)))
        print('  NESTED POOLED: DP %.3f  flat %.3f  -> %s  (beats flat on %.1f%% of wells)'
              % (hd, hf, 'BEATS flat' if hd < hf else 'does NOT beat flat', 100 * beats))
        out[twh] = dict(auc=auc, nested_dp=hd, nested_flat=hf, beats=beats,
                        per_well=np.concatenate(held), per_flat=np.concatenate(held_flat),
                        wells=[P[i]['wid'] for f in folds for i in f[1]],
                        gkeys=[P[i]['gkey'] for f in folds for i in f[1]], picks=picks)

    print('\n=== SUMMARY: does the better emission rescue the DP? ===')
    print('%-6s %10s %12s %12s %14s' % ('TWH', 'AUC', 'nested DP', 'flat', 'beats flat %'))
    for twh in TWHS:
        r = out[twh]
        print('%-6d %10.4f %12.3f %12.3f %13.1f%%'
              % (twh, r['auc'], r['nested_dp'], r['nested_flat'], 100 * r['beats']))
    print('\nN1 reference (TWH=8, same protocol): nested DP 13.644 vs flat 12.722, beats flat 37.5%')
    print('Deployed honest line ~8.86. GATE: must beat flat AND materially narrow the gap to deployed.')

    # ---- failure analysis by typewell group key ----
    best_twh = min(TWHS, key=lambda t: out[t]['nested_dp'])
    r = out[best_twh]
    df = pd.DataFrame(dict(well=r['wells'], gkey=r['gkeys'],
                           dp=r['per_well'], flat=r['per_flat']))
    df['gain'] = df.flat - df.dp
    print(f'\n=== failure cases, TWH={best_twh} (gain = flat - DP; negative means the DP hurt) ===')
    print('  wells helped %d / hurt %d' % ((df.gain > 0).sum(), (df.gain <= 0).sum()))
    print('  worst 5:')
    for _, x in df.nsmallest(5, 'gain').iterrows():
        print('    %-10s gkey %-10.1f DP %7.3f flat %7.3f gain %+7.3f' % (x.well, x.gkey, x.dp, x.flat, x.gain))
    print('  best 5:')
    for _, x in df.nlargest(5, 'gain').iterrows():
        print('    %-10s gkey %-10.1f DP %7.3f flat %7.3f gain %+7.3f' % (x.well, x.gkey, x.dp, x.flat, x.gain))
    g = df.groupby('gkey').agg(n=('gain', 'size'), mean_gain=('gain', 'mean'))
    g = g[g.n >= 2].sort_values('mean_gain')
    if len(g):
        print('  by typewell group key (groups with >=2 eval wells):')
        print(g.round(3).to_string())


if __name__ == '__main__':
    main()
