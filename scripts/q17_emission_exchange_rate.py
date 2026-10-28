"""Q17 prerequisite — how much emission AUC would a learned scorer need to matter?

Q17 proposes spending a Kaggle GPU run on a tiny LEARNED scorer/ranker, justified by the Q10/Q11/Q13
signal. Before spending it, the premise is testable at zero GPU cost.

Q10 established the exchange rate between emission quality and DP trajectory error from exactly TWO
points (TWH=8 AUC 0.7331 -> DP 13.206; TWH=1 AUC 0.7632 -> DP 12.170), i.e. ~1 RMSE per +0.03 AUC, and
concluded that closing the remaining 12.17 -> 8.86 gap "would need an implausible AUC". A two-point slope
is a weak basis for a 3.3 RMSE extrapolation, and it is precisely the premise Q17 rests on.

This script replaces the two-point slope with the full CURVE. It interpolates the learned TWH=1 emission
toward an ORACLE emission and sweeps the mixing weight:

    C_mix(alpha) = z( (1 - alpha) * z(C_learned) + alpha * z(C_oracle) ),   C_oracle[j,s] = |grid[s] - tru[j]|

Lower C is better in this DP, so C_oracle is a perfect emission. Sweeping alpha from 0 to 1 walks the
emission continuously from "what we actually have" to "perfect", and at each step measures BOTH:

  - held-out-WELL pair AUC, on Q10's negative-sampling protocol (true state vs a state 8-60 grid units
    away), so the AUC axis is directly comparable to N3's and Q10's numbers;
  - the nested DP trajectory RMSE, using Q10's DP, wells, protocol and 2-fold nesting unchanged.

The output answers the question Q17 actually needs: what AUC must a learned scorer reach before the DP
line reaches the deployed honest line's 8.8626? If that AUC is far outside what a tiny model could add to
0.763, the GPU run is not warranted and Q17 closes on arithmetic rather than on a training run.

Protocol is inherited from Q10 unchanged: splits BY WELL, >= 40 eval wells, transition hyper-parameter
chosen NESTED (selected on one half of the eval wells, scored on the disjoint half, both ways).

Env: MAXW_TRAIN, MAXW_EVAL, ALPHAS, LAMS, SMOKE.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q10_twh1_scorer_dp as q10  # noqa: E402  (reuse Q10's loader, scorer, prep and DP verbatim)

MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
ALPHAS = [float(x) for x in os.environ.get('ALPHAS', '0,0.05,0.1,0.2,0.35,0.5,0.75,1.0').split(',')]
LAMS = [float(x) for x in os.environ.get('LAMS', '1,5,20,60,150,400').split(',')]
TWH = 1
DEPLOYED = 8.8626   # deployed honest line 54844628, pooled toe RMSE
STEP = q10.STEP


def zrow(A):
    """Per-row z-score, matching how Q10 normalises its emission."""
    return (A - A.mean(1, keepdims=True)) / (A.std(1, keepdims=True) + 1e-9)


def build_oracle(P):
    """Perfect emission: cost rises with distance from the true TVT. Lower is better, as in Q10."""
    grid = P['grid']
    return zrow(np.abs(grid[None, :] - P['tru'][:, None]))


def auc_of(P_list, alpha, rs_seed=7):
    """Held-out-WELL pair AUC of the mixed emission, on Q10's negative-sampling protocol."""
    from sklearn.metrics import roc_auc_score
    rs = np.random.RandomState(rs_seed)
    sc, lab = [], []
    for P in P_list:
        Cm = P['Cmix'][alpha]
        S, grid = P['S'], P['grid']
        for j in range(len(Cm)):
            s_true = int(round((P['tru'][j] - grid[0]) / STEP))
            if s_true < 0 or s_true >= S:
                continue
            off = int(rs.choice([-1, 1]) * rs.randint(8, 60))
            s_neg = s_true + off
            if s_neg < 0 or s_neg >= S:
                continue
            # lower C is better, so the discriminant score is -C
            sc.extend([-Cm[j, s_true], -Cm[j, s_neg]])
            lab.extend([1.0, 0.0])
    return float(roc_auc_score(lab, sc)) if len(set(lab)) == 2 else float('nan')


