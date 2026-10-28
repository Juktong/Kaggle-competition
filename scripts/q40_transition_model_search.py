"""Q40 — transition-model search on the alignment DP.

Q17 closed the EMISSION lever and established the rule that emission AUC is not a valid proxy for
trajectory quality. Q10 and N1 both name the TRANSITION model as the remaining open lever. This searches
it directly, and validates on DP OUTPUT only — never on a pointwise emission metric.

WHAT THE CURRENT TRANSITION MODEL IS (`scripts/q10_twh1_scorer_dp.py:run_dp`):

    step = C[j, lo:hi] + lam * |t - s| / BAND

i.e. an L1 penalty on the change in TVT state, one parameter, depending only on the previous state. That
is the entire transition model. Everything below is a strictly richer family containing it:

  l1     lam*|d|/BAND                          the baseline
  l2     lam*(d/BAND)^2                        quadratic — cheap small moves, expensive large ones
  huber  L2 below `hub` grid units, L1 above   small drift cheap, genuine jumps not over-penalised
  drift  lam*|d - mu|/BAND                     TRAJECTORY-DERIVED PRIOR: penalise deviation from the
                                               well's own heel-estimated drift, not from zero
  curv   lam*|d - d_prev|/BAND                 penalise CHANGE OF SLOPE rather than slope
  l1curv lam*|d|/BAND + lam2*|d - d_prev|/BAND both, 2 parameters

`mu` is estimated **only from the known prefix** (median per-row change in `TVT_input`, scaled by the
DP's row subsampling), so it is test-available. The baseline `l1` is the mu=0 special case of `drift`,
which makes that arm a clean single-factor test of "does the DP wrongly assume zero drift is free?".

PROTOCOL (inherited from Q10/Q17, and from the standing rules): splits BY WELL; >= 40 eval wells; every
transition parameter chosen NESTED (selected on one half of the eval wells, scored on the disjoint half,
both ways). Gates, per the task: nested gain over the l1 baseline > 0 AND helps > 50% of wells AND
3-well bootstrap 5th percentile > 0.

NOTE ON SUBMITTABILITY, stated up front so the gates are not over-read: this line sits at ~12.2 against
the deployed honest line's 8.86. Passing the research gates here would NOT make it submittable; it would
make the transition lever worth pursuing. Those are different bars and the report keeps them apart.

Env: MAXW_TRAIN, MAXW_EVAL, LAMS, SMOKE.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q10_twh1_scorer_dp as q10  # noqa: E402

MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '40'))
LAMS = [float(x) for x in os.environ.get('LAMS', '5,20,60,150,400').split(',')]
LAM2S = [float(x) for x in os.environ.get('LAM2S', '20,60,150').split(',')]
HUBS = [float(x) for x in os.environ.get('HUBS', '5,15').split(',')]
TWH = 1
BAND, K, STEP, SUB = q10.BAND, q10.K, q10.STEP, q10.SUB


def prefix_drift(wid):
    """Per-DP-step TVT drift estimated from the KNOWN prefix only (test-available)."""
    hw = pd.read_csv(f'{q10.D}/{wid}__horizontal_well.csv', usecols=['MD', 'Z', 'GR', 'TVT', 'TVT_input'])
    kn = hw['TVT_input'].notna().values
    v = hw['TVT_input'].values[kn].astype(float)
    if len(v) < 30:
        return 0.0
    d = np.diff(v[-400:])
    d = d[np.isfinite(d)]
    return float(np.median(d) * SUB / STEP) if len(d) else 0.0


def run_dp_v(P, variant, lam, lam2=0.0, hub=10.0):
    """Q10's beam DP with the transition term swapped. variant='l1' reproduces run_dp exactly."""
    C, S, grid = P['C'], P['S'], P['grid']
    mu = P.get('mu', 0.0)
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    beams = [([s0], 0.0)]
    for j in range(len(C)):
        cand = []
        for path, cost in beams:
            s = path[-1]
            dprev = (path[-1] - path[-2]) if len(path) >= 2 else 0.0
            lo, hi = max(0, s - BAND), min(S, s + BAND + 1)
            d = np.arange(lo, hi) - s
            if variant == 'l1':
                pen = lam * np.abs(d) / BAND
            elif variant == 'l2':
                pen = lam * (d / BAND) ** 2
            elif variant == 'huber':
                a = np.abs(d)
                pen = lam * np.where(a <= hub, 0.5 * (a / BAND) ** 2 * (BAND / max(hub, 1e-9)),
                                     (a - 0.5 * hub) / BAND)
            elif variant == 'drift':
                pen = lam * np.abs(d - mu) / BAND
            elif variant == 'curv':
                pen = lam * np.abs(d - dprev) / BAND
            elif variant == 'l1curv':
                pen = lam * np.abs(d) / BAND + lam2 * np.abs(d - dprev) / BAND
            else:
                raise ValueError(variant)
            step = C[j, lo:hi] + pen
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
    top1 = grid[np.clip(np.array(beams[0][0][1:]), 0, S - 1)]
    return float(np.sqrt(np.mean((top1 - P['tru']) ** 2)))


