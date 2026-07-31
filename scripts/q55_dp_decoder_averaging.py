"""Q55 — DP decoder averaging: beam average, and a forward-backward soft-min posterior.

Q54 left an explicit instruction: MEASURE THE K=6 BEAM SPREAD FIRST and report it before anything else,
because if the beam holds six near-identical paths then averaging it is inert by construction. That
diagnostic is section 1 and runs before any arm.

TWO OPERATORS, both leaving emission and transition untouched:

  A. BEAM AVERAGE. `run_dp` keeps K=6 beams and returns beams[0]. Average them weighted by exp(-cost/T).
     T -> 0 recovers beams[0] exactly, which is checked as a degeneracy control.

  B. FORWARD-BACKWARD SOFT-MIN POSTERIOR. The beam is only 6 paths. The proper soft-DTW /
     differentiable-DP operator replaces the hard min in the Bellman recursion with a soft-min at
     temperature gamma over ALL states, then reports the posterior MEAN state at each step:

         V_j(t) = C[j,t] + softmin_gamma_s( V_{j-1}(s) + pen(s,t) )      forward
         W_j(t) = softmin_gamma_u( W_{j+1}(u) + C[j+1,u] + pen(t,u) )    backward
         posterior_j propto exp( -(V_j + W_j) / gamma ),  output its mean

     This is a genuinely different object from the beam: it spans every state rather than six paths, and
     it is the operator Q21 found already deployed inside the PF ensemble (a softmax over paths at T=5,
     sitting at a nested optimum of a 27-member family). It has never been applied to the DP.

Protocol: Q10/Q40 harness, same split seed, >= 40 eval wells, splits BY WELL, every temperature chosen
NESTED, validated on DP OUTPUT only (Q17's rule).

Env: MAXW_TRAIN, MAXW_EVAL, LAMS, TS, GAMMAS.
"""
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q10_twh1_scorer_dp as q10  # noqa: E402

MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
LAMS = [float(x) for x in os.environ.get('LAMS', '20,60,150').split(',')]
TS = [float(x) for x in os.environ.get('TS', '0.01,0.1,0.5,2,10').split(',')]
GAMMAS = [float(x) for x in os.environ.get('GAMMAS', '0.05,0.2,1.0,5.0').split(',')]
TWH = 1
BAND, K, STEP = q10.BAND, q10.K, q10.STEP


def beams_of(P, lam):
    """Q10's run_dp, but returning the whole beam (paths + costs) instead of only beams[0]."""
    C, S, grid = P['C'], P['S'], P['grid']
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    beams = [([s0], 0.0)]
    for j in range(len(C)):
        cand = []
        for path, cost in beams:
            s = path[-1]
            lo, hi = max(0, s - BAND), min(S, s + BAND + 1)
            step = C[j, lo:hi] + lam * np.abs(np.arange(lo, hi) - s) / BAND
            for t in np.argsort(step)[:K]:
                cand.append((path + [lo + int(t)], cost + float(step[t])))
        cand.sort(key=lambda v: v[1])
        seen, beams = set(), []
        for p_, c_ in cand:
            if p_[-1] in seen:
                continue
            seen.add(p_[-1])
            beams.append((p_, c_))
            if len(beams) >= K:
                break
    paths = np.array([b[0][1:] for b in beams], float)
    costs = np.array([b[1] for b in beams], float)
    return paths, costs, grid, S


def beam_avg_rmse(P, lam, T):
    paths, costs, grid, S = beams_of(P, lam)
    c = costs - costs.min()
    w = np.exp(-c / max(T, 1e-12))
    w /= w.sum()
    st = (w[:, None] * paths).sum(0)
    pred = np.interp(st, np.arange(S), grid)
    return float(np.sqrt(np.mean((pred - P['tru']) ** 2)))


def softmin(A, g, axis):
    m = A.min(axis=axis, keepdims=True)
    return (m - g * np.log(np.exp(-(A - m) / g).sum(axis=axis, keepdims=True))).squeeze(axis)


