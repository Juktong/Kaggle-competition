"""V2 — Structural-surface predictability probe (foundation for BIG N-A).

Compliance
----------
The 6 structural surfaces (ANCC/ASTNU/ASTNL/EGFDU/EGFDL/BUDA) are TRAIN-ONLY: the TEST
horizontal wells carry only {MD,X,Y,Z,GR,TVT_input}. Here the surfaces are used ONLY as
LABELS to train a surface predictor. Every feature fed to the predictor AND to the downstream
TVT-residual model is test-available (GR windows, trajectory X/Y/Z/MD, distance-from-cut,
known-heel anchor, typewell GR stats). Surfaces are never read at inference. The downstream
TVT model consumes the predictor's OOF outputs (avoids train/test feature mismatch), exactly
the N-A deployment principle.

Geometry note
-------------
Z and the surfaces live in the ELEVATION frame (~ -9200..-9850); TVT is a positive stratigraphic
coordinate (~11236). The meaningful, Z-detrended structural quantity is (surface - Z) = the
signed bit-to-horizon offset (which formation the bit sits in). We predict that.

Questions
---------
(1) FOUNDATION  — can test-available inputs predict (surf - Z) out-of-fold? R^2 > 0 means the
    structural offset carries signal beyond a constant.
(2) CEILING (ORACLE, diagnostic only, NOT achievable) — feed the TRUE (surf - Z) as features into
    a TVT-residual model; nested blend vs DWT. If even TRUE surfaces give blend weight <= 0, the
    entire structural-label route is closed regardless of how well we can predict surfaces.
(3) ACHIEVABLE (the real gate) — feed the OOF-PREDICTED (surf - Z) as features into a TVT-residual
    model; nested blend vs DWT: RMSE, corr(err,DWT), blend-weight sign/stability.

PASS: any surface OOF R^2 > 0 AND achievable predicted-surface nested blend weight stable POSITIVE
      (not a negative-weight lambda-disguise / drift-amplification).
STOP: all surface R^2 <= 0 OR achievable blend weight <= 0.
"""
import numpy as np, pandas as pd, glob, time, os, lightgbm as lgb

DATA = "/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
NPZ  = os.path.join(os.environ["CLAUDE_JOB_DIR"], "tmp", "combo_state.npz")
SURF = ['ANCC', 'ASTNU', 'ASTNL', 'EGFDU', 'EGFDL', 'BUDA']
SUB  = 10          # subsample every SUB toe rows (CPU probe)
NJ   = 2
t0 = time.time()
rng = np.random.RandomState(0)
def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))
def lgbm(**kw):
    p = dict(n_estimators=250, num_leaves=31, learning_rate=0.04, min_child_samples=50,
             subsample=0.8, colsample_bytree=0.8, subsample_freq=1, n_jobs=NJ, verbose=-1)
    p.update(kw); return lgb.LGBMRegressor(**p)

# ---- DWT OOF ----
z = np.load(NPZ, allow_pickle=True)
d = pd.DataFrame(dict(well=z['well'], ridx=z['ridx'].astype(int), oof=z['oof'], yt=z['yt'],
                      base=z['base'], cut=z['cut'], is_toe=z['is_toe']))
g = {w: s.reset_index(drop=True) for w, s in d.groupby('well')}
print(f"[{time.time()-t0:.0f}s] DWT OOF: {len(d)} rows, {len(g)} wells", flush=True)

def grfeat(gr, idx):
    out = np.empty((len(idx), 6), np.float32)
    for j, i in enumerate(idx):
        w1 = gr[max(0, i-10):i+11]; w2 = gr[max(0, i-30):i+31]
        w1 = w1[~np.isnan(w1)];     w2 = w2[~np.isnan(w2)]
        gi = gr[i] if not np.isnan(gr[i]) else (w2.mean() if len(w2) else 0.0)
        out[j] = [gi, w1.mean() if len(w1) else gi, w1.std() if len(w1) else 0.0,
                  w2.mean() if len(w2) else gi, w2.std() if len(w2) else 0.0,
                  (w1.max()-w1.min()) if len(w1) else 0.0]
    return out

