"""Q41 — non-homogeneous ensemble search, validated by well against the deployed honest line.

WHY THIS IS NOT A REPEAT. The 2026-07-22 corrected-gate audit tested SINGLE candidates against the 3-well
gate and every one failed, including `topk96_l75`, which has the best OOF (8.5070, +0.3556 vs deployed)
but a 3-well 5th percentile of -1.946 and beats baseline in only 59% of draws. Its recorded lesson was
that the per-well gain std (~1.3) far exceeds the mean gain, so the 5th percentile is negative for
everything.

That is a VARIANCE failure, and averaging is the one operation that reduces variance — Rule #1's
transferable class. So the question this task can actually add is:

    does an ensemble of decorrelated members clear the 3-well gate that every single member fails?

Members are the local predictions with truth on 760 wells / 3.72M rows. The genuinely decorrelated axis is
DWT (deterministic wavelet) vs PF (particle filter) — recorded corr 0.511 — while the structural-field
variants are near-duplicates of each other (Q18: pred-corr >= 0.99996), so mixing those is exactly the
"average near-duplicates" the task forbids. Both are included so the distinction is measured, not asserted.

BLOCKER, recorded rather than worked around: the frontier family exists locally only as TEST-SET
submission CSVs (14,151 rows, 3 wells, no truth). The honest+frontier ensemble the task asks for FIRST
therefore cannot be validated by well at all. It is reported as a blocker in the write-up, not guessed at.

Protocol: splits BY WELL; every weight/arm chosen NESTED; gates are (a) nested gain over the DEPLOYED
line > 0, (b) helps a majority of wells, (c) 3-well bootstrap 5th percentile > 0.

Env: OUT.
"""
import itertools

import numpy as np

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
DEPLOYED = 's_54844628'
MEMBERS = ['dwt', 'pf', 'base', 's_54844628', 's_54878409', 's_a20_w25',
           'base_k96', 's_k96_aniso', 'topk96_l75']
WEIGHTS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def main():
    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    well = z['well'].astype(str)
    truth = z['truth'].astype(np.float64)
    uw, inv = np.unique(well, return_inverse=True)
    n_w = np.bincount(inv).astype(np.float64)
    P = {m: z[m].astype(np.float64) for m in MEMBERS}
    good = np.isfinite(truth)
    for m in MEMBERS:
        good &= np.isfinite(P[m])
    print('wells %d | rows %d (%d finite across all members)' % (len(uw), len(truth), good.sum()))

    inv_g, truth_g = inv[good], truth[good]
    n_wg = np.bincount(inv_g, minlength=len(uw)).astype(np.float64)
    Pg = {m: P[m][good] for m in MEMBERS}

    def sse(pred):
        return np.bincount(inv_g, weights=(pred - truth_g) ** 2, minlength=len(uw))

    def rmse(s):
        return float(np.sqrt(s.sum() / n_wg.sum()))

    S = {}
    for m in MEMBERS:
        S[('single', m)] = sse(Pg[m])

    print('\n=== members (pooled RMSE) and correlation of their ERRORS with the deployed line ===')
    e_dep = Pg[DEPLOYED] - truth_g
    print('%-14s %10s %14s' % ('member', 'pooled', 'corr(err, deployed)'))
    for m in MEMBERS:
        c = float(np.corrcoef(Pg[m] - truth_g, e_dep)[0, 1])
        print('%-14s %10.4f %14.4f' % (m, rmse(S[('single', m)]), c))

    # pairs at a weight grid  +  equal-weight triples  +  per-row median / trimmed
    for a, b in itertools.combinations(MEMBERS, 2):
        for w in WEIGHTS:
            S[('pair', (a, b, w))] = sse(w * Pg[a] + (1 - w) * Pg[b])
    tri = ['dwt', 'pf', 's_54844628', 'topk96_l75', 's_k96_aniso']
    for c3 in itertools.combinations(tri, 3):
        S[('tri', c3)] = sse(np.mean([Pg[m] for m in c3], axis=0))
        S[('med3', c3)] = sse(np.median(np.stack([Pg[m] for m in c3]), axis=0))
    S[('med5', tuple(tri))] = sse(np.median(np.stack([Pg[m] for m in tri]), axis=0))
    S[('mean5', tuple(tri))] = sse(np.mean([Pg[m] for m in tri], axis=0))
    print('\narms built: %d' % len(S))

    base_s = S[('single', DEPLOYED)]
    base_r = rmse(base_s)
    print('deployed %s pooled %.4f' % (DEPLOYED, base_r))

    print('\n=== top 12 arms by pooled RMSE ===')
    order = sorted(S, key=lambda k: rmse(S[k]))[:12]
    print('%-46s %10s %10s' % ('arm', 'pooled', 'vs dep'))
    for k in order:
        print('%-46s %10.4f %+10.4f' % (str(k)[:46], rmse(S[k]), base_r - rmse(S[k])))

    # nested selection across ALL arms, by well
    n = len(uw)
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    keys = list(S)
    held, hbase, picks = [], [], []
    for sel, rep in folds:
        best = min(keys, key=lambda k: np.sqrt(S[k][sel].sum() / n_wg[sel].sum()))
        picks.append(best)
        held.append(S[best][rep])
        hbase.append(base_s[rep])
    hs, bs = np.concatenate(held), np.concatenate(hbase)
    hc = np.concatenate([n_wg[rep] for _, rep in folds])
    nested, nbase = float(np.sqrt(hs.sum() / hc.sum())), float(np.sqrt(bs.sum() / hc.sum()))
    gw = np.sqrt(bs / hc) - np.sqrt(hs / hc)
    rs = np.random.RandomState(7)
    b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('\n=== NESTED across all %d arms, splits BY WELL ===' % len(keys))
    print('  picks: %s' % [str(p)[:60] for p in picks])
    print('  selected %.4f  vs deployed %.4f  gain %+.4f' % (nested, nbase, nbase - nested))
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.4f  50th %+.4f  95th %+.4f  P(>0) %.4f'
          % (100 * np.mean(gw > 0), *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))

    ok = (nbase - nested > 0) and (np.percentile(b3, 5) > 0) and (np.mean(gw > 0) > 0.5)
    print('\nGATE: nested gain > 0 AND helps a majority AND 3-well 5th > 0  ->  %s'
          % ('PASS' if ok else 'FAIL'))

    # does ANY arm clear the 3-well gate on its own, evaluated per-arm (not nested)?
    print('\n=== per-arm 3-well 5th percentile vs deployed (the condition every single failed in 07-22) ===')
    rows = []
    for k in keys:
        g = np.sqrt(base_s / n_wg) - np.sqrt(S[k] / n_wg)
        bb = np.array([g[rs.randint(0, n, 3)].mean() for _ in range(3000)])
        rows.append((np.percentile(bb, 5), 100 * np.mean(g > 0), rmse(S[k]), k))
    rows.sort(reverse=True)
    print('%-44s %10s %8s %10s' % ('arm', '3w 5th', 'helps%', 'pooled'))
    for p5, hp, r, k in rows[:10]:
        print('%-44s %+10.4f %7.1f%% %10.4f' % (str(k)[:44], p5, hp, r))
    print('\narms with 3-well 5th > 0: %d of %d' % (sum(1 for r in rows if r[0] > 0), len(rows)))


if __name__ == '__main__':
    main()
