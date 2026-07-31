"""Q14 — bounded weight scan of the frontier's PF bimodal branch hedge.

The variant-matrix round established that the hedge is the LARGEST post-SP45 effect and that it is a
PURE ADDITIVE SHIFT: +2.0 ft on all 4301 rows of well 00e12e8b, exactly zero on the other two wells
(verified here again: a single unique delta of 2.0). That makes the whole weight scan analytically
constructible from outputs already on disk -- no Kaggle run, no quota:

    variant(w) = submission_before_branch_hedge + w * 2.0  on 00e12e8b rows only
    w = 0 -> hedge OFF     w = 1 -> the submitted 54968060 (public 6.643)

Because the shift is constant on a fixed row set, the diff against 54968060 is exact and closed-form:
    rmse(variant(w), 54968060) = |w - 1| * 2.0 * sqrt(4301/14151) = |w - 1| * 1.1027
so the homogeneity threshold of 0.50 is crossed at |w - 1| >= 0.4534.
"""
import numpy as np
import pandas as pd

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
REFS = {'54968060 (6.643)': f'{SH}/a2full_out/submission.csv',
        '54990075 (6.690)': f'{SH}/sp45full_out/submission.csv',
        '54844628 (7.891)': f'{SH}/dep_out/submission.csv'}
HOM = 0.50
WS = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

base = pd.read_csv(f'{SH}/a2full_out/submission_before_branch_hedge.csv')
final = pd.read_csv(f'{SH}/a2full_out/submission.csv')
assert (base.id.values == final.id.values).all()
d = final.tvt.values - base.tvt.values
hedged = d != 0
uniq = np.unique(np.round(d[hedged], 6))
print('hedge rows %d/%d (%.1f%%), unique delta %s' % (hedged.sum(), len(d), 100 * hedged.mean(), uniq))
assert len(uniq) == 1, 'hedge is not a single constant shift'
SHIFT = float(uniq[0])
well = pd.Series(base.id).str.rsplit('_', n=1).str[0].values
refs = {k: pd.read_csv(v) for k, v in REFS.items()}
for k, r in refs.items():
    assert (r.id.values == base.id.values).all(), k

print('\n=== static weight scan: rmse vs each scored reference ===')
print('%-8s %14s %14s %14s %10s %9s' % ('w', *REFS.keys(), 'max|d| vs', 'non-hom'))
print('%-8s %14s %14s %14s %10s %9s' % ('', '', '', '', '54968060', 'vs 6.643'))
rows = []
for w in WS:
    v = base.tvt.values + w * SHIFT * hedged
    cells, hom = [], None
    for k, r in refs.items():
        e = v - r.tvt.values
        cells.append(float(np.sqrt(np.mean(e ** 2))))
        if k.startswith('54968060'):
            hom = cells[-1] >= HOM
            mx = float(np.max(np.abs(e)))
    rows.append((w, *cells, mx, hom))
    print('%-8g %14.4f %14.4f %14.4f %10.3f %9s' % (w, *cells, mx, 'YES' if hom else 'no'))
print('\nclosed form: rmse vs 54968060 = |w-1| * %.1f * sqrt(%d/%d) = |w-1| * %.4f'
      % (SHIFT, hedged.sum(), len(d), SHIFT * np.sqrt(hedged.sum() / len(d))))

print('\n=== sanity of the extreme variants (w=0 hedge OFF, w=2 double) ===')
for w in (0.0, 2.0):
    v = base.tvt.values + w * SHIFT * hedged
    print('  w=%g  min %.1f max %.1f  finite %s' % (w, v.min(), v.max(), bool(np.isfinite(v).all())))
    for k in sorted(set(well)):
        m = well == k
        s = np.diff(v[m])
        print('     %s n=%-5d span %7.1f  max|step| %6.3f  p99|step| %6.3f'
              % (k, m.sum(), v[m].max() - v[m].min(), np.max(np.abs(s)), np.percentile(np.abs(s), 99)))