# ---- build per-toe-row dataset ----
FB=[]; SB=[]; YY=[]; BB=[]; OO=[]; WW=[]
nwell = 0
for f in sorted(glob.glob(f"{DATA}/*__horizontal_well.csv")):
    wid = f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    cols = ['MD','X','Y','Z','GR'] + SURF
    h = pd.read_csv(f, usecols=cols)
    s = g[wid]; c = int(s.cut.iloc[0]); ri = s.ridx.values
    if ri.max() >= len(h):  # ridx must index the horizontal rows
        continue
    keep = np.arange(0, len(ri), SUB); ri = ri[keep]
    gr = h['GR'].values.astype(float)
    X = h['X'].values.astype(float); Y = h['Y'].values.astype(float)
    Z = h['Z'].values.astype(float); MD = h['MD'].values.astype(float)
    Zc = Z[c] if c < len(Z) else Z[0]; MDc = MD[c] if c < len(MD) else MD[0]
    zi = Z[ri]; mdi = MD[ri]
    dist = (ri - c).astype(float)
    dZ = zi - Zc; dMD = mdi - MDc
    incl = dZ / (dMD + 1e-6)
    # typewell GR stats (test-available)
    tw = pd.read_csv(f.replace('__horizontal_well.csv', '__typewell.csv'), usecols=['TVT','GR'])
    tgr = tw['GR'].values.astype(float); ttvt = tw['TVT'].values.astype(float)
    tgr = tgr[np.isfinite(tgr)]
    if len(tgr) == 0: tgr = np.array([0.0])
    twf = [tgr.mean(), tgr.std(), tgr.min(), tgr.max(),
           float(np.nanmax(ttvt)-np.nanmin(ttvt)) if np.isfinite(ttvt).any() else 0.0]
    base = s.base.values[keep].astype(np.float32)
    # BASE feature matrix (all test-available)
    grf = grfeat(gr, ri)
    fb = np.column_stack([grf,                                   # 6 GR-window stats
                          X[ri], Y[ri], zi, mdi,                 # trajectory
                          dist, dist/1000.0, np.sqrt(np.maximum(dist,0)),
                          base, dZ, dMD, incl,                   # anchor + shape
                          np.tile(twf, (len(ri),1))]).astype(np.float32)  # 5 typewell stats
    # surface targets: (surf - Z), Z-detrended structural offset
    sv = h[SURF].values[ri].astype(np.float32) - zi[:,None]
    FB.append(fb); SB.append(sv)
    YY.append(s.yt.values[keep].astype(np.float32)); BB.append(base)
    OO.append(s.oof.values[keep].astype(np.float32)); WW.append(np.array([wid]*len(ri)))
    nwell += 1
    if nwell % 150 == 0: print(f"[{time.time()-t0:.0f}s] built {nwell} wells", flush=True)

Fb = np.concatenate(FB); Sv = np.concatenate(SB)
Y = np.concatenate(YY); B = np.concatenate(BB); O = np.concatenate(OO); W = np.concatenate(WW)
print(f"[{time.time()-t0:.0f}s] dataset: {Fb.shape} rows, surf {Sv.shape}, {nwell} wells", flush=True)

# ---- folds (GroupKFold by well) ----
uw = np.unique(W); perm = rng.permutation(len(uw)); f5 = {uw[perm[i]]: i % 5 for i in range(len(uw))}
fold = np.array([f5[w] for w in W])
Yd = (Y - B).astype(np.float32)   # TVT residual target

# ---- STAGE 1: surface predictability (OOF R^2 for each surf-Z) + OOF-predicted surf matrix ----
print(f"\n=== STAGE 1: surface (surf-Z) OOF predictability ===", flush=True)
Poof = np.zeros_like(Sv)   # OOF-predicted surf-Z, per row per surface
for k, name in enumerate(SURF):
    tgt = Sv[:, k]; m = np.isfinite(tgt)
    pred = np.full(len(tgt), np.nan, np.float32)
    for fo in range(5):
        tr = (fold != fo) & m; te = (fold == fo)
        mdl = lgbm().fit(Fb[tr], tgt[tr]); pred[te] = mdl.predict(Fb[te])
    Poof[:, k] = pred
    mm = m & np.isfinite(pred)
    ss_res = np.sum((tgt[mm]-pred[mm])**2); ss_tot = np.sum((tgt[mm]-tgt[mm].mean())**2)
    r2 = 1 - ss_res/ss_tot if ss_tot > 0 else float('nan')
    print(f"  {name:6s}  surf-Z mean={np.nanmean(tgt):8.1f} std={np.nanstd(tgt):7.1f}  "
          f"OOF R2={r2:+.3f}  RMSE={rmse(tgt[mm],pred[mm]):7.2f}  (n={mm.sum()})", flush=True)

