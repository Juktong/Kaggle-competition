"""D1: PF re-run retaining ALL K seed paths + per-path features, for the top-K path ranker.

The shipped PF keeps only the likelihood-weighted mean. Here we keep every seed path and compute, per path,
features that are ALL test-available at inference (no truth):
  loglik, softmax weight, rank-by-lik, smoothness (std of 2nd diff), jump count, total move,
  direction changes, anchor seam consistency, typewell range-pressure, distance to DWT, distance to the
  structural field, distance to the PF weighted mean, per-well context (n_eval, heel drift).
`path_rmse` is stored too, but ONLY as the ranker's training target - never as an inference feature.

Checkpointed / resumable / detached-safe. Env: NS, MAXW, BATCH, CKPT, LOG, OUTDIR.
"""
import os, time, glob, numpy as np, pandas as pd
from collections import defaultdict
from joblib import Parallel, delayed

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
code = open('/home/ubuntu/.claude/jobs/06dd2efb/tmp/SUNNY_CODE.py').read()
cut = code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
funcs = code[:cut].replace("INPUT_DIR = find_input_dir()", "INPUT_DIR = os.path.abspath('data/rogii')")
ns = {}; exec(funcs, ns)
run_pfilter = ns['run_particle_filter']; load_well = ns['load_well']; TRAIN_DIR = ns['TRAIN_DIR']

NS = int(os.environ.get('NS', '24')); MAXW = int(os.environ.get('MAXW', '773')); BATCH = int(os.environ.get('BATCH', '8'))
SCALE = 5.0
CKPT = os.environ.get('CKPT', os.path.join(SH, 'topk_feat.csv'))
PATHDIR = os.environ.get('OUTDIR', os.path.join(SH, 'topk_paths'))
LOG = os.environ.get('LOG', os.path.join(SH, 'topk.log'))
os.makedirs(PATHDIR, exist_ok=True)

# references on identical rows
cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dwv = cs['well'][tM].astype(str); dov = cs['oof'][tM].astype(np.float64); dyv = cs['yt'][tM].astype(np.float64); drv = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(dwv, drv, dov, dyv): dwt[w][r] = (o, y)
del cs
stz = np.load(os.path.join(SH, 'struct_oof.npz'), allow_pickle=True)
sidx = defaultdict(dict)
for w, r, s in zip(stz['well'].astype(str), stz['ridx'].astype(int), stz['struct'].astype(np.float64)): sidx[w][int(r)] = s

train_wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(os.path.join(TRAIN_DIR, '*__horizontal_well.csv')))
rng = np.random.RandomState(42); order = list(train_wids); rng.shuffle(order); wids = order[:MAXW]
done = set()
if os.path.exists(CKPT):
    try: done = set(pd.read_csv(CKPT, usecols=['well'])['well'].astype(str).unique())
    except Exception: pass
todo = [w for w in wids if w not in done]

# --- pre-slice per-well reference arrays: joblib must NOT pickle the 3.78M-row dicts ---
WELLREF = {}
for _w in wids:
    if _w not in dwt: continue
    _rows = sorted(dwt[_w].keys())
    _ri = np.array(_rows, dtype=np.int32)
    _dv = np.array([dwt[_w][r][0] for r in _rows], dtype=np.float64)
    _yv = np.array([dwt[_w][r][1] for r in _rows], dtype=np.float64)
    _sd = sidx.get(_w, {})
    _sv = np.array([_sd.get(int(r), np.nan) for r in _rows], dtype=np.float64)
    WELLREF[_w] = (_ri, _dv, _yv, _sv)
dwt.clear(); sidx.clear()

def log(s):
    with open(LOG, 'a') as f: f.write(s + '\n')
    print(s, flush=True)

