"""N3 — coarse-to-fine multi-scale GR matching (diagnostic, no Kaggle, no submission).

The earlier local-window GR scorer line was closed with a named cause: a ~34x vertical scale mismatch in
the pairing. G3.2's docstring claims it fixed this ("MATCHED EXTENT") by making the horizontal side a
point feature. Measured on the same eval wells, the mismatch is still there:

    median TVT extent spanned by G3.2's 33-row horizontal window : 0.537 ft
    G3.2's typewell window (TWH=8, STEP=1)                       : 17 ft      -> ~32x

So the horizontal side sees ~0.5 ft of section while the typewell side is asked about 17 ft. This script
sweeps the vertical scale on the typewell side to find where the discriminative structure actually lives.

Decomposition: undecimated (a-trous) Haar, which PRESERVES LENGTH -- essential because `tfeat` indexes the
profile by state s, so a decimated DWT would break the state grid. Level j has scale 2^j ft:
    A_{j+1}[n] = (A_j[n] + A_j[n - 2^j]) / 2      (edge-replicated)
    D_{j+1}    = A_j - A_{j+1}
pywt is not installed in this environment, hence the explicit implementation.

Phase A answers the task question: AUC per level under G3.2's exact protocol (HW=16, TWH=8), with both
hand-coded scores (no training) and the same tiny MLP (comparable to G3.2's 0.7242).
Phase B tests the extent-mismatch hypothesis directly by sweeping the typewell window TWH.

Env: MAXW_TRAIN, MAXW_EVAL, EPOCHS.
"""
import os
import glob

import numpy as np
import pandas as pd

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '12'))
EPOCHS = int(os.environ.get('EPOCHS', '8'))
STEP = 1.0
HW = 16
NLEV = 4

np.random.seed(11)


def atrous_haar(x, nlev=NLEV):
    """Undecimated Haar: returns approximations A0..A_nlev and details D1..D_nlev, all len(x)."""
    A = [np.asarray(x, float)]
    Dt = []
    for j in range(nlev):
        sh = 2 ** j
        prev = A[-1]
        shifted = np.concatenate([np.repeat(prev[0], min(sh, len(prev))), prev[:-sh]]) if sh < len(prev) \
            else np.repeat(prev[0], len(prev))
        a = 0.5 * (prev + shifted)
        A.append(a)
        Dt.append(prev - a)
    return A, Dt


