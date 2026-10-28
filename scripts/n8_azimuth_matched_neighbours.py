"""N8 — azimuth-matched neighbour selection for the deployed cross-well structural field.

Reuses the loading/caching/tree machinery of `scripts/n2_increment_structural_field.py`, whose deployed
construction was verified byte-exact against the banked `struct_oof.npz` (and reproduces the banked pooled
8.8626 to -0.0000 on the full 760-well split). The ONLY change here is an azimuth-similarity filter on the
surviving-neighbour set; group key, duplicate guard, IDW kernel, k, anchor length, gate and W all stay at
deployed values.

Rationale (from `reports/n6_public_solution_audit_2026-07-28.md`): a public methodology repo selects
offset-well priors from spatially-close AZIMUTH-MATCHED neighbours, because two wells at the same
orientation drilled in opposite directions encounter the formation in opposite sequence (updip vs
downdip), so the sign of the local TVT-Z slope differs. Azimuth difference is therefore computed on the
FULL circle -- 0 deg and 180 deg are different, not equivalent.

Known risk, measured in N2: the deployed neighbourhood is effectively single-well (99.38% of the k=12
contributing points share the nearest point's well). A filter that removes that dominant neighbour may do
more harm than good. That is what this task tests.

Preflight: AZ_TOL=180 disables the filter and MUST reproduce the banked struct byte-exactly.

Env: SMOKE_N, AZ_TOLS, OUT.
"""
import os
import sys
import glob
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from n2_increment_structural_field import get, tree_of, D, SH, K, ANCHOR, MIN_SEP  # noqa: E402

SMOKE_N = int(os.environ.get('SMOKE_N', '0'))
AZ_TOLS = [float(x) for x in os.environ.get('AZ_TOLS', '15,30,45,90,180').split(',')]
OUT = os.environ.get('OUT', f'{SH}/n8_struct_azimuth.npz')

_az = {}


def azimuth_of(w):
    """Mean drilling direction in degrees [0,360), step-length weighted. Test-available (X/Y only)."""
    if w not in _az:
        h = get(w)
        dx, dy = np.diff(h['X'].values), np.diff(h['Y'].values)
        m = np.hypot(dx, dy) > 0.5          # ignore near-vertical build rows
        if m.sum() < 5:
            m = np.ones(len(dx), bool)
        _az[w] = float(np.degrees(np.arctan2(dy[m].sum(), dx[m].sum())) % 360.0)
    return _az[w]


def ang_diff(a, b):
    """Signed-azimuth difference on the FULL circle, in [0,180]. 0 and 180 are NOT equivalent."""
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


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
    print(f'targets={len(targets)}  az_tols={AZ_TOLS}  (SMOKE_N={SMOKE_N})', flush=True)

    OW, OR = [], []
    OS = {t: [] for t in AZ_TOLS}
    META = []
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
        az_t = azimuth_of(wid)

        # surviving neighbours under the deployed duplicate guard, with their XY separation
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
            sep = float(np.median(d))
            if sep < MIN_SEP:
                continue
            surv.append((m, sep, ang_diff(az_t, azimuth_of(m))))
        if not surv:
            continue
        nearest_well = min(surv, key=lambda s: s[1])[0]

        row_meta = dict(well=wid, n_surv=len(surv),
                        az_spread=float(np.median([s[2] for s in surv])))
        for tol in AZ_TOLS:
            keep = [s for s in surv if s[2] <= tol]
            row_meta[f'nnb_{tol:g}'] = len(keep)
            row_meta[f'lost_nearest_{tol:g}'] = int(nearest_well not in [k[0] for k in keep])
            if not keep:
                OS[tol].append(np.full(len(ridx), np.nan, np.float32))
                continue
            px, py, pr = [], [], []
            for m, _, _ in keep:
                mh = get(m)
                rr = mh['TVT'].values + mh['Z'].values
                ok = np.isfinite(rr)
                px.append(mh['X'].values[ok][::4])
                py.append(mh['Y'].values[ok][::4])
                pr.append(rr[ok][::4])
            PX, PY, PR = np.concatenate(px), np.concatenate(py), np.concatenate(pr)
            dd, ii = cKDTree(np.column_stack([PX, PY])).query(xy, k=min(K, len(PR)))
            if dd.ndim == 1:
                dd, ii = dd[:, None], ii[:, None]
            wgt = 1.0 / (dd + 1.0)
            r_pred = (wgt * PR[ii]).sum(1) / wgt.sum(1)
            anchor = float(np.nanmean(hw['TVT_input'].values[kn_idx] + Z[kn_idx] - r_pred[kn_idx]))
            OS[tol].append((r_pred + anchor - Z)[ridx].astype(np.float32))
        OW.append(np.full(len(ridx), wid))
        OR.append(ridx)
        META.append(row_meta)

    M = pd.DataFrame(META)
    out = dict(well=np.concatenate(OW).astype(str), ridx=np.concatenate(OR).astype(np.int32))
    for tol in AZ_TOLS:
        out[f'struct_az{tol:g}'] = np.concatenate(OS[tol])
    np.savez_compressed(OUT, **out)
    M.to_csv(OUT.replace('.npz', '_meta.csv'), index=False)
    print(f'\nsaved {OUT}: wells={len(OW)} rows={sum(len(x) for x in OR)}')
    print('\n=== filter effect ===')
    print('%-8s %10s %10s %14s' % ('az_tol', 'mean nnb', 'nnb=0 %', 'lost nearest %'))
    for tol in AZ_TOLS:
        print('%-8g %10.2f %9.1f%% %13.1f%%'
              % (tol, M[f'nnb_{tol:g}'].mean(), 100 * (M[f'nnb_{tol:g}'] == 0).mean(),
                 100 * M[f'lost_nearest_{tol:g}'].mean()))
    print('\nmedian azimuth spread among surviving neighbours: %.1f deg' % M.az_spread.median())


if __name__ == '__main__':
    main()
