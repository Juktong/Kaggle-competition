"""N2 — increment-target refinement of the deployed cross-well structural field.

DEPLOYED construction (from `struct_oof_produce.py`, the builder behind `54844628`):

    r        = TVT + Z                                   (stratigraphic residual)
    r_pred   = IDW(k=12, w=1/(d+1)) over the POOLED points of all surviving neighbour wells
    anchor   = mean(r_true - r_pred) over the target's own last 100 known heel rows
    pred     = r_pred + anchor - Z

Note what the anchor does algebraically:

    pred = (r_pred - mean(r_pred over heel)) + mean(r_true over heel) - Z

so the LEVEL of r_pred cancels exactly and only the increment r_pred(row) - mean(r_pred at heel)
enters the prediction. The deployed field is therefore ALREADY heel-anchored and level-invariant:
adding any constant to every neighbour's r leaves the output unchanged. The N2 premise as written
("the deployed field interpolates the level, swap it for the increment") does not hold, and a literal
swap would be a no-op. This script verifies that numerically, then tests the nearest formulation that
IS materially different.

WHAT IS ACTUALLY DIFFERENT — per-well increment averaging. The deployed estimator pools neighbour
POINTS and then takes the 12 nearest overall, so at any row the 12 contributing points may come from
different wells sitting at different stratigraphic levels; when the nearest-neighbour well identity
switches along the target path, that level difference enters the increment as a step. Computing each
neighbour's increment WITHIN that well first cancels its level, and only then averages across wells:

    delta_m(row) = r_m(nearest point in well m) - mean over heel rows of r_m
    delta(row)   = sum_m w_m(row) delta_m(row) / sum_m w_m(row),   w_m = 1/(d_m + 1)
    pred(row)    = delta(row) + mean(r_true over heel) - Z(row)

Group key, duplicate guard, IDW kernel, anchor length, gate and W are all held at deployed values so
the comparison isolates one factor.

Run:  SMOKE_N=40 python3 scripts/n2_increment_structural_field.py     (smoke)
      python3 scripts/n2_increment_structural_field.py                (full, 760 wells)
"""
import os
import glob
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
K = 12
ANCHOR = 100
MIN_SEP = 150.0
SMOKE_N = int(os.environ.get('SMOKE_N', '0'))
OUT = os.environ.get('OUT', f'{SH}/n2_struct_increment.npz')

_cache, _tree = {}, {}


def get(w):
    if w not in _cache:
        _cache[w] = pd.read_csv(f'{D}/{w}__horizontal_well.csv',
                                usecols=['X', 'Y', 'Z', 'TVT', 'TVT_input'])
    return _cache[w]


def tree_of(w):
    if w not in _tree:
        h = get(w)
        _tree[w] = cKDTree(np.column_stack([h['X'].values, h['Y'].values]))
    return _tree[w]


_rtree = {}


def rtree_of(w):
    """KD-tree over the finite-r points of well w, plus that well's r values. Built once per well."""
    if w not in _rtree:
        mh = get(w)
        rr = mh['TVT'].values + mh['Z'].values
        ok = np.isfinite(rr)
        t = cKDTree(np.column_stack([mh['X'].values[ok], mh['Y'].values[ok]])) if ok.sum() else None
        _rtree[w] = (t, rr[ok])
    return _rtree[w]


