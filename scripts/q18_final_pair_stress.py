"""Q18 — final-pair stress test. Decision task: NO submission, no GPU, no Kaggle call.

Extends `scripts/final_selection_simulator.py` with everything the 2026-07-28/29 queue established.
Three additions, in order of how much they move the decision:

1. A FOURTH view — **our-account-first** (both slots from our own account). The existing package carries
   score / diversity / provenance; ownership is a distinct constraint from provenance, because
   `54968060` is our account but is public-derived, so provenance-first does not select it.

2. **The degradation stress Q18 asks for**, in closed form: how far must `54922806` degrade before
   `54968060` or `54844628` takes slot 1, under each hypothesis.

3. **The load-bearing addition — is the gap that decides slot 1 even resolvable at 3-well scale?**
   Slot 1 currently rests on 6.563 vs 6.643, a gap of 0.080. The competition scores 3 wells. N4 measured
   that the scored quantity itself spans 3.49..15.14 across random 3-well draws for a FIXED model, but
   that spread is common-mode and cancels in a ranking. What does NOT cancel is the candidate x draw
   INTERACTION: two candidates can swap order on a different 3-well subset. That interaction is
   measurable locally, on 9 candidate prediction columns with truth over 760 wells, and it is measured
   here rather than assumed: for every local candidate pair, the pooled gap is compared against the
   probability that a random 3-well draw reverses the pooled ranking.

Candidate 55064411 (Q14 frontier hedge-OFF, our account) is carried as a CONTINGENT entrant: it is still
PENDING with no public score, so it is swept parametrically rather than given an assumed value.

The true private score is not visible and is never used.
"""
import itertools
import os

import numpy as np

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
NDRAW = int(os.environ.get('NDRAW', '20000'))
DRAW_WELLS = 3            # the competition scores 3 wells

CANDIDATES = {
    '54922806_frontier_overlapON': dict(
        public=6.563, retrieval=0.080, family='frontier', account='teammate',
        prov='public-derived', oof=False),
    '54968060_frontier_overlapOFF': dict(
        public=6.643, retrieval=0.0, family='frontier', account='ours',
        prov='public-derived', oof=False),
    '54896975_frontier_overlapON': dict(
        public=6.669, retrieval=0.080, family='frontier', account='teammate',
        prov='public-derived', oof=False),
    '54923144_frontier_gr_sigma': dict(
        public=6.678, retrieval=0.080, family='frontier', account='teammate',
        prov='public-derived', oof=False),
    '54990075_frontier_sp45only': dict(
        public=6.690, retrieval=0.0, family='frontier', account='ours',
        prov='public-derived', oof=False),
    '54844628_honest': dict(
        public=7.891, retrieval=0.0, family='honest', account='ours',
        prov='fully owned', oof=True),
}
HYPS = ['H-visible', 'H-hidden', 'mixed']
NEAR_TIE = 0.01


def score(c, hyp, extra=0.0):
    d = CANDIDATES[c]
    bump = extra if c == '54922806_frontier_overlapON' else 0.0
    if hyp == 'H-visible':
        return d['public'] + bump
    if hyp == 'H-hidden':
        return d['public'] + d['retrieval'] + bump
    return d['public'] + 0.5 * d['retrieval'] + bump


def pair_rows(extra=0.0):
    rows = []
    for pair in itertools.combinations(sorted(CANDIDATES), 2):
        per = {h: min(score(pair[0], h, extra), score(pair[1], h, extra)) for h in HYPS}
        A, B = CANDIDATES[pair[0]], CANDIDATES[pair[1]]
        rows.append(dict(
            pair=pair, per=per, worst=max(per.values()), mean=sum(per.values()) / len(per),
            fam_div=0.0 if A['family'] == B['family'] else 1.0,
            has_oof=A['oof'] or B['oof'],
            has_owned='fully owned' in (A['prov'], B['prov']),
            all_ours=A['account'] == 'ours' and B['account'] == 'ours'))
    rows.sort(key=lambda r: (r['worst'], r['mean']))
    return rows


def four_views(rows):
    best = rows[0]['worst']
    tied = [r for r in rows if r['worst'] <= best + NEAR_TIE]
    out = {}
    out['score-first'] = rows[0]
    out['diversity-first'] = sorted(tied, key=lambda r: (-r['fam_div'], r['mean']))[0]
    pf = [r for r in rows if r['has_owned'] and r['has_oof']]
    out['provenance-first'] = pf[0] if pf else None
    oa = [r for r in rows if r['all_ours']]
    out['our-account-first'] = oa[0] if oa else None
    return out


def nm(r):
    return '%s + %s' % (r['pair'][0].split('_')[0], r['pair'][1].split('_')[0])


