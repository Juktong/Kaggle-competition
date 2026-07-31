"""Q54 — cumulative corridor constraint on the alignment DP (the Sakoe-Chiba analogue).

SCOPE CORRECTION, made before running anything. The task asked for "Sakoe-Chiba corridor + Itakura slope
limits". The slope-limit half is ALREADY CLOSED by N1, and with a better constraint than the generic
Itakura cap: N1 derived the admissible PER-STEP interval from well geometry,

    t - s  in  [ (-dZ - tan(dmax)*dH)/STEP , (-dZ + tan(dmax)*dH)/STEP ]

and tested `unbounded` / `centred` / `bounded(dmax)` at 4/8/16 degrees under nested selection. Its verdict
was negative: the band binds 83-97% of transitions, so it is not inert, but it does not improve the DP.
Re-running a generic per-step cap would be a strictly weaker repeat of that, so it is not done here.

WHAT IS ACTUALLY UNTESTED is the CUMULATIVE corridor. N1's bound is per-step, between consecutive rows;
Sakoe-Chiba's is GLOBAL, on total deviation from the reference. These are different objects, and the
distinction is exactly Q40's mechanism: a per-step allowance does not bound accumulation, because ~477
steps each permitted a fractional move still permit unbounded total drift. A global corridor bounds the
accumulated deviation REGARDLESS of path length.

So this script tests one thing:

    admissible states at step j:  |state_j - anchor_state| <= C          (hard mask, not a penalty)

swept jointly with lambda and chosen NESTED by well. C = infinity reproduces the current DP exactly, which
is checked as a degeneracy control.

A BINDING DIAGNOSTIC IS REPORTED FROM THE START. N1's first smoke reported the band binding on 0.0% of
transitions, which was an artefact of asking the wrong question; that cost a debugging round. Here the
fraction of steps at which the corridor actually excludes the unconstrained argmin is measured directly,
so an inert constraint cannot be mistaken for a tested one.

Protocol: Q10/Q40 harness, same split seed, >= 40 eval wells, splits BY WELL, nested selection, validated
on DP OUTPUT only (Q17's rule).

Env: MAXW_TRAIN, MAXW_EVAL, LAMS, CORRS.
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
CORRS = [float(x) for x in os.environ.get('CORRS', '20,40,80,160,320,1e9').split(',')]
TWH = 1
BAND, K, STEP = q10.BAND, q10.K, q10.STEP


def run_dp_corr(P, lam, C, count_bind=False):
    """Q10's beam DP plus a HARD cumulative corridor |state - anchor| <= C. C=inf reproduces run_dp."""
    Cm, S, grid = P['C'], P['S'], P['grid']
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    lo_g, hi_g = max(0, int(np.floor(s0 - C))), min(S, int(np.ceil(s0 + C)) + 1)
    beams = [([s0], 0.0)]
    nb_bind = nb_tot = 0
    for j in range(len(Cm)):
        cand = []
        for path, cost in beams:
            s = path[-1]
            lo, hi = max(0, s - BAND), min(S, s + BAND + 1)
            step = Cm[j, lo:hi] + lam * np.abs(np.arange(lo, hi) - s) / BAND
            if count_bind:
                nb_tot += 1
                a = lo + int(np.argmin(step))
                if a < lo_g or a >= hi_g:
                    nb_bind += 1
            clo, chi = max(lo, lo_g), min(hi, hi_g)
            if chi <= clo:                       # corridor excludes the whole window: clamp to its edge
                t_abs = int(np.clip(s, lo_g, hi_g - 1))
                cand.append((path + [t_abs], cost + float(Cm[j, t_abs] + lam * abs(t_abs - s) / BAND)))
                continue
            sub = step[clo - lo:chi - lo]
            for t in np.argsort(sub)[:K]:
                cand.append((path + [clo + int(t)], cost + float(sub[t])))
        cand.sort(key=lambda v: v[1])
        seen, beams = set(), []
        for p_, c_ in cand:
            if p_[-1] in seen:
                continue
            seen.add(p_[-1])
            beams.append((p_, c_))
            if len(beams) >= K:
                break
    top1 = grid[np.clip(np.array(beams[0][0][1:]), 0, S - 1)]
    r = float(np.sqrt(np.mean((top1 - P['tru']) ** 2)))
    return (r, nb_bind / max(nb_tot, 1)) if count_bind else r


def main():
    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(f'{q10.D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print('train %d | eval %d (same split seed as Q10/Q40)' % (len(tr_w), len(ev_w)), flush=True)
    net, mu_, sd_ = q10.train_scorer(tr_w, TWH)
    P_list = [p for p in (q10.prep(w, net, mu_, sd_, TWH) for w in ev_w) if p is not None]
    flat = np.array([P['flat'] for P in P_list])
    print('prepped %d wells | flat-anchor %.3f | deployed honest 8.8626\n'
          % (len(P_list), np.sqrt(np.mean(flat ** 2))), flush=True)

    # degeneracy control: C = inf must reproduce Q40's l1 arm exactly
    print('=== degeneracy control: C = inf vs the unconstrained run_dp ===')
    for lam in LAMS:
        a = np.array([q10.run_dp(P, lam) for P in P_list])
        b = np.array([run_dp_corr(P, lam, 1e9) for P in P_list])
        print('  lam %-6g max|corridor(inf) - run_dp| = %.10f' % (lam, np.abs(a - b).max()))

    per, bind = {}, {}
    for lam in LAMS:
        for C in CORRS:
            rs, bs = [], []
            for P in P_list:
                r, f = run_dp_corr(P, lam, C, count_bind=True)
                rs.append(r); bs.append(f)
            per[(lam, C)] = np.array(rs)
            bind[(lam, C)] = float(np.mean(bs))

    print('\n=== pooled RMSE by (lam, corridor C) — and how often the corridor BINDS ===')
    print('%-8s %s' % ('lam', ''.join('%14s' % ('C=%g' % c if c < 1e8 else 'C=inf') for c in CORRS)))
    for lam in LAMS:
        print('%-8g %s' % (lam, ''.join('%14.3f' % np.sqrt(np.mean(per[(lam, c)] ** 2)) for c in CORRS)))
    print('%-8s %s' % ('bind%', ''.join('%13.1f%%' % (100 * bind[(LAMS[0], c)]) for c in CORRS)))

    keys = list(per)
    base_keys = [(l, 1e9) for l in LAMS]
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
    print('\n=== NESTED (corridor + lam) vs the unconstrained DP, splits BY WELL ===')
    print('  picks %s' % [(l, ('inf' if c > 1e8 else c)) for l, c in picks])
    print('  selected %.3f  vs unconstrained %.3f  gain %+.3f'
          % (np.sqrt(np.mean(h ** 2)), np.sqrt(np.mean(b ** 2)), np.sqrt(np.mean(b ** 2)) - np.sqrt(np.mean(h ** 2))))
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.3f  50th %+.3f  95th %+.3f  P(>0) %.4f'
          % (100 * np.mean(gw > 0), *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
    ok = (np.sqrt(np.mean(b ** 2)) - np.sqrt(np.mean(h ** 2)) > 0) and (np.percentile(b3, 5) > 0) \
        and (np.mean(gw > 0) > 0.5)
    print('\nGATE: nested gain > 0 AND helps a majority AND 3-well 5th > 0  ->  %s' % ('PASS' if ok else 'FAIL'))
    print('NOTE: this line is ~12.2 vs the deployed honest 8.8626 — passing would make the transition lever')
    print('      worth pursuing, NOT make the artifact submittable.')


if __name__ == '__main__':
    main()
