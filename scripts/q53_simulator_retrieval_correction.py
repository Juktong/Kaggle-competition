"""Q53 — re-run the final-pair views with Q39's corrected stage decomposition.

WHAT WAS WRONG. `scripts/final_selection_simulator.py` and `scripts/q18_final_pair_stress.py` encode
`retrieval = 0.080` for overlap-ON candidates, documented as `54968060 6.643 - 54922806 6.563`. Q39's code
diff showed those two kernels differ in TWO stages: `54922806` also carries `*1.3` on the PF GR sigma.
Against the pristine baseline (6.6735, the mean of the code-identical replicate pair 54896975 6.669 /
54923144 6.678):

    overlap / retrieval   54968060 6.643 vs 6.6735  ->  -0.031   (overlap OFF slightly HELPS)
    GR sigma *1.3         54922806 6.563 vs 6.6735  ->  -0.1105

and -0.1105 - (-0.031) = -0.080 reproduces the old figure as a difference of two different stages.

TWO AXES, because one of them is the whole argument.

  retrieval_delta : what an overlap-ON candidate gains when overlap goes inert on novel wells.
                    measured -0.031; swept over {-0.031, 0.0, +0.080 (the old, wrong assumption)}.

  sigma_transfers : whether 54922806's GR-sigma edge survives on novel wells.
                    TRUE  -> it keeps the -0.1105 (it is a likelihood-width parameter, not a lookup).
                    FALSE -> under H-hidden it reverts to the pristine baseline.
                    Q36 measured this exact multiplier on 760 wells with truth: it helps only 42.1% of
                    wells with a NEGATIVE median per-well gain. So FALSE is the arm our own held-out
                    evidence supports, and it is NOT a pessimistic strawman.

Everything is arithmetic over already-recorded public scores. No GPU, no smoke, no submission.
"""
import itertools

PRISTINE = 6.6735          # mean of the code-identical replicate pair (spread 0.009)
SIGMA_EDGE = -0.1105       # 54922806 6.563 - PRISTINE
HYPS = ['H-visible', 'H-hidden', 'mixed']

# stage composition per candidate, from Q39's code diffs
CAND = {
    '54922806_frontier': dict(public=6.563, overlap_on=True,  has_sigma=True,
                              family='frontier', account='teammate', prov='public-derived', oof=False),
    '54968060_frontier': dict(public=6.643, overlap_on=False, has_sigma=False,
                              family='frontier', account='ours', prov='public-derived', oof=False),
    '54896975_frontier': dict(public=6.669, overlap_on=True,  has_sigma=False,
                              family='frontier', account='teammate', prov='public-derived', oof=False),
    '54923144_frontier': dict(public=6.678, overlap_on=True,  has_sigma=False,
                              family='frontier', account='teammate', prov='public-derived', oof=False),
    '54990075_frontier': dict(public=6.690, overlap_on=False, has_sigma=False,
                              family='frontier', account='ours', prov='public-derived', oof=False),
    '55064411_frontier': dict(public=6.695, overlap_on=False, has_sigma=False,
                              family='frontier', account='ours', prov='public-derived', oof=False),
    '54844628_honest':   dict(public=7.891, overlap_on=False, has_sigma=False,
                              family='honest', account='ours', prov='fully owned', oof=True),
}
PAIR_A = ('54922806_frontier', '54844628_honest')     # score / diversity / provenance-first
PAIR_B = ('54968060_frontier', '54844628_honest')     # our-account-first


def score(c, hyp, rdelta, sigma_transfers):
    d = CAND[c]
    s = d['public']
    if hyp == 'H-visible':
        return s
    hidden = s
    if d['overlap_on']:
        hidden += rdelta                       # overlap goes inert on novel wells
    if d['has_sigma'] and not sigma_transfers:
        hidden -= SIGMA_EDGE                   # the edge does not survive -> revert toward baseline
    if hyp == 'H-hidden':
        return hidden
    return 0.5 * (s + hidden)                  # mixed


def pair_worst(pair, rdelta, st):
    per = {h: min(score(pair[0], h, rdelta, st), score(pair[1], h, rdelta, st)) for h in HYPS}
    return max(per.values()), sum(per.values()) / len(per), per


def best_pair(rdelta, st, require=None):
    rows = []
    for p in itertools.combinations(sorted(CAND), 2):
        if require and not require(p):
            continue
        w, m, _ = pair_worst(p, rdelta, st)
        rows.append((w, m, p))
    rows.sort()
    return rows


def main():
    print('Q53 — corrected decomposition. PRISTINE %.4f | SIGMA_EDGE %+.4f\n' % (PRISTINE, SIGMA_EDGE))

    print('=== the two axes, and what each cell does to the two candidate pairs ===')
    print('%-9s %-9s | %-28s | %-28s | %s'
          % ('retrieval', 'sigma', 'A: 54922806+54844628', 'B: 54968060+54844628', 'price of B (our-account)'))
    for rdelta in (-0.031, 0.0, 0.080):
        for st in (True, False):
            wa, ma, _ = pair_worst(PAIR_A, rdelta, st)
            wb, mb, _ = pair_worst(PAIR_B, rdelta, st)
            print('%-9.3f %-9s | worst %.4f  mean %.4f | worst %.4f  mean %.4f | worst %+.4f  mean %+.4f'
                  % (rdelta, st, wa, ma, wb, mb, wb - wa, mb - ma))
    print('\n  (retrieval +0.080 with sigma=True is the OLD, confounded model; -0.031 is the measured value)')

    print('\n=== tie structure: how many pairs are within 0.01 of the best worst case? ===')
    for rdelta in (-0.031, 0.0, 0.080):
        for st in (True, False):
            rows = best_pair(rdelta, st)
            best = rows[0][0]
            tied = [r for r in rows if r[0] <= best + 0.01]
            print('  retrieval %+.3f sigma_transfers=%-5s -> best worst %.4f, %d pair(s) tied, top = %s + %s'
                  % (rdelta, st, best, len(tied), rows[0][2][0].split("_")[0], rows[0][2][1].split("_")[0]))
    print('  (Q18 under the old model reported 9 tied pairs at 6.643)')

    print('\n=== H-hidden score of the two slot-1 options, per cell ===')
    print('%-9s %-9s %14s %14s %10s' % ('retrieval', 'sigma', '54922806', '54968060', 'gap'))
    for rdelta in (-0.031, 0.0, 0.080):
        for st in (True, False):
            a = score('54922806_frontier', 'H-hidden', rdelta, st)
            b = score('54968060_frontier', 'H-hidden', rdelta, st)
            print('%-9.3f %-9s %14.4f %14.4f %10.4f' % (rdelta, st, a, b, b - a))

    print('\n=== four views under the MEASURED cell (retrieval -0.031) ===')
    for st in (True, False):
        print('\n--- sigma_transfers = %s ---' % st)
        views = {
            'score-first': best_pair(-0.031, st)[0],
            'diversity-first': best_pair(-0.031, st, lambda p: CAND[p[0]]['family'] != CAND[p[1]]['family'])[0],
            'provenance-first': best_pair(-0.031, st, lambda p: any(CAND[x]['oof'] and CAND[x]['prov'] == 'fully owned' for x in p))[0],
            'our-account-first': best_pair(-0.031, st, lambda p: all(CAND[x]['account'] == 'ours' for x in p))[0],
        }
        for k, (w, m, p) in views.items():
            print('  %-18s %-24s worst %.4f  mean %.4f' % (k, p[0].split('_')[0] + ' + ' + p[1].split('_')[0], w, m))


if __name__ == '__main__':
    main()
