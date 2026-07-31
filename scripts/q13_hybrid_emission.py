"""Q13 — typewell + coverage-gated self hybrid emission, gated on TYPEWELL UNCERTAINTY.

Two of Q13's three proposed ingredients are already settled, so this round tests only the untested one.

  ALREADY CLOSED — naive combination. Q12's `both` arm is exactly a typewell+self hybrid emission (the two
  feature blocks concatenated into one scorer): +0.0012 pooled over 60 held-out wells, beating typewell on
  51.7% of them. A coin flip.
  ALREADY CLOSED — the prefix-coverage gate. Q12 measured corr(coverage, both - typewell) = 0.0604 and
  corr(coverage, self - typewell) = 0.0867, with `self` negative in all five coverage bands. Coverage
  carries no stratifying information, so "self helps where prefix coverage is high" is disproven.

  UNTESTED — the typewell-UNCERTAINTY gate: "self helps only where the typewell score is uncertain".
  Q12/N9 never measured this because they only ever scored two candidate states per row (the true state
  and one negative), so no emission profile existed from which to compute uncertainty. This script
  computes the FULL emission profile over all states for both templates, which makes the gate measurable.

Design. Per toe row, over all candidate states:
    C_tw[row, state]  TWH=1 typewell emission        C_se[row, state]  self emission (coverage-masked)
    uncertainty u(row) = top1 - top2 margin of C_tw  (small margin = ambiguous; test-available)
    hybrid        C_h = C_tw + w * C_se * covered
The end metric is the |argmax error| in feet — how far the emission's best state sits from the true TVT —
which is what a DP actually consumes, rather than a pair-level AUC. Everything is stratified by u.

Splits are BY WELL. Env: MAXW_TRAIN, MAXW_EVAL, EPOCHS, WS.
"""
import os
import sys
import glob

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import n9_self_correlation as N9  # noqa: E402

D = N9.D
N3 = N9.N3
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
EPOCHS = int(os.environ.get('EPOCHS', '8'))
TWH = N9.TWH
STEP = N3.STEP
HW = N3.HW
SUB = int(os.environ.get('SUB', '10'))
WS = [float(x) for x in os.environ.get('WS', '0,0.25,0.5,1.0').split(',')]


def train(wells, arm, seed=0):
    import torch
    import torch.nn as nn
    X, Y, _, _ = N9.build(wells, arm)
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


