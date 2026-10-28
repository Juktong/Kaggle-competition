"""N4 — calibrated per-well uncertainty for the honest line, by split conformal on the banked OOF.

Targets the WIDTH of the honest model's own error distribution per well, not the sign of any candidate's
harm (that was the closed anti-harm guard, AUC 0.53). The width is a better-posed quantity and admits a
distribution-free coverage guarantee.

No model is refitted. The banked nested-OOF predictions of `54844628` are read from
`aligned_preds.npz` (toe-only rows, 760 wells, pooled RMSE 8.8626 = the banked figure).

Conditioning features are TEST-AVAILABLE ONLY. Test wells expose `MD,X,Y,Z,GR,TVT_input` plus the
typewell `TVT,GR`; `nnb` and the closest-surviving-mate distance derive from neighbour X/Y, which is
also test-available. No structural surface, no `Geology`, no truth.

Splits are BY WELL, never by row: rows inside a well are strongly correlated (lag-1 residual
autocorrelation +0.9998), so a row-level split would leak and report meaningless coverage.

Run: python3 scripts/n4_conformal_well_uncertainty.py    (CPU, ~2 min, no Kaggle, no quota)
"""
import glob
import os

import numpy as np
import pandas as pd

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
TRAIN = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
TEST_WELLS = ['000d7d20', '00bbac68', '00e12e8b']
LEVELS = [0.80, 0.90, 0.95]
SEED = 0


def per_well_oof():
    """Per-well OOF RMSE of the deployed honest candidate, plus the neighbour metadata."""
    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    well = z['well'].astype(str)
    err = z['s_54844628'].astype(np.float64) - z['truth'].astype(np.float64)
    df = pd.DataFrame(dict(well=well, e2=err ** 2, ae=np.abs(err),
                           nnb=z['nnb'].astype(np.float64),
                           closest_surv=z['closest_surv'].astype(np.float64)))
    g = df.groupby('well')
    out = pd.DataFrame(dict(rmse=np.sqrt(g.e2.mean()), mae=g.ae.mean(), n_toe=g.size(),
                            nnb=g.nnb.first(), closest_surv=g.closest_surv.first()))
    return out.reset_index(), df


def well_features():
    """Test-available per-well geometry / log features."""
    rows = []
    for p in sorted(glob.glob(f'{TRAIN}/*__horizontal_well.csv')):
        w = os.path.basename(p).split('__')[0]
        d = pd.read_csv(p, usecols=['MD', 'X', 'Y', 'Z', 'GR', 'TVT_input'])
        md, x, y, z, gr = (d[c].values.astype(np.float64) for c in ['MD', 'X', 'Y', 'Z', 'GR'])
        known = d.TVT_input.notna().values
        if known.sum() < 5 or (~known).sum() < 5:
            continue
        dz, dmd = np.diff(z), np.diff(md)
        dh = np.hypot(np.diff(x), np.diff(y))
        last_known_md = md[known][-1]
        rows.append(dict(
            well=w,
            prefix_frac=float(known.mean()),
            toe_md=float(md[-1] - last_known_md),          # length of the extrapolation
            prefix_md=float(last_known_md - md[0]),
            well_md=float(md[-1] - md[0]),
            gr_std=float(np.nanstd(gr)),
            gr_std_toe=float(np.nanstd(gr[~known])),
            mean_incl=float(np.nanmean(np.abs(dz / np.where(dmd > 0, dmd, np.nan)))),
            tortuosity=float(np.nanstd(dz / np.where(dh > 1e-9, dh, np.nan))),
        ))
    return pd.DataFrame(rows)


