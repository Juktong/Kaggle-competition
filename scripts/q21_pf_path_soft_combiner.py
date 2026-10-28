"""Q21 — soft combiners over the 96 stored PF candidate paths.

Q11 measured, on these same artifacts: PF mean 10.9905, ORACLE best-of-96 7.1579 (better than the deployed
honest 8.8626), worst-of-96 22.1407. A truth-free top-K RANKER converted only +0.1492 = 3.9% of the
+3.8326 oracle headroom and failed the gate. Q11's conclusion was about HARD SELECTION.

This task tests SOFT combination instead. The framing that makes it well-posed:

    the PF mean is the T -> infinity limit of a temperature softmax over the path log-likelihoods,
    and hard selection (what Q11 closed) is the T -> 0 limit.

So sweeping T with the temperature chosen NESTED asks exactly one question: is there an interior operating
point between "average everything" and "pick the best" that beats averaging everything? Every family below
has that same shape -- one scalar that interpolates between the PF mean and something sharper:

  softmax(T)      w_i propto exp((ll_i - max)/T)          T -> inf : mean        T -> 0 : argmax
  top-m mean      uniform mean of the m best by loglik    m = 96   : mean        m = 1  : argmax
  trimmed(q)      per-row mean after trimming q tails     q = 0    : mean        q -> .5: median
  median          per-row median across the 96            (robust, no parameter)
  interp(a)       (1-a)*mean + a*best-loglik path         a = 0    : mean        a = 1  : argmax

None of these fit per-well weights, so all stay inside the class Rule #1 records as transferring; the only
fitted quantity is one global scalar, and it is nested.

Protocol: splits BY WELL; every scalar chosen NESTED (selected on one half of the wells, scored on the
disjoint half, both ways); per-well win rate and a 3-WELL bootstrap reported, plus tail risk and
non-homogeneity against the deployed line.

Env: MAXW, OUT.
"""
import glob
import os

import numpy as np

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
DEPLOYED = 8.8626           # honest line 54844628, pooled toe RMSE
MAXW = int(os.environ.get('MAXW', '10000'))

TEMPS = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 100.0]
TOPMS = [1, 2, 4, 8, 16, 32, 64, 96]
TRIMS = [0.05, 0.10, 0.20, 0.35]
INTERPS = [0.1, 0.25, 0.5, 0.75, 1.0]


def combos(paths, mean, ll):
    """Return {name: combined_path}. paths (96,n), mean (n,), ll (96,)."""
    out = {'pf_mean': mean.astype(np.float64)}
    P = paths.astype(np.float64)
    lln = ll.astype(np.float64) - ll.max()
    order = np.argsort(-lln)                       # best loglik first
    best = P[order[0]]
    for T in TEMPS:
        w = np.exp(lln / T)
        w /= w.sum()
        out[f'softmax_T{T:g}'] = (w[:, None] * P).sum(0)
    for m in TOPMS:
        out[f'topm_{m}'] = P[order[:m]].mean(0)
    out['median'] = np.median(P, axis=0)
    for q in TRIMS:
        k = int(np.floor(q * P.shape[0]))
        S = np.sort(P, axis=0)
        out[f'trim_{q:g}'] = S[k:P.shape[0] - k].mean(0) if k > 0 else P.mean(0)
    for a in INTERPS:
        out[f'interp_{a:g}'] = (1 - a) * mean.astype(np.float64) + a * best
    return out


