"""N7 — quasi-3D wellbore tortuosity as a predictor of our honest line's per-well error.

PROVENANCE NOTE (read before citing these numbers). The task specifies implementing from
Jing, J., Ye, W., Cao, C., Ran, X. (2022), "Actual wellbore tortuosity evaluation using a new
quasi-three-dimensional approach", Petroleum 8, 118-127. **The paper's full text could not be retrieved
in this environment** (ScienceDirect returns HTTP 403; the DOI guess resolves to a different article).
What is implemented here follows the principles stated in the paper's abstract -- a "Peak-Valley"
decomposition of the trajectory into oscillation segments, and indices incorporating both the amplitude
and the frequency of fluctuation, computed separately in the inclination and azimuth planes and then
combined -- but it is **our implementation of those principles, not a verified reproduction of the
paper's exact equations**. No code was copied from any third-party repository.

To keep the conclusion from hinging on one formula, a FAMILY of tortuosity measures is computed
(industry-standard dogleg severity, plane-separated accumulated angular change, and Peak-Valley
amplitude/frequency indices). If none of them predicts per-well error, the direction closes regardless of
which exact index the paper intends.

All inputs are MD/X/Y/Z only, so every quantity is test-available on the full well including the toe
(only TVT is hidden at test time).

Run: SMOKE_N=40 python3 scripts/n7_q3d_tortuosity.py     (smoke)
     python3 scripts/n7_q3d_tortuosity.py                (all wells + the decisive correlation test)
"""
import os
import glob

import numpy as np
import pandas as pd

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
SMOKE_N = int(os.environ.get('SMOKE_N', '0'))
MIN_PROM = float(os.environ.get('MIN_PROM', '0.5'))     # degrees, turning-point prominence
# Survey-station spacing (ft). The raw data is on a 1 ft MD grid with ~0.01 ft XY resolution, so angles
# differenced at 1 ft are dominated by coordinate quantization: a 0.01 ft lateral wobble over a 1 ft step
# is ~0.6 deg of spurious azimuth swing. The first smoke exposed this directly -- dogleg severity came out
# at ~49 deg/100ft (physically impossible; real DLS is 0-15) and the median detected oscillation amplitude
# sat exactly at the 0.5 deg detection threshold with one "oscillation" every ~2 ft. Real directional
# surveys are taken every 30-100 ft, so the trajectory is resampled to STATION_FT before any angle is
# computed. STATION_FT is swept in the report rather than fixed by assumption.
STATION_FT = float(os.environ.get('STATION_FT', '30'))


def _angles(md, x, y, z):
    """Inclination (deg from vertical) and unwrapped azimuth (deg) from successive XYZ deltas."""
    dx, dy, dz = np.diff(x), np.diff(y), np.diff(z)
    ds = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
    ok = ds > 1e-9
    inc = np.full(len(ds), np.nan)
    inc[ok] = np.degrees(np.arccos(np.clip(-dz[ok] / ds[ok], -1, 1)))   # Z is elevation, down is -Z
    azi = np.full(len(ds), np.nan)
    h = np.hypot(dx, dy)
    m = h > 1e-9
    azi[m] = np.degrees(np.arctan2(dy[m], dx[m]))
    azi = pd.Series(azi).interpolate(limit_direction='both').values
    inc = pd.Series(inc).interpolate(limit_direction='both').values
    azi = np.degrees(np.unwrap(np.radians(azi)))
    return inc, azi, ds, md[1:]


def _peak_valley(sig, md, min_prom=MIN_PROM):
    """Peak-Valley decomposition: turning points with at least `min_prom` degrees of swing.

    Returns per-segment amplitudes (deg) and wavelengths (ft) between consecutive turning points.
    A simple prominence filter suppresses measurement chatter so that only real oscillations count.
    """
    if len(sig) < 3:
        return np.array([]), np.array([])
    turns = [0]
    direction = 0
    last = sig[0]
    for i in range(1, len(sig)):
        d = sig[i] - last
        if abs(d) < min_prom:
            continue
        s = 1 if d > 0 else -1
        if direction == 0:
            direction = s
        elif s != direction:
            turns.append(i - 1)
            direction = s
        last = sig[i]
    turns.append(len(sig) - 1)
    turns = np.array(sorted(set(turns)))
    if len(turns) < 2:
        return np.array([]), np.array([])
    amp = np.abs(np.diff(sig[turns]))
    lam = np.abs(np.diff(md[turns]))
    keep = (amp >= min_prom) & (lam > 0)
    return amp[keep], lam[keep]


def _plane_indices(sig, md, ds_total, tag):
    """Accumulated angular change + Peak-Valley amplitude/frequency indices for one plane."""
    out = {}
    total_change = float(np.nansum(np.abs(np.diff(sig))))
    out[f'T_{tag}'] = 100.0 * total_change / max(ds_total, 1e-9)          # deg per 100 ft
    amp, lam = _peak_valley(sig, md)
    n = len(amp)
    out[f'nseg_{tag}'] = n
    if n == 0:
        out[f'Gamma_{tag}'] = 0.0
        out[f'freq_{tag}'] = 0.0
        out[f'amp_med_{tag}'] = 0.0
        out[f'TQG_{tag}'] = 0.0
        return out
    # amplitude concentration: large when a few big swings dominate the total swing
    out[f'Gamma_{tag}'] = float(np.sum(amp ** 2) / max(np.sum(amp), 1e-9))
    out[f'freq_{tag}'] = 1000.0 * n / max(ds_total, 1e-9)                 # oscillations per 1000 ft
    out[f'amp_med_{tag}'] = float(np.median(amp))
    # combined index incorporating amplitude AND frequency, per the abstract's stated principle
    out[f'TQG_{tag}'] = float(out[f'T_{tag}'] * out[f'Gamma_{tag}'] * np.sqrt(out[f'freq_{tag}']))
    return out


