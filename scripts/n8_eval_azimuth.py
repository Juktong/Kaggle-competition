"""N8 evaluation — score each azimuth-tolerance variant inside the deployed blend and run the 3-well gate.

Deployed combination (verified to reproduce the banked numbers exactly in N2):
    gate  = nnb >= 4 AND closest_all < 1000 ft        (87.28% of rows)
    pred  = 0.85*base + 0.15*struct on gated rows, base elsewhere
    base  = 0.5*DWT + 0.5*PF                          (pooled OOF 9.2987)
    deployed struct -> pooled OOF 8.8626 = `54844628`

Fallback: where the azimuth filter leaves a well with no surviving neighbour the struct is NaN, which is
the deployed "struct contribution disabled" case -- those rows fall back to `base`, exactly as production
does when a well has no surviving mate.

Usage: python3 scripts/n8_eval_azimuth.py [--npz ...] [--nboot 20000]
"""
import argparse
import sys
import os

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_three_well_gate import three_well_gate  # noqa: E402

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
W = 0.15


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', default=f'{SH}/n8_struct_azimuth.npz')
    ap.add_argument('--nboot', type=int, default=20000)
    a = ap.parse_args()

    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    well = z['well'].astype(str)
    ridx = z['ridx'].astype(int)
    base = z['base'].astype(np.float64)
    dep = z['s_54844628'].astype(np.float64)
    truth = z['truth'].astype(np.float64)
    gate_mask = (z['nnb'].astype(np.float64) >= 4) & (z['closest_all'].astype(np.float64) < 1000)

    v = np.load(a.npz, allow_pickle=True)
    kv = pd.MultiIndex.from_arrays([v['well'].astype(str), v['ridx'].astype(int)])
    tgt = pd.MultiIndex.from_arrays([well, ridx])
    cols = [c for c in v.files if c.startswith('struct_az')]
    cols.sort(key=lambda c: float(c.replace('struct_az', '')))

    print('aligned rows %d over %d wells' % (len(well), len(set(well))))
    meta_p = a.npz.replace('.npz', '_meta.csv')
    if os.path.exists(meta_p):
        M = pd.read_csv(meta_p)
        print('\n=== filter effect (full split) ===')
        print('%-8s %10s %10s %14s' % ('az_tol', 'mean nnb', 'nnb=0 %', 'lost nearest %'))
        for c in cols:
            t = c.replace('struct_az', '')
            if f'nnb_{t}' in M:
                print('%-8s %10.2f %9.1f%% %13.1f%%'
                      % (t, M[f'nnb_{t}'].mean(), 100 * (M[f'nnb_{t}'] == 0).mean(),
                         100 * M[f'lost_nearest_{t}'].mean()))
        print('median azimuth spread among surviving neighbours: %.1f deg' % M.az_spread.median())

    print('\n%-16s %10s %12s %14s' % ('variant', 'pooled', 'vs 8.8626', 'rows w/o struct'))
    keep = {}
    for c in cols:
        s = pd.Series(v[c].astype(np.float64), index=kv).reindex(tgt).values
        cand = base.copy()
        g = gate_mask & np.isfinite(s)
        cand[g] = (1 - W) * base[g] + W * s[g]
        pooled = float(np.sqrt(np.mean((cand - truth) ** 2)))
        print('%-16s %10.4f %12.4f %13.1f%%'
              % (c, pooled, 8.8626 - pooled, 100 * (gate_mask & ~np.isfinite(s)).mean()))
        keep[c] = cand

    print('\n=== 3-WELL GATE vs the deployed 54844628 (the only gate that decides) ===')
    for c, cand in keep.items():
        if c == 'struct_az180':
            continue
        r = three_well_gate(cand, dep, truth, well, nboot=a.nboot)
        p = r['boot3_pct']
        print('\n%s' % c)
        print('  pooled gain vs deployed: %+.4f  (over %d wells)' % (r['all_gain'], r['n_wells']))
        print('  per-well gain: mean %+.4f median %+.4f std %.4f | helped %.1f%% hurt %.1f%%'
              % (r['per_well_mean'], r['per_well_median'], r['per_well_std'],
                 100 * r['helped'], 100 * r['hurt']))
        print('  3-WELL bootstrap: 1st %+.4f  5th %+.4f  25th %+.4f  50th %+.4f  95th %+.4f'
              % (p[1], p[5], p[25], p[50], p[95]))
        print('  P(gain>0) = %.4f' % r['boot3_prob_pos'])
        print('  760-well REFERENCE (not a gate): mean %+.4f 5th %+.4f'
              % (r['ref760_mean'], r['ref760_5th']))
        print('  actual 3 test wells (OOF proxy): %+.4f' % r['actual_test_gain'])
        print('  GATE PASS: %s   (conditional: %s)' % (r['gate_pass'], r['gate_conditional']))


if __name__ == '__main__':
    main()