# ----------------------------------------------------------------------------------------------
# 3-well draw interaction, measured on local candidates with truth
# ----------------------------------------------------------------------------------------------
def three_well_reversal():
    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    truth = z['truth'].astype(np.float64)
    well = z['well'].astype(str)
    cols = ['dwt', 'pf', 'base', 's_54844628', 's_54878409', 's_a20_w25',
            'base_k96', 's_k96_aniso', 'topk96_l75']
    uw, inv = np.unique(well, return_inverse=True)
    n_w = np.bincount(inv).astype(np.float64)
    sse = {}
    for c in cols:
        e = (z[c].astype(np.float64) - truth) ** 2
        sse[c] = np.bincount(inv, weights=e)
    print('local candidates: %d over %d wells (%d rows)' % (len(cols), len(uw), len(truth)))
    print('%-16s %10s' % ('candidate', 'pooled'))
    for c in cols:
        print('%-16s %10.4f' % (c, np.sqrt(sse[c].sum() / n_w.sum())))

    rs = np.random.RandomState(0)
    draws = rs.randint(0, len(uw), size=(NDRAW, DRAW_WELLS))
    res = []
    for a, b in itertools.combinations(cols, 2):
        ra = np.sqrt(sse[a].sum() / n_w.sum())
        rb = np.sqrt(sse[b].sum() / n_w.sum())
        gap = abs(ra - rb)
        da = np.sqrt(sse[a][draws].sum(1) / n_w[draws].sum(1))
        db = np.sqrt(sse[b][draws].sum(1) / n_w[draws].sum(1))
        # pooled says a<b ; how often does a 3-well draw say otherwise?
        rev = float(np.mean((da - db) * (ra - rb) < 0))
        res.append((gap, rev, a, b))
    res.sort()
    print('\n=== does a 3-well draw preserve the pooled ranking? (%d draws each) ===' % NDRAW)
    print('%-38s %10s %14s' % ('pair', 'pooled gap', 'P(reversed)'))
    for gap, rev, a, b in res:
        print('%-38s %10.4f %13.1f%%' % ('%s vs %s' % (a, b), gap, 100 * rev))
    return np.array([r[0] for r in res]), np.array([r[1] for r in res])


def main():
    print('=== per-candidate estimated private score (lower is better) ===')
    print('%-30s %7s %7s %7s %7s  %-9s %-9s %s'
          % ('candidate', 'public', 'H-vis', 'H-hid', 'mixed', 'family', 'account', 'prov'))
    for c in sorted(CANDIDATES, key=lambda k: CANDIDATES[k]['public']):
        d = CANDIDATES[c]
        print('%-30s %7.3f %s  %-9s %-9s %s'
              % (c, d['public'], ' '.join('%7.3f' % score(c, h) for h in HYPS),
                 d['family'], d['account'], d['prov']))

    rows = pair_rows()
    print('\n=== pair evaluation (best-of-2) — top 8 by worst case ===')
    print('%-46s %6s %6s %6s %6s %7s %5s %6s'
          % ('pair', 'H-vis', 'H-hid', 'WORST', 'mean', 'famDiv', 'OOF', 'ours'))
    for r in rows[:8]:
        print('%-46s %6.3f %6.3f %6.3f %6.3f %7.1f %5s %6s'
              % (nm(r), r['per']['H-visible'], r['per']['H-hidden'], r['worst'], r['mean'],
                 r['fam_div'], r['has_oof'], r['all_ours']))

    v = four_views(rows)
    print('\n=== FOUR VIEWS ===')
    for k in ('score-first', 'diversity-first', 'provenance-first', 'our-account-first'):
        r = v[k]
        print('  %-18s %-26s worst %.3f  mean %.3f  famDiv %.0f'
              % (k, nm(r), r['worst'], r['mean'], r['fam_div']) if r else '  %-18s (none)' % k)
    sf, oa = v['score-first'], v['our-account-first']
    print('\n  PRICE OF THE OUR-ACCOUNT CONSTRAINT: worst %+.3f, mean %+.3f'
          % (oa['worst'] - sf['worst'], oa['mean'] - sf['mean']))

    print('\n=== stress: how far must 54922806 degrade to lose slot 1? ===')
    print('%-34s %12s %12s' % ('threshold (delta on 54922806)', 'H-visible', 'H-hidden'))
    for rival in ('54968060_frontier_overlapOFF', '54844628_honest'):
        d_vis = CANDIDATES[rival]['public'] - CANDIDATES['54922806_frontier_overlapON']['public']
        d_hid = (CANDIDATES[rival]['public'] + CANDIDATES[rival]['retrieval']
                 - CANDIDATES['54922806_frontier_overlapON']['public']
                 - CANDIDATES['54922806_frontier_overlapON']['retrieval'])
        print('%-34s %12.3f %12.3f' % ('vs ' + rival.split('_')[0], d_vis, d_hid))
    print('  (delta = extra degradation of 54922806 beyond the modelled retrieval penalty;')
    print('   a NEGATIVE H-hidden threshold means the rival is already ahead under that hypothesis)')

    print('\n=== contingent entrant 55064411 (our-account frontier hedge-OFF, still PENDING) ===')
    print('  %-14s %s' % ('if public', 'consequence for slot 1'))
    for p in (6.40, 6.50, 6.563, 6.60, 6.643, 6.70):
        if p < CANDIDATES['54922806_frontier_overlapON']['public']:
            c = 'becomes best public overall -> takes slot 1 on ALL four views'
        elif p < CANDIDATES['54968060_frontier_overlapOFF']['public']:
            c = 'best OUR-ACCOUNT frontier -> takes slot 1 on our-account-first only'
        else:
            c = 'no change (worse than 54968060, our existing our-account frontier)'
        print('  %-14.3f %s' % (p, c))

    gaps, revs = three_well_reversal()
    print('\n=== reading the slot-1 gaps against that scale ===')
    for label, g in (('slot-1 gap 54922806 vs 54968060', 0.080),
                     ('frontier vs honest gap', 1.328)):
        near = np.argsort(np.abs(gaps - g))[:3]
        print('  %-34s gap %.3f | nearest measured pairs: %s'
              % (label, g, ', '.join('%.3f->%.0f%%' % (gaps[i], 100 * revs[i]) for i in sorted(near))))
    small = revs[gaps <= 0.30]
    if len(small):
        print('  measured pairs with pooled gap <= 0.30: P(reversed) mean %.1f%% (n=%d)'
              % (100 * small.mean(), len(small)))
    big = revs[gaps >= 1.0]
    if len(big):
        print('  measured pairs with pooled gap >= 1.00: P(reversed) mean %.1f%% (n=%d)'
              % (100 * big.mean(), len(big)))
    print('\nNO SUBMISSION. Decision task only; the private score is never used.')


if __name__ == '__main__':
    main()