def load(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR']).sort_values('TVT')
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tv = tw['TVT'].values.astype(float)
    tg = tw['GR'].fillna(tw['GR'].mean()).values.astype(float)
    grid = np.arange(np.nanmin(tv), np.nanmax(tv), STEP)
    prof = np.interp(grid, tv, tg)
    return hw, gr, grid, prof


def hfeat(gr, i, hw_rows=HW):
    a, b = max(0, i - hw_rows), min(len(gr), i + hw_rows + 1)
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


def build_pairs(wells, band_of_prof, twh, hw_rows=HW):
    """band_of_prof: prof -> the profile band to use. Returns X, Y, NCC, LVL."""
    X, Y, NCC, LVL = [], [], [], []
    rs = np.random.RandomState(7)
    for wid in wells:
        try:
            hw, gr, grid, prof = load(wid)
        except Exception:
            continue
        pb = band_of_prof(prof)
        tvt = hw['TVT'].values.astype(float)
        n = len(gr)
        for i in np.arange(hw_rows, n - hw_rows, max(1, (n - 2 * hw_rows) // 40)):
            if not np.isfinite(tvt[i]):
                continue
            s_true = int((tvt[i] - grid[0]) / STEP)
            if s_true < twh or s_true >= len(grid) - twh:
                continue
            fh = hfeat(gr, i, hw_rows)
            s_neg = s_true + int(rs.choice([-1, 1]) * rs.randint(8, 60))
            if s_neg < twh or s_neg >= len(grid) - twh:
                continue
            for s, y in ((s_true, 1.0), (s_neg, 0.0)):
                X.append(pairfeat(fh, tfeat(pb, s, twh)))
                Y.append(y)
                a, b = max(0, i - hw_rows), min(len(gr), i + hw_rows + 1)
                whz = gr[a:b]
                wt = pb[max(0, s - twh):s + twh + 1]
                m = min(len(whz), len(wt))
                zh = (whz[:m] - whz[:m].mean()) / (whz[:m].std() + 1e-6)
                zt = (wt[:m] - wt[:m].mean()) / (wt[:m].std() + 1e-6)
                NCC.append(float(np.mean(zh * zt)))
                LVL.append(-abs(float(whz.mean()) - float(wt.mean())))
    return (np.array(X, np.float32), np.array(Y, np.float32),
            np.array(NCC), np.array(LVL))


def learned_auc(X, Y, epochs=EPOCHS):
    import torch
    import torch.nn as nn
    from sklearn.metrics import roc_auc_score
    mu, sd = X.mean(0), X.std(0) + 1e-6
    Xn = (X - mu) / sd
    perm = np.random.RandomState(0).permutation(len(Y))
    tr, va = perm[:int(0.8 * len(Y))], perm[int(0.8 * len(Y)):]
    torch.manual_seed(0)
    torch.set_num_threads(2)
    net = nn.Sequential(nn.Linear(X.shape[1], 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    lf = nn.BCEWithLogitsLoss()
    Xt, Yt = torch.tensor(Xn), torch.tensor(Y)
    for _ in range(epochs):
        net.train()
        p = torch.randperm(len(tr))
        for k in range(0, len(tr), 512):
            b = torch.tensor(tr)[p[k:k + 512]]
            opt.zero_grad()
            lf(net(Xt[b]).squeeze(-1), Yt[b]).backward()
            opt.step()
    net.eval()
    with torch.no_grad():
        return float(roc_auc_score(Y[va], net(Xt[torch.tensor(va)]).squeeze(-1).numpy()))


def main():
    from sklearn.metrics import roc_auc_score
    wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    train_w = wids[:MAXW_TRAIN]
    print(f'train wells {len(train_w)} (same split as G3.2)', flush=True)

    # scale context
    ex = []
    for w in train_w[:12]:
        d = pd.read_csv(f'{D}/{w}__horizontal_well.csv', usecols=['TVT'])['TVT'].values.astype(float)
        ex.append(np.nanmedian([abs(d[i + HW] - d[i - HW]) for i in range(HW, len(d) - HW, 50)]))
    print(f'median TVT extent of the {2*HW+1}-row horizontal window: {np.median(ex):.3f} ft'
          f'   (G3.2 typewell window at TWH=8 is 17 ft -> ~{17/max(np.median(ex),1e-9):.0f}x)', flush=True)

    print('\n=== PHASE A: AUC per decomposition level, G3.2 protocol (HW=16, TWH=8) ===')
    print('%-14s %6s %10s %10s %10s' % ('band', 'scale', 'NCC', 'level', 'LEARNED'))
    bands = [('A0 (raw)', 1, lambda p: atrous_haar(p)[0][0])]
    for j in range(1, NLEV + 1):
        bands.append((f'A{j} approx', 2 ** j, (lambda jj: (lambda p: atrous_haar(p)[0][jj]))(j)))
    for j in range(1, NLEV + 1):
        bands.append((f'D{j} detail', 2 ** j, (lambda jj: (lambda p: atrous_haar(p)[1][jj - 1]))(j)))
    res = []
    for name, sc, fn in bands:
        X, Y, NCC, LVL = build_pairs(train_w, fn, twh=8)
        perm = np.random.RandomState(0).permutation(len(Y))
        va = perm[int(0.8 * len(Y)):]
        a_ncc = roc_auc_score(Y[va], NCC[va])
        a_lvl = roc_auc_score(Y[va], LVL[va])
        a_lrn = learned_auc(X, Y)
        res.append((name, sc, a_ncc, a_lvl, a_lrn))
        print('%-14s %5dft %10.4f %10.4f %10.4f' % (name, sc, a_ncc, a_lvl, a_lrn), flush=True)
    print('\nG3.2 single-scale reference: LEARNED 0.7242, NCC 0.5010, level 0.6423')
    bestA = max([r for r in res if r[0].startswith('A')], key=lambda r: r[4])
    print(f'best approximation band: {bestA[0]} (scale {bestA[1]} ft) LEARNED {bestA[4]:.4f}')

    print('\n=== PHASE B: typewell window sweep at the best band (extent-match test) ===')
    fn_best = dict((n, f) for n, _, f in bands)[bestA[0]]
    print('%-10s %8s %10s %10s' % ('TWH', 'window', 'NCC', 'LEARNED'))
    bres = []
    for twh in [1, 2, 4, 8, 16, 32]:
        X, Y, NCC, LVL = build_pairs(train_w, fn_best, twh=twh)
        perm = np.random.RandomState(0).permutation(len(Y))
        va = perm[int(0.8 * len(Y)):]
        a_ncc = roc_auc_score(Y[va], NCC[va])
        a_lrn = learned_auc(X, Y)
        bres.append((twh, a_ncc, a_lrn))
        print('%-10d %7dft %10.4f %10.4f' % (twh, 2 * twh + 1, a_ncc, a_lrn), flush=True)
    bb = max(bres, key=lambda r: r[2])
    print(f'\nbest TWH={bb[0]} (window {2*bb[0]+1} ft) LEARNED {bb[2]:.4f}')
    print('GATE: a level must exceed G3.2 0.7242 to be handed to N1 as the scorer input.')


if __name__ == '__main__':
    main()