def fb_softmin_rmse(P, lam, g):
    """Forward-backward soft-min posterior mean over ALL states."""
    C, S, grid = P['C'], P['S'], P['grid']
    n = len(C)
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    offs = np.arange(-BAND, BAND + 1)
    pen = lam * np.abs(offs) / BAND                      # transition cost by offset
    BIG = 1e9

    def sweep(V):
        """softmin over s of V[s] + pen(s->t), for every t. Windowed by BAND."""
        out = np.full(S, BIG)
        M = np.full((len(offs), S), BIG)
        for i, o in enumerate(offs):
            src = np.roll(V, o)                          # V at s = t - o
            if o > 0:
                src[:o] = BIG
            elif o < 0:
                src[o:] = BIG
            M[i] = src + pen[i]
        out = softmin(M, g, axis=0)
        return out

    V = np.full(S, BIG)
    V[s0] = 0.0
    Vs = np.empty((n, S))
    for j in range(n):
        V = sweep(V) + C[j]
        Vs[j] = V
    W = np.zeros(S)
    Ws = np.empty((n, S))
    for j in range(n - 1, -1, -1):
        Ws[j] = W
        if j > 0:
            W = sweep(W + C[j])
    A = Vs + Ws
    A -= A.min(axis=1, keepdims=True)
    Pst = np.exp(-A / g)
    Pst /= Pst.sum(axis=1, keepdims=True)
    st = (Pst * np.arange(S)[None, :]).sum(1)
    pred = np.interp(st, np.arange(S), grid)
    return float(np.sqrt(np.mean((pred - P['tru']) ** 2)))


def exact_dp(P, lam):
    """EXACT Viterbi over ALL states — the true optimum of the SAME objective run_dp approximates.

    Included because the smoke revealed the soft-min posterior converging to a state far from the anchor.
    That turned out not to be a bug: it is the objective's real optimum, and it is far worse in RMSE. This
    arm measures both the objective cost and the RMSE so the two can be compared directly.
    """
    C, S, grid = P['C'], P['S'], P['grid']
    n = len(C)
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    offs = np.arange(-BAND, BAND + 1)
    pen = lam * np.abs(offs) / BAND
    BIG = 1e18
    V = np.full(S, BIG)
    V[s0] = 0.0
    bp = np.zeros((n, S), np.int32)
    for j in range(n):
        M = np.full((len(offs), S), BIG)
        for i, o in enumerate(offs):
            src = np.roll(V, o)
            if o > 0:
                src[:o] = BIG
            elif o < 0:
                src[o:] = BIG
            M[i] = src + pen[i]
        k = M.argmin(0)
        V = M[k, np.arange(S)] + C[j]
        bp[j] = np.arange(S) - offs[k]
    t = int(V.argmin())
    best = float(V.min())
    path = [t]
    for j in range(n - 1, 0, -1):
        t = int(bp[j, t])
        path.append(t)
    pred = grid[np.array(path[::-1])]
    return best, float(np.sqrt(np.mean((pred - P['tru']) ** 2)))


def beam_cost_only(P, lam):
    paths, costs, grid, S = beams_of(P, lam)
    return float(costs[0])


def nested(per, keys, base_keys, n):
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    held, hbase, picks = [], [], []
    for sel, rep in folds:
        b = min(keys, key=lambda k: np.sqrt(np.mean(per[k][sel] ** 2)))
        bb = min(base_keys, key=lambda k: np.sqrt(np.mean(per[k][sel] ** 2)))
        picks.append(b)
        held.append(per[b][rep]); hbase.append(per[bb][rep])
    return np.concatenate(held), np.concatenate(hbase), picks