def main():
    cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz')
    tM = cs['is_toe']
    dwell, dr = cs['well'][tM].astype(str), cs['ridx'][tM].astype(int)
    toe_rows = defaultdict(set)
    for w, r in zip(dwell, dr):
        toe_rows[w].add(int(r))
    del cs

    gkey = {}
    for f in glob.glob(f'{D}/*__typewell.csv'):
        wid = os.path.basename(f).split('__')[0]
        try:
            gkey[wid] = round(float(np.nanmax(pd.read_csv(f, usecols=['TVT'])['TVT'].values)), 1)
        except Exception:
            pass
    groups = defaultdict(list)
    for wid, k in gkey.items():
        groups[k].append(wid)

    targets = sorted(toe_rows)
    if SMOKE_N:
        targets = targets[:SMOKE_N]
    print(f'targets={len(targets)}  groups={len(groups)}  (SMOKE_N={SMOKE_N})', flush=True)

    OW, OR, OD, OP, OI, SWITCH = [], [], [], [], [], []
    for n, wid in enumerate(targets):
        if n % 50 == 0:
            print(f'  [{n}/{len(targets)}]', flush=True)
        if wid not in gkey:
            continue
        hw = get(wid)
        kn = hw['TVT_input'].notna().values
        if kn.sum() < ANCHOR:
            continue
        ridx = np.array(sorted(toe_rows[wid]))
        if len(ridx) < 10:
            continue
        X, Y, Z = hw['X'].values, hw['Y'].values, hw['Z'].values
        xy = np.column_stack([X, Y])
        kn_idx = np.where(kn)[0][-ANCHOR:]

        # ---- surviving neighbours under the deployed duplicate guard ----
        surv = []
        for m in groups.get(gkey[wid], []):
            if m == wid:
                continue
            try:
                mh = get(m)
            except Exception:
                continue
            if len(mh) < 5:
                continue
            d, _ = tree_of(m).query(xy[::10], k=1)
            if float(np.median(d)) < MIN_SEP:
                continue
            surv.append(m)
        if not surv:
            continue

        # ---- DEPLOYED: pool points, k nearest overall, IDW, then heel anchor ----
        px, py, pr, powner = [], [], [], []
        for j, m in enumerate(surv):
            mh = get(m)
            rr = mh['TVT'].values + mh['Z'].values
            ok = np.isfinite(rr)
            px.append(mh['X'].values[ok][::4])
            py.append(mh['Y'].values[ok][::4])
            pr.append(rr[ok][::4])
            powner.append(np.full(ok.sum() // 4 + (1 if ok.sum() % 4 else 0), j)[:len(pr[-1])])
        PX, PY, PR = np.concatenate(px), np.concatenate(py), np.concatenate(pr)
        POW = np.concatenate(powner)
        dd, ii = cKDTree(np.column_stack([PX, PY])).query(xy, k=min(K, len(PR)))
        if dd.ndim == 1:
            dd, ii = dd[:, None], ii[:, None]
        wgt = 1.0 / (dd + 1.0)
        r_pred = (wgt * PR[ii]).sum(1) / wgt.sum(1)
        anchor = float(np.nanmean(hw['TVT_input'].values[kn_idx] + Z[kn_idx] - r_pred[kn_idx]))
        pred_dep = r_pred + anchor - Z

        # mechanism metrics: does the pooled-point estimator actually MIX wells?
        #   - how often the nearest-point WELL identity changes along the path
        #   - what fraction of the k contributing points share the nearest point's well
        own = POW[ii]
        own1 = own[:, 0]
        same_frac = float(np.mean(own == own1[:, None]))
        SWITCH.append((wid, len(surv), float(np.mean(np.diff(own1) != 0)), same_frac))

        # ---- ONE-FACTOR ISOLATION: identical neighbour selection and identical weights as the
        # deployed estimator, changing ONLY whether each contributing point enters as a LEVEL or as a
        # within-well INCREMENT. H[j] is well j's own level measured at the target's heel.
        H = np.zeros(len(surv))
        for j, m in enumerate(surv):
            t, rv = rtree_of(m)
            _, ih = t.query(xy[kn_idx], k=1)
            H[j] = float(np.mean(rv[ih]))
        r_pred_iso = (wgt * (PR[ii] - H[own])).sum(1) / wgt.sum(1)
        pred_iso = r_pred_iso + float(np.mean(hw['TVT_input'].values[kn_idx] + Z[kn_idx])) - Z
        OI.append(pred_iso[ridx].astype(np.float32))

        # ---- NEW: per-well increment, level cancelled inside each neighbour first ----
        num = np.zeros(len(X))
        den = np.zeros(len(X))
        for m in surv:
            t, rv = rtree_of(m)
            if t is None or len(rv) < 5:
                continue
            dm, im = t.query(xy, k=1)
            rm = rv[im]
            dm_inc = rm - float(np.mean(rm[kn_idx]))       # this well's own level cancels
            w_m = 1.0 / (dm + 1.0)
            num += w_m * dm_inc
            den += w_m
        delta = np.where(den > 0, num / np.maximum(den, 1e-12), 0.0)
        r_true_heel = float(np.mean(hw['TVT_input'].values[kn_idx] + Z[kn_idx]))
        pred_new = delta + r_true_heel - Z

        OW.append(np.full(len(ridx), wid))
        OR.append(ridx)
        OD.append(pred_dep[ridx].astype(np.float32))
        OP.append(pred_new[ridx].astype(np.float32))

    np.savez_compressed(
        OUT,
        well=np.concatenate(OW).astype(str), ridx=np.concatenate(OR).astype(np.int32),
        struct_deployed_repro=np.concatenate(OD), struct_increment=np.concatenate(OP),
        struct_increment_iso=np.concatenate(OI),
        sw_well=np.array([s[0] for s in SWITCH]).astype(str),
        sw_nnb=np.array([s[1] for s in SWITCH], dtype=np.int32),
        sw_frac=np.array([s[2] for s in SWITCH], dtype=np.float32),
        sw_same=np.array([s[3] for s in SWITCH], dtype=np.float32))
    sw = np.array([s[2] for s in SWITCH]); sm = np.array([s[3] for s in SWITCH])
    print(f'\nsaved {OUT}: wells={len(OW)} rows={sum(len(x) for x in OR)}')
    print('nearest-point WELL identity switches on %.4f of consecutive row pairs '
          '(median over wells %.4f, p90 %.4f)' % (sw.mean(), np.median(sw), np.percentile(sw, 90)))
    print('fraction of the k=12 contributing points sharing the nearest point\'s well: '
          'mean %.4f  median %.4f  p10 %.4f' % (sm.mean(), np.median(sm), np.percentile(sm, 10)))


if __name__ == '__main__':
    main()
