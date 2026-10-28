"""Diagnose the bootstrap left tail at K=96 and test a GUARDED ranker.

The gate fails only on stability: bootstrap 5th pct is -0.0158 while the mean gain is +0.1558.
If the left tail comes from a small identifiable set of wells, a conservative test-available guard
(apply the ranker only where it is safe, keep the PF weighted mean elsewhere) may keep most of the gain
while removing the tail -- the same pattern that made the structural field submittable.
Guard candidates must be TEST-AVAILABLE and are selected NESTED by well.
"""
import os, glob, numpy as np, pandas as pd
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
FEAT=f'{SH}/topk96_feat.csv'; PATHDIR=f'{SH}/topk96_paths'; FOLDS=5
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
def gated(w): return nnb.get(w,0)>=4 and np.isfinite(closest.get(w,np.nan)) and closest.get(w,1e9)<1000
def well_sse(w,pf):
    S=store[w]; base=0.5*S['dwt'].astype(np.float64)+0.5*pf.astype(np.float64); out=base
    if gated(w) and np.isfinite(S['struct']).all(): out=0.85*base+0.15*S['struct'].astype(np.float64)
    e=out-S['truth'].astype(np.float64); return float(np.sum(e*e)),len(e)
def pooled(d):
    s=sum(a for a,_ in d.values()); n=sum(b for _,b in d.values()); return float(np.sqrt(s/n))
import lightgbm as lgb
df['tgt']=df.groupby('well')['path_rmse'].transform(lambda s:(s-s.mean())/(s.std()+1e-9))
rng=np.random.RandomState(0); fold={w:i%FOLDS for i,w in enumerate(rng.permutation(np.array(wells)))}
df['fold']=df.well.map(fold)
sel={}
for f in range(FOLDS):
    tr=df[(df.fold!=f)&df.well.isin(wells)]; te=df[(df.fold==f)&df.well.isin(wells)]
    m=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.05,num_leaves=31,min_child_samples=50,
                        verbose=-1).fit(tr[FEATURES].fillna(0).values,tr['tgt'].values)
    te=te.assign(score=m.predict(te[FEATURES].fillna(0).values))
    for w,g in te.groupby('well'): sel[w]=int(g.loc[g.score.idxmin(),'seed'])
LAM=0.75
sse_mean={w:well_sse(w,store[w]['mean']) for w in wells}
sse_rank={w:well_sse(w,(1-LAM)*store[w]['mean']+LAM*store[w]['paths'][sel[w]]) for w in wells}
base_r=pooled(sse_mean); rank_r=pooled(sse_rank)
print(f"wells={len(wells)}  deployed={base_r:.4f}  ranker(lam=.75)={rank_r:.4f}  gain {base_r-rank_r:+.4f}\n")
# per-well RMSE delta
d={w: np.sqrt(sse_mean[w][0]/sse_mean[w][1]) - np.sqrt(sse_rank[w][0]/sse_rank[w][1]) for w in wells}
dv=np.array([d[w] for w in wells])
print(f"per-well gain: mean={dv.mean():+.3f} median={np.median(dv):+.3f}")
print(f"  wells helped {100*np.mean(dv>0):.1f}%   hurt {100*np.mean(dv<0):.1f}%")
print(f"  worst 5 wells: {np.round(np.sort(dv)[:5],2)}   best 5: {np.round(np.sort(dv)[-5:],2)}")
print(f"  total SSE change from HURT wells only: {sum(sse_rank[w][0]-sse_mean[w][0] for w in wells if d[w]<0):.3e}")
print(f"  total SSE change from HELPED wells only: {sum(sse_rank[w][0]-sse_mean[w][0] for w in wells if d[w]>0):.3e}\n")
# test-available guard signals, aggregated per well
agg=df.groupby('well').agg(likdisp=('loglik','std'), wmax=('w','max'), wstd=('w','std'),
                           neval=('n_eval','first'), hd=('heel_drift','first'),
                           dmean=('d_mean','mean'), dmean_min=('d_mean','min'),
                           smooth=('smooth','mean'))
agg['sel_w']=[df[(df.well==w)&(df.seed==sel[w])]['w'].values[0] if len(df[(df.well==w)&(df.seed==sel[w])]) else np.nan for w in agg.index]
print("corr(per-well gain, guard signal):")
for c in ['likdisp','wmax','wstd','neval','hd','dmean','dmean_min','smooth','sel_w']:
    v=agg.loc[wells,c].values.astype(float)
    ok=np.isfinite(v)
    if ok.sum()>50: print(f"   {c:10s} {np.corrcoef(v[ok],dv[ok])[0,1]:+.3f}")
np.save(f'{SH}/k96_wellgain.npy', dv)
agg.to_csv(f'{SH}/k96_guard_agg.csv')
print("\nsaved per-well gains + guard aggregates")
