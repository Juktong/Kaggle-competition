"""Q57 — dip-state-augmented DP: state = (TVT, dip) instead of TVT alone.

Source: Q45's architecture scan found `tiktoktrendz/rogii-dip-aware-hmm-gbm`, whose HMM transition searches
41 dip rates with a momentum factor — i.e. its state carries a dip. Every transition arm this project has
run used a TVT-ONLY state (Q40's 45 soft per-step penalties, N1's per-step geometric bound, Q54's global
corridor), and Q55 closed the decoder side while finding the DP objective misaligned with RMSE.

THE MECHANISM THIS TESTS, AND WHY IT FOLLOWS FROM Q54. The deployed transition charges `lam*|ds|/BAND` for
EVERY step. A sustained dip of 1 grid unit per step over ~477 steps therefore costs `60*477/60 = 477` — the
DP simply cannot afford to move steadily, which is exactly Q54's measurement: at the optimal lam=60 the DP
path deviates +-3.0 ft from the anchor while the TRUTH deviates +-19.4 ft. Augmenting the state makes a
CONSTANT dip free:

    state (s, d);  transition (s, d) -> (s', d')
    cost = C[j, s']  +  mu * |s' - (s + d')| / BAND   +  nu * |d' - d| / DSC
                        ^ deviation from the dip PREDICTION      ^ dip-change penalty

Travelling at a constant rate now pays nothing in either term. Dip continuity becomes a property of the
STATE rather than a penalty on the increment, which changes the objective's shape instead of its
coefficients — the one direction Q55's closure left open.

DEGENERACY CONTROL (Q54's rule). With the dip grid {0} and nu = 0 the cost collapses to
`C[j,s'] + mu*|s'-s|/BAND`, which IS `run_dp` with lam = mu. So the augmented DP strictly CONTAINS the
deployed one, and the control is an exact-equality check rather than an approximate one.

ACTIVATION DIAGNOSTIC (N1's and Q54's rule). Both earlier rounds first produced an inert constraint and
nearly reported it as "no effect". Here the report states how often the selected dip is non-zero and how
often it changes, plus Q40's accumulated-pull quantity (|mean dip| x steps) against the +-19.4 ft the truth
actually requires — an inert arm has to be visible as inert.

Q55 CHECK. Objective COST is reported alongside RMSE. If augmentation lowers the cost but not the RMSE,
that is Q55's misalignment finding reappearing and is to be reported as such, not as a tuning failure.

Env: MAXW_TRAIN, MAXW_EVAL, MUS, NUS, DIPS, TIMING.
"""
import glob
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q10_twh1_scorer_dp as q10  # noqa: E402

MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
MUS = [float(x) for x in os.environ.get('MUS', '20,60,150').split(',')]
NUS = [float(x) for x in os.environ.get('NUS', '0,0.25,1,4').split(',')]   # on the emission scale (C is z-scored)
DIPS = [int(x) for x in os.environ.get('DIPS', '1,5,9').split(',')]   # dip-grid sizes (odd, centred on 0)
PERDIP = os.environ.get('PERDIP', '1') == '1'
DSC = float(os.environ.get('DSC', '1.0'))                            # dip-change normaliser
TWH = 1
BAND, K, STEP = q10.BAND, q10.K, q10.STEP


def dip_grid(n):
    """n odd, centred on 0, unit spacing in grid units per DP step (the grid is ~1 ft)."""
    assert n % 2 == 1
    h = n // 2
    return np.arange(-h, h + 1, dtype=float)


