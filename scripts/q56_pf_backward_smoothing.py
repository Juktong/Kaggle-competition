"""Q56 — backward smoothing of the DEPLOYED particle filter, scored inside the DWT+PF blend.

THE MODELLING GAP. `run_particle_filter` (SUNNY_CODE cell 108, the function `scripts/pf_forward_oof.py`
execs and the one that feeds the honest line) computes

    res[i] = dot(w_i, pos_i - z_i)

i.e. the FILTERED mean at row i, which conditions on observations 1..i only. But the entire toe GR log is
available at prediction time — we predict TVT for rows whose GR we can already see. So every row except the
last is estimated from strictly less information than we hold. That is a modelling gap, not a tuning knob.

WHICH SMOOTHER, AND WHY NOT TEXTBOOK FFBSi. FFBSi re-weights step-i particles by
`w_i^k * p(x_{i+1}^j | x_i^k)`. Here the transition is very nearly deterministic —
`pos += rate*dm + 0.005*eps`, `rate = 0.998*rate + 0.002*eps` — so that backward kernel is numerically
degenerate: for any j, p(x_{i+1}^j | x_i^k) is ~0 except on j's own lineage. In that limit FFBSi collapses
onto the ANCESTRAL-PATH smoother, which is therefore what is implemented (Kitagawa's filter-smoother):
retain the resampling ancestry, then propagate the FINAL weights backwards through the genealogy,

    sm[i] = sum_j w_end[j] * pos_i^{ancestor_i(j)} - z_i

which conditions row i on observations 1..end. This is exact for this model rather than an approximation of
a degenerate kernel, and it is an averaging operation, so Q40's compounding warning does not apply.

ITS KNOWN FAILURE MODE IS MEASURED, NOT ASSUMED. Ancestral smoothers suffer PATH DEGENERACY: after enough
resampling steps every lineage shares one ancestor, so far from the end the "smoothed" estimate is a single
particle's path — LESS averaging than the filter, not more. Section 2 measures the ancestor ESS against
lookahead before any arm is scored, exactly as Q54/Q55 required a spread/binding diagnostic first. The
BLOCK arms exist because of it: block(L) restarts the backward pass every L rows, so lookahead is bounded
by L and the genealogy cannot collapse.

ARMS. mode in {full, block400, block100, block25} x alpha in {0.25, 0.5, 1.0}, where
`pred = (1-alpha)*forward + alpha*smoothed`. alpha=0 is the control and is byte-identical by construction.
All arms come from ONE forward pass per seed — the smoothing is post-processing on the retained trellis — so
the whole grid costs about the same as a single q36 multiplier.

DEGENERACY CONTROL (Directive 4 / Q54's rule). The trellis-retaining forward pass is not retyped: it is
derived from the deployed source by four ANCHORED insertions, each asserted unique, so it cannot drift by
transcription. Then its output is checked for EXACT equality (`np.array_equal`) against the untouched
deployed `run_particle_filter` and `run_pf_lik_ensemble`. That is a check against the deployed function
itself, not against this script's own OFF path.

SCORING. Inside the blend, `0.5*dwt + 0.5*pf_new`, reusing the deployed `dwt` column from
`aligned_preds.npz` unchanged, with the (well, ridx) alignment and truth-equality assertions from
`scripts/q36_gr_sigma_in_blend_oof.py`. The PF enters at weight 0.5, so any PF-level effect HALVES before
it reaches the honest line; blend-level numbers are what is reported.

GATE: nested by-well gain > 0 AND helps > 50% of wells AND 3-well bootstrap 5th > 0.

Env: MAXW, NS, JOBS, ALPHAS, MODES, OUT.
"""
import glob
import json
import os
import re
import time

import numpy as np
from joblib import Parallel, delayed
from scipy.signal import savgol_filter

NB = 'kaggle_kernel_henry_v10_sunny80_blend/rogii-henry-v10-sunny80-blend.ipynb'
MAIN = '/home/ubuntu/workstation/JoeProject/Kaggle-competition'
# the data is gitignored, so a git WORKTREE has no `data/rogii`; fall back to the main checkout, as
# `scripts/q10_twh1_scorer_dp.py` already hard-codes. Without this the deployed source silently reports
# "Test wells: []" and the well list comes back empty.
DATA = os.environ.get('ROGII_DATA') or ('data/rogii' if os.path.isdir('data/rogii') else f'{MAIN}/data/rogii')
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
NS = int(os.environ.get('NS', '32'))
JOBS = int(os.environ.get('JOBS', '2'))
ALPHAS = [float(x) for x in os.environ.get('ALPHAS', '0.25,0.5,1.0').split(',')]
MODES = os.environ.get('MODES', 'full,block400,block100,block25').split(',')
SGWINS = [int(x) for x in os.environ.get('SGWINS', '51,201,601').split(',') if x]
OUT = os.environ.get('OUT', 'reports/logs/q56_blend_per_well.npz')

