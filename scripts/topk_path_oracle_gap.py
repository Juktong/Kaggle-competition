"""Direction C (cheap-first): oracle best-of-K gap for PF seed-paths.
If picking the truth-closest seed path (ORACLE) barely beats the likelihood-weighted average, a learned path
ranker has no headroom -> close C early. If the gap is large, build the ranker with the per-path features
computed here (likelihood, smoothness, jump, anchor consistency, typewell range pressure, DWT agreement)."""
import os, glob, time, numpy as np, pandas as pd
from collections import defaultdict

JOB = os.environ['CLAUDE_JOB_DIR']
code = open('/home/ubuntu/.claude/jobs/06dd2efb/tmp/SUNNY_CODE.py').read()
cut = code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
funcs = code[:cut].replace("INPUT_DIR = find_input_dir()", "INPUT_DIR = os.path.abspath('data/rogii')")
ns = {}; exec(funcs, ns)
run_pfilter = ns['run_particle_filter']; load_well = ns['load_well']; TRAIN_DIR = ns['TRAIN_DIR']

NS = int(os.environ.get('NS', '24')); MAXW = int(os.environ.get('MAXW', '20')); SCALE = 5.0
D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
cs = np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM = cs['is_toe']
dw = cs['well'][tM].astype(str); do = cs['oof'][tM].astype(np.float64); dy = cs['yt'][tM].astype(np.float64); dr = cs['ridx'][tM].astype(int)
dwt = defaultdict(dict)
for w, r, o, y in zip(dw, dr, do, dy): dwt[w][r] = (o, y)

allw = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng = np.random.RandomState(5); rng.shuffle(allw)
wids = [w for w in allw if w in dwt][:MAXW]

rows = []
t0 = time.time()
for wid in wids:
    try:
        hw, tw = load_well(wid, 'train')
        toe = hw['TVT_input'].isna().values; tidx = np.where(toe)[0]
        if toe.sum() < 10: continue
        keep = [(j, ii) for j, ii in enumerate(tidx) if ii in dwt[wid]]
        if len(keep) < 10: continue
        preds, liks = [], []
        for s in range(NS):
            p, ll = run_pfilter(hw, tw, n_particles=500, seed=s)
            preds.append(np.asarray(p, float)); liks.append(float(ll))
        P = np.stack(preds, 0); L = np.array(liks)
        w_ = np.exp((L - L.max()) / SCALE); w_ = w_ / w_.sum()
        mean = (w_[:, None] * P).sum(0)
        Y = np.array([dwt[wid][ii][1] for _, ii in keep])
        Dv = np.array([dwt[wid][ii][0] for _, ii in keep])
        sel = np.array([ii for _, ii in keep])
        # per-seed RMSE on the aligned toe rows
        seed_rmse = np.array([np.sqrt(np.mean((P[s][sel] - Y) ** 2)) for s in range(NS)])
        avg_rmse = np.sqrt(np.mean((mean[sel] - Y) ** 2))
        oracle_rmse = seed_rmse.min()
        maxlik_rmse = seed_rmse[int(np.argmax(L))]          # deployable: pick the highest-likelihood seed
        blend_rmse = np.sqrt(np.mean((0.5 * Dv + 0.5 * mean[sel] - Y) ** 2))
        # oracle blend: best seed blended with DWT
        oracle_blend = min(np.sqrt(np.mean((0.5 * Dv + 0.5 * P[s][sel] - Y) ** 2)) for s in range(NS))
        rows.append(dict(well=wid, n=len(keep), avg=avg_rmse, oracle=oracle_rmse, maxlik=maxlik_rmse,
                         worst=seed_rmse.max(), spread=seed_rmse.std(),
                         blend=blend_rmse, oracle_blend=oracle_blend,
                         lik_corr=np.corrcoef(L, -seed_rmse)[0, 1] if np.std(L) > 1e-9 else np.nan))
        print(f"  {wid}: avg={avg_rmse:.2f} oracle={oracle_rmse:.2f} maxlik={maxlik_rmse:.2f} blend={blend_rmse:.2f} oracle_blend={oracle_blend:.2f}", flush=True)
    except Exception as e:
        print(f"  {wid} ERR {e}", flush=True)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(JOB, 'tmp/c_topk_oracle.csv'), index=False)
def pool(col):  # row-count-weighted pooled RMSE
    return np.sqrt(np.sum(df[col] ** 2 * df.n) / df.n.sum())
print(f"\nwells={len(df)} time={(time.time()-t0)/60:.1f}m  NS={NS}")
print(f"  PF weighted-average   pooled RMSE = {pool('avg'):.4f}   <- current PF")
print(f"  PF ORACLE best-seed   pooled RMSE = {pool('oracle'):.4f}   <- upper bound for a path ranker")
print(f"  PF max-likelihood seed pooled RMSE= {pool('maxlik'):.4f}   <- deployable single-path pick")
print(f"  PF worst seed          pooled RMSE= {pool('worst'):.4f}")
print(f"  DWT+PF blend (avg)     pooled RMSE= {pool('blend'):.4f}")
print(f"  DWT+PF blend (ORACLE seed) pooled = {pool('oracle_blend'):.4f}   <- upper bound if ranker were perfect")
print(f"  mean corr(seed loglik, -seed RMSE) = {df.lik_corr.mean():.3f}  (does likelihood identify the good path?)")
print("\n=> If oracle ~= avg, no ranker headroom. If maxlik >> avg, likelihood is not a usable ranking signal.")
