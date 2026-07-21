"""Proposal L4: ANISOTROPIC (dip-aware) structural field vs the deployed isotropic IDW.

Motivation (reports/per_well_bias_structure_2026-07-21.md): the dominant remaining error is per-well
DRIFT along the toe (slope std 13.28 ft) rather than a level offset (std 4.72 ft). The deployed field
weights group-mates by isotropic XY distance, which ignores that structure varies slowly ALONG STRIKE
and quickly ALONG DIP. A geometric-anisotropy kernel should track drift better.

Method (identical to the deployed field except for the distance metric):
  1. fit a plane  r ~ a + b*X + c*Y  over the surviving group-mates -> dip direction u = (b,c)/|(b,c)|,
     strike direction v perpendicular to u
  2. anisotropic distance:  d^2 = (delta . u)^2 + (delta . v)^2 / A^2     (A >= 1 compresses strike)
     A = 1 reproduces the deployed isotropic field exactly (control)
  3. IDW k=12, w = 1/(d+1); anchor on the target's own last ANCHOR known heel rows; TVT = r_pred + anchor - Z

All A values are computed in ONE pass because loading mate point clouds dominates the cost.
Everything used is test-available: group key from the target's own typewell, mates are TRAIN wells,
anchor from the target's own known rows. Same MIN_SEP duplicate guard.
Env: K, ANCHOR, MIN_SEP, MAXW, ANISOS, OUT.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
K = int(os.environ.get('K', '12')); ANCHOR = int(os.environ.get('ANCHOR', '100'))
MIN_SEP = float(os.environ.get('MIN_SEP', '150')); MAXW = int(os.environ.get('MAXW', '10000'))
ANISOS = [float(x) for x in os.environ.get('ANISOS', '1,2,3,5').split(',')]
OUT = os.environ.get('OUT', os.path.join(SH, 'struct_aniso.npz'))

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dwell = cs['well'][tM].astype(str); dr = cs['ridx'][tM].astype(int)
toe_rows = defaultdict(set)
for w, r in zip(dwell, dr): toe_rows[w].add(int(r))
del cs

gkey = {}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid = os.path.basename(f).split('__')[0]
    try: gkey[wid] = round(float(np.nanmax(pd.read_csv(f, usecols=['TVT'])['TVT'].values)), 1)
    except Exception: pass
groups = defaultdict(list)
for wid, k in gkey.items(): groups[k].append(wid)
print(f'{len(groups)} groups; ANISOS={ANISOS}', flush=True)

cache = {}
def get(w):
    if w not in cache:
        cache[w] = pd.read_csv(f'{D}/{w}__horizontal_well.csv', usecols=['X', 'Y', 'Z', 'TVT', 'TVT_input'])
    return cache[w]
_tree = {}
def tree_of(w):
    if w not in _tree:
        h = get(w); _tree[w] = cKDTree(np.column_stack([h['X'].values, h['Y'].values]))
    return _tree[w]

targets = sorted(toe_rows.keys())[:MAXW]
OW, OR = [], []
OS = {a: [] for a in ANISOS}
META = []
for n, wid in enumerate(targets):
    if n % 50 == 0: print(f'  [{n}/{len(targets)}]', flush=True)
    if wid not in gkey: continue
    try: hw = get(wid)
    except Exception: continue
    kn_mask = hw['TVT_input'].notna().values
    if kn_mask.sum() < ANCHOR: continue
    ridx = np.array(sorted(toe_rows[wid]))
    if len(ridx) < 10: continue
    X = hw['X'].values; Y = hw['Y'].values; Z = hw['Z'].values
    tgt_xy = np.column_stack([X, Y])
    px, py, pr, seps, surv_seps = [], [], [], [], []
    for m in groups.get(gkey[wid], []):
        if m == wid: continue
        try: mh = get(m)
        except Exception: continue
        if len(mh) < 5: continue
        d, _ = tree_of(m).query(tgt_xy[::10], k=1)
        sep = float(np.median(d)); seps.append(sep)
        if sep < MIN_SEP: continue                       # duplicate guard
        rr = mh['TVT'].values + mh['Z'].values; ok = np.isfinite(rr)
        px.append(mh['X'].values[ok][::4]); py.append(mh['Y'].values[ok][::4]); pr.append(rr[ok][::4])
        surv_seps.append(sep)                      # separations of mates that SURVIVED the guard
    nnb = len(px); closest = float(min(seps)) if seps else np.nan
    closest_surv = float(min(surv_seps)) if surv_seps else np.nan
    if nnb == 0:
        META.append((wid, 0, closest, len(ridx), 0.0, 0.0, np.nan)); continue
    PX = np.concatenate(px); PY = np.concatenate(py); PR = np.concatenate(pr)

    # dip direction from a plane fit over the mates
    mx, my = PX.mean(), PY.mean()
    A = np.column_stack([np.ones(len(PX)), PX - mx, PY - my])
    try:
        coef = np.linalg.solve(A.T @ A + 1e-6 * np.eye(3), A.T @ PR)
        gx, gy = float(coef[1]), float(coef[2])
    except Exception:
        gx, gy = 0.0, 0.0
    gn = np.hypot(gx, gy)
    if gn < 1e-12: u = np.array([1.0, 0.0])
    else:          u = np.array([gx, gy]) / gn
    v = np.array([-u[1], u[0]])                          # strike, perpendicular to dip

    kn_idx = np.where(kn_mask)[0][-ANCHOR:]
    P = np.column_stack([PX, PY])
    for a in ANISOS:
        # transform into the (dip, strike/A) frame; euclidean distance there == anisotropic distance
        Pt = np.column_stack([P @ u, (P @ v) / a])
        Tt = np.column_stack([tgt_xy @ u, (tgt_xy @ v) / a])
        dd, ii = cKDTree(Pt).query(Tt, k=min(K, len(PR)))
        if dd.ndim == 1: dd = dd[:, None]; ii = ii[:, None]
        wgt = 1.0 / (dd + 1.0)
        r_pred = (wgt * PR[ii]).sum(1) / wgt.sum(1)
        anchor = float(np.nanmean(hw['TVT_input'].values[kn_idx] + Z[kn_idx] - r_pred[kn_idx]))
        OS[a].append((r_pred + anchor - Z)[ridx].astype(np.float32))
    OW.append(np.full(len(ridx), wid)); OR.append(ridx)
    META.append((wid, nnb, closest, len(ridx), gn, float(np.degrees(np.arctan2(u[1], u[0]))), closest_surv))

out = dict(well=np.concatenate(OW).astype(str), ridx=np.concatenate(OR).astype(np.int32),
           meta_well=np.array([m[0] for m in META]).astype(str),
           meta_nnb=np.array([m[1] for m in META], dtype=np.int32),
           meta_closest=np.array([m[2] for m in META], dtype=np.float32),
           meta_gradmag=np.array([m[4] for m in META], dtype=np.float32),
           meta_dipdeg=np.array([m[5] for m in META], dtype=np.float32),
           meta_closest_surv=np.array([m[6] for m in META], dtype=np.float32))
for a in ANISOS: out[f'struct_a{a:g}'] = np.concatenate(OS[a])
np.savez_compressed(OUT, **out)
print(f"\nsaved {OUT}: wells={len(OW)} rows={sum(len(x) for x in OR)} anisos={ANISOS}")
