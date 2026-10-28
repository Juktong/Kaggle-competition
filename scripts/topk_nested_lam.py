"""K=48 final verdict with NESTED lambda: lambda is chosen on training-half wells and applied to the
held-out half, so the shrinkage strength is never selected using the rows it is scored on.

This applies the same standard used to reject direction 2's hgb lam=0.25 result ("a lambda sweep is
not a validation"). Also reports the seeds-only effect (24 -> 48 seed PF weighted mean, no ranker).
"""
import os, glob, numpy as np, pandas as pd
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
FEAT=os.environ.get('FEAT',f'{SH}/topk48_feat.csv'); PATHDIR=os.environ.get('PATHDIR',f'{SH}/topk48_paths'); FOLDS=5; NBOOT=400
FEATURES=['loglik','w','lik_rank','smooth','jumps','total_move','dir_changes',
          'seam','out_of_range','d_dwt','d_struct','d_mean','n_eval','heel_drift']
df=pd.read_csv(FEAT); df=df[df.seed>=0].copy()
store={}
for f in glob.glob(os.path.join(PATHDIR,'*.npz')):
    w=os.path.basename(f)[:-4]; z=np.load(f)
    store[w]=dict(paths=z['paths'].astype(np.float32),mean=z['mean'].astype(np.float32),
                  dwt=z['dwt'].astype(np.float32),struct=z['struct'].astype(np.float32),
                  truth=z['truth'].astype(np.float32))
wells=sorted(set(df.well.astype(str))&set(store))
stz=np.load(f'{SH}/struct_oof.npz',allow_pickle=True)
nnb=dict(zip(stz['meta_well'].astype(str),stz['meta_nnb'].astype(int)))
closest=dict(zip(stz['meta_well'].astype(str),stz['meta_closest'].astype(float)))
W_STRUCT=0.15
def gated(w): return nnb.get(w,0)>=4 and np.isfinite(closest.get(w,np.nan)) and closest.get(w,1e9)<1000
def well_sse(w,pf):
    S=store[w]; base=0.5*S['dwt'].astype(np.float64)+0.5*pf.astype(np.float64); out=base
    if gated(w) and np.isfinite(S['struct']).all():
        out=(1-W_STRUCT)*base+W_STRUCT*S['struct'].astype(np.float64)
    e=out-S['truth'].astype(np.float64); return float(np.sum(e*e)),len(e)
def pooled(d):
    s=sum(a for a,_ in d.values()); n=sum(b for _,b in d.values()); return float(np.sqrt(s/n))
sse_mean={w:well_sse(w,store[w]['mean']) for w in wells}
base_r=pooled(sse_mean)
print(f"wells={len(wells)}")
print(f"  deployed pipeline w/ this K's PF mean = {base_r:.4f}   (submitted 54844628 used a 24-seed PF: 8.8626)")
print(f"  -> seeds-only effect (24 -> this K, NO ranker) = {8.8626-base_r:+.4f}\n",flush=True)

import lightgbm as lgb
df['tgt']=df.groupby('well')['path_rmse'].transform(lambda s:(s-s.mean())/(s.std()+1e-9))
rng=np.random.RandomState(0)
fold={w:i%FOLDS for i,w in enumerate(rng.permutation(np.array(wells)))}
df['fold']=df.well.map(fold)
maxlik={}
for w in wells:
    g=df[df.well==w]; maxlik[w]=int(g.loc[g.loglik.idxmax(),'seed'])
# nested ranker selection (unchanged: selection is already nested by well)
sel={}
for f in range(FOLDS):
    tr=df[(df.fold!=f)&df.well.isin(wells)]; te=df[(df.fold==f)&df.well.isin(wells)]
    if len(tr)<50 or len(te)==0: continue
    m=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.05,num_leaves=31,
                        min_child_samples=50,verbose=-1).fit(tr[FEATURES].fillna(0).values,tr['tgt'].values)
    te=te.assign(score=m.predict(te[FEATURES].fillna(0).values))
    for w,g in te.groupby('well'): sel[w]=int(g.loc[g.score.idxmin(),'seed'])
for w in wells: sel.setdefault(w,maxlik[w])
LAMS=[0.0,0.25,0.5,0.75,1.0]
sse_by_lam={lam:{w:well_sse(w,(1-lam)*store[w]['mean']+lam*store[w]['paths'][sel[w]]) for w in wells} for lam in LAMS}
for lam in LAMS:
    print(f"  lam={lam:.2f}: {pooled(sse_by_lam[lam]):.4f}  gain {base_r-pooled(sse_by_lam[lam]):+.4f}",flush=True)

print("\n=== NESTED lambda (chosen on training-half wells, applied to held-out half; 5 seeds) ===",flush=True)
wl=np.array(wells); outs=[]; picks=[]
for seed in range(5):
    rg=np.random.RandomState(seed); sh=wl.copy(); rg.shuffle(sh)
    half=set(sh[:len(sh)//2])
    tot=n=0.0; chosen={}
    for tr_set in [half,set(wl)-half]:
        te_set=set(wl)-tr_set
        bl,bv=0.0,np.inf
        for lam in LAMS:
            s=sum(sse_by_lam[lam][w][0] for w in tr_set); m=sum(sse_by_lam[lam][w][1] for w in tr_set)
            if s/m<bv: bv,bl=s/m,lam
        picks.append(bl)
        tot+=sum(sse_by_lam[bl][w][0] for w in te_set); n+=sum(sse_by_lam[bl][w][1] for w in te_set)
    outs.append(np.sqrt(tot/n))
nested=float(np.mean(outs))
print(f"  lambda picks: {picks}")
print(f"  NESTED-lambda result = {nested:.4f}   gain vs deployed(this K) {base_r-nested:+.4f}")
print(f"                                        gain vs SUBMITTED 8.8626 {8.8626-nested:+.4f}",flush=True)

# bootstrap the nested-lambda gain (rebuild nested preds per bootstrap sample is expensive; use the
# per-well sse of the most-picked lambda, which is what a deployment would actually ship)
from collections import Counter
ship_lam=Counter(picks).most_common(1)[0][0]
print(f"\n  deployable lambda (most-picked) = {ship_lam}")
bsse=sse_by_lam[ship_lam]
rb=np.random.RandomState(7); gains=[]
for _ in range(NBOOT):
    samp=wl[rb.randint(0,len(wl),len(wl))]
    s1=sum(sse_mean[w][0] for w in samp); n1=sum(sse_mean[w][1] for w in samp)
    s2=sum(bsse[w][0] for w in samp); n2=sum(bsse[w][1] for w in samp)
    gains.append(np.sqrt(s1/n1)-np.sqrt(s2/n2))
g=np.array(gains)
print(f"  bootstrap({NBOOT}) gain vs this-K deployed: mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} 1st={np.percentile(g,1):+.4f} frac>0={100*np.mean(g>0):.0f}%")
meets=(base_r-nested)>=0.10 and np.percentile(g,5)>0
print(f"\n  GATE (+0.10 AND stably positive bootstrap): {'MEETS' if meets else 'DOES NOT MEET'}")