def main():
    files = sorted(glob.glob(f'{SH}/topk96_paths/*.npz'))[:MAXW]
    print('path files: %d' % len(files), flush=True)

    names = None
    sse, cnt, wells = {}, [], []
    orc, wst, mean_chk = [], [], []
    dep_sse, dep_pairs = [], []
    for i, f in enumerate(files):
        z = np.load(f, allow_pickle=True)
        P, mean, tru, ll = z['paths'], z['mean'], z['truth'].astype(np.float64), z['loglik']
        g = np.isfinite(tru) & np.isfinite(mean)
        if g.sum() < 10 or P.shape[0] < 8:
            continue
        c = combos(P, mean, ll)
        if names is None:
            names = list(c)
            sse = {k: [] for k in names}
        for k in names:
            sse[k].append(float(np.sum((c[k][g] - tru[g]) ** 2)))
        cnt.append(int(g.sum()))
        wells.append(os.path.basename(f)[:-4])
        e = (P[:, g].astype(np.float64) - tru[g]) ** 2
        per = np.sqrt(e.mean(1))
        orc.append(float(np.sum(e[per.argmin()])))
        wst.append(float(np.sum(e[per.argmax()])))
        mean_chk.append(float(np.abs(P.astype(np.float64).mean(0) - mean).max()))
        if (i + 1) % 200 == 0:
            print('  %d wells' % (i + 1), flush=True)

    n = len(cnt)
    C = np.array(cnt, float)
    S = {k: np.array(v) for k, v in sse.items()}
    print('usable wells %d | rows %d' % (n, int(C.sum())))
    print('max |paths.mean(0) - stored mean| over wells: %.4g  -> stored `mean` is %s'
          % (max(mean_chk), 'the uniform mean of the 96' if max(mean_chk) < 1e-3 else 'NOT the uniform mean'))

    R = lambda a: float(np.sqrt(a.sum() / C.sum()))
    base = R(S['pf_mean'])
    orcR, wstR = R(np.array(orc)), R(np.array(wst))
    print('\n=== references on these %d wells ===' % n)
    print('  PF mean          %8.4f   (Q11 reference 10.9905)' % base)
    print('  ORACLE best-of-96 %7.4f   (Q11 reference  7.1579)' % orcR)
    print('  worst-of-96      %8.4f   (Q11 reference 22.1407)' % wstR)
    print('  deployed honest  %8.4f' % DEPLOYED)
    print('  oracle headroom vs PF mean: %+.4f | tail risk %+.4f' % (base - orcR, base - wstR))

    print('\n=== every combiner, pooled (lower is better) ===')
    print('%-16s %10s %12s %14s' % ('combiner', 'RMSE', 'vs PF mean', '% headroom'))
    for k in names:
        r = R(S[k])
        print('%-16s %10.4f %12.4f %13.1f%%' % (k, r, base - r, 100 * (base - r) / max(base - orcR, 1e-9)))

    # nested selection ACROSS ALL families, by well
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    held, heldb, picks = [], [], []
    for sel, rep in folds:
        best_k = min(names, key=lambda k: np.sqrt(S[k][sel].sum() / C[sel].sum()))
        picks.append(best_k)
        held.append(S[best_k][rep])
        heldb.append(S['pf_mean'][rep])
    hs, bs = np.concatenate(held), np.concatenate(heldb)
    hc = np.concatenate([C[rep] for _, rep in folds])
    nested, nbase = float(np.sqrt(hs.sum() / hc.sum())), float(np.sqrt(bs.sum() / hc.sum()))
    print('\nNESTED across all %d combiners (picks %s)' % (len(names), picks))
    print('  selected %.4f  vs PF mean %.4f  gain %+.4f  (%.1f%% of oracle headroom)'
          % (nested, nbase, nbase - nested, 100 * (nbase - nested) / max(base - orcR, 1e-9)))
    print('  Q11 prior top-K ranker converted +0.1492 = 3.9%')

    gw = np.sqrt(bs / hc) - np.sqrt(hs / hc)
    rs = np.random.RandomState(7)
    b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.4f  50th %+.4f  95th %+.4f  P(>0) %.4f'
          % (100 * np.mean(gw > 0), *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))

    print('\nGATE: beat the PF mean nested AND 3-well 5th > 0 AND help a majority of wells;')
    print('      and to matter for a submission it must also come materially closer to the deployed %.4f.'
          % DEPLOYED)


if __name__ == '__main__':
    main()