def main():
    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(f'{q10.D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    net, mu_, sd_ = q10.train_scorer(tr_w, TWH)
    P_list = [p for p in (q10.prep(w, net, mu_, sd_, TWH) for w in ev_w) if p is not None]
    print('train %d | eval %d | prepped %d\n' % (len(tr_w), len(ev_w), len(P_list)), flush=True)

    # ---- 1. BEAM SPREAD DIAGNOSTIC, first, as Q54 instructed -------------------------------------
    print('=== 1. K=6 BEAM SPREAD (Q54 required this before anything else) ===')
    print('%-8s %14s %14s %14s %14s' % ('lam', 'mean row range', 'p90 row range', 'max row range', 'rmse b0 vs bK'))
    for lam in LAMS:
        rng_, mx_, dr_ = [], [], []
        for P in P_list:
            paths, costs, grid, S = beams_of(P, lam)
            rr = paths.max(0) - paths.min(0)
            rng_.append(rr.mean()); mx_.append(rr.max())
            p0 = np.interp(paths[0], np.arange(S), grid)
            pk = np.interp(paths[-1], np.arange(S), grid)
            dr_.append(np.sqrt(np.mean((p0 - pk) ** 2)))
        print('%-8g %14.3f %14.3f %14.3f %14.3f'
              % (lam, np.mean(rng_), np.percentile(rng_, 90), np.max(mx_), np.mean(dr_)), flush=True)
    print('  (row range = spread across the 6 beams at one row, in grid units ~ ft;')
    print('   truth deviates +-19.4 ft from the anchor, and the DP path only +-3.0 -- Q54)')

    per = {}
    for lam in LAMS:
        per[('base', lam)] = np.array([q10.run_dp(P, lam) for P in P_list])
        for T in TS:
            per[('beam', lam, T)] = np.array([beam_avg_rmse(P, lam, T) for P in P_list])
    print('\n=== 2. degeneracy control: beam average at T -> 0 must equal run_dp ===')
    for lam in LAMS:
        d = np.abs(per[('beam', lam, min(TS))] - per[('base', lam)]).max()
        print('  lam %-6g T=%-6g max|beam_avg - run_dp| = %.10f' % (lam, min(TS), d))

    for lam in LAMS:
        for g in GAMMAS:
            per[('fb', lam, g)] = np.array([fb_softmin_rmse(P, lam, g) for P in P_list])
        print('  fb softmin done for lam=%g' % lam, flush=True)

    print('\n=== 2b. THE OBJECTIVE ITSELF: exact Viterbi optimum vs the beam ===')
    print('%-8s %14s %14s | %12s %12s' % ('lam', 'beam cost', 'EXACT cost', 'beam RMSE', 'exact RMSE'))
    for lam in LAMS:
        bc = np.array([beam_cost_only(P, lam) for P in P_list])
        ec, er = zip(*[exact_dp(P, lam) for P in P_list])
        ec, er = np.array(ec), np.array(er)
        per[('exact', lam)] = er
        print('%-8g %14.1f %14.1f | %12.3f %12.3f'
              % (lam, bc.mean(), ec.mean(),
                 float(np.sqrt(np.mean(per[('base', lam)] ** 2))), float(np.sqrt(np.mean(er ** 2)))),
              flush=True)
        print('        exact cost lower on %d/%d wells (it is the true optimum), yet exact RMSE worse on %d/%d'
              % ((ec < bc).sum(), len(bc), (er > per[('base', lam)]).sum(), len(er)))

    R = lambda a: float(np.sqrt(np.mean(a ** 2)))
    print('\n=== 3. pooled RMSE ===')
    print('%-8s %10s | %s | %s' % ('lam', 'base',
                                   ' '.join('T=%-6g' % t for t in TS),
                                   ' '.join('g=%-6g' % g for g in GAMMAS)))
    for lam in LAMS:
        print('%-8g %10.3f | %s | %s'
              % (lam, R(per[('base', lam)]),
                 ' '.join('%8.3f' % R(per[('beam', lam, t)]) for t in TS),
                 ' '.join('%8.3f' % R(per[('fb', lam, g)]) for g in GAMMAS)))

    base_keys = [('base', l) for l in LAMS]
    n = len(P_list)
    for name, keys in (('beam average only', [k for k in per if k[0] in ('base', 'beam')]),
                       ('soft-min only', [k for k in per if k[0] in ('base', 'fb')]),
                       ('both', list(per))):
        h, b, picks = nested(per, keys, base_keys, n)
        gw = b - h
        rs = np.random.RandomState(7)
        b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
        ok = (R(b) - R(h) > 0) and (np.percentile(b3, 5) > 0) and (np.mean(gw > 0) > 0.5)
        print('\n=== NESTED: %s ===' % name)
        print('  picks %s' % picks)
        print('  selected %.3f  vs base %.3f  gain %+.3f | helps %.1f%% | 3-well 5th %+.3f  P(>0) %.4f  -> %s'
              % (R(h), R(b), R(b) - R(h), 100 * np.mean(gw > 0), np.percentile(b3, 5), (b3 > 0).mean(),
                 'PASS' if ok else 'FAIL'))
    print('\nNOTE: ~12.2 here vs the deployed honest 8.8626 — passing would make the lever worth pursuing,')
    print('      NOT make the artifact submittable.')


if __name__ == '__main__':
    main()
