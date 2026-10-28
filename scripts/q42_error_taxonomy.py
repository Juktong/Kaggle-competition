"""Q42 — error taxonomy of the deployed honest line, and the coarse-group version of Q16.

Q16 measured whether the SIGNED row-level residual of 54844628 is predictable from test-available features
on held-out wells. It is not: CV R^2 = -0.0802 by well, i.e. the fitted per-row structure ANTI-transfers.

This task asks the coarser question the prompt names explicitly: **does that change at group level?** A
group-level constant is a far lower-variance estimator than a per-row GBM, so coarsening is a real
hypothesis rather than a rephrasing. It is tested the only way that counts — estimate each group's mean
signed residual on TRAIN wells, apply it to HELD-OUT wells, and measure whether the correction helps.

Segments, all test-available:
  nnb                  structural-field neighbour count
  closest_all          distance to the closest mate well
  closest_surv         distance to the closest surviving mate
  row_frac             position within the toe (0 = heel end, 1 = toe end)
  rows_from_anchor     absolute distance from the last known row
  dwt_pf_disagree      |dwt - pf|, the two mechanisms' disagreement
  struct_contrib       how much the structural field actually moved the row
  prefix_frac          known-prefix fraction of the well            (N4 per-well)
  well_md / gr_std / mean_incl / tortuosity                          (N4 per-well)

Protocol: 5-fold GroupKFold BY WELL. Gates: nested gain > 0 AND helps a majority of wells AND 3-well
bootstrap 5th percentile > 0.

Context that sets expectations honestly: Q41 established that the 3-well 5th percentile is MAXIMISED by
leaving the deployed line unchanged and degrades monotonically with the size of any change, and that
clearing zero at n=3 needs a mean per-well gain of roughly 1.2. So the 3-well condition is expected to
fail for anything this task can produce; the informative output is the TAXONOMY and whether group-level
sign is predictable at all.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
NBINS = 5


def main():
    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    well = z['well'].astype(str)
    truth = z['truth'].astype(np.float64)
    pred = z['s_54844628'].astype(np.float64)
    resid = pred - truth                                   # SIGNED
    d = pd.DataFrame(dict(
        well=well, ridx=z['ridx'].astype(int), resid=resid,
        nnb=z['nnb'].astype(float), closest_all=z['closest_all'].astype(float),
        closest_surv=z['closest_surv'].astype(float),
        dwt_pf_disagree=np.abs(z['dwt'].astype(float) - z['pf'].astype(float)),
        struct_contrib=pred - z['base'].astype(np.float64)))
    d['row_frac'] = d.groupby('well').ridx.transform(lambda s: (s - s.min()) / max(s.max() - s.min(), 1))
    d['rows_from_anchor'] = d.groupby('well').ridx.transform(lambda s: s - s.min())
    U = pd.read_csv(f'{SH}/n4_well_uncertainty.csv')
    keep = [c for c in ['well', 'prefix_frac', 'well_md', 'gr_std', 'gr_std_toe', 'mean_incl', 'tortuosity']
            if c in U.columns]
    d = d.merge(U[keep], on='well', how='left')

    FEATS = [c for c in d.columns if c not in ('well', 'ridx', 'resid')]
    print('rows %d | wells %d | segment features %d' % (len(d), d.well.nunique(), len(FEATS)))
    print('deployed line: pooled RMSE %.4f | mean signed residual %+.4f | median %+.4f'
          % (np.sqrt(np.mean(resid ** 2)), resid.mean(), np.median(resid)))

    wells = d.well.values
    n_w = d.groupby('well').size()
    uw = np.array(sorted(d.well.unique()))
    widx = {w: i for i, w in enumerate(uw)}
    wi = np.array([widx[w] for w in wells])
    base_sse = np.bincount(wi, weights=resid ** 2, minlength=len(uw))
    cnt = np.bincount(wi, minlength=len(uw)).astype(float)

    print('\n=== 1. TAXONOMY: mean signed residual by quintile of each segment ===')
    print('%-18s %s' % ('feature', ''.join('%10s' % ('q%d' % (i + 1)) for i in range(NBINS)) + '     spread'))
    binmap = {}
    for f in FEATS:
        v = d[f].values.astype(float)
        if not np.isfinite(v).any():
            continue
        try:
            b = pd.qcut(pd.Series(v), NBINS, labels=False, duplicates='drop').values
        except Exception:
            continue
        nb = int(np.nanmax(b)) + 1 if np.isfinite(np.nanmax(b)) else 0
        if nb < 2:
            continue
        b = np.where(np.isfinite(b), b, -1).astype(int)
        binmap[f] = (b, nb)
        m = [resid[b == k].mean() if (b == k).sum() else np.nan for k in range(nb)]
        print('%-18s %s %+9.3f' % (f, ''.join('%+10.3f' % x for x in m), np.nanmax(m) - np.nanmin(m)))

    print('\n=== 2. OUT-OF-FOLD group-constant correction, GroupKFold(5) BY WELL ===')
    print('  (estimate each group mean signed residual on TRAIN wells, subtract it on HELD-OUT wells)')
    print('%-18s %10s %10s %9s %11s' % ('feature', 'OOF RMSE', 'vs base', 'helps%', '3-well 5th'))
    rs = np.random.RandomState(7)
    base_r = float(np.sqrt(np.mean(resid ** 2)))
    results = []
    for f, (b, nb) in binmap.items():
        corr = np.zeros(len(d))
        for tr, te in GroupKFold(5).split(b.reshape(-1, 1), resid, groups=wells):
            for k in range(nb):
                mtr = (b[tr] == k)
                if mtr.sum() >= 50:
                    mu = resid[tr][mtr].mean()
                    corr[te[b[te] == k]] = mu
        newr = resid - corr
        new_sse = np.bincount(wi, weights=newr ** 2, minlength=len(uw))
        oof = float(np.sqrt(new_sse.sum() / cnt.sum()))
        gw = np.sqrt(base_sse / cnt) - np.sqrt(new_sse / cnt)
        b3 = np.array([gw[rs.randint(0, len(uw), 3)].mean() for _ in range(20000)])
        p5 = np.percentile(b3, 5)
        results.append((base_r - oof, f, oof, 100 * np.mean(gw > 0), p5))
        print('%-18s %10.4f %+10.4f %8.1f%% %+11.4f' % (f, oof, base_r - oof, 100 * np.mean(gw > 0), p5))

    results.sort(reverse=True)
    print('\n=== 3. best segment, and the gate ===')
    gain, f, oof, helps, p5 = results[0]
    print('  best feature: %-16s OOF %.4f  gain %+.4f  helps %.1f%%  3-well 5th %+.4f'
          % (f, oof, gain, helps, p5))
    ok = (gain > 0) and (helps > 50) and (p5 > 0)
    print('  GATE: gain > 0 AND helps a majority AND 3-well 5th > 0  ->  %s' % ('PASS' if ok else 'FAIL'))
    print('  segments with a positive OOF gain: %d of %d' % (sum(1 for r in results if r[0] > 0), len(results)))
    print('  segments clearing the 3-well 5th:   %d of %d' % (sum(1 for r in results if r[4] > 0), len(results)))

    print('\n=== 4. does coarsening rescue Q16? group-level signed-residual R^2, OOF by well ===')
    ss_tot = float(np.sum((resid - resid.mean()) ** 2))
    for gain, f, oof, helps, p5 in results[:6]:
        b, nb = binmap[f]
        corr = np.zeros(len(d))
        for tr, te in GroupKFold(5).split(b.reshape(-1, 1), resid, groups=wells):
            for k in range(nb):
                mtr = (b[tr] == k)
                if mtr.sum() >= 50:
                    mu = resid[tr][mtr].mean()
                    corr[te[b[te] == k]] = mu
        r2 = 1 - float(np.sum((resid - corr) ** 2)) / ss_tot
        print('  %-18s OOF R^2 = %+.5f' % (f, r2))
    print('  Q16 reference (row-level GBM, same protocol): R^2 = -0.0802')


if __name__ == '__main__':
    main()
