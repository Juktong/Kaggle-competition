"""Q58 producer — row-level forward and ancestral-smoothed PF predictions for every well.

Q56 saved only per-well SSE, so the structural-field stage cannot be re-fitted from its output. This script
produces the missing artifact: the actual per-row PF predictions, forward and smoothed, aligned to
`aligned_preds.npz` by (well, ridx), so the downstream re-fit is pure arithmetic and can be iterated without
re-running the filter.

Two differences from Q56, both deliberate:

  * NS = 64, the DEPLOYED configuration. Q36 and Q56 both ran NS=32 to bound wall-time and both had to carry
    a caveat about it. This run removes that caveat.
  * only two arms are produced (forward, full smoother). Q56 already chose among modes and alphas; here the
    row-level output is what matters and alpha is applied downstream, where it can be re-chosen nested
    without re-running anything.

The smoother, the trellis twin and its byte-for-byte degeneracy check are imported unchanged from
`scripts/q56_pf_backward_smoothing.py` rather than re-implemented.

Env: MAXW, NS, JOBS, OUT.
"""
import glob
import importlib.util
import os
import time

import numpy as np
from joblib import Parallel, delayed

SPEC = importlib.util.spec_from_file_location(
    'q56', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'q56_pf_backward_smoothing.py'))
q56 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q56)

SH = q56.SH
NS = int(os.environ.get('NS', '64'))
JOBS = int(os.environ.get('JOBS', '2'))
OUT = os.environ.get('OUT', os.path.join(SH, 'q58_pf_smoothed_preds.npz'))


def main():
    ns = q56.build_namespace()
    load_well, TRAIN_DIR = ns['load_well'], ns['TRAIN_DIR']

    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    nw, nr = z['well'].astype(str), z['ridx'].astype(int)
    ntru = z['truth'].astype(np.float64)
    order = np.argsort(nw, kind='stable')
    uw, starts = np.unique(nw[order], return_index=True)
    ends = np.append(starts[1:], len(order))
    idx = {w: (nr[sl], ntru[sl]) for w, sl in
           ((w, order[a:b]) for w, a, b in zip(uw, starts, ends))}

    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(os.path.join(TRAIN_DIR, '*__horizontal_well.csv')))
    wids = [w for w in wids if w in idx][:int(os.environ.get('MAXW', str(len(wids))))]
    print('wells %d | NS %d (DEPLOYED config) | JOBS %d -> %s' % (len(wids), NS, JOBS, OUT), flush=True)

    # degeneracy control, inherited from q56 and re-run here so this artifact carries its own proof
    hw0, tw0 = load_well(wids[0], 'train')
    a_out, a_ll = ns['run_particle_filter'](hw0, tw0, n_particles=500, seed=0)
    b_out, b_ll, _ = ns['run_particle_filter_tr'](hw0, tw0, n_particles=500, seed=0)
    assert np.array_equal(a_out, b_out, equal_nan=True) and a_ll == b_ll
    print('degeneracy control: array_equal(deployed run_particle_filter, trellis twin) = True', flush=True)

    def one(wid):
        try:
            hw, tw = load_well(wid, 'train')
            toe = hw['TVT_input'].isna().values
            if toe.sum() < 10 or hw['TVT_input'].notna().sum() < 10:
                return None
            rid, tru_w = idx[wid]
            pos = np.flatnonzero(toe)
            if len(pos) != len(rid) or not np.array_equal(pos, rid):
                return ('MISALIGN', wid, len(pos), len(rid))
            truth = hw['TVT'].values.astype(np.float64)[toe]
            if not np.allclose(truth, tru_w, atol=1e-3, equal_nan=True):
                return ('TRUTHDIFF', wid, 0, 0)
            fwd, liks, sm = [], [], []
            for s in range(NS):
                out, ll, (P, A, W, zv, evidx, res) = ns['run_particle_filter_tr'](
                    hw, tw, n_particles=500, seed=s)
                fwd.append(out)
                liks.append(ll)
                full = out.copy()
                full[evidx] = q56.smooth(P, A, W, zv, 'full')
                sm.append(full)
            liks = np.array(liks)
            wts = np.exp((liks - liks.max()) / 5.0)
            wts /= wts.sum()
            ef = (wts[:, None] * np.stack(fwd, 0)).sum(0)[toe]
            es = (wts[:, None] * np.stack(sm, 0)).sum(0)[toe]
            return (wid, rid.astype(np.int32), ef.astype(np.float32), es.astype(np.float32))
        except Exception as exc:  # noqa: BLE001
            return ('ERR', wid, str(exc)[:160], 0)

    t0 = time.time()
    res = Parallel(n_jobs=JOBS, verbose=5)(delayed(one)(w) for w in wids)
    bad = [r for r in res if r and r[0] in ('ERR', 'MISALIGN', 'TRUTHDIFF')]
    ok = [r for r in res if r and r[0] not in ('ERR', 'MISALIGN', 'TRUTHDIFF')]
    print('\ndone %d wells in %.1f min | ok=%d bad=%d'
          % (len(wids), (time.time() - t0) / 60, len(ok), len(bad)), flush=True)
    for b in bad[:6]:
        print('   BAD', b)
    np.savez(OUT,
             well=np.concatenate([np.full(len(r[1]), r[0]) for r in ok]).astype(str),
             ridx=np.concatenate([r[1] for r in ok]),
             pf_fwd=np.concatenate([r[2] for r in ok]),
             pf_sm=np.concatenate([r[3] for r in ok]))
    print('wrote %s (%d wells, %d rows)' % (OUT, len(ok), sum(len(r[1]) for r in ok)))


if __name__ == '__main__':
    main()
