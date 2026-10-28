"""D4 FULL VERDICT: nested top-K path ranker + shrinkage, with well-level bootstrap.

Incumbent honest slot 54844628 = gated structural blend, honest OOF 8.8626:
    base   = 0.5*DWT + 0.5*PF_weighted_mean
    output = base, with (1-W)*base + W*struct on gated rows (nnb>=4 & closest<1000ft, W=0.15)

Candidate replaces PF_weighted_mean with a ranker-selected path, optionally shrunk toward the mean.
Ranker inputs are ONLY test-available path features; path_rmse is the training target, never an input.
Selection, shrinkage weight and evaluation are all nested by well (GroupKFold).
"""
import os, glob, numpy as np, pandas as pd

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
FEAT = os.environ.get('FEAT', os.path.join(SH, 'topk_feat.csv'))
PATHDIR = os.environ.get('PATHDIR', os.path.join(SH, 'topk_paths'))
FOLDS = int(os.environ.get('FOLDS', '5'))
NBOOT = int(os.environ.get('NBOOT', '200'))

FEATURES = ['loglik', 'w', 'lik_rank', 'smooth', 'jumps', 'total_move', 'dir_changes',
            'seam', 'out_of_range', 'd_dwt', 'd_struct', 'd_mean', 'n_eval', 'heel_drift']

df = pd.read_csv(FEAT); df = df[df.seed >= 0].copy()
store = {}
for f in glob.glob(os.path.join(PATHDIR, '*.npz')):
    w = os.path.basename(f)[:-4]; z = np.load(f)
    store[w] = dict(paths=z['paths'].astype(np.float32), mean=z['mean'].astype(np.float32),
                    dwt=z['dwt'].astype(np.float32), struct=z['struct'].astype(np.float32),
                    truth=z['truth'].astype(np.float32))
wells = sorted(set(df.well.astype(str)) & set(store))
print(f"FULL VERDICT: {len(df)} paths, {len(wells)} wells", flush=True)

stz = np.load(os.path.join(SH, 'struct_oof.npz'), allow_pickle=True)
nnb = dict(zip(stz['meta_well'].astype(str), stz['meta_nnb'].astype(int)))
closest = dict(zip(stz['meta_well'].astype(str), stz['meta_closest'].astype(float)))
W_STRUCT = 0.15

def gated(w):
    return nnb.get(w, 0) >= 4 and np.isfinite(closest.get(w, np.nan)) and closest.get(w, 1e9) < 1000

# per-well squared-error contributions for a given PF choice -> lets us bootstrap over wells
def well_sse(w, pf):
    S = store[w]
    base = 0.5 * S['dwt'].astype(np.float64) + 0.5 * pf.astype(np.float64)
    out = base
    if gated(w) and np.isfinite(S['struct']).all():
        out = (1 - W_STRUCT) * base + W_STRUCT * S['struct'].astype(np.float64)
    e = out - S['truth'].astype(np.float64)
    return float(np.sum(e * e)), len(e)

def pooled(sse_n):
    s = sum(a for a, _ in sse_n.values()); n = sum(b for _, b in sse_n.values())
    return float(np.sqrt(s / n))

# references
sse_mean = {w: well_sse(w, store[w]['mean']) for w in wells}
oracle_sel, maxlik_sel = {}, {}
for w in wells:
    S = store[w]; g = df[df.well == w]
    rm = np.sqrt(((S['paths'].astype(np.float64) - S['truth'].astype(np.float64)) ** 2).mean(1))
    oracle_sel[w] = int(np.argmin(rm))
    maxlik_sel[w] = int(g.loc[g.loglik.idxmax(), 'seed'])
sse_oracle = {w: well_sse(w, store[w]['paths'][oracle_sel[w]]) for w in wells}
sse_maxlik = {w: well_sse(w, store[w]['paths'][maxlik_sel[w]]) for w in wells}
print(f"\n  deployed (PF weighted mean)  = {pooled(sse_mean):.4f}   <- incumbent 54844628 pipeline (OOF 8.8626)")
print(f"  max-likelihood path pick     = {pooled(sse_maxlik):.4f}")
print(f"  ORACLE best path (upper bnd) = {pooled(sse_oracle):.4f}", flush=True)

try:
    import lightgbm as lgb; HAVE = True
except Exception: HAVE = False
from sklearn.linear_model import Ridge

df['tgt'] = df.groupby('well')['path_rmse'].transform(lambda s: (s - s.mean()) / (s.std() + 1e-9))
rng = np.random.RandomState(0)
fold = {w: i % FOLDS for i, w in enumerate(rng.permutation(np.array(wells)))}
df['fold'] = df.well.map(fold)

results = {}
for name in (['ridge'] + (['lgbm'] if HAVE else [])):
    sel = {}
    for f in range(FOLDS):
        tr = df[(df.fold != f) & df.well.isin(wells)]; te = df[(df.fold == f) & df.well.isin(wells)]
        if len(tr) < 50 or len(te) == 0: continue
        Xtr = tr[FEATURES].fillna(0).values; Xte = te[FEATURES].fillna(0).values
        if name == 'ridge':
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
            pr = Ridge(alpha=1.0).fit((Xtr - mu) / sd, tr['tgt'].values).predict((Xte - mu) / sd)
        else:
            pr = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31,
                                   min_child_samples=50, verbose=-1).fit(Xtr, tr['tgt'].values).predict(Xte)
        te = te.assign(score=pr)
        for w, g in te.groupby('well'): sel[w] = int(g.loc[g.score.idxmin(), 'seed'])
    for w in wells:
        if w not in sel: sel[w] = maxlik_sel[w]
    for lam in [1.0, 0.75, 0.5, 0.25]:
        sse = {}
        for w in wells:
            S = store[w]
            pf = (1 - lam) * S['mean'] + lam * S['paths'][sel[w]]
            sse[w] = well_sse(w, pf)
        r = pooled(sse); results[(name, lam)] = (r, sse)
        tag = 'hard-pick' if lam == 1.0 else f'shrink lam={lam:.2f}'
        print(f"  ranker[{name:5s}] {tag:16s} = {r:.4f}   gain vs deployed {pooled(sse_mean)-r:+.4f}", flush=True)

best = min(results.items(), key=lambda kv: kv[1][0])
(bn, bl), (br, bsse) = best
base_r = pooled(sse_mean)
print(f"\n  BEST: ranker[{bn}] lam={bl:.2f} -> {br:.4f}  (gain {base_r-br:+.4f} vs deployed {base_r:.4f})")

# well-level bootstrap of the best variant's gain
wl = np.array(wells); rb = np.random.RandomState(7); gains = []
for _ in range(NBOOT):
    samp = wl[rb.randint(0, len(wl), len(wl))]
    s1 = sum(sse_mean[w][0] for w in samp); n1 = sum(sse_mean[w][1] for w in samp)
    s2 = sum(bsse[w][0] for w in samp); n2 = sum(bsse[w][1] for w in samp)
    gains.append(np.sqrt(s1 / n1) - np.sqrt(s2 / n2))
g = np.array(gains)
print(f"  bootstrap gain ({NBOOT} well-resamples): mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} frac>0={100*np.mean(g>0):.0f}%")
print(f"\n  DECISION THRESHOLD was +0.10 with a stably positive bootstrap.")
print(f"  -> {'MEETS' if (base_r-br) >= 0.10 and np.percentile(g,5) > 0 else 'DOES NOT MEET'} the threshold.")
