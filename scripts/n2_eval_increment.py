"""N2 evaluation — score each structural-field variant inside the deployed blend and run the 3-well gate.

Deployed combination (verified to reproduce the banked numbers exactly):
    gate  = nnb >= 4 AND closest_all < 1000 ft        (87.28% of rows)
    pred  = 0.85*base + 0.15*struct on gated rows, base elsewhere
    base  = 0.5*DWT + 0.5*PF                          (pooled OOF 9.2987)
    deployed struct -> pooled OOF 8.8626 = `54844628`

Usage: python3 scripts/n2_eval_increment.py --npz <variants.npz>
"""
import argparse
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, '/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue/scripts')
from eval_three_well_gate import three_well_gate  # noqa: E402

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
W = 0.15


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--npz', default=f'{SH}/n2_struct_increment.npz')
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
    variants = [k for k in v.files if k.startswith('struct_')]

    print('variant columns:', variants)
    print('aligned rows %d over %d wells' % (len(well), len(set(well))))
    print('\nmechanism metrics (from the builder):')
    print('  nearest-point well identity switches: mean %.4f  median %.4f'
          % (v['sw_frac'].mean(), np.median(v['sw_frac'])))
    print('  fraction of k=12 points sharing the nearest point\'s well: mean %.4f  p10 %.4f'
          % (v['sw_same'].mean(), np.percentile(v['sw_same'], 10)))

    print('\n%-26s %9s %9s %12s %10s' % ('variant', 'rows', 'pooled', 'vs 8.8626', 'vs struct'))
    keep = {}
    for name in variants:
        s = pd.Series(v[name].astype(np.float64), index=kv).reindex(tgt).values
        m = np.isfinite(s)
        cand = base.copy()
        g = gate_mask & m
        cand[g] = (1 - W) * base[g] + W * s[g]
        # restrict scoring to the rows this variant covers, for a like-for-like pooled number
        sub = m
        pooled = float(np.sqrt(np.mean((cand[sub] - truth[sub]) ** 2)))
        pooled_dep = float(np.sqrt(np.mean((dep[sub] - truth[sub]) ** 2)))
        print('%-26s %9d %9.4f %12.4f %10.4f'
              % (name, sub.sum(), pooled, 8.8626 - pooled, pooled_dep - pooled))
        keep[name] = (cand, sub)

    print('\n=== 3-WELL GATE vs the deployed 54844628 (the only gate that decides) ===')
    for name, (cand, sub) in keep.items():
        if name == 'struct_deployed_repro':
            continue
        r = three_well_gate(cand[sub], dep[sub], truth[sub], well[sub], nboot=a.nboot)
        p = r['boot3_pct']
        print('\n%s' % name)
        print('  pooled gain vs deployed: %+.4f  (over %d wells)' % (r['all_gain'], r['n_wells']))
        print('  per-well gain: mean %+.4f median %+.4f std %.4f | helped %.1f%% hurt %.1f%%'
              % (r['per_well_mean'], r['per_well_median'], r['per_well_std'],
                 100 * r['helped'], 100 * r['hurt']))
        print('  3-WELL bootstrap: 1st %+.4f  5th %+.4f  25th %+.4f  50th %+.4f  95th %+.4f'
              % (p[1], p[5], p[25], p[50], p[95]))
        print('  P(gain>0) = %.4f' % r['boot3_prob_pos'])
        print('  760-well REFERENCE (not a gate): mean %+.4f 5th %+.4f' % (r['ref760_mean'], r['ref760_5th']))
        print('  actual 3 test wells (OOF proxy): %+.4f' % r['actual_test_gain'])
        print('  GATE PASS: %s   (conditional: %s)' % (r['gate_pass'], r['gate_conditional']))


if __name__ == '__main__':
    main()
