"""A1: produce the group-anchored structural-field OOF for all 773 train wells AND SAVE per-row predictions
plus per-well neighbour metadata, so stress (A2) and audit (A5) need no re-run.

Deployable definition (must match inference exactly):
  group key   = round(max(typewell.TVT), 1)        [from the target's OWN typewell -> test-available]
  neighbours  = same-group TRAIN wells with median trajectory XY separation >= MIN_SEP  [duplicate guard]
  field       = IDW(k=K, w=1/(d+1)) over neighbours' (X, Y, r=TVT+Z)
  anchor      = mean(r_true - r_pred) over the target's OWN last ANCHOR known heel rows
  prediction  = r_pred + anchor - Z
  fallback    = if no surviving neighbour -> struct contribution disabled (weight 0)
Saved: well, ridx, struct (per row) + per-well n_neighbours / closest_mate_sep.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
K = int(os.environ.get('K', '12')); ANCHOR = int(os.environ.get('ANCHOR', '100'))
MIN_SEP = float(os.environ.get('MIN_SEP', '150'))
MAXW = int(os.environ.get('MAXW', '10000'))
OUT = os.environ.get('OUT', os.path.join(SH, 'struct_oof_rowdist.npz'))

cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dwell = cs['well'][tM].astype(str); dr = cs['ridx'][tM].astype(int)
toe_rows = defaultdict(set)
for w, r in zip(dwell, dr): toe_rows[w].add(int(r))
del cs

print('building typewell groups...', flush=True)
gkey = {}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid = os.path.basename(f).split('__')[0]
    try: gkey[wid] = round(float(np.nanmax(pd.read_csv(f, usecols=['TVT'])['TVT'].values)), 1)
    except Exception: pass
groups = defaultdict(list)
for wid, k in gkey.items(): groups[k].append(wid)
print(f'  {len(groups)} groups', flush=True)

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
OW, OR, OS, OND = [], [], [], []
META = []
for n, wid in enumerate(targets):
    if n % 50 == 0: print(f'  [{n}/{len(targets)}]', flush=True)
    if wid not in gkey: continue
    try: hw = get(wid)
    except Exception: continue
    kn_mask = hw['TVT_input'].notna().values
    if kn_mask.sum() < ANCHOR: continue
    tset = toe_rows[wid]
    ridx = np.array(sorted(tset))
    if len(ridx) < 10: continue
    X = hw['X'].values; Y = hw['Y'].values; Z = hw['Z'].values
    tgt_xy = np.column_stack([X, Y])
    mates = [m for m in groups.get(gkey[wid], []) if m != wid]
    px, py, pr, seps = [], [], [], []
    for m in mates:
        try: mh = get(m)
        except Exception: continue
        if len(mh) < 5: continue
        d, _ = tree_of(m).query(tgt_xy[::10], k=1)
        sep = float(np.median(d)); seps.append(sep)
        if sep < MIN_SEP: continue                      # duplicate guard
        rr = mh['TVT'].values + mh['Z'].values
        ok = np.isfinite(rr)
        px.append(mh['X'].values[ok][::4]); py.append(mh['Y'].values[ok][::4]); pr.append(rr[ok][::4])
    nnb = len(px)
    closest = float(min(seps)) if seps else np.nan
    if nnb == 0:
        META.append((wid, 0, closest, len(ridx))); continue   # fallback: no struct contribution
    PX = np.concatenate(px); PY = np.concatenate(py); PR = np.concatenate(pr)
    dd, ii = cKDTree(np.column_stack([PX, PY])).query(tgt_xy, k=min(K, len(PR)))
    if dd.ndim == 1: dd = dd[:, None]; ii = ii[:, None]
    wgt = 1.0 / (dd + 1.0)
    r_pred = (wgt * PR[ii]).sum(1) / wgt.sum(1)
    kn_idx = np.where(kn_mask)[0][-ANCHOR:]
    anchor = float(np.nanmean(hw['TVT_input'].values[kn_idx] + Z[kn_idx] - r_pred[kn_idx]))
    pred = r_pred + anchor - Z
    nn0 = dd[:, 0] if dd.ndim > 1 else dd
    OW.append(np.full(len(ridx), wid)); OR.append(ridx); OS.append(pred[ridx].astype(np.float32))
    OND.append(nn0[ridx].astype(np.float32))
    META.append((wid, nnb, closest, len(ridx)))

np.savez_compressed(OUT,
                    well=np.concatenate(OW).astype(str), ridx=np.concatenate(OR).astype(np.int32),
                    struct=np.concatenate(OS), nn_dist=np.concatenate(OND),
                    meta_well=np.array([m[0] for m in META]).astype(str),
                    meta_nnb=np.array([m[1] for m in META], dtype=np.int32),
                    meta_closest=np.array([m[2] for m in META], dtype=np.float32),
                    meta_nrows=np.array([m[3] for m in META], dtype=np.int32))
print(f"\nsaved {OUT}: wells_with_struct={len(OW)} rows={sum(len(x) for x in OR)} wells_total={len(META)}")
print(f"  wells with 0 neighbours (fallback): {sum(1 for m in META if m[1]==0)}")
