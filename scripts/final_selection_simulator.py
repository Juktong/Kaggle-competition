"""G3.4 — robust final-selection simulator (no submission, no GPU).

Final score = best of the 2 selected submissions on the PRIVATE set. The private set is unknown; two
hypotheses are live:
  H-visible : private = held-out rows of the SAME 3 visible wells (which are duplicated in train)
  H-hidden  : private = novel wells with no train duplicate
plus a mixed case. For each candidate we estimate a private score under each hypothesis, then evaluate
every 2-subset by expected score and by worst-case (min-regret) across hypotheses.

Estimation rules (stated, not hidden):
  H-visible : private ~= public (public and private are row splits of the same wells; within-well
              residual autocorrelation is +0.9998, so the two halves track each other closely).
  H-hidden  : retrieval/overlap contributions go inert (no train duplicate to look up), so a candidate's
              score degrades by its measured retrieval dependence:
                - overlap-ON frontier branches lose the ~0.080 measured overlap contribution
                  (6.643 - 6.563), i.e. they revert toward the no-retrieval frontier level;
                - no-retrieval candidates (54968060, 54844628, SP45-only) are unchanged in expectation;
                - an extra novel-well penalty applies equally to all candidates and therefore cancels in
                  the ranking, so it is set to 0.
"""
import itertools, json

# label -> dict(public, retrieval_dependence, provenance, note)
CANDIDATES = {
    '54922806_frontier_overlapON': dict(public=6.563, retrieval=0.080, prov='teammate/public-derived',
                                        note='best public; overlap-ON branch'),
    '54968060_frontier_overlapOFF': dict(public=6.643, retrieval=0.0, prov='ours/public-derived',
                                         note='validated no-retrieval run (G1.2)'),
    '54896975_frontier_overlapON': dict(public=6.669, retrieval=0.080, prov='teammate/public-derived',
                                        note='same family'),
    '54923144_frontier_gr_sigma':  dict(public=6.678, retrieval=0.080, prov='teammate/public-derived',
                                        note='same family, GR-sigma branch'),
    '54844628_honest':             dict(public=7.891, retrieval=0.0, prov='fully owned',
                                        note='760-well nested OOF + bootstrap validated'),
}

def score(c, hyp):
    d = CANDIDATES[c]
    if hyp == 'H-visible':
        return d['public']
    if hyp == 'H-hidden':
        return d['public'] + d['retrieval']      # retrieval contribution goes inert -> score worsens
    if hyp == 'mixed':
        return d['public'] + 0.5 * d['retrieval']
    raise ValueError(hyp)

HYPS = ['H-visible', 'H-hidden', 'mixed']

def main():
    print("=== per-candidate estimated private score (lower is better) ===")
    print(f"{'candidate':32s} {'public':>7} {'H-visible':>10} {'H-hidden':>9} {'mixed':>7}  provenance")
    for c in sorted(CANDIDATES, key=lambda k: CANDIDATES[k]['public']):
        print(f"{c:32s} {CANDIDATES[c]['public']:>7.3f} " +
              " ".join(f"{score(c,h):>9.3f}" for h in HYPS) + f"  {CANDIDATES[c]['prov']}")

    print("\n=== every 2-subset: final = best of the two under each hypothesis ===")
    rows = []
    for pair in itertools.combinations(sorted(CANDIDATES), 2):
        per = {h: min(score(pair[0], h), score(pair[1], h)) for h in HYPS}
        worst = max(per.values())                 # min-regret criterion: minimise the worst case
        mean = sum(per.values()) / len(per)
        rows.append((pair, per, worst, mean))
    rows.sort(key=lambda r: (r[2], r[3]))
    print(f"{'pair':66s} {'H-vis':>7} {'H-hid':>7} {'mixed':>7} {'WORST':>7} {'mean':>7}")
    for pair, per, worst, mean in rows[:10]:
        nm = f"{pair[0]} + {pair[1]}"
        print(f"{nm:66s} {per['H-visible']:>7.3f} {per['H-hidden']:>7.3f} {per['mixed']:>7.3f} {worst:>7.3f} {mean:>7.3f}")

    best_pair, best_per, best_worst, best_mean = rows[0]
    print(f"\nMIN-REGRET PAIR: {best_pair[0]} + {best_pair[1]}")
    print(f"  worst-case {best_worst:.3f}, mean {best_mean:.3f}")
    print("\nNOTE: under these rules the retrieval penalty (0.080) is small, so pair ranking is driven")
    print("      mainly by raw public. Provenance is NOT in the objective -- it is a separate,")
    print("      owner-level consideration recorded in the final-slot package.")

if __name__ == '__main__':
    main()
