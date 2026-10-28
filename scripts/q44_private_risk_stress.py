"""Q44 — private-regime stress on the frontier family and the final slot pair.

We cannot see the private score, so this is arithmetic + Monte Carlo over already-recorded public scores
under explicit scenario axes. No GPU, no submission, no new measurement.

WHAT THIS ADDS OVER Q18 / Q53. Q53 already swept the two axes that decide slot 1 deterministically
(retrieval_delta x sigma_transfers). Its private "score" was a point estimate per cell. That is the wrong
shape for a best-of-2 decision, because best-of-2 pays off in the TAIL: you keep the better of two
submissions, so what matters is the joint distribution, not two point estimates. Q44 therefore models the
DRAW itself.

THE THREE UNCERTAINTIES, AND WHERE EACH ATTACHES — they are different objects and were being conflated:

  1. measurement noise on a PUBLIC score, sd ~= 0.03  (Q45, external: 14 unchanged resubmissions of 5
     kernels; sd 0.027-0.037, spreads to 0.112). This says two variants cannot be RANKED by public score
     unless they differ by >= ~0.1. It does NOT apply to the private score of a banked submission: the
     submitted file is fixed, and the private rows are scored from that same file.

  2. draw non-representativeness, sd of the DIFFERENCE ~= 2.4 ft cross-family. Calibrated to Q18's measured
     statement that the honest line beats the frontier line on ~29% of random 3-well draws at a public gap
     of 1.328: z = Phi^-1(0.29) = -0.553  ->  sigma_diff = 1.328 / 0.553 = 2.40. This is the dominant term
     and it is ~80x the measurement noise.

  3. verification / obligation risk, which is NOT a score at all. It cannot be added to an RMSE, so it is
     modelled as a selectability constraint and priced separately in units of "expected score you are
     paying for it".

The noise is decomposed so that the correlation structure is explicit:

    eps_c = family_shock[family(c)] + idio_c ,   sd(idio) = s_I ,  sd(family_shock) = s_F

    within-family difference sd = sqrt(2)*s_I           <- frontier variants are near-identical outputs
    cross-family  difference sd = sqrt(2*(s_F^2+s_I^2)) <- calibrated to 2.40

Env: DRAW (scale on the draw noise), NSIM.
"""
import itertools
import os

import numpy as np

PRISTINE = 6.6735          # mean of the code-identical replicate pair 54896975 / 54923144
SIGMA_EDGE = -0.1105       # 54922806 6.563 - PRISTINE  (the GR-sigma *1.3 term)
HYPS = ['H-visible', 'H-hidden', 'mixed']
NSIM = int(os.environ.get('NSIM', '40000'))

# ---- noise calibration (see docstring) ----
PUB_MEAS_SD = 0.03                     # Q45, external, 14 resubmissions
WITHIN_DIFF_SD = 0.15                  # frontier variants: pred-corr >= 0.99996 locally
CROSS_DIFF_SD = 2.40                   # calibrated to Q18's 29% reversal at a 1.328 gap
S_I = WITHIN_DIFF_SD / np.sqrt(2)
S_F = np.sqrt(max(CROSS_DIFF_SD ** 2 - 2 * S_I ** 2, 0.0) / 2)

CAND = {
    #                       public  overlap_on  sigma  family      account     3rd-party artifacts that
    #                                                                          AFFECT predictions
    '54922806': dict(public=6.563, ov=True,  sig=True,  fam='frontier', acct='teammate', dep=2, oof=False,
                     prov='public-derived + teammate-run'),
    '54968060': dict(public=6.643, ov=False, sig=False, fam='frontier', acct='ours', dep=2, oof=False,
                     prov='public-derived, our account'),
    '54896975': dict(public=6.669, ov=True,  sig=False, fam='frontier', acct='teammate', dep=2, oof=False,
                     prov='public-derived + teammate-run'),
    '54923144': dict(public=6.678, ov=True,  sig=False, fam='frontier', acct='teammate', dep=2, oof=False,
                     prov='public-derived + teammate-run'),
    '54990075': dict(public=6.690, ov=False, sig=False, fam='frontier', acct='ours', dep=2, oof=False,
                     prov='public-derived, our account'),
    '55064411': dict(public=6.695, ov=False, sig=False, fam='frontier', acct='ours', dep=2, oof=False,
                     prov='public-derived, our account'),
    '54844628': dict(public=7.891, ov=False, sig=False, fam='honest',   acct='ours', dep=1, oof=True,
                     prov='fully owned code, 760-well nested OOF'),
}
PAIR_A = ('54922806', '54844628')       # score- / diversity- / provenance-first (Q18, Q33, Q53)
PAIR_B = ('54968060', '54844628')       # our-account-first / ownership-first
PAIR_C = ('54922806', '54968060')       # frontier+frontier, family diversity 0 — the control
PAIR_D = ('55064411', '54844628')       # our-account frontier, worst on public — contingent entrant