# ---- the four anchors, each asserted unique in the deployed source ----
A_DEF = 'def run_particle_filter(hw, tw, n_particles=500, seed=42):'
A_RES = '    res = np.empty(len(ev))\n'
A_NEF = '        n_eff = 1.0 / (w**2).sum()\n'
A_IDX = '            idx = np.clip(np.searchsorted(cum, u0 + np.arange(N) / N), 0, N - 1)\n'
A_SET = '        res[i] = float(np.dot(w, pos - z_v[i]))\n'
A_RET = '    return out_vals, log_lik'


def deployed_source():
    nb = json.load(open(NB))
    cells = [c for c in nb['cells'] if c['cell_type'] == 'code']
    s = ''.join(cells[108]['source'])
    m = re.search(r"SUNNY_CODE\s*=\s*'(.*?)'\n", s, re.S)
    code = m.group(1).encode().decode('unicode_escape')
    cut = code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
    return code[:cut].replace('INPUT_DIR = find_input_dir()', f'INPUT_DIR = os.path.abspath({DATA!r})')


def build_namespace():
    """Exec the deployed source UNTOUCHED, then add a trellis-retaining twin derived by insertion."""
    funcs = deployed_source()
    ns = {}
    exec(funcs, ns)                                    # the deployed functions, unmodified

    for a in (A_DEF, A_RES, A_NEF, A_IDX, A_SET, A_RET):
        assert funcs.count(a) == 1, 'anchor not unique in deployed source: %r' % a[:50]

    tr = funcs
    tr = tr.replace(A_DEF, 'def run_particle_filter_tr(hw, tw, n_particles=500, seed=42):')
    tr = tr.replace(A_RES, A_RES + (
        '    assert n_particles < 32767\n'
        '    _T = len(ev)\n'
        '    P_ = np.empty((_T, n_particles), dtype=np.float32)\n'
        '    W_ = np.empty((_T, n_particles), dtype=np.float32)\n'
        '    A_ = np.empty((_T, n_particles), dtype=np.int16)\n'
        '    _ar = np.arange(n_particles, dtype=np.int16)\n'))
    tr = tr.replace(A_NEF, '        A_[i] = _ar\n' + A_NEF)
    tr = tr.replace(A_IDX, A_IDX + '            A_[i] = idx\n')
    tr = tr.replace(A_SET, A_SET + '        P_[i] = pos\n        W_[i] = w\n')
    tr = tr.replace(A_RET, '    return out_vals, log_lik, (P_, A_, W_, z_v, np.asarray(ev.index), res)')
    exec(tr, ns)
    return ns


def smooth(P, A, W, z, mode):
    """Ancestral-path smoother. `full` = one backward pass from the end; `blockL` restarts every L rows."""
    T, N = P.shape
    L = T if mode == 'full' else int(mode.replace('block', ''))
    sm = np.empty(T)
    for b0 in range(0, T, L):
        b1 = min(b0 + L, T) - 1
        sl = np.arange(N, dtype=np.int64)
        w = W[b1].astype(np.float64)
        for i in range(b1, b0 - 1, -1):
            sm[i] = float(np.dot(w, P[i][sl])) - z[i]
            sl = A[i][sl].astype(np.int64)
    return sm


def ancestor_ess(A, W, max_look=600):
    """Path-degeneracy diagnostic: distinct ancestors and ancestor ESS vs lookahead, from the last row."""
    T, N = A.shape
    sl = np.arange(N, dtype=np.int64)
    w = W[T - 1].astype(np.float64)
    look, uniq, ess = [], [], []
    for k in range(min(max_look, T)):
        i = T - 1 - k
        wa = np.bincount(sl, weights=w, minlength=N)
        look.append(k)
        uniq.append(int(np.unique(sl).size))
        ess.append(float(1.0 / np.sum(wa ** 2)))
        sl = A[i][sl].astype(np.int64)
    return np.array(look), np.array(uniq), np.array(ess)