def one(wid, ref):
    try:
        ref_ri, ref_dv, ref_yv, ref_sv = ref
        hw, tw = load_well(wid, 'train')
        kn = hw['TVT_input'].notna().values; toe = ~kn
        if toe.sum() < 10 or kn.sum() < 10: return None
        tidx = np.where(toe)[0]
        pos = {int(v): j for j, v in enumerate(tidx)}
        sel = [(pos[int(r)], b) for b, r in enumerate(ref_ri) if int(r) in pos]
        if len(sel) < 10: return None
        kj = np.array([a for a, _ in sel]); ki = np.array([int(ref_ri[b]) for _, b in sel])
        Yv = np.array([ref_yv[b] for _, b in sel]); Dv = np.array([ref_dv[b] for _, b in sel])
        Sv = np.array([ref_sv[b] for _, b in sel])
        preds, liks = [], []
        for s in range(NS):
            p, ll = run_pfilter(hw, tw, n_particles=500, seed=s)
            preds.append(np.asarray(p, float)); liks.append(float(ll))
        P = np.stack(preds, 0); L = np.array(liks)
        wgt = np.exp((L - L.max()) / SCALE); wgt = wgt / wgt.sum()
        mean = (wgt[:, None] * P).sum(0)
        tw_tvt = tw['TVT'].values.astype(float); tlo, thi = np.nanmin(tw_tvt), np.nanmax(tw_tvt)
        last_kn = np.where(kn)[0][-1]; last_tvt = float(hw['TVT_input'].values[last_kn])
        n_eval = int(toe.sum())
        tail = hw[kn].tail(30); dt = np.diff(tail['TVT_input'].values); dm = np.diff(tail['MD'].values); mm = dm > 0
        hdrift = float(np.median(np.abs(dt[mm] / dm[mm]))) if mm.sum() >= 3 else 0.0
        rank = np.argsort(np.argsort(-L))
        rows = []
        for s in range(NS):
            pv = P[s][ki]; full = P[s]
            d2 = np.diff(full[tidx], 2) if len(tidx) > 2 else np.array([0.0])
            d1 = np.diff(full[tidx]) if len(tidx) > 1 else np.array([0.0])
            rows.append(dict(
                well=wid, seed=s, loglik=L[s], w=wgt[s], lik_rank=int(rank[s]),
                smooth=float(np.std(d2)), jumps=int(np.sum(np.abs(d1) > 1.0)),
                total_move=float(abs(full[tidx][-1] - full[tidx][0])) if len(tidx) else 0.0,
                dir_changes=int(np.sum(np.diff(np.sign(d1)) != 0)) if len(d1) > 1 else 0,
                seam=float(abs(full[tidx[0]] - last_tvt)),
                out_of_range=float(np.mean((full[tidx] < tlo) | (full[tidx] > thi))),
                d_dwt=float(np.mean(np.abs(pv - Dv))),
                d_struct=float(np.mean(np.abs(pv - Sv))) if np.isfinite(Sv).all() else np.nan,
                d_mean=float(np.mean(np.abs(pv - mean[ki]))),
                n_eval=n_eval, heel_drift=hdrift,
                path_rmse=float(np.sqrt(np.mean((pv - Yv) ** 2))),          # TRAINING TARGET ONLY
                mean_rmse=float(np.sqrt(np.mean((mean[ki] - Yv) ** 2))),
                dwt_rmse=float(np.sqrt(np.mean((Dv - Yv) ** 2))),
            ))
        np.savez_compressed(os.path.join(PATHDIR, f'{wid}.npz'),
                            ridx=ki.astype(np.int32), paths=P[:, ki].astype(np.float32),
                            mean=mean[ki].astype(np.float32), dwt=Dv.astype(np.float32),
                            struct=Sv.astype(np.float32), truth=Yv.astype(np.float32), loglik=L.astype(np.float32))
        return rows
    except Exception as e:
        return [dict(well=wid, seed=-1, loglik=np.nan, err=str(e)[:60])]

log(f"=== D1 top-K path dump NS={NS} todo={len(todo)} done={len(done)} ===")
t0 = time.time()
for i in range(0, len(todo), BATCH):
    batch = todo[i:i + BATCH]
    res = Parallel(n_jobs=2)(delayed(one)(w, WELLREF[w]) for w in batch if w in WELLREF)
    rows = [r for rr in res if rr for r in rr]
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(CKPT, mode='a', header=not os.path.exists(CKPT), index=False)
    ndone = len(done) + i + len(batch)
    log(f"[{(time.time()-t0)/60:5.1f}m] wells~{min(ndone, len(wids))}/{len(wids)}")
log("DONE")
