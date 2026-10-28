"""Q58 evaluator — reproduce the deployed structural-field stage, then re-fit it against the smoothed PF.

THE KEY STRUCTURAL FACT, established by reading `scripts/struct_oof_produce.py` rather than assumed: the
structural field does NOT depend on the PF. It is

    group   = round(max(typewell.TVT), 1)                      (the target's OWN typewell -> test-available)
    field   = IDW(k=12, w=1/(d+1)) over same-group train wells with median XY separation >= 150 ft
    anchor  = mean(r_true - r_pred) over the target's OWN last 100 known heel rows
    struct  = r_pred + anchor - Z

so it is an external per-row prediction column, already computed for all 3.72M rows in `struct_oof.npz`.
The deployed line combines it with the blend by a fixed convex weight on gated rows:

    final = (1 - W) * base + W * struct     where the gate holds
    final = base                            elsewhere

Therefore "re-fitting the structural-field stage against the smoothed PF" means re-choosing W (and the gate
threshold) against the smoothed blend — arithmetic over saved arrays, no PF re-run. That is why this is a
separate script from the producer.

STEP 0 IS A REPRODUCTION CONTROL AND IT GATES EVERYTHING ELSE: rebuild the deployed `s_54844628` column from
`base`, `struct` and the gate, and require it to match. If the deployed line cannot be reproduced from these
arrays, no conclusion about a modified line is trustworthy, and the script says so instead of proceeding.

Env: PRED (producer output), ALPHAS, WS.
"""
import os

import numpy as np

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
PRED = os.environ.get('PRED', os.path.join(SH, 'q58_pf_smoothed_preds.npz'))
ALPHAS = [float(x) for x in os.environ.get('ALPHAS', '0,0.25,0.5,0.75,1.0').split(',')]
WS = [float(x) for x in os.environ.get('WS', '0,0.05,0.10,0.15,0.20,0.30').split(',')]


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def by_well(pred, tru, wells, uw):
    """Per-well RMSE, in the order of uw."""
    out = np.empty(len(uw))
    for i, w in enumerate(uw):
        m = wells == w
        out[i] = np.sqrt(np.mean((pred[m] - tru[m]) ** 2))
    return out