def savgol_arm(ens_f, evidx, win, poly=2):
    """CONTROL: plain non-causal Savitzky-Golay smoothing of the FORWARD output over the toe rows.

    Why this control is necessary. The ancestral smoother returns a weighted average over surviving
    lineages, which is mechanically SMOOTHER than the filtered mean. Truth is smooth, so any temporal
    smoothing of the forward output would improve RMSE regardless of whether later observations contributed
    information. Without this arm, "backward smoothing helps" could not be distinguished from "the PF output
    is noisier than the signal". savgol uses ONLY the forward prediction — no trellis, no lookahead
    likelihood — so the difference between the two isolates what the genealogy actually adds.
    """
    v = np.asarray(ens_f, float).copy()
    seg = v[evidx]
    w = int(min(win, len(seg) - (1 - len(seg) % 2)))
    if w < poly + 2:
        return v
    if w % 2 == 0:
        w -= 1
    v[evidx] = savgol_filter(seg, w, poly)
    return v


def pf_arms(ns, hw, tw, n_seeds, modes, alphas, scale=5.0, n_particles=500, diag=False):
    """One forward pass per seed; every arm is post-processing on the retained trellis."""
    fwd, liks, sms, dg = [], [], {m: [] for m in modes}, None
    for s in range(n_seeds):
        out, ll, (P, A, W, z, evidx, res) = ns['run_particle_filter_tr'](
            hw, tw, n_particles=n_particles, seed=s)
        fwd.append(out)
        liks.append(ll)
        if diag and s == 0:
            dg = ancestor_ess(A, W)
        for m in modes:
            sm = smooth(P, A, W, z, m)
            full = out.copy()
            full[evidx] = sm
            sms[m].append(full)
    liks = np.array(liks)
    wts = np.exp((liks - liks.max()) / scale)
    wts /= wts.sum()
    ens_f = (wts[:, None] * np.stack(fwd, 0)).sum(0)
    arms = {('fwd', 0.0): ens_f}
    for m in modes:
        ens_s = (wts[:, None] * np.stack(sms[m], 0)).sum(0)
        for a in alphas:
            arms[(m, a)] = (1 - a) * ens_f + a * ens_s
    for win in SGWINS:                              # the denoising control, same alpha grid
        ens_g = savgol_arm(ens_f, evidx, win)
        for a in alphas:
            arms[('sg%d' % win, a)] = (1 - a) * ens_f + a * ens_g
    return arms, dg


