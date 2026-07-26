"""G3.4 / H — robust final-selection simulator (no submission, no GPU).

Final score = **best of the 2 selected submissions** on the private set, so the object to optimise is the
PAIR, not the individual candidate. The private set is unknown; three hypotheses are carried:

  H-visible : private = held-out rows of the SAME 3 visible wells (duplicated in train)
  H-hidden  : private = novel wells with no train duplicate
  mixed     : half weight on each

Because no single criterion dominates, this tool emits **three explicit recommendations** instead of one
blended verdict:

  score-first      : minimise the modelled worst-case / mean private score. Lineage ignored.
  diversity-first  : among pairs tied on score, prefer members that fail independently (different
                     pipeline family / lower prediction correlation).
  provenance-first : require at least one slot to be a fully-owned, OOF-validated pipeline.

Estimation rules (stated, not hidden):
  H-visible : private ~= public (public/private are row splits of the same wells; within-well residual
              autocorrelation +0.9998, so the halves track each other).
  H-hidden  : retrieval/overlap contributions go inert (no train duplicate to look up), so a candidate
              degrades by its MEASURED retrieval dependence = 0.080
              (= 6.643 overlap-OFF - 6.563 overlap-ON, i.e. 54968060 vs 54922806). No-retrieval
              candidates are unchanged. A novel-well penalty common to every candidate cancels in the
              ranking and is set to 0.
  The true private score is NOT visible and is never used.
"""
import itertools

CANDIDATES = {
    '54922806_frontier_overlapON': dict(
        public=6.563, retrieval=0.080, family='frontier', prov='public-derived (teammate)',
        oof=False, note='best public; overlap-ON branch'),
    '54968060_frontier_overlapOFF': dict(
        public=6.643, retrieval=0.0, family='frontier', prov='public-derived (our account)',
        oof=False, note='validated no-retrieval run (G1.2)'),
    '54896975_frontier_overlapON': dict(
        public=6.669, retrieval=0.080, family='frontier', prov='public-derived (teammate)',
        oof=False, note='same family'),
    '54923144_frontier_gr_sigma': dict(
        public=6.678, retrieval=0.080, family='frontier', prov='public-derived (teammate)',
        oof=False, note='same family, GR-sigma branch'),
    '54990075_frontier_sp45only': dict(
        public=6.690, retrieval=0.0, family='frontier', prov='public-derived (our account)',
        oof=False, note='SP45-only; post-SP45 stages shown to earn their place'),
    '54844628_honest': dict(
        public=7.891, retrieval=0.0, family='honest', prov='fully owned',
        oof=True, note='DWT+PF+structural field; 760-well nested OOF + bootstrap'),
}

# measured prediction correlations between locally-available outputs (higher = more redundant)
PRED_CORR = {
    ('54844628_honest', '54968060_frontier_overlapOFF'): 0.99997,
    ('54844628_honest', '54990075_frontier_sp45only'): 0.99996,
    ('54968060_frontier_overlapOFF', '54990075_frontier_sp45only'): 0.99999,
}
HYPS = ['H-visible', 'H-hidden', 'mixed']
NEAR_TIE = 0.01          # pairs within this of the best worst-case count as tied on score


def score(c, hyp):
    d = CANDIDATES[c]
    if hyp == 'H-visible':
        return d['public']
    if hyp == 'H-hidden':
        return d['public'] + d['retrieval']
    if hyp == 'mixed':
        return d['public'] + 0.5 * d['retrieval']
    raise ValueError(hyp)


def diversity(a, b):
    """(family diversity 0/1, correlation-based independence term or None)."""
    fam = 0.0 if CANDIDATES[a]['family'] == CANDIDATES[b]['family'] else 1.0
    corr = PRED_CORR.get((a, b)) or PRED_CORR.get((b, a))
    corr_term = (1.0 - corr) * 1e4 if corr is not None else None
    return fam, corr_term


