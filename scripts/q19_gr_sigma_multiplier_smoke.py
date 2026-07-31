"""Q19 smoke — the one-token GR-sigma widening found in a public kernel, tested honestly.

FIND. `leonidzaporozhets/new-strategy-score-6-213` advertises public 6.213 against our 6.563. Its
notebook is byte-identical to our own upstream base (`kaggle_kernel_kaiwalya_public_tvt_6626_repro`) on
44 of 45 code cells after whitespace/comment normalisation. The single functional difference is one token
in the PF likelihood:

    gs = float(np.clip(np.nanstd(kn.GR.fillna(0).values - tw_at_k), 10., 60.))         # ours
    gs = float(np.clip(np.nanstd(kn.GR.fillna(0).values - tw_at_k), 10., 60.)) * 1.3   # theirs

`gs` is the GR noise sigma in the PF likelihood (`d = (gr - expected) / gs`). Multiplying it widens the
assumed measurement noise, flattening the likelihood — a SHRINKAGE/regularisation change, which is the
class the project ledger records as transferring (Rule #1: averaging and shrinkage transfer; hard
selection and fitted weights do not). That makes it worth honest evaluation rather than dismissal.

WHY TEST IT LOCALLY RATHER THAN TRUST 6.213. The advertised number is a single 3-well public draw, and
Q18 measured that pooled gaps <= 0.30 reverse on ~45% of random 3-well draws. Our own honest PF
(`scripts/pf_honest_forward.py:22`) contains the IDENTICAL sigma line, so the same knob can be measured
on 760 train wells with truth, split BY WELL and nested — evidence of a completely different quality
than an advertised leaderboard number.

Protocol: splits BY WELL; the multiplier is chosen NESTED (selected on one half of the eval wells,
scored on the disjoint half, both ways), per the standing rule that a sweep is not a validation.

Env: MAXW (wells), MULTS, SEEDS, SMOKE.
"""
import glob
import os

import numpy as np
import pandas as pd

import pf_honest_forward as PFH

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MAXW = int(os.environ.get('MAXW', '60'))
MULTS = [float(x) for x in os.environ.get('MULTS', '1.0,1.15,1.3,1.5,2.0').split(',')]
SEEDS = int(os.environ.get('SEEDS', '1'))


def run_well(wid, mult, seed):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv',
                     usecols=['MD', 'X', 'Y', 'Z', 'GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR'])
    ev = hw['TVT_input'].isna().values
    if ev.sum() < 20 or (~ev).sum() < 50:
        return None
    # patch the module-level sigma by scaling inside a wrapper: re-implement the one line via monkeypatch
    PFH._GS_MULT = mult
    pred, _ = PFH.run_particle_filter(hw, tw, seed=seed)
    truth = hw['TVT'].values.astype(float)
    m = ev & np.isfinite(truth) & np.isfinite(pred)
    if m.sum() < 20:
        return None
    return float(np.sum((pred[m] - truth[m]) ** 2)), int(m.sum())


def main():
    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    wids = wids[:MAXW]
    print('wells %d | multipliers %s | seeds %d' % (len(wids), MULTS, SEEDS), flush=True)

    sse = {m: [] for m in MULTS}
    cnt = {m: [] for m in MULTS}
    kept = []
    for wid in wids:
        row = {}
        ok = True
        for m in MULTS:
            acc_s, acc_n = 0.0, 0
            for s in range(SEEDS):
                r = run_well(wid, m, 42 + s)
                if r is None:
                    ok = False
                    break
                acc_s += r[0]
                acc_n += r[1]
            if not ok:
                break
            row[m] = (acc_s, acc_n)
        if not ok:
            continue
        kept.append(wid)
        for m in MULTS:
            sse[m].append(row[m][0])
            cnt[m].append(row[m][1])
    n = len(kept)
    print('usable wells: %d' % n, flush=True)
    if n < 4:
        print('too few wells for a nested split; smoke inconclusive')
        return

    S = {m: np.array(sse[m]) for m in MULTS}
    C = {m: np.array(cnt[m]) for m in MULTS}
    print('\n%-10s %12s %14s' % ('multiplier', 'pooled RMSE', 'vs mult=1.0'))
    base = np.sqrt(S[1.0].sum() / C[1.0].sum()) if 1.0 in S else float('nan')
    for m in MULTS:
        r = np.sqrt(S[m].sum() / C[m].sum())
        print('%-10g %12.4f %14.4f' % (m, r, base - r))

    # per-well win rate of the best non-unit multiplier
    pw = {m: np.sqrt(S[m] / C[m]) for m in MULTS}
    for m in MULTS:
        if m == 1.0:
            continue
        d = pw[1.0] - pw[m]
        print('  mult %-5g helps %.1f%% of wells | mean per-well gain %+.4f' %
              (m, 100 * np.mean(d > 0), d.mean()))

    # nested 2-fold selection BY WELL
    idx = np.arange(n)
    folds = [(idx[:n // 2], idx[n // 2:]), (idx[n // 2:], idx[:n // 2])]
    held, held_base, picks = [], [], []
    for sel, rep in folds:
        best = min(MULTS, key=lambda m: np.sqrt(S[m][sel].sum() / C[m][sel].sum()))
        picks.append(best)
        held.append((S[best][rep], C[best][rep]))
        held_base.append((S[1.0][rep], C[1.0][rep]))
    hs = np.concatenate([h[0] for h in held]); hc = np.concatenate([h[1] for h in held])
    bs = np.concatenate([h[0] for h in held_base]); bc = np.concatenate([h[1] for h in held_base])
    nested = float(np.sqrt(hs.sum() / hc.sum()))
    nbase = float(np.sqrt(bs.sum() / bc.sum()))
    print('\nNESTED (multiplier chosen on one half, scored on the disjoint half; picks %s)' % picks)
    print('  nested selected %.4f   vs mult=1.0 %.4f   gain %+.4f' % (nested, nbase, nbase - nested))

    # 3-well bootstrap on the nested per-well gains
    gw = np.sqrt(bs / bc) - np.sqrt(hs / hc)
    rs = np.random.RandomState(7)
    b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('  3-WELL bootstrap of the nested gain: 5th %+.4f  50th %+.4f  95th %+.4f  P(gain>0) %.4f'
          % (*np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
    print('\nGATE: promote to a frontier kernel run only if the nested gain is positive AND the 3-well')
    print('      bootstrap 5th percentile > 0.')


if __name__ == '__main__':
    main()