def main():
    ns = build_namespace()
    load_well, TRAIN_DIR = ns['load_well'], ns['TRAIN_DIR']

    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    nw, nr = z['well'].astype(str), z['ridx'].astype(int)
    ndwt, ntru = z['dwt'].astype(np.float64), z['truth'].astype(np.float64)
    order = np.argsort(nw, kind='stable')
    uw, starts = np.unique(nw[order], return_index=True)
    ends = np.append(starts[1:], len(order))
    idx = {w: (nr[sl], ndwt[sl], ntru[sl]) for w, sl in
           ((w, order[a:b]) for w, a, b in zip(uw, starts, ends))}

    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(os.path.join(TRAIN_DIR, '*__horizontal_well.csv')))
    wids = [w for w in wids if w in idx][:int(os.environ.get('MAXW', str(len(wids))))]
    ARMS = MODES + ['sg%d' % w for w in SGWINS]
    KEYS = [('fwd', 0.0)] + [(m, a) for m in ARMS for a in ALPHAS]
    print('npz wells %d | wells to run %d | NS %d | JOBS %d | ARMS %s | ALPHAS %s'
          % (len(idx), len(wids), NS, JOBS, ARMS, ALPHAS), flush=True)

    # ---------- 1. DEGENERACY CONTROL against the UNTOUCHED deployed functions ----------
    print('\n=== 1. DEGENERACY CONTROL: the trellis twin vs the deployed function, byte-for-byte ===')
    w0 = wids[0]
    hw0, tw0 = load_well(w0, 'train')
    for s in (0, 1, 7):
        a_out, a_ll = ns['run_particle_filter'](hw0, tw0, n_particles=500, seed=s)
        b_out, b_ll, (P, A, W, zv, evidx, res) = ns['run_particle_filter_tr'](
            hw0, tw0, n_particles=500, seed=s)
        assert np.array_equal(a_out, b_out, equal_nan=True), 'trellis twin diverged at seed %d' % s
        assert a_ll == b_ll
        print('  seed %-2d  array_equal(deployed, trellis) = True   log_lik identical = True' % s)
    ens_dep = ns['run_pf_lik_ensemble'](hw0, tw0, n_particles=500, n_seeds=8, scale=5.0)
    arms0, dg = pf_arms(ns, hw0, tw0, 8, MODES, ALPHAS, diag=True)
    same = np.array_equal(ens_dep, arms0[('fwd', 0.0)], equal_nan=True)
    print('  ensemble: array_equal(deployed run_pf_lik_ensemble, alpha=0 arm) = %s' % same)
    assert same, 'the alpha=0 arm must reproduce the deployed ensemble exactly'
    # the smoothed value at the LAST row must equal the filtered one (no lookahead there)
    for m in MODES:
        d = abs(float(arms0[(m, 1.0)][-1] - arms0[('fwd', 0.0)][-1]))
        print('  mode %-9s |smoothed - filtered| at the final row = %.3e (must be ~0)' % (m, d))

    # ---------- 2. PATH DEGENERACY, measured before any arm is scored ----------
    print('\n=== 2. PATH DEGENERACY: ancestor ESS vs lookahead (seed 0, well %s, T=%d) ===' % (w0, len(dg[0])))
    print('  %-10s %14s %14s' % ('lookahead', 'distinct anc.', 'ancestor ESS'))
    for k in (0, 1, 2, 5, 10, 25, 50, 100, 200, 400, 599):
        if k < len(dg[0]):
            print('  %-10d %14d %14.2f' % (dg[0][k], dg[1][k], dg[2][k]))
    coll = np.flatnonzero(dg[2] < 2.0)
    print('  ancestor ESS drops below 2.0 at lookahead %s'
          % (int(dg[0][coll[0]]) if len(coll) else 'never within the window'))
    print('  (this is why the block arms exist: block(L) bounds lookahead at L rows)')

    # ---------- 3. the run ----------
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
            arms, _ = pf_arms(ns, hw, tw, NS, MODES, ALPHAS)
            out = {}
            for k in KEYS:
                blend = 0.5 * dwt_w + 0.5 * np.asarray(arms[k], float)[toe]
                out[k] = (float(((blend[good] - truth[good]) ** 2).sum()), int(good.sum()))
            return (wid, out)
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
    if len(ok) < 8:
        print('too few usable wells; inconclusive')
        return

    S = {k: np.array([r[1][k][0] for r in ok]) for k in KEYS}
    C = np.array([r[1][KEYS[0]][1] for r in ok], float)
    np.savez(OUT, wells=np.array([r[0] for r in ok]), counts=C,
             **{'sse_%s_%g' % k: S[k] for k in KEYS})

    base = float(np.sqrt(S[('fwd', 0.0)].sum() / C.sum()))
    pw = {k: np.sqrt(S[k] / C) for k in KEYS}
    print('\n=== 4. blend RMSE by arm (deployed blend `base` = 9.2987; honest line 8.8626) ===')
    print('%-12s %10s %10s %10s   %s' % ('mode', 'a=0.25', 'a=0.5', 'a=1.0', 'helps%% / mean gain at best a'))
    print('%-12s %10.4f' % ('forward', base))
    for m in ARMS:
        row = ''.join('%10.4f' % float(np.sqrt(S[(m, a)].sum() / C.sum())) for a in ALPHAS)
        ba = min(ALPHAS, key=lambda a: np.sqrt(S[(m, a)].sum() / C.sum()))
        d = pw[('fwd', 0.0)] - pw[(m, ba)]
        print('%-12s %s   a=%.2f: helps %.1f%% | mean %+.4f | median %+.4f'
              % (m, row, ba, 100 * np.mean(d > 0), d.mean(), np.median(d)))

    n = len(ok)
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    hs, hc, bs_, picks = [], [], [], []
    for sel, rep in folds:
        best = min(KEYS, key=lambda k: np.sqrt(S[k][sel].sum() / C[sel].sum()))
        picks.append(best)
        hs.append(S[best][rep]); hc.append(C[rep]); bs_.append(S[('fwd', 0.0)][rep])
    hs, hc, bs_ = (np.concatenate(x) for x in (hs, hc, bs_))
    nested, nbase = float(np.sqrt(hs.sum() / hc.sum())), float(np.sqrt(bs_.sum() / hc.sum()))
    gw = np.sqrt(bs_ / hc) - np.sqrt(hs / hc)
    rs = np.random.RandomState(7)
    b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('\n=== 5. NESTED (splits BY WELL, arm chosen on one half, scored on the disjoint half) ===')
    print('  picks %s' % [(m, a) for m, a in picks])
    print('  selected %.4f  vs forward %.4f  gain %+.4f' % (nested, nbase, nbase - nested))
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.4f  50th %+.4f  95th %+.4f  P(>0) %.4f'
          % (100 * np.mean(gw > 0), *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
    good = (nbase - nested > 0) and (np.percentile(b3, 5) > 0) and (np.mean(gw > 0) > 0.5)
    print('\nGATE: nested gain > 0 AND helps a majority AND 3-well 5th > 0  ->  %s' % ('PASS' if good else 'FAIL'))
    print('NOTE: the PF enters the honest blend at weight 0.5, so a PF-level effect is HALVED here already;')
    print('      a further gated structural-field stage lies between this blend and the deployed 8.8626.')


if __name__ == '__main__':
    main()
