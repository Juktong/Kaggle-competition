"""N9 — self-correlation: the lateral's own known zone as the matching template.

Question: can a toe row be located in TVT by matching its GR against the well's OWN known-zone GR, rather
than against the typewell? The mechanism is that a horizontal well re-crosses similar stratigraphic levels
along the lateral, so toe GR can match prefix GR recorded at the same TVT. Unlike the typewell, the prefix
shares one instrument and one baseline with the target rows, so the cross-instrument level offset — the
cue N3 showed dominates — is removed by construction.

ONE-FACTOR COMPARISON. Everything is held at N3's protocol: same candidate state grid (from the typewell's
TVT range), same pair sampling, same features, same tiny MLP, same TWH. The ONLY change is where the
profile comes from:
    typewell arm : prof[s] = typewell GR interpolated at TVT = grid[s]      (N3's control)
    self arm     : prof[s] = mean GR of PREFIX rows whose TVT falls in bin s
    both arm     : the two feature blocks concatenated

Splits are BY WELL, never by pair — N3 established that a random pair split mis-ranks configurations and
understates absolute AUC, because pairs from one well share a typewell and a GR baseline.

Measured coverage (200 wells, 963,869 toe rows): 63.5% of toe rows have a prefix row within 0.5 ft of
their true TVT, 67.4% within 2 ft, 84.8% within 10 ft; 61.8% fall inside the prefix TVT range at all.
13% of wells have under 10% of toe rows in range — for those the mechanism cannot apply.

Env: MAXW_TRAIN, MAXW_EVAL, TWH, EPOCHS.
"""
import os
import sys
import glob

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import n3_multiscale_gr_matching as N3  # noqa: E402

D = N3.D
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
TWH = int(os.environ.get('TWH', '1'))          # N3's best typewell window
EPOCHS = int(os.environ.get('EPOCHS', '8'))
STEP = N3.STEP
HW = N3.HW


def load_full(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR']).sort_values('TVT')
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tv = tw['TVT'].values.astype(float)
    tg = tw['GR'].fillna(tw['GR'].mean()).values.astype(float)
    grid = np.arange(np.nanmin(tv), np.nanmax(tv), STEP)
    prof_tw = np.interp(grid, tv, tg)
    # ---- self profile: prefix GR binned by its own known TVT, on the SAME grid ----
    kn = hw['TVT_input'].notna().values
    ptvt = hw['TVT_input'].values[kn].astype(float)
    pgr = gr[kn]
    idx = np.clip(np.round((ptvt - grid[0]) / STEP).astype(int), 0, len(grid) - 1)
    acc = np.zeros(len(grid))
    cnt = np.zeros(len(grid))
    np.add.at(acc, idx, pgr)
    np.add.at(cnt, idx, 1.0)
    covered = cnt > 0
    prof_self = np.where(covered, acc / np.maximum(cnt, 1), np.nan)
    if covered.sum() >= 2:
        prof_self = pd.Series(prof_self).interpolate(limit_direction='both').values
    else:
        prof_self = np.full(len(grid), float(np.nanmean(pgr)))
    return hw, gr, grid, prof_tw, prof_self, covered, kn


def build(wells, arm):
    """Pairs under N3's protocol; `arm` selects the profile source."""
    X, Y, LVL, COV = [], [], [], []
    rs = np.random.RandomState(7)
    for wid in wells:
        try:
            hw, gr, grid, prof_tw, prof_self, covered, kn = load_full(wid)
        except Exception:
            continue
        tvt = hw['TVT'].values.astype(float)
        n = len(gr)
        toe = ~kn
        for i in np.arange(HW, n - HW, max(1, (n - 2 * HW) // 40)):
            if not np.isfinite(tvt[i]) or not toe[i]:
                continue                                   # score TOE rows only
            s_true = int((tvt[i] - grid[0]) / STEP)
            if s_true < TWH or s_true >= len(grid) - TWH:
                continue
            fh = N3.hfeat(gr, i, HW)
            s_neg = s_true + int(rs.choice([-1, 1]) * rs.randint(8, 60))
            if s_neg < TWH or s_neg >= len(grid) - TWH:
                continue
            for s, y in ((s_true, 1.0), (s_neg, 0.0)):
                f_tw = N3.pairfeat(fh, N3.tfeat(prof_tw, s, TWH))
                f_se = N3.pairfeat(fh, N3.tfeat(prof_self, s, TWH))
                X.append({'typewell': f_tw, 'self': f_se,
                          'both': np.concatenate([f_tw, f_se])}[arm])
                Y.append(y)
                src = prof_tw if arm == 'typewell' else prof_self
                a, b = max(0, i - HW), min(len(gr), i + HW + 1)
                LVL.append(-abs(float(gr[a:b].mean())
                                - float(src[max(0, s - TWH):s + TWH + 1].mean())))
                COV.append(bool(covered[min(s, len(covered) - 1)]))
    return (np.array(X, np.float32), np.array(Y, np.float32),
            np.array(LVL), np.array(COV))


def main():
    from sklearn.metrics import roc_auc_score
    import torch
    import torch.nn as nn

    wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, va_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print(f'train wells {len(tr_w)} | validation wells {len(va_w)} (DISJOINT)  TWH={TWH}')

    def fit(arm, seed=0):
        Xtr, Ytr, _, _ = build(tr_w, arm)
        Xva, Yva, LVLva, COVva = build(va_w, arm)
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
        torch.manual_seed(seed)
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
        with torch.no_grad():
            pv = net(torch.tensor(((Xva - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
        out = dict(auc=roc_auc_score(Yva, pv), lvl=roc_auc_score(Yva, LVLva),
                   n=len(Yva), cov=float(COVva.mean()))
        if 0 < COVva.mean() < 1 and len(set(Yva[COVva])) == 2:
            out['auc_cov'] = roc_auc_score(Yva[COVva], pv[COVva])
            out['auc_unc'] = (roc_auc_score(Yva[~COVva], pv[~COVva])
                              if len(set(Yva[~COVva])) == 2 else float('nan'))
        return out

    print('\n=== held-out-WELL AUC, N3 protocol, only the template source changes ===')
    print('%-12s %10s %10s %10s %12s %12s' % ('arm', 'LEARNED', 'level', 'cov frac',
                                              'AUC|covered', 'AUC|uncov'))
    res = {}
    for arm in ['typewell', 'self', 'both']:
        r = fit(arm)
        res[arm] = r
        print('%-12s %10.4f %10.4f %10.4f %12s %12s'
              % (arm, r['auc'], r['lvl'], r['cov'],
                 ('%.4f' % r['auc_cov']) if 'auc_cov' in r else '   n/a',
                 ('%.4f' % r['auc_unc']) if 'auc_unc' in r else '   n/a'))
    print('\nN3 banked baselines (same split, same protocol): typewell TWH=1 LEARNED 0.7655 +/- 0.0030,'
          '\n                                                  no-training level score 0.7352')
    print('\nseed stability of the leading self/both arm:')
    best = max(['self', 'both'], key=lambda a: res[a]['auc'])
    seeds = [fit(best, seed=s)['auc'] for s in range(3)]
    print('  %s: %s  -> mean %.4f std %.4f'
          % (best, ' '.join('%.4f' % s for s in seeds), np.mean(seeds), np.std(seeds)))
    print('\nGATE: the self arm must beat the typewell arm to be worth carrying forward.')


if __name__ == '__main__':
    main()