def run_dp_dip(P, mu, nu, ndip, want_diag=False, perdip=True):
    """Beam DP over the augmented state (s, d). ndip=1, nu=0 reproduces q10.run_dp with lam=mu.

    `perdip` keeps K beams PER DIP VALUE instead of K overall. This is not a tuning choice — it is what
    makes the augmentation testable at all. Measured in the first smoke: with a single global top-K the dip
    arm is EXACTLY inert (dip != 0 on 0.0% of steps, identical cost and RMSE to the TVT-only DP). The cause
    is arithmetic, not a bug: switching the dip on costs `nu` immediately and saves `mu*|d|/BAND` only on
    every LATER step, so a globally greedy beam pays the whole penalty up front and prunes every d != 0
    candidate before its deferred payoff can be realised. Over ~477 steps a sustained d=1 saves ~477 for a
    one-off cost of nu — the hypothesis is worth keeping alive, and per-dip beams are the minimal way to do
    it. This is Q55's finding from the other side: there the beam's greedy suboptimality was protective,
    here the same greediness is what blocks a structurally better model from ever being explored.
    """
    Cm, S, grid = P['C'], P['S'], P['grid']
    D = dip_grid(ndip)
    nD = len(D)
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    off = np.arange(-BAND, BAND + 1)
    # beams: (path_states, path_dips, last_s, last_d_index, cost)
    beams = [([s0], [0.0], s0, int(np.argmin(np.abs(D))), 0.0)]
    for j in range(len(Cm)):
        cand = []
        for path, dips, s, di, cost in beams:
            lo, hi = max(0, s - BAND), min(S, s + BAND + 1)
            cols = np.arange(lo, hi)
            # (nD, len(cols)) : deviation of s' from the dip prediction s + d'
            dev = np.abs(cols[None, :] - (s + D[:, None]))
            step = Cm[j, lo:hi][None, :] + mu * dev / BAND + (nu * np.abs(D - D[di]) / DSC)[:, None]
            flat = step.ravel()
            # with per-dip beams the shortlist must be able to supply K candidates for every dip value,
            # otherwise the global top-K would silently re-impose the pruning this flag exists to prevent
            nk = min(K * nD if (perdip and nD > 1) else K, flat.size)
            kbest = np.argpartition(flat, nk - 1)[:nk]
            for f in kbest[np.argsort(flat[kbest])]:
                a, b = divmod(int(f), len(cols))
                cand.append((path + [lo + b], dips + [D[a]], lo + b, a, cost + float(flat[f])))
        cand.sort(key=lambda v: v[4])
        seen, beams = set(), []
        cap = K * nD if (perdip and nD > 1) else K
        per = [0] * nD
        for c in cand:
            key = (c[2], c[3])
            if key in seen:
                continue
            if perdip and nD > 1 and per[c[3]] >= K:      # K beams PER DIP, not K overall
                continue
            seen.add(key)
            per[c[3]] += 1
            beams.append(c)
            if len(beams) >= cap:
                break
    best = beams[0]
    top1 = grid[np.clip(np.array(best[0][1:]), 0, S - 1)]
    rmse = float(np.sqrt(np.mean((top1 - P['tru']) ** 2)))
    if not want_diag:
        return rmse, best[4]
    d = np.array(best[1][1:])
    dev_anchor = np.abs(top1 - P['anchor'])
    return rmse, best[4], dict(
        nonzero=float(np.mean(d != 0)),
        changed=float(np.mean(np.diff(d) != 0)) if len(d) > 1 else 0.0,
        mean_abs_dip=float(np.mean(np.abs(d))),
        accum_pull=float(abs(np.mean(d)) * len(d)),          # Q40's accumulated-pull quantity
        path_dev_max=float(dev_anchor.max()), path_dev_p90=float(np.percentile(dev_anchor, 90)),
        truth_dev_max=float(np.abs(P['tru'] - P['anchor']).max()), steps=len(d))