def nested_dp(P_list, alpha):
    """Q10's 2-fold nesting: lam selected on one half of the wells, scored on the disjoint half."""
    per = {}
    for lam in LAMS:
        per[lam] = np.array([q10.run_dp(dict(P, C=P['Cmix'][alpha]), lam) for P in P_list])
    n = len(P_list)
    idx = np.arange(n)
    folds = [(idx[:n // 2], idx[n // 2:]), (idx[n // 2:], idx[:n // 2])]
    fl = np.array([P['flat'] for P in P_list])
    held, held_flat, picks = [], [], []
    for sel, rep in folds:
        best = min(LAMS, key=lambda l: np.sqrt(np.mean(per[l][sel] ** 2)))
        picks.append(best)
        held.append(per[best][rep])
        held_flat.append(fl[rep])
    hd = float(np.sqrt(np.mean(np.concatenate(held) ** 2)))
    hf = float(np.sqrt(np.mean(np.concatenate(held_flat) ** 2)))
    beats = float(np.mean(np.concatenate(held) < np.concatenate(held_flat)))
    fixed = {lam: float(np.sqrt(np.mean(per[lam] ** 2))) for lam in LAMS}
    return hd, hf, beats, picks, fixed


def main():
    import glob
    smoke = os.environ.get('SMOKE', '0') == '1'
    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(f'{q10.D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)          # same seed as Q10 -> same split
    rng.shuffle(wids)
    tr_w = wids[:MAXW_TRAIN]
    ev_w = wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print('train wells %d | eval wells %d (DISJOINT, same split seed as Q10)' % (len(tr_w), len(ev_w)))
    print('ALPHAS %s' % ALPHAS)
    print('LAMS   %s' % LAMS, flush=True)

    t0 = time.time()
    net, mu, sd = q10.train_scorer(tr_w, TWH)
    print('scorer trained in %.1fs; held-out-WELL AUC (Q10 protocol) = %.4f'
          % (time.time() - t0, q10.scorer_auc(net, mu, sd, ev_w, TWH)), flush=True)

    t0 = time.time()
    P_list = [p for p in (q10.prep(w, net, mu, sd, TWH) for w in ev_w) if p is not None]
    print('prepped %d eval wells in %.1fs (emission computed ONCE, reused for every alpha)'
          % (len(P_list), time.time() - t0), flush=True)

    for P in P_list:
        Cz = zrow(P['C'])
        Oz = build_oracle(P)
        P['Cmix'] = {a: zrow((1 - a) * Cz + a * Oz) for a in ALPHAS}

    flat_all = float(np.sqrt(np.mean([P['flat'] ** 2 for P in P_list])))
    print('\nflat-anchor on these %d wells: %.3f   deployed honest reference: %.4f\n'
          % (len(P_list), flat_all, DEPLOYED), flush=True)

    print('%-7s %9s %12s %10s %13s %14s' % ('alpha', 'AUC', 'nested DP', 'flat', 'beats flat %', 'lam picks'))
    rows, fixed_rows = [], []
    for a in ALPHAS:
        t = time.time()
        auc = auc_of(P_list, a)
        hd, hf, beats, picks, fixed = nested_dp(P_list, a)
        rows.append((a, auc, hd))
        fixed_rows.append((a, auc, fixed))
        print('%-7g %9.4f %12.3f %10.3f %12.1f%% %14s   (%.0fs)'
              % (a, auc, hd, hf, 100 * beats, '/'.join('%g' % p for p in picks), time.time() - t),
              flush=True)

    # CONTROL: is the flatness a real property of the emission, or just lam-selection noise?
    # Show every FIXED lam across alpha. If no single lam improves as AUC rises in the reachable
    # range, the flatness is a property of the DP, not of the nesting.
    print('\n=== control: DP at every FIXED lam (no selection) ===')
    print('%-7s %8s %s' % ('alpha', 'AUC', ''.join('%9s' % ('lam=%g' % l) for l in LAMS)))
    for a, auc, fx in fixed_rows:
        print('%-7g %8.4f %s' % (a, auc, ''.join('%9.3f' % fx[l] for l in LAMS)))
    print('flat-anchor %.3f on all rows above' % flat_all)
    reach = [(a, auc, fx) for a, auc, fx in fixed_rows if auc <= 0.82]
    if len(reach) >= 2:
        print('\n  within the reachable AUC range (<= 0.82), best fixed-lam DP per alpha:')
        for a, auc, fx in reach:
            bl = min(LAMS, key=lambda l: fx[l])
            print('    alpha %-6g AUC %.4f -> best %8.3f at lam=%g' % (a, auc, fx[bl], bl))

    print('\n=== what AUC would a learned scorer need? ===')
    A = np.array([r[1] for r in rows])
    R = np.array([r[2] for r in rows])
    ok = np.isfinite(A) & np.isfinite(R)
    A, R = A[ok], R[ok]
    order = np.argsort(A)
    A, R = A[order], R[order]
    if R.min() <= DEPLOYED <= R.max():
        auc_needed = float(np.interp(DEPLOYED, R[::-1], A[::-1]))
        print('  DP reaches the deployed %.4f at emission AUC ~ %.4f' % (DEPLOYED, auc_needed))
        print('  current learned-scorer AUC ~ %.4f  ->  required improvement %+.4f AUC'
              % (A[0], auc_needed - A[0]))
    else:
        print('  the deployed %.4f is not bracketed by the swept range (DP spans %.3f..%.3f)'
              % (DEPLOYED, R.min(), R.max()))
    if len(A) >= 2:
        print('  local exchange rate near the current operating point: %.2f RMSE per +0.01 AUC'
              % ((R[0] - R[1]) / max(A[1] - A[0], 1e-9) * 0.01))
    print('\n  Q10 two-point reference: ~1.0 RMSE per +0.03 AUC (i.e. 0.35 RMSE per +0.01 AUC)')
    print('\nGATE: a Kaggle GPU run on a tiny learned scorer is warranted only if the AUC it would need')
    print('      is a plausible increment on the current ~0.76, given the model is a small MLP on 17')
    print('      hand-built features and N3 already measured the TWH sweep.')
    if smoke:
        print('\n[SMOKE] completed end-to-end; scale up by unsetting SMOKE.')


if __name__ == '__main__':
    main()