def well_tortuosity(wid, toe_only=True):
    d = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['MD', 'X', 'Y', 'Z', 'TVT_input'])
    md = d['MD'].values.astype(float)
    x, y, z = (d[c].values.astype(float) for c in ['X', 'Y', 'Z'])
    known = d['TVT_input'].notna().values
    if toe_only:
        i0 = int(np.where(known)[0][-1]) if known.any() else 0
        md, x, y, z = md[i0:], x[i0:], y[i0:], z[i0:]
    if len(md) < 5:
        return None
    # resample to survey-station spacing before differencing (see STATION_FT note above)
    if STATION_FT > 1.0:
        grid = np.arange(md[0], md[-1], STATION_FT)
        if len(grid) < 5:
            return None
        x, y, z = (np.interp(grid, md, v) for v in (x, y, z))
        md = grid
    inc, azi, ds, md_s = _angles(md, x, y, z)
    L = float(np.nansum(ds))
    r = dict(well=wid, span_ft=L)
    r.update(_plane_indices(inc, md_s, L, 'incline'))
    r.update(_plane_indices(azi, md_s, L, 'azimuth'))
    r['TQG_Q3D'] = float(np.hypot(r['TQG_incline'], r['TQG_azimuth']))
    # industry-standard dogleg severity, as an independent reference measure
    a1, a2 = np.radians(inc[:-1]), np.radians(inc[1:])
    p1, p2 = np.radians(azi[:-1]), np.radians(azi[1:])
    dl = np.degrees(np.arccos(np.clip(np.cos(a1) * np.cos(a2)
                                      + np.sin(a1) * np.sin(a2) * np.cos(p2 - p1), -1, 1)))
    seg = np.maximum(ds[1:], 1e-9)
    dls = 100.0 * dl / seg
    r['dls_mean'] = float(np.nanmean(dls))
    r['dls_p90'] = float(np.nanpercentile(dls, 90))
    r['dls_max'] = float(np.nanmax(dls))
    return r


def main():
    wids = sorted(os.path.basename(p).split('__')[0]
                  for p in glob.glob(f'{D}/*__horizontal_well.csv'))
    if SMOKE_N:
        wids = wids[:SMOKE_N]
    rows = [r for r in (well_tortuosity(w) for w in wids) if r is not None]
    T = pd.DataFrame(rows)
    feats = [c for c in T.columns if c not in ('well',)]
    print(f'wells {len(T)}  (SMOKE_N={SMOKE_N})')
    print('\n=== sanity: are the indices finite and scale-sane? ===')
    print(T[feats].describe().loc[['min', '50%', 'max']].T.round(4).to_string())
    bad = {c: int((~np.isfinite(T[c])).sum()) for c in feats}
    print('non-finite counts:', {k: v for k, v in bad.items() if v} or 'none')
    T.to_csv(f'{SH}/n7_tortuosity.csv', index=False)
    print(f'wrote {SH}/n7_tortuosity.csv')

    if SMOKE_N:
        print('\n(smoke only -- rerun without SMOKE_N for the correlation test)')
        return

    # ---- the decisive test: does tortuosity predict our honest line's per-well error? ----
    U = pd.read_csv(f'{SH}/n4_well_uncertainty.csv')
    M = U.merge(T, on='well', how='inner')
    print(f'\n=== correlation vs the banked per-well honest OOF RMSE ({len(M)} wells) ===')
    print('%-18s %9s %10s' % ('feature', 'pearson', 'spearman'))
    for c in feats:
        a, b = M[c].values, M.rmse.values
        m = np.isfinite(a) & np.isfinite(b)
        if m.sum() < 50 or np.nanstd(a[m]) < 1e-12:
            continue
        print('%-18s %9.4f %10.4f'
              % (c, np.corrcoef(a[m], b[m])[0, 1],
                 pd.Series(a[m]).corr(pd.Series(b[m]), method='spearman')))

    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import KFold
    N4_FEATS = ['nnb', 'closest_surv', 'prefix_frac', 'toe_md', 'prefix_md', 'well_md',
                'gr_std', 'gr_std_toe', 'mean_incl', 'tortuosity']
    N4_FEATS = [c for c in N4_FEATS if c in M.columns]
    ylog = np.log(M.rmse.values)

    def cv_r2(cols):
        X = M[cols].replace([np.inf, -np.inf], np.nan).fillna(M[cols].median()).values
        oof = np.zeros(len(M))
        for tr, te in KFold(5, shuffle=True, random_state=0).split(X):
            g = GradientBoostingRegressor(random_state=0, n_estimators=200, max_depth=2,
                                          learning_rate=0.05).fit(X[tr], ylog[tr])
            oof[te] = g.predict(X[te])
        return 1 - float(np.sum((ylog - oof) ** 2)) / float(np.sum((ylog - ylog.mean()) ** 2))

    print('\n=== 5-fold CV R^2 on log(per-well OOF RMSE) -- N4 measured 0.0736 for its feature set ===')
    print('  N4 feature set alone          : %.4f' % cv_r2(N4_FEATS))
    print('  tortuosity family alone       : %.4f' % cv_r2(feats))
    print('  N4 + tortuosity               : %.4f' % cv_r2(N4_FEATS + feats))
    print('\nGATE: the tortuosity family must beat 0.0736 to justify touching the model.')


if __name__ == '__main__':
    main()
