"""Q16 prerequisite — is the deployed honest line's SIGNED residual predictable at all?

Q16 proposes "bounded residual corrections" gated on confidence. That premise requires the SIGNED
row-level residual of 54844628 to be predictable from test-available features on held-out wells. Two
pieces of banked evidence bear on it and neither is sufficient to answer it:

  - the ledger lists post-hoc residual correction as CLOSED, but on an older feature set;
  - N4 measured the predictability of the error MAGNITUDE per well (CV R^2 0.0736 on log per-well RMSE)
    and found conditional conformal intervals WIDER than marginal ones. Magnitude is a weaker
    requirement than sign, so N4 bounds this from one side only.

This script measures the signed-residual R^2 directly, splitting BY WELL, before any router is built. If
it is ~0 the direction closes without a full implementation; that is the cheapest possible resolution.

Features are test-available only: neighbour diagnostics from the structural field, the DWT/PF
disagreement, the struct contribution actually applied, row position in the toe, and the per-well
features banked by N4.

The learner is HistGradientBoostingRegressor rather than the exact-split GradientBoostingRegressor: the
exact-split variant is single-threaded and did not finish 5 folds x 300 trees on 3.7M rows inside a 40 min
cap. The histogram variant fits the SAME model family multithreaded on the FULL row set, so the estimate
is made on all the data rather than on a subsample.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'

z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
well = z['well'].astype(str)
d = pd.DataFrame(dict(
    well=well, ridx=z['ridx'].astype(int),
    resid=z['s_54844628'].astype(float) - z['truth'].astype(float),      # SIGNED
    nnb=z['nnb'].astype(float), closest_all=z['closest_all'].astype(float),
    closest_surv=z['closest_surv'].astype(float),
    dwt_pf_disagree=np.abs(z['dwt'].astype(float) - z['pf'].astype(float)),
    struct_contrib=z['s_54844628'].astype(float) - z['base'].astype(float),
))
# row position within each well's toe (test-available)
d['row_frac'] = d.groupby('well').ridx.transform(lambda s: (s - s.min()) / max(s.max() - s.min(), 1))
d['rows_from_anchor'] = d.groupby('well').ridx.transform(lambda s: s - s.min())
U = pd.read_csv(f'{SH}/n4_well_uncertainty.csv')
keep = [c for c in ['well', 'prefix_frac', 'toe_md', 'prefix_md', 'well_md', 'gr_std', 'gr_std_toe',
                    'mean_incl', 'tortuosity'] if c in U.columns]
d = d.merge(U[keep], on='well', how='left')

FE = [c for c in d.columns if c not in ('well', 'ridx', 'resid')]
print('rows %d over %d wells | features %d' % (len(d), d.well.nunique(), len(FE)))
print('signed residual: mean %+.4f  std %.4f  |  RMSE of the deployed line %.4f'
      % (d.resid.mean(), d.resid.std(), np.sqrt(np.mean(d.resid ** 2))))

X = d[FE].replace([np.inf, -np.inf], np.nan).fillna(d[FE].median()).values
y = d.resid.values
oof = np.zeros(len(d))
for tr, te in GroupKFold(5).split(X, y, groups=d.well.values):
    g = HistGradientBoostingRegressor(random_state=0, max_iter=300, max_depth=3,
                                      learning_rate=0.05, early_stopping=False).fit(X[tr], y[tr])
    oof[te] = g.predict(X[te])
    print('  fold done (%d train / %d test rows)' % (len(tr), len(te))); sys.stdout.flush()
ss_res = float(np.sum((y - oof) ** 2)); ss_tot = float(np.sum((y - y.mean()) ** 2))
print('\n=== signed-residual predictability, GroupKFold BY WELL ===')
print('  CV R^2                : %.4f' % (1 - ss_res / ss_tot))
print('  corr(pred, actual)    : %.4f' % np.corrcoef(oof, y)[0, 1])
print('  N4 reference (magnitude, log per-well RMSE): 0.0736')

print('\n=== if we applied the correction, what happens? ===')
base_rmse = float(np.sqrt(np.mean(y ** 2)))
print('  %-34s %10s %12s' % ('correction strength', 'pooled', 'vs deployed'))
for a in (0.0, 0.25, 0.5, 1.0):
    r = float(np.sqrt(np.mean((y - a * oof) ** 2)))
    print('  %-34s %10.4f %12.4f' % (f'resid - {a:g} * predicted', r, base_rmse - r))

pw = d.assign(oof=oof).groupby('well').apply(
    lambda g: pd.Series({
        'base': np.sqrt(np.mean(g.resid ** 2)),
        'corr50': np.sqrt(np.mean((g.resid - 0.5 * g.oof) ** 2))}), include_groups=False)
gain = pw.base - pw.corr50
print('\n  per-well gain at strength 0.5: mean %+.4f median %+.4f | helped %.1f%% hurt %.1f%%'
      % (gain.mean(), gain.median(), 100 * (gain > 0).mean(), 100 * (gain < 0).mean()))
rs = np.random.RandomState(7)
b3 = np.array([gain.values[rs.randint(0, len(gain), 3)].mean() for _ in range(20000)])
print('  3-WELL bootstrap: 5th %+.4f  50th %+.4f  95th %+.4f  P(gain>0) %.4f'
      % (*np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
print('\nGATE: a bounded residual correction needs a materially positive signed-residual R^2 AND a')
print('      3-well bootstrap 5th percentile > 0.')