def profiles(wid, nets):
    """Full emission profiles over all states for both templates, on subsampled toe rows."""
    import torch
    try:
        hw, gr, grid, prof_tw, prof_self, covered, kn = N9.load_full(wid)
    except Exception:
        return None
    tvt = hw['TVT'].values.astype(float)
    toe = np.where(~kn)[0][::SUB]
    if len(toe) < 20:
        return None
    S = len(grid)
    TF_tw = np.stack([N3.tfeat(prof_tw, s, TWH) for s in range(S)])
    TF_se = np.stack([N3.tfeat(prof_self, s, TWH) for s in range(S)])
    out = {}
    for arm, TF in (('typewell', TF_tw), ('self', TF_se)):
        net, mu, sd = nets[arm]
        C = np.empty((len(toe), S), float)
        with torch.no_grad():
            for j, i in enumerate(toe):
                fh = N3.hfeat(gr, i, HW)
                F = np.concatenate([np.repeat(fh[None], S, 0), TF, fh[None] - TF,
                                    np.abs(fh[0] - TF[:, 0])[:, None],
                                    np.abs(fh[2] - TF[:, 2])[:, None]], 1)
                v = net(torch.tensor(((F - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
                C[j] = (v - v.mean()) / (v.std() + 1e-9)      # higher = better match
        out[arm] = C
    return dict(wid=wid, grid=grid, tru=tvt[toe], covered=covered,
                anchor=float(hw['TVT_input'].values[kn][-1]),
                C_tw=out['typewell'], C_se=out['self'])


def main():
    wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print(f'train wells {len(tr_w)} | eval wells {len(ev_w)} (DISJOINT)  TWH={TWH}  WS={WS}', flush=True)

    nets = {a: train(tr_w, a) for a in ('typewell', 'self')}
    print('scorers trained', flush=True)

    rows = []
    PROF = {}
    for n, wid in enumerate(ev_w):
        if n % 10 == 0:
            print(f'  [{n}/{len(ev_w)}]', flush=True)
        P = profiles(wid, nets)
        if P is None:
            continue
        PROF[wid] = P
        grid, tru, cov = P['grid'], P['tru'], P['covered']
        Ctw, Cse = P['C_tw'], P['C_se']
        cov_row = cov[None, :].astype(float)                 # coverage mask over states
        srt = np.sort(Ctw, axis=1)
        margin = srt[:, -1] - srt[:, -2]                     # top1 - top2: small = ambiguous
        for w in WS:
            Ch = Ctw + w * Cse * cov_row
            err = np.abs(grid[np.argmax(Ch, axis=1)] - tru)
            for j in range(len(tru)):
                rows.append((wid, w, float(margin[j]), float(err[j])))
    A = pd.DataFrame(rows, columns=['well', 'w', 'margin', 'err'])
    print(f'\nrows {len(A) // len(WS)} per weight, over {A.well.nunique()} eval wells')

    base = A[A.w == 0.0].set_index(['well', A[A.w == 0.0].groupby('well').cumcount()])
    print('\n=== |argmax error| in ft, by self weight (0 = typewell only) ===')
    print('%-8s %10s %10s %10s %12s' % ('w', 'mean', 'median', 'p90', 'within 5ft'))
    for w in WS:
        g = A[A.w == w]
        print('%-8g %10.3f %10.3f %10.3f %11.3f' % (w, g.err.mean(), g.err.median(),
                                                    g.err.quantile(.9), (g.err <= 5).mean()))

    print('\n=== the UNCERTAINTY gate: does self help where the typewell emission is ambiguous? ===')
    b = A[A.w == 0.0].reset_index(drop=True)
    b['q'] = pd.qcut(b['margin'], 5, labels=False, duplicates='drop')
    print('%-22s %8s %12s %s' % ('typewell margin band', 'n', 'tw-only err',
                                 ''.join('  w=%-6g' % w for w in WS if w > 0)))
    for q in sorted(b['q'].dropna().unique()):
        m = b['q'] == q
        lo, hi = b.loc[m, 'margin'].min(), b.loc[m, 'margin'].max()
        cells = []
        for w in WS:
            if w == 0:
                continue
            gw = A[A.w == w].reset_index(drop=True)
            cells.append(gw.loc[m.values, 'err'].mean() - b.loc[m, 'err'].mean())
        print('%-22s %8d %12.3f %s'
              % (f'{lo:.2f}-{hi:.2f}', int(m.sum()), b.loc[m, 'err'].mean(),
                 ''.join('%9.3f' % c for c in cells)))
    print('  (cells are hybrid minus typewell-only mean |error|; negative = the hybrid helps)')

    bw = max([w for w in WS if w > 0])
    gw = A[A.w == bw].reset_index(drop=True)
    d = gw['err'].values - b['err'].values
    print('\n  corr(typewell margin, hybrid advantage) at w=%g : %.4f'
          % (bw, np.corrcoef(b['margin'].values, -d)[0, 1]))
    pw = pd.DataFrame(dict(well=b.well, d=d)).groupby('well').d.mean()
    print('  per-well: hybrid helps on %.1f%% of eval wells (mean delta %+.4f ft)'
          % (100 * (pw < 0).mean(), pw.mean()))
    # ---- the decision-relevant stage: does the emission gain survive a DP into a TRAJECTORY? ----
    # An |argmax error| of ~150 ft is an emission diagnostic, not a candidate. Q10's DP with the
    # typewell-only TWH=1 emission reached 12.170 against a flat anchor of 12.722 and deployed ~8.86.
    # The same DP is run here on the hybrid emission, with lam chosen NESTED on disjoint well halves.
    print('\n=== DP on the hybrid emission (Q10 transition rule, nested lam) ===', flush=True)
    BAND, K, LAMS = 60, 6, [5.0, 10.0, 20.0, 60.0, 100.0]

    def run_dp(C, grid, anchor, lam):
        S = C.shape[1]
        s0 = int(np.clip((anchor - grid[0]) / STEP, 0, S - 1))
        beams = [([s0], 0.0)]
        for j in range(len(C)):
            cand = []
            for path, cost in beams:
                s = path[-1]
                lo, hi = max(0, s - BAND), min(S, s + BAND + 1)
                step = -C[j, lo:hi] + lam * np.abs(np.arange(lo, hi) - s) / BAND
                for t in np.argsort(step)[:K]:
                    cand.append((path + [lo + int(t)], cost + float(step[t])))
            cand.sort(key=lambda v: v[1])
            seen, beams = set(), []
            for p_, c_ in cand:
                if p_[-1] in seen:
                    continue
                seen.add(p_[-1]); beams.append((p_, c_))
                if len(beams) >= K:
                    break
        return grid[np.clip(np.array(beams[0][0][1:]), 0, S - 1)]

    per = {w: {l: [] for l in LAMS} for w in WS}
    flats = []
    for n, wid in enumerate(ev_w):
        P = PROF.get(wid)
        if P is None:
            continue
        grid, tru, cov = P['grid'], P['tru'], P['covered']
        anchor = P['anchor']
        flats.append(float(np.sqrt(np.mean((anchor - tru) ** 2))))
        for w in WS:
            Ch = P['C_tw'] + w * P['C_se'] * cov[None, :].astype(float)
            for l in LAMS:
                pth = run_dp(Ch, grid, anchor, l)
                per[w][l].append(float(np.sqrt(np.mean((pth - tru) ** 2))))
    flats = np.array(flats)
    fl = float(np.sqrt(np.mean(flats ** 2)))
    print('  flat-anchor on these %d wells: %.3f  | deployed honest 8.8626 | Q10 typewell-only DP 12.170'
          % (len(flats), fl))
    print('  %-8s %s %12s' % ('w', ''.join('%9s' % ('lam=%g' % l) for l in LAMS), 'nested'))
    nn_ = len(flats); idx = np.arange(nn_)
    folds = [(idx[:nn_ // 2], idx[nn_ // 2:]), (idx[nn_ // 2:], idx[:nn_ // 2])]
    for w in WS:
        A_ = {l: np.array(per[w][l]) for l in LAMS}
        held = []
        for sel, rep in folds:
            best = min(LAMS, key=lambda l: np.sqrt(np.mean(A_[l][sel] ** 2)))
            held.append(A_[best][rep])
        hd = float(np.sqrt(np.mean(np.concatenate(held) ** 2)))
        print('  %-8g %s %12.3f' % (w, ''.join('%9.3f' % np.sqrt(np.mean(A_[l] ** 2)) for l in LAMS), hd))
    print('\nGATE: the hybrid must beat typewell-only overall, or in a gate band that the margin predicts,')
    print('      AND the emission gain must survive into a trajectory that narrows the gap to deployed.')


if __name__ == '__main__':
    main()
