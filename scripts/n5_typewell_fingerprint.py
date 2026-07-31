"""N5 — typewell-fingerprint well families (time-boxed diagnostic, no Kaggle, no submission).

Question: does near-matching a test well's typewell GR-vs-TVT curve against all 773 train typewells
identify an analogue set that the DEPLOYED spatial gate does not already find?

Already bounded by measurement (`reports/new_direction_search_2026-07-28.md` M3): 773 train wells map to
752 distinct typewell files (group sizes {1: 739, 2: 12, 10: 1}), and none of the 3 test wells shares a
typewell byte-identically with any train well. So exact grouping is unusable; this tests near-matching.

The deployed structural field's neighbour rule (from `struct_oof_produce.py`) is the comparison baseline:
    group key = round(max(typewell.TVT), 1)          <- a typewell-derived key, already in production
    neighbours = same-group train wells with median trajectory XY separation >= 150 ft
    gate = nnb >= 4 AND closest surviving mate < 1000 ft

NOTE on self-matches: the 3 test wells also appear in `train/` under the same id (a different heel/toe
split of the same well). That train copy is a trivial self-match and is reported separately, never
counted as a discovered analogue.

Run: python3 scripts/n5_typewell_fingerprint.py     (CPU, ~1 min)
"""
import glob
import os

import numpy as np
import pandas as pd

ROOT = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii'
TEST_WELLS = ['000d7d20', '00bbac68', '00e12e8b']
MIN_SEP = 150.0
GATE_CLOSEST = 1000.0
STEP = 1.0
MIN_OVERLAP = 50.0      # ft of shared TVT range required for a correlation to be meaningful


def load_tw(path):
    d = pd.read_csv(path, usecols=['TVT', 'GR']).sort_values('TVT')
    tv = d['TVT'].values.astype(float)
    gr = d['GR'].values.astype(float)
    m = np.isfinite(tv) & np.isfinite(gr)
    return tv[m], gr[m]


def xy_of(split, wid):
    d = pd.read_csv(f'{ROOT}/{split}/{wid}__horizontal_well.csv', usecols=['X', 'Y'])
    return d['X'].values.astype(float), d['Y'].values.astype(float)


def main():
    train_ids = sorted(os.path.basename(p).split('__')[0]
                       for p in glob.glob(f'{ROOT}/train/*__typewell.csv'))
    tw_train = {w: load_tw(f'{ROOT}/train/{w}__typewell.csv') for w in train_ids}
    gkey = {w: round(float(np.nanmax(tv)), 1) for w, (tv, _) in tw_train.items()}
    print(f'train typewells {len(tw_train)}')

    for tid in TEST_WELLS:
        ttv, tgr = load_tw(f'{ROOT}/test/{tid}__typewell.csv')
        tx, ty = xy_of('test', tid)
        tgkey = round(float(np.nanmax(ttv)), 1)
        rows = []
        for w, (tv, gr) in tw_train.items():
            lo, hi = max(ttv.min(), tv.min()), min(ttv.max(), tv.max())
            if hi - lo < MIN_OVERLAP:
                continue
            g = np.arange(lo, hi, STEP)
            a = np.interp(g, ttv, tgr)
            b = np.interp(g, tv, gr)
            if a.std() < 1e-9 or b.std() < 1e-9:
                continue
            rows.append(dict(train_well=w, corr=float(np.corrcoef(a, b)[0, 1]),
                             overlap_ft=float(hi - lo), same_group=(gkey[w] == tgkey)))
        R = pd.DataFrame(rows).sort_values('corr', ascending=False).reset_index(drop=True)

        # spatial separation of each candidate from this test well (median nearest-point distance)
        from scipy.spatial import cKDTree
        tree = cKDTree(np.column_stack([tx, ty]))
        def sep(w):
            x, y = xy_of('train', w)
            d, _ = tree.query(np.column_stack([x, y])[::10], k=1)
            return float(np.median(d))

        top = R.head(6).copy()
        top['xy_sep_ft'] = [sep(w) for w in top.train_well]
        self_row = R[R.train_well == tid]

        print(f'\n=== test well {tid}  (typewell group key {tgkey}, {len(R)} candidates with '
              f'>= {MIN_OVERLAP:.0f} ft overlap) ===')
        if not self_row.empty:
            i = int(self_row.index[0])
            print(f'  SELF-MATCH (its own train copy): corr {self_row.iloc[0]["corr"]:.4f}, '
                  f'rank {i+1} of {len(R)}  -- excluded from the analogue set below')
        print('  %-14s %8s %10s %11s %10s' % ('train well', 'corr', 'overlap', 'same_group', 'xy_sep_ft'))
        shown = 0
        for _, r in top.iterrows():
            if r.train_well == tid:
                continue
            print('  %-14s %8.4f %9.0fft %11s %9.0f' % (r.train_well, r['corr'], r.overlap_ft,
                                                        r.same_group, r.xy_sep_ft))
            shown += 1
            if shown >= 5:
                break
        others = R[R.train_well != tid]
        print(f'  correlation distribution over {len(others)} non-self candidates: '
              f'max {others["corr"].max():.4f}  p99 {others["corr"].quantile(.99):.4f}  '
              f'p50 {others["corr"].quantile(.5):.4f}')

        # what the DEPLOYED gate already finds for this well
        same = [w for w in train_ids if w != tid and gkey[w] == tgkey]
        seps = {w: sep(w) for w in same}
        surv = [w for w in same if seps[w] >= MIN_SEP]
        closest = min(seps.values()) if seps else float('nan')
        closest_surv = min((seps[w] for w in surv), default=float('nan'))
        print(f'  DEPLOYED gate: same-group train wells {len(same)}, surviving the 150 ft guard '
              f'{len(surv)}, closest mate {closest:.0f} ft, closest surviving {closest_surv:.0f} ft'
              f'  -> gate {"PASS" if (len(surv) >= 4 and closest < GATE_CLOSEST) else "FAIL"}')
        # overlap between fingerprint top-5 and the deployed neighbour set
        fp5 = [w for w in others.head(5).train_well]
        inter = [w for w in fp5 if w in set(surv)]
        print(f'  fingerprint top-5 also in the deployed surviving-neighbour set: '
              f'{len(inter)}/5  {inter}')


if __name__ == '__main__':
    main()