def arms():
    out = [('l1', dict(lam=l)) for l in LAMS]
    out += [('l2', dict(lam=l)) for l in LAMS]
    out += [('drift', dict(lam=l)) for l in LAMS]
    out += [('curv', dict(lam=l)) for l in LAMS]
    out += [('huber', dict(lam=l, hub=h)) for l in LAMS for h in HUBS]
    out += [('l1curv', dict(lam=l, lam2=l2)) for l in LAMS for l2 in LAM2S]
    return out


def nested(per, keys, P_list, base_keys):
    """2-fold nested selection BY WELL within a key set; returns (rmse, per-well array, picks)."""
    n = len(P_list)
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    held, hbase, picks = [], [], []
    for sel, rep in folds:
        best = min(keys, key=lambda k: np.sqrt(np.mean(per[k][sel] ** 2)))
        bbase = min(base_keys, key=lambda k: np.sqrt(np.mean(per[k][sel] ** 2)))
        picks.append(best)
        held.append(per[best][rep])
        hbase.append(per[bbase][rep])
    h, b = np.concatenate(held), np.concatenate(hbase)
    return float(np.sqrt(np.mean(h ** 2))), float(np.sqrt(np.mean(b ** 2))), h, b, picks


def main():
    import glob
    wids = sorted(os.path.basename(f).split('__')[0]
                  for f in glob.glob(f'{q10.D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(11)
    rng.shuffle(wids)
    tr_w, ev_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]
    print('train %d | eval %d (same split seed as Q10/Q17)' % (len(tr_w), len(ev_w)), flush=True)

    net, mu_, sd_ = q10.train_scorer(tr_w, TWH)
    P_list = [p for p in (q10.prep(w, net, mu_, sd_, TWH) for w in ev_w) if p is not None]
    for P in P_list:
        P['mu'] = prefix_drift(P['wid'])
    mus = np.array([P['mu'] for P in P_list])
    print('prepped %d wells | prefix drift per DP step: mean %+.3f  median %+.3f  |mu|>1 in %.0f%% of wells'
          % (len(P_list), mus.mean(), np.median(mus), 100 * np.mean(np.abs(mus) > 1)), flush=True)

    A = arms()
    per = {}
    for v, kw in A:
        key = (v, tuple(sorted(kw.items())))
        per[key] = np.array([run_dp_v(P, v, **kw) for P in P_list])
    flat = np.array([P['flat'] for P in P_list])
    print('flat-anchor %.3f | deployed honest reference 8.8626\n' % np.sqrt(np.mean(flat ** 2)), flush=True)

    print('%-8s %-26s %10s' % ('variant', 'params', 'pooled'))
    for v, kw in A:
        key = (v, tuple(sorted(kw.items())))
        print('%-8s %-26s %10.3f' % (v, kw, np.sqrt(np.mean(per[key] ** 2))))

    base_keys = [k for k in per if k[0] == 'l1']
    print('\n=== nested, BY WELL: each variant family vs the l1 baseline family ===')
    print('%-10s %10s %10s %10s %9s %26s' % ('family', 'nested', 'l1 base', 'gain', 'helps%', 'picks'))
    results = {}
    for fam in ('l1', 'l2', 'drift', 'curv', 'huber', 'l1curv'):
        keys = [k for k in per if k[0] == fam]
        h, b, hv, bv, picks = nested(per, keys, P_list, base_keys)
        helps = 100 * np.mean(bv > hv)
        results[fam] = (h, b, hv, bv, helps)
        print('%-10s %10.3f %10.3f %+10.3f %8.1f%% %26s'
              % (fam, h, b, b - h, helps, [p[0] + str(dict(p[1])) for p in picks][:1]))

    print('\n=== ALL families pooled into one nested selection (the honest question) ===')
    h, b, hv, bv, picks = nested(per, list(per), P_list, base_keys)
    helps = 100 * np.mean(bv > hv)
    gw = bv - hv
    rs = np.random.RandomState(7)
    b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('  nested-over-everything %.3f  vs l1 baseline %.3f  gain %+.3f' % (h, b, b - h))
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.3f  50th %+.3f  95th %+.3f  P(>0) %.4f'
          % (helps, *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
    print('  picks: %s' % [(p[0], dict(p[1])) for p in picks])
    ok = (b - h > 0) and (np.percentile(b3, 5) > 0) and (helps > 50)
    print('\nGATE: nested gain > 0 AND helps > 50%% of wells AND 3-well 5th > 0  ->  %s'
          % ('PASS' if ok else 'FAIL'))
    print('NOTE: this line is ~12.2 vs the deployed honest 8.8626, so passing here would make the')
    print('      transition lever worth pursuing, NOT make this artifact submittable.')


if __name__ == '__main__':
    main()