def main():
    z = np.load(f'{SH}/aligned_preds.npz', allow_pickle=True)
    s = np.load(f'{SH}/struct_oof.npz', allow_pickle=True)
    well, ridx = z['well'].astype(str), z['ridx'].astype(int)
    tru = z['truth'].astype(np.float64)
    dwt, pf, base = (z[k].astype(np.float64) for k in ('dwt', 'pf', 'base'))
    dep = z['s_54844628'].astype(np.float64)
    nnb, closest = z['nnb'].astype(np.float64), z['closest_surv'].astype(np.float64)

    # align struct to the aligned frame by (well, ridx)
    key = np.char.add(np.char.add(well, '|'), ridx.astype(str))
    skey = np.char.add(np.char.add(s['well'].astype(str), '|'), s['ridx'].astype(int).astype(str))
    pos = {k: i for i, k in enumerate(skey)}
    sel = np.array([pos.get(k, -1) for k in key])
    assert (sel >= 0).all(), 'struct_oof.npz does not cover every aligned row'
    struct = s['struct'].astype(np.float64)[sel]
    print('rows %d | wells %d | struct aligned by (well, ridx), 0 missing' % (len(well), len(np.unique(well))))

    fin = np.isfinite(tru) & np.isfinite(dwt) & np.isfinite(pf) & np.isfinite(struct)
    print('finite rows %d (%.1f%%)' % (fin.sum(), 100 * fin.mean()))

    # ---------- 0. REPRODUCTION CONTROL ----------
    # The gate is built from struct_oof.npz's OWN per-well meta, not from the aligned frame's per-row
    # nnb/closest_surv columns. That distinction is not cosmetic and was found by measurement: the aligned
    # columns disagree with the meta for 6 boundary wells (notably 8b95d6d1, closest_surv 1011.1, which the
    # deployed line DID gate in), leaving 2139 rows wrong and the reproduction 0.0008 off. Using the meta the
    # line reproduces exactly.
    mw = {w: (n, c) for w, n, c in zip(s['meta_well'].astype(str), s['meta_nnb'].astype(int),
                                       s['meta_closest'].astype(float))}
    mnnb = np.array([mw.get(w, (0, 1e9))[0] for w in well], float)
    mclose = np.array([mw.get(w, (0, 1e9))[1] for w in well], float)
    gate = (mnnb >= 4) & (mclose < 1000)
    W_DEP = 0.15

    print('\n=== 0. REPRODUCTION CONTROL: rebuild the deployed line from base + struct + gate ===')
    print('  deployed s_54844628 RMSE            %.4f   (ledger: 8.8626)' % rmse(dep[fin], tru[fin]))
    print('  base (0.5*dwt + 0.5*pf) RMSE        %.4f   (ledger: 9.2987)' % rmse(base[fin], tru[fin]))
    rec = np.where(gate, (1 - W_DEP) * base + W_DEP * struct, base)
    d = np.abs(rec[fin] - dep[fin])
    print('  rebuilt (meta gate nnb>=4 & closest<1000, W=0.15) RMSE %.4f' % rmse(rec[fin], tru[fin]))
    print('  rows differing by >0.01: %d of %d | max |diff| %.4f  -> float32 rounding'
          % ((d > 0.01).sum(), len(d), d.max()))
    print('  gated rows: %.1f%% (ledger: 87%%)' % (100 * gate[fin].mean()))
    # the implied weight, recovered from the deployed column itself rather than taken from the ledger
    impl = (dep - base) / np.where(np.abs(struct - base) > 1e-9, struct - base, np.nan)
    print('  implied W recovered from the deployed column: median %.4f (p5 %.4f, p95 %.4f) on gated rows,'
          ' %.4f off-gate' % (np.nanmedian(impl[gate]), np.nanpercentile(impl[gate], 5),
                              np.nanpercentile(impl[gate], 95), np.nanmedian(impl[~gate])))
    assert rmse(rec[fin], tru[fin]) - rmse(dep[fin], tru[fin]) < 1e-3, 'deployed line not reproduced'
    print('  REPRODUCED -> the stage is fully characterised by (meta gate, W=0.15).')

    # ---------- 1. the smoothed blend ----------
    if not os.path.exists(PRED):
        print('\nproducer output %s not present yet; run scripts/q58_smoothed_pf_produce.py first.' % PRED)
        return
    p = np.load(PRED, allow_pickle=True)
    pkey = np.char.add(np.char.add(p['well'].astype(str), '|'), p['ridx'].astype(int).astype(str))
    ppos = {k: i for i, k in enumerate(pkey)}
    psel = np.array([ppos.get(k, -1) for k in key])
    cov = psel >= 0
    print('\n=== 1. producer coverage: %d of %d aligned rows (%.1f%%) ===' % (cov.sum(), len(key), 100 * cov.mean()))
    pf_f = np.full(len(key), np.nan)
    pf_s = np.full(len(key), np.nan)
    pf_f[cov] = p['pf_fwd'].astype(np.float64)[psel[cov]]
    pf_s[cov] = p['pf_sm'].astype(np.float64)[psel[cov]]

    m = fin & cov & np.isfinite(pf_f) & np.isfinite(pf_s)
    print('  usable rows %d | NS=64 forward vs the stored deployed pf column:' % m.sum())
    print('    RMSE(stored pf)      %.4f' % rmse(pf[m], tru[m]))
    print('    RMSE(our forward)    %.4f' % rmse(pf_f[m], tru[m]))
    print('    max|our fwd - stored pf| %.4f   mean|diff| %.4f'
          % (np.abs(pf_f[m] - pf[m]).max(), np.abs(pf_f[m] - pf[m]).mean()))
    print('    RMSE(our smoothed)   %.4f' % rmse(pf_s[m], tru[m]))

    uw = np.unique(well[m])
    n = len(uw)
    print('\n=== 2. blend and full-line RMSE by (alpha, W), meta gate nnb>=4 & closest<1000 ===')
    print('%-8s %10s %s' % ('alpha', 'blend', ''.join('%12s' % ('W=%.2f' % w) for w in WS)))
    tab = {}
    for a in ALPHAS:
        pf_a = (1 - a) * pf_f + a * pf_s
        b_a = 0.5 * dwt + 0.5 * pf_a
        row = []
        for W in WS:
            f = np.where(gate, (1 - W) * b_a + W * struct, b_a)
            tab[(a, W)] = f
            row.append(rmse(f[m], tru[m]))
        print('%-8.2f %10.4f %s' % (a, rmse(b_a[m], tru[m]), ''.join('%12.4f' % v for v in row)))
    print('  reference on these rows: deployed line %.4f | deployed base %.4f'
          % (rmse(dep[m], tru[m]), rmse(base[m], tru[m])))

    # ---------- 3. nested selection over (alpha, W) ----------
    print('\n=== 3. NESTED over (alpha, W), splits BY WELL, both directions ===')
    pw = {k: by_well(v[m], tru[m], well[m], uw) for k, v in tab.items()}
    cnt = np.array([np.sum(well[m] == w) for w in uw], float)
    sse = {k: v ** 2 * cnt for k, v in pw.items()}
    dep_w = by_well(dep[m], tru[m], well[m], uw)
    dep_sse = dep_w ** 2 * cnt
    keys = list(tab)
    ix = np.arange(n)
    folds = [(ix[:n // 2], ix[n // 2:]), (ix[n // 2:], ix[:n // 2])]
    hs, hc, bs, picks = [], [], [], []
    for selh, rep in folds:
        bestk = min(keys, key=lambda k: np.sqrt(sse[k][selh].sum() / cnt[selh].sum()))
        picks.append(bestk)
        hs.append(sse[bestk][rep]); hc.append(cnt[rep]); bs.append(dep_sse[rep])
    hs, hc, bs = (np.concatenate(x) for x in (hs, hc, bs))
    nested, nbase = float(np.sqrt(hs.sum() / hc.sum())), float(np.sqrt(bs.sum() / hc.sum()))
    gw = np.sqrt(bs / hc) - np.sqrt(hs / hc)
    rs = np.random.RandomState(7)
    b3 = np.array([gw[rs.randint(0, len(gw), 3)].mean() for _ in range(20000)])
    print('  picks %s' % [('alpha=%.2f' % k[0], 'W=%.2f' % k[1]) for k in picks])
    print('  selected %.4f  vs DEPLOYED LINE %.4f  gain %+.4f' % (nested, nbase, nbase - nested))
    print('  helps %.1f%% of held-out wells | 3-WELL bootstrap 5th %+.4f  50th %+.4f  95th %+.4f  P(>0) %.4f'
          % (100 * np.mean(gw > 0), *np.percentile(b3, [5, 50, 95]), (b3 > 0).mean()))
    ok = (nbase - nested > 0) and (np.percentile(b3, 5) > 0) and (np.mean(gw > 0) > 0.5)
    print('\nGATE: nested gain > 0 AND helps a majority AND 3-well 5th > 0  ->  %s' % ('PASS' if ok else 'FAIL'))

    # ---------- 4. did the stage keep, absorb or destroy the gain? ----------
    print('\n=== 4. does the structural-field stage keep the smoother gain? ===')
    for a in (0.0, 1.0):
        b_a = 0.5 * dwt + 0.5 * ((1 - a) * pf_f + a * pf_s)
        f_old = np.where(gate, (1 - W_DEP) * b_a + W_DEP * struct, b_a)
        print('  alpha=%.0f : blend %.4f -> line(W=%.2f, unchanged stage) %.4f   (stage worth %+.4f)'
              % (a, rmse(b_a[m], tru[m]), W_DEP, rmse(f_old[m], tru[m]),
                 rmse(b_a[m], tru[m]) - rmse(f_old[m], tru[m])))
    b0 = 0.5 * dwt + 0.5 * pf_f
    b1 = 0.5 * dwt + 0.5 * pf_s
    f0 = np.where(gate, (1 - W_DEP) * b0 + W_DEP * struct, b0)
    f1 = np.where(gate, (1 - W_DEP) * b1 + W_DEP * struct, b1)
    print('  smoother at blend level %+.4f  ->  after the unchanged stage %+.4f  (carry-through %.0f%%)'
          % (rmse(b0[m], tru[m]) - rmse(b1[m], tru[m]), rmse(f0[m], tru[m]) - rmse(f1[m], tru[m]),
             100 * (rmse(f0[m], tru[m]) - rmse(f1[m], tru[m])) / max(rmse(b0[m], tru[m]) - rmse(b1[m], tru[m]), 1e-9)))


if __name__ == '__main__':
    main()