def blend_report(gp, tag):
    err = np.corrcoef(gp - Y, O - Y)[0, 1]
    ws = []; bl = O.copy()
    for fo in range(5):
        tr = fold != fo; te = fold == fo
        a = (gp - O)[tr]; b = (Y - O)[tr]; den = np.sum(a*a)
        w = float(np.sum(a*b)/den) if den > 0 else 0.0; ws.append(w)
        wc = max(-0.1, min(0.7, w)); bl[te] = (1-wc)*O[te] + wc*gp[te]
    sgn = 'POSITIVE' if np.mean(ws) > 0.02 else ('~zero' if np.mean(ws) >= -0.02 else 'NEGATIVE(λ-disguise)')
    print(f"  {tag}: RMSE={rmse(gp,Y):.4f}  DWT={rmse(O,Y):.4f}  corr(err,DWT)={err:.3f}  "
          f"blendW mean={np.mean(ws):+.3f} folds=[{','.join(f'{w:+.2f}' for w in ws)}] {sgn}  "
          f"nested-blend={rmse(bl,Y):.4f}", flush=True)
    return np.mean(ws)

def tvt_oof(Xf):
    gp = np.zeros(len(Xf))
    for fo in range(5):
        tr = fold != fo; te = fold == fo
        mdl = lgbm().fit(Xf[tr], Yd[tr]); gp[te] = B[te] + mdl.predict(Xf[te])
    return gp

# ---- STAGE 0: same-input baseline (BASE only) ----
print(f"\n=== STAGE 0: TVT-residual, BASE features only (same-input sanity) ===", flush=True)
gp0 = tvt_oof(Fb); w0 = blend_report(gp0, "BASE-only")

# ---- STAGE 2: ORACLE ceiling (TRUE surf-Z as features) ----
print(f"\n=== STAGE 2: ORACLE ceiling — BASE + TRUE surf-Z (diagnostic, NOT achievable) ===", flush=True)
gp2 = tvt_oof(np.column_stack([Fb, Sv]).astype(np.float32)); w2 = blend_report(gp2, "BASE+TRUE-surf")

# ---- STAGE 3: ACHIEVABLE (OOF-predicted surf-Z as features) ----
print(f"\n=== STAGE 3: ACHIEVABLE gate — BASE + OOF-PREDICTED surf-Z ===", flush=True)
gp3 = tvt_oof(np.column_stack([Fb, Poof]).astype(np.float32)); w3 = blend_report(gp3, "BASE+PRED-surf")

# ---- STAGE 4: partial-oracle precision sweep — how accurate must surfaces be to help? ----
# Interpolate predicted -> true surf-Z. alpha=0 uses the achievable predictor; alpha=1 uses the
# oracle. This locates the surface-accuracy threshold where the nested blend weight turns positive,
# answering the N-B question "would a STRONGER surface predictor (GPU) recover the oracle signal?".
print(f"\n=== STAGE 4: partial-oracle precision sweep (predicted -> true surf-Z) ===", flush=True)
true_filled = np.where(np.isfinite(Sv), Sv, Poof).astype(np.float32)   # use pred where true missing
finite_true = np.isfinite(Sv).all(1)
for alpha in [0.0, 0.25, 0.5, 0.75, 0.9, 1.0]:
    surf_mix = (Poof + alpha * (true_filled - Poof)).astype(np.float32)
    srmse = float(np.sqrt(np.mean((surf_mix[finite_true] - Sv[finite_true])**2)))
    gp = tvt_oof(np.column_stack([Fb, surf_mix]).astype(np.float32))
    blend_report(gp, f"alpha={alpha:.2f} (surf-RMSE={srmse:5.1f} ft)")

# ---- cache arrays for cheap re-analysis ----
cache = os.path.join(os.environ["CLAUDE_JOB_DIR"], "tmp", "v2_arrays.npz")
np.savez_compressed(cache, Fb=Fb, Sv=Sv, Poof=Poof, Y=Y, B=B, O=O, W=W, fold=fold)
print(f"[{time.time()-t0:.0f}s] cached arrays -> {cache}", flush=True)

# ---- verdict ----
print(f"\n=== V2 VERDICT ===", flush=True)
print(f"  oracle-ceiling blendW={w2:+.3f}  achievable blendW={w3:+.3f}  base-only blendW={w0:+.3f}", flush=True)
if w2 <= 0.02:
    print("  ORACLE blend weight <= 0 → even TRUE surfaces do not decorrelate from DWT; the structural-", flush=True)
    print("  label route is CLOSED regardless of predictability. STOP. No GPU (N-A/N-B) warranted.", flush=True)
elif w3 <= 0.02:
    print("  Oracle shows ceiling but ACHIEVABLE (predicted-surface) blend weight <= 0 → predictability", flush=True)
    print("  gap kills the signal. STOP on current features. Consider stronger surface predictor only if", flush=True)
    print("  oracle ceiling is materially large.", flush=True)
else:
    print("  ACHIEVABLE blend weight POSITIVE → V2 PASS candidate; scale validation (spatial-block + full", flush=True)
    print("  rows) before any GPU/submit.", flush=True)
print(f"[{time.time()-t0:.0f}s] done", flush=True)
