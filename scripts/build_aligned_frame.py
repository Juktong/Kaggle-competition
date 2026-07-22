"""Build a single aligned per-row prediction frame so all candidates and the 3-well gate share ONE row
order (aligned on well, ridx). Prevents alignment bugs across candidate families.

Columns produced (all OOF, honest):
  truth, well, ridx, nnb, closest_all, closest_surv
  dwt, pf, base(=0.5dwt+0.5pf)
  s_54844628  : deployed isotropic struct, gate closest_all<1000, W=0.15  (public 7.891)
  s_54878409  : aniso A50, gate closest_surv<1000, W=0.25                 (public 7.953)
  s_a20_w25   : aniso A20, gate closest_surv<1000, W=0.25
  base_k96    : 0.5dwt+0.5*PF_K96 mean  (seeds-only)
  s_k96_aniso : base_k96 with aniso A50 W=0.25 gated
  topk96_l75  : ranker-selected K96 path, shrink lambda=0.75, then aniso struct  (the top-K candidate)
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
dz=np.load(f'{SH}/decomp_features.npz',allow_pickle=True)
dw=dz['well'].astype(str); dwt=dz['dwt'].astype(np.float64); pf=dz['pf'].astype(np.float64)
blend=dz['blend'].astype(np.float64); truth=dz['truth'].astype(np.float64)
sv=np.load(f'{SH}/struct_aniso_surv.npz',allow_pickle=True)
sw=sv['well'].astype(str); sr=sv['ridx'].astype(int)
s1=sv['struct_a1'].astype(np.float64); s50=sv['struct_a50'].astype(np.float64)
sv2=np.load(f'{SH}/struct_aniso_surv2.npz',allow_pickle=True)
s20=sv2['struct_a20'].astype(np.float64)
nnb=dict(zip(sv['meta_well'].astype(str),sv['meta_nnb'].astype(int)))
call=dict(zip(sv['meta_well'].astype(str),sv['meta_closest'].astype(float)))
csurv=dict(zip(sv['meta_well'].astype(str),sv['meta_closest_surv'].astype(float)))

di=defaultdict(list); sidx=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(sw): sidx[w].append(i)

# K96 paths: per well, need mean and ranker-selected path. Reuse the nested-lambda ranker selection.
feat=pd.read_csv(f'{SH}/topk96_feat.csv'); feat=feat[feat.seed>=0].copy()
FEATURES=['loglik','w','lik_rank','smooth','jumps','total_move','dir_changes','seam','out_of_range','d_dwt','d_struct','d_mean','n_eval','heel_drift']
store={}
for f in glob.glob(f'{SH}/topk96_paths/*.npz'):
    w=os.path.basename(f)[:-4]; z=np.load(f)
    store[w]=dict(ridx=z['ridx'].astype(int), paths=z['paths'].astype(np.float64),
                  mean=z['mean'].astype(np.float64))
# nested-by-well ranker selection (5-fold)
import lightgbm as lgb
wells_k=sorted(set(feat.well.astype(str))&set(store))
feat['tgt']=feat.groupby('well')['path_rmse'].transform(lambda s:(s-s.mean())/(s.std()+1e-9))
rng=np.random.RandomState(0); fold={w:i%5 for i,w in enumerate(rng.permutation(np.array(wells_k)))}
feat['fold']=feat.well.map(fold)
sel={}
for fo in range(5):
    tr=feat[(feat.fold!=fo)&feat.well.isin(wells_k)]; te=feat[(feat.fold==fo)&feat.well.isin(wells_k)]
    if len(tr)<50 or len(te)==0: continue
    m=lgb.LGBMRegressor(n_estimators=300,learning_rate=0.05,num_leaves=31,min_child_samples=50,verbose=-1).fit(tr[FEATURES].fillna(0).values,tr['tgt'].values)
    te=te.assign(score=m.predict(te[FEATURES].fillna(0).values))
    for w,g in te.groupby('well'): sel[w]=int(g.loc[g.score.idxmin(),'seed'])
maxlik={}
for w in wells_k:
    g=feat[feat.well==w]; maxlik[w]=int(g.loc[g.loglik.idxmax(),'seed'])
for w in wells_k: sel.setdefault(w,maxlik[w])

W,RIDX,TR,DWT,PF,S1,S50,S20,PFK96,TOPK=[],[],[],[],[],[],[],[],[],[]
NNB,CALL,CSURV=[],[],[]
common=sorted(set(dw)&set(sw))
for w in common:
    a=np.array(di[w]); b=np.array(sidx[w])
    if len(a)!=len(b): continue
    ridx_s=sr[b]
    # K96 aligned by ridx
    m96=np.full(len(a),np.nan); tk=np.full(len(a),np.nan)
    if w in store:
        st=store[w]; pos={int(r):j for j,r in enumerate(st['ridx'])}
        selpath=st['paths'][sel[w]] if w in sel else st['mean']
        for k,r in enumerate(ridx_s):
            j=pos.get(int(r))
            if j is not None:
                m96[k]=st['mean'][j]
                tk[k]=0.25*st['mean'][j]+0.75*selpath[j]   # lambda=0.75 shrink
    W.append(np.full(len(a),w)); RIDX.append(ridx_s); TR.append(truth[a])
    DWT.append(dwt[a]); PF.append(pf[a]); S1.append(s1[b]); S50.append(s50[b]); S20.append(s20[b])
    PFK96.append(m96); TOPK.append(tk)
    NNB.append(np.full(len(a),nnb.get(w,0),float)); CALL.append(np.full(len(a),call.get(w,np.nan),float))
    CSURV.append(np.full(len(a),csurv.get(w,np.nan),float))
def cat(x): return np.concatenate(x)
well=cat(W); ridx=cat(RIDX); tr=cat(TR); dwtv=cat(DWT); pfv=cat(PF)
s1v=cat(S1); s50v=cat(S50); s20v=cat(S20); pfk96=cat(PFK96); topk=cat(TOPK)
nnbv=cat(NNB); callv=cat(CALL); csurvv=cat(CSURV)
base=0.5*dwtv+0.5*pfv
g_old=(nnbv>=4)&(callv<1000)&np.isfinite(callv)
g_new=(nnbv>=4)&(csurvv<1000)&np.isfinite(csurvv)
def gated(bs,st,W_,g): p=bs.copy(); p[g]=(1-W_)*bs[g]+W_*st[g]; return p
s_dep=gated(base,s1v,0.15,g_old)                 # 54844628
s_ani=gated(base,s50v,0.25,g_new)                # 54878409
s_a20=gated(base,s20v,0.25,g_new)
# K96 fallbacks where missing -> base
base_k96=base.copy(); ok96=np.isfinite(pfk96); base_k96[ok96]=0.5*dwtv[ok96]+0.5*pfk96[ok96]
s_k96_ani=gated(base_k96,s50v,0.25,g_new)
topk_full=base.copy(); okt=np.isfinite(topk); 
tbase=base.copy(); tbase[okt]=0.5*dwtv[okt]+0.5*topk[okt]
s_topk=gated(tbase,s50v,0.25,g_new)
rmse=lambda p:float(np.sqrt(np.mean((p-tr)**2)))
out=dict(well=well.astype(str),ridx=ridx.astype(np.int32),truth=tr.astype(np.float32),
         nnb=nnbv.astype(np.float32),closest_all=callv.astype(np.float32),closest_surv=csurvv.astype(np.float32),
         dwt=dwtv.astype(np.float32),pf=pfv.astype(np.float32),base=base.astype(np.float32),
         s_54844628=s_dep.astype(np.float32),s_54878409=s_ani.astype(np.float32),
         s_a20_w25=s_a20.astype(np.float32),base_k96=base_k96.astype(np.float32),
         s_k96_aniso=s_k96_ani.astype(np.float32),topk96_l75=s_topk.astype(np.float32))
np.savez_compressed(f'{SH}/aligned_preds.npz',**out)
print(f"rows={len(tr)} wells={len(set(well))}")
for nm in ['dwt','pf','base','s_54844628','s_54878409','s_a20_w25','base_k96','s_k96_aniso','topk96_l75']:
    print(f"  {nm:14s} OOF={rmse(out[nm].astype(np.float64)):.4f}")
print(f"K96 coverage: {100*ok96.mean():.1f}%  topk coverage: {100*okt.mean():.1f}%")
print("saved aligned_preds.npz")
