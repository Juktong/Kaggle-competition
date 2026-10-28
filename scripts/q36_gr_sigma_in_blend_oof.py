"""Q36 — GR-sigma widening measured INSIDE the deployed DWT+PF blend.

Q19 found the public 6.213 kernel differs from our pristine base by one token, `* 1.3`, on the PF
likelihood's GR noise sigma, and measured it at +2.3513 nested with 1.5 a confirmed interior optimum --
but tail-driven (helped only 41.7% of wells) and failing the 3-well gate (bootstrap 5th -4.1145).

TWO CORRECTIONS TO WHAT Q19 ACTUALLY MEASURED, both of which this script fixes:

1. Q19 patched `scripts/pf_honest_forward.py`, a STANDALONE conservative PF (500 particles, ONE seed).
   The honest line's PF component is not that. It is `run_pf_lik_ensemble` -- a **likelihood-weighted
   ensemble over n_seeds seeds** of `run_particle_filter` -- and its source is `SUNNY_CODE` in cell 108
   of `kaggle_kernel_henry_v10_sunny80_blend`, which `scripts/pf_forward_oof.py` execs. That ensembling
   is precisely the averaging Rule #1 says damps tails, and Q19's single-seed measurement had it absent.
2. Q19 scored the PF STANDALONE. In the deployed line the PF enters at **weight 0.5**:
   `base = 0.5*dwt + 0.5*pf` (verified numerically: max|base - 0.5*dwt - 0.5*pf| = 4.9e-4, float32
   rounding). A change to the PF is therefore halved before it reaches the honest line.

So this script measures the multiplier where it actually acts: inside the ensemble, then inside the
blend. The deployed `dwt` column is reused unchanged from `aligned_preds.npz` and aligned by (well, ridx),
with a truth-equality assertion so a misalignment cannot pass silently.

Protocol: splits BY WELL; the multiplier is chosen NESTED (selected on one half of the wells, scored on
the disjoint half, both ways); per-well win rate and a 3-WELL bootstrap are reported, not just pooled RMSE.

GATE (from the task): promote only if the nested gain is positive AND the 3-well bootstrap 5th percentile
> 0 AND it helps a majority of wells. A tail-driven pooled gain does NOT pass.

Env: MAXW, MULTS, NS, JOBS, OUT.
"""
import glob
import json
import os
import re
import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

NB = 'kaggle_kernel_henry_v10_sunny80_blend/rogii-henry-v10-sunny80-blend.ipynb'
DATA = os.environ.get('ROGII_DATA', 'data/rogii')
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MULTS = [float(x) for x in os.environ.get('MULTS', '1.0,1.3,1.5').split(',')]
NS = int(os.environ.get('NS', '32'))
JOBS = int(os.environ.get('JOBS', '2'))
OUT = os.environ.get('OUT', 'reports/logs/q36_blend_per_well.npz')

GS_SRC = "    gs = float(np.clip(np.nanstd(kn['GR'].fillna(0).values - tw_at_k), 10., 60.))"


def load_funcs(mult):
    """Exec the DEPLOYED PF source with the GR sigma scaled by `mult`. mult=1.0 is byte-equivalent."""
    nb = json.load(open(NB))
    cells = [c for c in nb['cells'] if c['cell_type'] == 'code']
    s = ''.join(cells[108]['source'])
    m = re.search(r"SUNNY_CODE\s*=\s*'(.*?)'\n", s, re.S)
    code = m.group(1).encode().decode('unicode_escape')
    cut = code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
    funcs = code[:cut].replace('INPUT_DIR = find_input_dir()', f'INPUT_DIR = os.path.abspath({DATA!r})')
    assert funcs.count(GS_SRC) == 1, 'expected exactly one GR-sigma line in the deployed source'
    if mult != 1.0:
        funcs = funcs.replace(GS_SRC, GS_SRC + f' * {mult!r}')
        assert f'* {mult!r}' in funcs
    ns = {}
    exec(funcs, ns)
    return ns