def quality(c, hyp, rdelta, sigma_transfers):
    """Expected private RMSE of candidate c before the draw, under one deterministic scenario cell."""
    d = CAND[c]
    s = d['public']
    hidden = s + (rdelta if d['ov'] else 0.0) - (SIGMA_EDGE if (d['sig'] and not sigma_transfers) else 0.0)
    return {'H-visible': s, 'H-hidden': hidden, 'mixed': 0.5 * (s + hidden)}[hyp]


def simulate(hyp, rdelta, st, draw_scale, rng):
    """Return {cand: array of NSIM private scores} with the family/idio correlation structure."""
    fams = sorted({d['fam'] for d in CAND.values()})
    shock = {f: rng.normal(0, S_F * draw_scale, NSIM) for f in fams}
    out = {}
    for c, d in CAND.items():
        out[c] = (quality(c, hyp, rdelta, st) + shock[d['fam']]
                  + rng.normal(0, S_I * draw_scale, NSIM))
    return out


def pair_stats(sims, pair):
    """Best-of-2 keeps the better (lower) private score. Report mean and the BAD tail."""
    v = np.minimum(sims[pair[0]], sims[pair[1]])
    return v.mean(), np.percentile(v, 95), np.percentile(v, 5)


def main():
    print('Q44 — private-regime stress. NSIM %d' % NSIM)
    print('noise decomposition: s_F %.4f  s_I %.4f  -> within-family diff sd %.3f, cross-family %.3f'
          % (S_F, S_I, np.sqrt(2) * S_I, np.sqrt(2 * (S_F ** 2 + S_I ** 2))))
    print('public measurement noise (Q45, external, NOT applicable to a banked private score): sd %.3f\n'
          % PUB_MEAS_SD)

    # ---------- 0. the scale question, answered first ----------
    print('=== 0. SCALE: what each uncertainty is worth, in the same units ===')
    print('  deterministic stage terms that separate the slot-1 options:')
    print('    GR sigma *1.3          %+.4f' % SIGMA_EDGE)
    print('    overlap / retrieval    %+.4f  (measured, Q39; OFF slightly helps)' % -0.031)
    print('    bimodal hedge          %+.4f  (Q39; Q45 re-read: ~1.7 sd of the public floor -> unresolved)'
          % 0.052)
    print('  uncertainties:')
    print('    public measurement sd  %.4f   -> two variants are unrankable below ~%.2f' % (PUB_MEAS_SD, 3 * PUB_MEAS_SD))
    print('    private draw sd (diff) %.4f   -> %.0fx the largest stage term'
          % (CROSS_DIFF_SD, CROSS_DIFF_SD / abs(SIGMA_EDGE)))

    # ---------- 1. deterministic cells (Q53's axes) x the draw ----------
    rng = np.random.RandomState(44)
    print('\n=== 1. PAIR VALUE under every scenario cell (mean and 95th pct = the bad tail) ===')
    print('%-11s %-6s %-11s | %-22s | %-22s | %s'
          % ('retrieval', 'sigma', 'hyp', 'A 54922806+54844628', 'B 54968060+54844628', 'B - A'))
    agg = {}
    for rdelta, rlabel in ((-0.031, 'measured'), (0.0, 'inert'), (0.080, 'old model'), (0.200, 'spurious')):
        for st in (True, False):
            for hyp in HYPS:
                sims = simulate(hyp, rdelta, st, 1.0, rng)
                ma, ta, _ = pair_stats(sims, PAIR_A)
                mb, tb, _ = pair_stats(sims, PAIR_B)
                pbetter = float(np.mean(np.minimum(sims[PAIR_B[0]], sims[PAIR_B[1]])
                                        < np.minimum(sims[PAIR_A[0]], sims[PAIR_A[1]])))
                agg[(rdelta, st, hyp)] = (ma, ta, mb, tb, pbetter)
                print('%-11s %-6s %-11s | mean %.4f p95 %.4f | mean %.4f p95 %.4f | mean %+.4f p95 %+.4f  P(B<A) %.3f'
                      % (rlabel, st, hyp, ma, ta, mb, tb, mb - ma, tb - ta, pbetter))

    # ---------- 2. the draw-representativeness axis ----------
    print('\n=== 2. IS THE PUBLIC 3-WELL DRAW REPRESENTATIVE? (measured cell: retrieval -0.031, sigma False) ===')
    print('%-22s | %-22s | %-22s | %s' % ('draw noise scale', 'A mean / p95', 'B mean / p95', 'P(B<A)'))
    for scale, lab in ((0.0, 'representative (0x)'), (0.25, 'mild (0.25x)'), (1.0, 'as measured (1x)'),
                       (1.5, 'non-representative 1.5x')):
        sims = simulate('H-hidden', -0.031, False, scale, rng)
        ma, ta, _ = pair_stats(sims, PAIR_A)
        mb, tb, _ = pair_stats(sims, PAIR_B)
        pb = float(np.mean(np.minimum(sims[PAIR_B[0]], sims[PAIR_B[1]])
                           < np.minimum(sims[PAIR_A[0]], sims[PAIR_A[1]])))
        print('%-22s | %8.4f / %8.4f | %8.4f / %8.4f | %.3f' % (lab, ma, ta, mb, tb, pb))

    # ---------- 3. diversity is not free once the draw is modelled ----------
    print('\n=== 3. DIVERSITY: frontier+honest vs frontier+frontier (H-hidden, measured cell) ===')
    sims = simulate('H-hidden', -0.031, False, 1.0, rng)
    for lab, pair in (('A  54922806 + 54844628  (diverse)', PAIR_A),
                      ('B  54968060 + 54844628  (diverse, ours)', PAIR_B),
                      ('C  54922806 + 54968060  (frontier only)', PAIR_C),
                      ('D  55064411 + 54844628  (diverse, ours)', PAIR_D)):
        m, t, b = pair_stats(sims, pair)
        single = sims[pair[0]]
        print('  %-40s mean %.4f  p95 %.4f  p5 %.4f | vs slot-1 alone: mean %+.4f  p95 %+.4f'
              % (lab, m, t, b, m - single.mean(), t - np.percentile(single, 95)))
    print('  (Q18 priced the honest slot-2 as free insurance under a POINT model. With the draw modelled it')
    print('   is not free in the mean — it is worth measuring what it buys in the tail, which is the column')
    print('   that matters for best-of-2.)')

    # ---------- 4. provenance availability as a CONSTRAINT, not a score ----------
    print('\n=== 4. TEAMMATE PROVENANCE AVAILABLE vs UNAVAILABLE (a selectability constraint) ===')
    for avail in (True, False):
        pool = [c for c in CAND if avail or CAND[c]['acct'] == 'ours']
        rows = []
        for p in itertools.combinations(sorted(pool), 2):
            sims = simulate('H-hidden', -0.031, False, 1.0, rng)
            m, t, _ = pair_stats(sims, p)
            rows.append((m, t, p))
        rows.sort()
        print('  teammate selectable=%-5s -> pool %d, best pair by mean: %s + %s (mean %.4f p95 %.4f)'
              % (avail, len(pool), rows[0][2][0], rows[0][2][1], rows[0][0], rows[0][1]))
        best_ours = [r for r in rows if all(CAND[c]['acct'] == 'ours' for c in r[2])]
        print('        best OURS-ONLY pair: %s + %s (mean %.4f p95 %.4f)'
              % (best_ours[0][2][0], best_ours[0][2][1], best_ours[0][0], best_ours[0][1]))

    # ---------- 5. the override price, stated in score units ----------
    print('\n=== 5. THE PRICE OF OWNERSHIP-FIRST (B over A), per deterministic cell ===')
    print('%-11s %-6s %-11s %12s %12s' % ('retrieval', 'sigma', 'hyp', 'mean cost', 'p95 cost'))
    worst_mean = worst_tail = -9
    for k, (ma, ta, mb, tb, _) in sorted(agg.items()):
        rdelta, st, hyp = k
        print('%-11.3f %-6s %-11s %+12.4f %+12.4f' % (rdelta, st, hyp, mb - ma, tb - ta))
        worst_mean = max(worst_mean, mb - ma)
        worst_tail = max(worst_tail, tb - ta)
    print('  WORST-CASE price of ownership-first across all %d cells: mean %+.4f | p95 %+.4f'
          % (len(agg), worst_mean, worst_tail))
    print('  For comparison: public measurement sd %.3f, private draw sd (diff) %.2f' % (PUB_MEAS_SD, CROSS_DIFF_SD))

    # ---------- 6. board-level reshuffle at our position ----------
    print('\n=== 6. HOW MUCH DOES THE PRIVATE DRAW MOVE OUR RANK? ===')
    # local board density from the Q45 refresh + the external snapshot: ranks 190-200 span 0.007 ft, and
    # ~570 teams sit inside +-0.037 of 6.473  ->  ~7700 teams per ft near the bronze line.
    dens = 570 / 0.074
    print('  local board density near 6.47-6.57: ~%.0f teams per ft (Q45 refresh + external snapshot)' % dens)
    for sd in (PUB_MEAS_SD, 0.5, CROSS_DIFF_SD):
        print('    a private shift of 1 sd = %.3f ft moves us ~%.0f ranks' % (sd, sd * dens))
    print('  our rank 1339 / 5914; bronze 6.470; our public 6.563 (gap %.3f ft = ~%.0f ranks)'
          % (6.563 - 6.470, (6.563 - 6.470) * dens))
    print('  => at 1 sd of draw noise the rank movement is larger than the entire distance to bronze,')
    print('     so the private ordering at our position is dominated by the draw, not by a 0.04 stage term.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