def main():
    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(f'{q10.D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print('train %d | eval %d (same split seed as Q10/Q40/Q54)' % (len(tr_w), len(ev_w)), flush=True)
    net, mu_, sd_ = q10.train_scorer(tr_w, TWH)
    P_list = [p for p in (q10.prep(w, net, mu_, sd_, TWH) for w in ev_w) if p is not None]
    flat = np.array([P['flat'] for P in P_list])
    print('prepped %d wells | flat-anchor %.3f | l1 lam=60 baseline 12.170 | deployed honest 8.8626\n'
          % (len(P_list), np.sqrt(np.mean(flat ** 2))), flush=True)

    # ---------- 1. degeneracy control ----------
    print('=== 1. DEGENERACY: dip grid {0} and nu=0 must reproduce run_dp with lam=mu ===')
    for mu in MUS:
        a = np.array([q10.run_dp(P, mu) for P in P_list])
        b = np.array([run_dp_dip(P, mu, 0.0, 1)[0] for P in P_list])
        print('  mu %-6g max|dip_dp(ndip=1,nu=0) - run_dp| = %.10f' % (mu, np.abs(a - b).max()))
        assert np.abs(a - b).max() < 1e-9, 'the augmented DP must contain the deployed one exactly'

    # ---------- 2. timing, before the full grid (task step 3) ----------
    if os.environ.get('TIMING', '1') == '1':
        print('\n=== 2. COST CONTROL: wall-time on 8 wells before the full sweep ===')
        for nd in DIPS:
            t0 = time.time()
            for P in P_list[:8]:
                run_dp_dip(P, 60.0, 1.0, nd, perdip=PERDIP)
            dt = time.time() - t0
            ncfg = 1 if nd == 1 else len(MUS) * len(NUS)
            print('  ndip %-3d  %.2f s / 8 wells  -> %.1f min for %d configs x %d wells'
                  % (nd, dt, dt / 8 * len(P_list) * ncfg / 60, ncfg, len(P_list)))

    # ---------- 3. the sweep ----------
    per, cost, diag = {}, {}, {}
    for nd in DIPS:
        nus = [0.0] if nd == 1 else NUS
        for mu in MUS:
            for nu in nus:
                rs, cs = [], []
                dg = None
                for i, P in enumerate(P_list):
                    r, c, *rest = run_dp_dip(P, mu, nu, nd, want_diag=(i == 0), perdip=PERDIP)
                    rs.append(r); cs.append(c)
                    if rest:
                        dg = rest[0]
                per[(nd, mu, nu)] = np.array(rs)
                cost[(nd, mu, nu)] = float(np.mean(cs))
                diag[(nd, mu, nu)] = dg
                print('  ndip %-3d mu %-6g nu %-6g  pooled %.3f  mean cost %.1f'
                      % (nd, mu, nu, np.sqrt(np.mean(per[(nd, mu, nu)] ** 2)), cost[(nd, mu, nu)]), flush=True)

    print('\n=== 4. pooled RMSE (rows = dip grid size x nu, cols = mu) ===')
    print('%-16s %s' % ('ndip / nu', ''.join('%12s' % ('mu=%g' % m) for m in MUS)))
    for nd in DIPS:
        for nu in ([0.0] if nd == 1 else NUS):
            print('%-16s %s' % ('%d / %g' % (nd, nu),
                                ''.join('%12.3f' % np.sqrt(np.mean(per[(nd, m, nu)] ** 2)) for m in MUS)))

    print('\n=== 5. ACTIVATION (well 0; an inert arm must be visible as inert) ===')
    print('%-16s %9s %9s %11s %11s %10s %10s' %
          ('ndip / nu / mu', 'dip!=0', 'dip chg', 'mean|dip|', 'accum pull', 'path dev', 'truth dev'))
    for key in sorted(diag):
        d = diag[key]
        if d is None:
            continue
        print('%-16s %8.1f%% %8.1f%% %11.3f %11.1f %10.1f %10.1f'
              % ('%d / %g / %g' % (key[0], key[2], key[1]), 100 * d['nonzero'], 100 * d['changed'],
                 d['mean_abs_dip'], d['accum_pull'], d['path_dev_max'], d['truth_dev_max']))
    print('  (Q54: at the optimum the DP path deviates ~3.0 ft from the anchor while truth deviates 19.4;')
    print('   accum pull = |mean dip| x steps is Q40\'s quantity — what the dip term is worth end-to-end)')

    print('\n=== 6. Q55 CHECK: does augmentation buy COST that does not become RMSE? ===')
    b60 = (1, 60.0, 0.0)
    print('  %-20s cost %10.1f   rmse %7.3f   <- the deployed objective (= run_dp lam=60)'
          % ('ndip=1 nu=0 mu=60', cost[b60], np.sqrt(np.mean(per[b60] ** 2))))
    for key in sorted(per, key=lambda k: cost[k])[:4]:
        print('  %-20s cost %10.1f   rmse %7.3f' % ('ndip=%d nu=%g mu=%g' % (key[0], key[2], key[1]),
                                                    cost[key], np.sqrt(np.mean(per[key] ** 2))))

    # ---------- 7. nested ----------
    keys = list(per)
    base_keys = [(1, m, 0.0) for m in MUS]
    n = len(P_list)
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    held, hbase, picks = [], [], []
    for sel, rep in folds:
        best = min(keys, key=lambda k: np.sqrt(np.mean(per[k][sel] ** 2)))
        bb = min(base_keys, key=lambda k: np.sqrt(np.mean(per[k][sel] ** 2)))
        picks.append(best)
        held.append(per[best][rep]); hbase.append(per[bb][rep])
    h, b = np.concatenate(held), np.concatenate(hbase)
    gw = b - h
    rs_ = np.random.RandomState(7)
    b3 = np.array([gw[rs_.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('\n=== 7. NESTED (splits BY WELL, both directions) ===')
    print('  picks %s' % [('ndip=%d' % k[0], 'mu=%g' % k[1], 'nu=%g' % k[2]) for k in picks])
    print('  selected %.3f  vs TVT-only baseline %.3f  gain %+.3f'
          % (np.sqrt(np.mean(h ** 2)), np.sqrt(np.mean(b ** 2)),
             np.sqrt(np.mean(b ** 2)) - np.sqrt(np.mean(h ** 2))))
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.3f  50th %+.3f  95th %+.3f  P(>0) %.4f'
          % (100 * np.mean(gw > 0), *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
    ok = (np.sqrt(np.mean(b ** 2)) - np.sqrt(np.mean(h ** 2)) > 0) and (np.percentile(b3, 5) > 0) \
        and (np.mean(gw > 0) > 0.5)
    print('\nGATE: nested gain > 0 AND helps a majority AND 3-well 5th > 0  ->  %s' % ('PASS' if ok else 'FAIL'))
    print('NOTE: this line is ~12.2 vs the deployed honest 8.8626 — passing would make state augmentation')
    print('      worth pursuing, NOT make the artifact submittable.')


if __name__ == '__main__':
    main()
