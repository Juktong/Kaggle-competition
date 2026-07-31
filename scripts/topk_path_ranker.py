"""D4: train a nested top-K path ranker and evaluate it against the current honest slot.

Current honest slot 54844628 = gated structural blend, honest OOF 8.8626:
    base   = 0.5*DWT + 0.5*PF_weighted_mean
    output = base, with (1-W)*base + W*struct on gated rows (nnb>=4 & closest<1000ft, W=0.15)

Candidate: replace PF_weighted_mean with a RANKER-SELECTED PF path, keeping everything else identical.
The ranker uses ONLY test-available path features (path_rmse / mean_rmse / dwt_rmse are targets/diagnostics,
never inputs). Selection and weights are nested by well (GroupKFold), never in-sample.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
FEAT = os.environ.get('FEAT', os.path.join(SH, 'topk_feat.csv'))
PATHDIR = os.environ.get('PATHDIR', os.path.join(SH, 'topk_paths'))

FEATURES = ['loglik', 'w', 'lik_rank', 'smooth', 'jumps', 'total_move', 'dir_changes',
            'seam', 'out_of_range', 'd_dwt', 'd_struct', 'd_mean', 'n_eval', 'heel_drift']
FORBIDDEN = ['path_rmse', 'mean_rmse', 'dwt_rmse']   # truth-derived: target/diagnostic only

df = pd.read_csv(FEAT)
df = df[df.seed >= 0].copy()
print(f"feature table: {len(df)} paths, {df.well.nunique()} wells")

# per-well path arrays
store = {}
for f in glob.glob(os.path.join(PATHDIR, '*.npz')):
    w = os.path.basename(f)[:-4]
    z = np.load(f)
    store[w] = dict(paths=z['paths'].astype(np.float64), mean=z['mean'].astype(np.float64),
                    dwt=z['dwt'].astype(np.float64), struct=z['struct'].astype(np.float64),
                    truth=z['truth'].astype(np.float64), ridx=z['ridx'].astype(int))
wells = sorted(set(df.well) & set(store))
print(f"wells with paths: {len(wells)}")

# gate metadata for the structural field (same definition as the deployed candidate)
stz = np.load(os.path.join(SH, 'struct_oof.npz'), allow_pickle=True)
nnb = dict(zip(stz['meta_well'].astype(str), stz['meta_nnb'].astype(int)))
closest = dict(zip(stz['meta_well'].astype(str), stz['meta_closest'].astype(float)))
W_STRUCT = 0.15

def assemble(sel_idx):
    """sel_idx: {well -> seed index} ; returns pooled RMSE of the full deployed pipeline."""
    num, den = 0.0, 0
    for w in wells:
        S = store[w]
        pf = S['paths'][sel_idx[w]] if sel_idx is not None else S['mean']
        base = 0.5 * S['dwt'] + 0.5 * pf
        out = base.copy()
        if nnb.get(w, 0) >= 4 and np.isfinite(closest.get(w, np.nan)) and closest.get(w, 1e9) < 1000 and np.isfinite(S['struct']).all():
            out = (1 - W_STRUCT) * base + W_STRUCT * S['struct']
        num += float(np.sum((out - S['truth']) ** 2)); den += len(S['truth'])
    return float(np.sqrt(num / den))

# reference points
mean_sel = None
oracle_sel = {}
maxlik_sel = {}
for w in wells:
    S = store[w]; g = df[df.well == w]
    rm = np.array([float(np.sqrt(np.mean((S['paths'][s] - S['truth']) ** 2))) for s in range(S['paths'].shape[0])])
    oracle_sel[w] = int(np.argmin(rm))
    maxlik_sel[w] = int(g.loc[g.loglik.idxmax(), 'seed'])
print(f"\n  deployed (PF weighted mean)  = {assemble(None):.4f}   <- incumbent 54844628 pipeline")
print(f"  max-likelihood path pick     = {assemble(maxlik_sel):.4f}")
print(f"  ORACLE best path (upper bnd) = {assemble(oracle_sel):.4f}")

# ---- nested ranker ----
try:
    import lightgbm as lgb; HAVE_LGB = True
except Exception:
    HAVE_LGB = False
from sklearn.linear_model import Ridge
print(f"  lightgbm available: {HAVE_LGB}")

df['tgt'] = df.groupby('well')['path_rmse'].transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))
uw = np.array(sorted(wells)); rng = np.random.RandomState(0)
FOLDS = 5
fold = {w: i % FOLDS for i, w in enumerate(rng.permutation(uw))}
df['fold'] = df.well.map(fold)

for name in (['ridge'] + (['lgbm'] if HAVE_LGB else [])):
    sel = {}
    for f in range(FOLDS):
        tr = df[(df.fold != f) & df.well.isin(wells)]
        te = df[(df.fold == f) & df.well.isin(wells)]
        if len(tr) < 50 or len(te) == 0: continue
        Xtr = tr[FEATURES].fillna(0).values; ytr = tr['tgt'].values
        Xte = te[FEATURES].fillna(0).values
        if name == 'ridge':
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
            m = Ridge(alpha=1.0).fit((Xtr - mu) / sd, ytr); pr = m.predict((Xte - mu) / sd)
        else:
            m = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=15,
                                  min_child_samples=50, verbose=-1).fit(Xtr, ytr)
            pr = m.predict(Xte)
        te = te.assign(score=pr)
        for w, g in te.groupby('well'):
            sel[w] = int(g.loc[g.score.idxmin(), 'seed'])     # lowest predicted normalized rmse
    missing = [w for w in wells if w not in sel]
    for w in missing: sel[w] = maxlik_sel[w]
    print(f"  NESTED ranker [{name}]          = {assemble(sel):.4f}   (wells selected {len(wells)-len(missing)}/{len(wells)})")
    # SHRINKAGE: averaging is variance reduction, so blend the picked path toward the weighted mean
    for lam in [0.25, 0.5, 0.75]:
        num, den = 0.0, 0
        for w in wells:
            S = store[w]
            pf = (1 - lam) * S['mean'] + lam * S['paths'][sel[w]]
            base = 0.5 * S['dwt'] + 0.5 * pf
            out = base.copy()
            if nnb.get(w, 0) >= 4 and np.isfinite(closest.get(w, np.nan)) and closest.get(w, 1e9) < 1000 and np.isfinite(S['struct']).all():
                out = (1 - W_STRUCT) * base + W_STRUCT * S['struct']
            num += float(np.sum((out - S['truth']) ** 2)); den += len(S['truth'])
        print(f"      shrink lam={lam:.2f}            = {float(np.sqrt(num/den)):.4f}")

print("\nGATE: a ranker must beat the deployed pipeline (and materially, given transfer noise) to be a candidate.")