def mondrian(cal, val, feat, nbin=4, level=0.90):
    """Mondrian (bin-conditional) split conformal on per-well RMSE.

    Bins are defined on the CALIBRATION wells only. Within each bin the conformal upper bound is the
    ceil((n+1)*level)/n empirical quantile of calibration RMSE; coverage is then measured on the
    held-out validation wells that fall in the same bin.
    """
    edges = np.quantile(cal[feat], np.linspace(0, 1, nbin + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    edges = np.unique(edges)
    cb = np.clip(np.digitize(cal[feat], edges[1:-1]), 0, len(edges) - 2)
    vb = np.clip(np.digitize(val[feat], edges[1:-1]), 0, len(edges) - 2)
    out = []
    for b in range(len(edges) - 1):
        c = cal.rmse.values[cb == b]
        v = val.rmse.values[vb == b]
        if len(c) < 10 or len(v) < 5:
            continue
        k = int(np.ceil((len(c) + 1) * level))
        q = np.sort(c)[min(k, len(c)) - 1]                # conformal upper bound
        out.append(dict(bin=b, lo=edges[b], hi=edges[b + 1], n_cal=len(c), n_val=len(v),
                        width=float(q), coverage=float(np.mean(v <= q)),
                        cal_med=float(np.median(c)), val_med=float(np.median(v))))
    return pd.DataFrame(out)


def marginal(cal, val, level):
    k = int(np.ceil((len(cal) + 1) * level))
    q = np.sort(cal.rmse.values)[min(k, len(cal)) - 1]
    return float(q), float(np.mean(val.rmse.values <= q))


def main():
    oof, _ = per_well_oof()
    fe = well_features()
    W = oof.merge(fe, on='well', how='inner')
    print('wells with both OOF and features:', len(W))
    print('pooled OOF RMSE over these wells: %.4f' % np.sqrt(np.average(W.rmse ** 2, weights=W.n_toe)))

    FEATS = ['nnb', 'closest_surv', 'prefix_frac', 'toe_md', 'prefix_md', 'well_md',
             'gr_std', 'gr_std_toe', 'mean_incl', 'tortuosity']
    print('\n=== does any test-available feature correlate with the per-well OOF RMSE? ===')
    print('%-16s %>8s %>9s' .replace('%>', '%') % ('feature', 'pearson', 'spearman'))
    cor = []
    for f in FEATS:
        a, b = W[f].values, W.rmse.values
        m = np.isfinite(a) & np.isfinite(b)
        pr = float(np.corrcoef(a[m], b[m])[0, 1])
        sp = float(pd.Series(a[m]).corr(pd.Series(b[m]), method='spearman'))
        cor.append((f, pr, sp))
        print('%-16s %8.4f %9.4f' % (f, pr, sp))
    cor.sort(key=lambda t: -abs(t[2]))
    best = cor[0][0]
    print('\nstrongest by |spearman|: %s (%.4f)' % (best, cor[0][1]))

    # ---- split by WELL, 50/50 ----
    rng = np.random.RandomState(SEED)
    perm = rng.permutation(len(W))
    cal, val = W.iloc[perm[:len(W) // 2]].copy(), W.iloc[perm[len(W) // 2:]].copy()
    print('\ncalibration wells %d | validation wells %d' % (len(cal), len(val)))

    print('\n=== A. MARGINAL split conformal (no conditioning) ===')
    print('%-7s %10s %10s' % ('level', 'width_ft', 'coverage'))
    for lv in LEVELS:
        q, c = marginal(cal, val, lv)
        print('%-7.2f %10.3f %10.3f' % (lv, q, c))

    print('\n=== B. MONDRIAN split conformal, binned on %s (4 bins) ===' % best)
    for lv in LEVELS:
        t = mondrian(cal, val, best, nbin=4, level=lv)
        if t.empty:
            continue
        print('\n level %.2f' % lv)
        print('  %-24s %6s %6s %10s %9s' % ('bin range', 'n_cal', 'n_val', 'width_ft', 'coverage'))
        for _, r in t.iterrows():
            print('  [%8.1f,%8.1f) %6d %6d %10.3f %9.3f'
                  % (r.lo, r.hi, r.n_cal, r.n_val, r.width, r.coverage))
        sep = t.width.max() / max(t.width.min(), 1e-9)
        print('  width separation (max/min across bins): %.3f' % sep)

    # ---- C. does ANY feature produce width separation? ----
    print('\n=== C. width separation by feature (level 0.90, 4 bins) ===')
    print('%-16s %10s %10s %14s' % ('feature', 'w_min', 'w_max', 'sep(max/min)'))
    seps = []
    for f in FEATS:
        t = mondrian(cal, val, f, nbin=4, level=0.90)
        if t.empty or len(t) < 2:
            continue
        s = t.width.max() / max(t.width.min(), 1e-9)
        seps.append((f, s, t.width.min(), t.width.max(), t.coverage.min(), t.coverage.max()))
        print('%-16s %10.3f %10.3f %14.3f' % (f, t.width.min(), t.width.max(), s))
    seps.sort(key=lambda t: -t[1])
    print('\nbest separation: %s = %.3fx  (coverage range %.3f..%.3f)'
          % (seps[0][0], seps[0][1], seps[0][4], seps[0][5]))

    # ---- E. how much per-well information do the features actually carry? ----
    # Width separation alone can look non-trivial while explaining almost none of the real spread.
    # Two decisive checks: cross-validated R^2 on log(RMSE), and average interval width at MATCHED
    # empirical coverage (a conditional interval only earns its keep if it is narrower on average).
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import KFold

    X = W[FEATS].replace([np.inf, -np.inf], np.nan).fillna(W[FEATS].median()).values
    ylog = np.log(W.rmse.values)
    oof_pred = np.zeros(len(W))
    for tr, te in KFold(5, shuffle=True, random_state=SEED).split(X):
        m = GradientBoostingRegressor(random_state=SEED, n_estimators=200, max_depth=2,
                                      learning_rate=0.05).fit(X[tr], ylog[tr])
        oof_pred[te] = m.predict(X[te])
    ss_res = float(np.sum((ylog - oof_pred) ** 2))
    ss_tot = float(np.sum((ylog - ylog.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot
    print('\n=== E. information content of the test-available features ===')
    print('5-fold CV R^2 predicting log(per-well OOF RMSE): %.4f' % r2)
    print('spearman(predicted, actual per-well RMSE):        %.4f'
          % pd.Series(oof_pred).corr(pd.Series(W.rmse.values), method='spearman'))
    print('true per-well RMSE spread: median %.3f  p90 %.3f  max %.3f  -> max/median %.2fx'
          % (W.rmse.median(), W.rmse.quantile(.9), W.rmse.max(), W.rmse.max() / W.rmse.median()))

    print('\naverage interval width at MATCHED empirical coverage (validation wells):')
    print('%-28s %10s %10s' % ('scheme', 'avg_width', 'coverage'))
    q_m, c_m = marginal(cal, val, 0.90)
    print('%-28s %10.3f %10.3f' % ('marginal (unconditional)', q_m, c_m))
    for f in [seps[0][0], 'nnb']:
        t = mondrian(cal, val, f, nbin=4, level=0.90)
        aw = float(np.average(t.width, weights=t.n_val))
        ac = float(np.average(t.coverage, weights=t.n_val))
        print('%-28s %10.3f %10.3f' % ('mondrian on %s' % f, aw, ac))

    # ---- D. the 3 visible test wells ----
    print('\n=== D. the 3 visible test wells in the distribution ===')
    print('%-10s %8s %8s %8s %10s %9s %9s'
          % ('well', 'rmse', 'pct', 'nnb', 'clos_surv', 'pfx_frac', 'toe_md'))
    for w in TEST_WELLS:
        r = W[W.well == w]
        if r.empty:
            print('%-10s  (not in the OOF frame)' % w)
            continue
        r = r.iloc[0]
        pct = float((W.rmse < r.rmse).mean())
        print('%-10s %8.3f %8.3f %8.0f %10.1f %9.3f %9.0f'
              % (w, r.rmse, pct, r.nnb, r.closest_surv, r.prefix_frac, r.toe_md))
    print('\nfleet per-well RMSE: median %.3f  p90 %.3f  max %.3f'
          % (W.rmse.median(), W.rmse.quantile(0.9), W.rmse.max()))
    W.to_csv(f'{SH}/n4_well_uncertainty.csv', index=False)
    print('\nwrote %s/n4_well_uncertainty.csv' % SH)
    return W


if __name__ == '__main__':
    main()