def main():
    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    nw = z['well'].astype(str)
    nr = z['ridx'].astype(int)
    ndwt = z['dwt'].astype(np.float64)
    ntru = z['truth'].astype(np.float64)
    order = np.argsort(nw, kind='stable')
    idx = {}
    uw, starts = np.unique(nw[order], return_index=True)
    ends = np.append(starts[1:], len(order))
    for w, a, b in zip(uw, starts, ends):
        sl = order[a:b]
        idx[w] = (nr[sl], ndwt[sl], ntru[sl])
    print('npz wells %d rows %d' % (len(idx), len(nw)), flush=True)

    base_ns = load_funcs(1.0)
    load_well, TRAIN_DIR = base_ns['load_well'], base_ns['TRAIN_DIR']
    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(os.path.join(TRAIN_DIR, '*__horizontal_well.csv')))
    maxw = int(os.environ.get('MAXW', str(len(wids))))
    wids = [w for w in wids if w in idx][:maxw]
    print('wells to run %d | MULTS %s | NS %d | JOBS %d' % (len(wids), MULTS, NS, JOBS), flush=True)

    NSPACE = {m: load_funcs(m) for m in MULTS}

    def one(wid):
        try:
            hw, tw = load_well(wid, 'train')
            toe = hw['TVT_input'].isna().values
            if toe.sum() < 10 or hw['TVT_input'].notna().sum() < 10:
                return None
            rid, dwt_w, tru_w = idx[wid]
            pos = np.flatnonzero(toe)
            if len(pos) != len(rid) or not np.array_equal(pos, rid):
                return ('MISALIGN', wid, len(pos), len(rid))
            truth = hw['TVT'].values.astype(np.float64)[toe]
            if not np.allclose(truth, tru_w, atol=1e-3, equal_nan=True):
                return ('TRUTHDIFF', wid, 0, 0)
            good = np.isfinite(truth) & np.isfinite(dwt_w)
            out = {}
            for m in MULTS:
                pf = NSPACE[m]['run_pf_lik_ensemble'](hw, tw, n_particles=500, n_seeds=NS, scale=5.0)
                blend = 0.5 * dwt_w + 0.5 * np.asarray(pf, float)[toe]
                e = (blend[good] - truth[good]) ** 2
                out[m] = (float(e.sum()), int(good.sum()))
            return (wid, out)
        except Exception as exc:  # noqa: BLE001
            return ('ERR', wid, str(exc)[:120], 0)

    t0 = time.time()
    res = Parallel(n_jobs=JOBS, verbose=5)(delayed(one)(w) for w in wids)
    bad = [r for r in res if r and r[0] in ('ERR', 'MISALIGN', 'TRUTHDIFF')]
    ok = [r for r in res if r and r[0] not in ('ERR', 'MISALIGN', 'TRUTHDIFF')]
    print('\ndone %d wells in %.1f min | ok=%d bad=%d' % (len(wids), (time.time() - t0) / 60, len(ok), len(bad)),
          flush=True)
    for b in bad[:5]:
        print('   BAD', b)
    if len(ok) < 8:
        print('too few usable wells; inconclusive')
        return

    wells = np.array([r[0] for r in ok])
    S = {m: np.array([r[1][m][0] for r in ok]) for m in MULTS}
    C = np.array([r[1][MULTS[0]][1] for r in ok], float)
    np.savez(OUT, wells=wells, counts=C, **{f'sse_{m:g}': S[m] for m in MULTS})

    print('\n%-10s %14s %14s' % ('multiplier', 'blend RMSE', 'vs mult=1.0'))
    base = float(np.sqrt(S[1.0].sum() / C.sum()))
    for m in MULTS:
        r = float(np.sqrt(S[m].sum() / C.sum()))
        print('%-10g %14.4f %14.4f' % (m, r, base - r))
    print('  (reference: deployed blend `base` = 9.2987 over 760 wells; honest line after the'
          ' structural field = 8.8626)')

    pw = {m: np.sqrt(S[m] / C) for m in MULTS}
    for m in MULTS:
        if m == 1.0:
            continue
        d = pw[1.0] - pw[m]
        print('  mult %-5g helps %.1f%% of wells | mean per-well gain %+.4f | median %+.4f'
              % (m, 100 * np.mean(d > 0), d.mean(), np.median(d)))

    n = len(ok)
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    held_s, held_c, base_s, picks = [], [], [], []
    for sel, rep in folds:
        best = min(MULTS, key=lambda m: np.sqrt(S[m][sel].sum() / C[sel].sum()))
        picks.append(best)
        held_s.append(S[best][rep]); held_c.append(C[rep]); base_s.append(S[1.0][rep])
    hs, hc, bs = (np.concatenate(x) for x in (held_s, held_c, base_s))
    nested = float(np.sqrt(hs.sum() / hc.sum()))
    nbase = float(np.sqrt(bs.sum() / hc.sum()))
    print('\nNESTED (picks %s)  selected %.4f  vs mult=1.0 %.4f  gain %+.4f'
          % (picks, nested, nbase, nbase - nested))

    gw = np.sqrt(bs / hc) - np.sqrt(hs / hc)
    rs = np.random.RandomState(7)
    b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.4f  50th %+.4f  95th %+.4f  P(>0) %.4f'
          % (100 * np.mean(gw > 0), *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))

    ok_gate = (nbase - nested > 0) and (np.percentile(b3, 5) > 0) and (np.mean(gw > 0) > 0.5)
    print('\nGATE: nested gain > 0 AND 3-well 5th > 0 AND helps a majority of wells  ->  %s'
          % ('PASS' if ok_gate else 'FAIL'))


if __name__ == '__main__':
    main()