def main():
    print("=== per-candidate estimated private score (lower is better) ===")
    print(f"{'candidate':30s} {'public':>7} {'H-vis':>7} {'H-hid':>7} {'mixed':>7}  {'family':9s} {'OOF':>5}  provenance")
    for c in sorted(CANDIDATES, key=lambda k: CANDIDATES[k]['public']):
        d = CANDIDATES[c]
        print(f"{c:30s} {d['public']:>7.3f} " + " ".join(f"{score(c,h):>7.3f}" for h in HYPS) +
              f"  {d['family']:9s} {str(d['oof']):>5}  {d['prov']}")

    rows = []
    for pair in itertools.combinations(sorted(CANDIDATES), 2):
        per = {h: min(score(pair[0], h), score(pair[1], h)) for h in HYPS}
        worst = max(per.values()); mean = sum(per.values()) / len(per)
        fam, corr_term = diversity(*pair)
        has_oof = CANDIDATES[pair[0]]['oof'] or CANDIDATES[pair[1]]['oof']
        has_owned = 'fully owned' in (CANDIDATES[pair[0]]['prov'], CANDIDATES[pair[1]]['prov'])
        rows.append(dict(pair=pair, per=per, worst=worst, mean=mean, fam_div=fam,
                         corr_term=corr_term, has_oof=has_oof, has_owned=has_owned))
    rows.sort(key=lambda r: (r['worst'], r['mean']))

    print("\n=== pair evaluation (best-of-2) — top 8 by worst case ===")
    print(f"{'pair':62s} {'H-vis':>6} {'H-hid':>6} {'WORST':>6} {'mean':>6} {'famDiv':>7} {'OOF':>5}")
    for r in rows[:8]:
        nm = f"{r['pair'][0]} + {r['pair'][1]}"
        print(f"{nm:62s} {r['per']['H-visible']:>6.3f} {r['per']['H-hidden']:>6.3f} "
              f"{r['worst']:>6.3f} {r['mean']:>6.3f} {r['fam_div']:>7.1f} {str(r['has_oof']):>5}")

    best_worst = rows[0]['worst']
    tied = [r for r in rows if r['worst'] <= best_worst + NEAR_TIE]

    print("\n=== THREE RECOMMENDATIONS ===")
    sf = rows[0]
    print(f"\n[score-first]      {sf['pair'][0]} + {sf['pair'][1]}")
    print(f"  worst={sf['worst']:.3f} mean={sf['mean']:.3f}. Minimises the modelled private score; lineage ignored.")
    print(f"  {len(tied)} pair(s) tie within {NEAR_TIE}, so this criterion alone does not pick a unique pair.")

    # family diversity first; then mean score. Prediction correlation is only a tiebreak WHEN MEASURED
    # for both — a missing correlation (teammate outputs are not available locally) must be neutral,
    # not treated as the worst case.
    df = sorted(tied, key=lambda r: (-r['fam_div'], r['mean'],
                                     -(r['corr_term'] if r['corr_term'] is not None else 0.0)))[0]
    print(f"\n[diversity-first]  {df['pair'][0]} + {df['pair'][1]}")
    print(f"  worst={df['worst']:.3f} (equal to score-first) family_diversity={df['fam_div']:.0f}.")
    print("  Among the score-tied pairs, prefers members that fail independently, so a family-wide")
    print("  problem in the frontier stack cannot remove both slots at once.")

    pf_pool = [r for r in rows if r['has_owned'] and r['has_oof']]
    if pf_pool:
        pf = pf_pool[0]
        print(f"\n[provenance-first] {pf['pair'][0]} + {pf['pair'][1]}")
        print(f"  worst={pf['worst']:.3f} mean={pf['mean']:.3f}. Requires one slot to be a fully-owned,")
        print("  OOF-validated pipeline; among those, takes the best worst case.")

    print("\nNOTE: the measured retrieval penalty (0.080) is small, so score-first is driven mainly by raw")
    print("      public. The true private score is not visible and is never used here.")


if __name__ == '__main__':
    main()
