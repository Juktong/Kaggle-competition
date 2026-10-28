"""New-direction probe: is TVT recoverable as (well geometry) + (a slowly-varying apparent dip)?

TVT is a stratigraphic thickness, so along a known well path it satisfies
    dTVT = -dZ + tan(delta) * dH
with dZ and dH known EXACTLY at every row (X/Y/Z/MD are test-available) and delta the local apparent
dip along the well azimuth. If delta were near-constant per well, TVT would reduce to a 2-parameter
object and the prediction problem would collapse.

This probe measures the honest version (dip fitted on the KNOWN prefix only) against the flat anchor,
and reports the oracle (whole-well dip) as an upper bound of the single-dip family.
Run: python3 scripts/nds_geometry_reparam_probe.py   (CPU, ~2 min, no Kaggle, no quota)
"""
import glob, os, numpy as np, pandas as pd

DATA = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii'


def main():
    ws = sorted(set(os.path.basename(p).split('__')[0]
                    for p in glob.glob(f'{DATA}/train/*__horizontal_well.csv')))
    res = []
    for w in ws:
        d = pd.read_csv(f'{DATA}/train/{w}__horizontal_well.csv')
        md, x, y, z, tvt, ti = (d[c].values.astype(float)
                                for c in ['MD', 'X', 'Y', 'Z', 'TVT', 'TVT_input'])
        if np.isnan(tvt).any():
            continue
        known = ~np.isnan(ti); toe = ~known
        if known.sum() < 30 or toe.sum() < 30:
            continue
        h = np.concatenate([[0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
        r = tvt + z                                  # stratigraphic residual, geometry removed
        fit = lambda m: np.linalg.lstsq(np.c_[h[m], np.ones(int(np.sum(m)))], r[m], rcond=None)[0]
        idx = np.where(known)[0]
        tail = np.zeros(len(d), bool); tail[idx[int(0.7 * len(idx)):]] = True
        cP, cR, cO = fit(known), fit(tail), fit(np.ones(len(d), bool))
        geom = lambda c: -z + (c[0] * h + c[1])
        f = lambda p: float(np.sqrt(np.mean((p[toe] - tvt[toe]) ** 2)))
        res.append(dict(w=w, n_toe=int(toe.sum()),
                        flat=f(np.full(len(d), tvt[known][-1])),
                        zero_dip=f(-z + r[known][-1]),
                        prefix_dip=f(geom(cP)), recency_dip=f(geom(cR)), oracle_dip=f(geom(cO))))
    df = pd.DataFrame(res)
    tot = lambda k: float(np.sqrt(np.average(df[k] ** 2, weights=df.n_toe)))
    print('wells evaluated', len(df))
    print('\nrow-weighted RMSE on hidden toe rows')
    for k, lab in [('flat', 'flat anchor (carry last known TVT)'),
                   ('zero_dip', 'geometry only, zero dip'),
                   ('prefix_dip', 'geometry + prefix-fit constant dip  [HONEST]'),
                   ('recency_dip', 'geometry + dip fit on last 30% of prefix [HONEST]'),
                   ('oracle_dip', 'geometry + ORACLE whole-well dip  [upper bound]')]:
        print('  %-46s %9.4f' % (lab, tot(k)))
    print('\nprefix_dip beats flat on %.1f%% of wells; recency_dip on %.1f%%'
          % (100 * (df.prefix_dip < df.flat).mean(), 100 * (df.recency_dip < df.flat).mean()))
    return df


if __name__ == '__main__':
    main()
