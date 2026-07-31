"""Direction C: latent facies/stratigraphic TOKEN sequence alignment (not raw GR NCC).
Hypothesis: tokenizing GR into facies states (KMeans on multi-feature windows) before alignment is
more robust to repeated lithology / cycle-skipping than raw-GR matching. Test the ORACLE best-of-K
ceiling of a token-based DP alignment vs DWT and vs the raw-GR oracle (which tied DWT).
test-available inputs only.
"""
import numpy as np, pandas as pd, glob, sys, time
from sklearn.cluster import MiniBatchKMeans
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
NW=int(sys.argv[1]) if len(sys.argv)>1 else 120; LAM=6.0; K=8
t0=time.time()
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
df=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt']))
g={w:s.set_index('ridx') for w,s in df.groupby('well')}
def desc(v):
    v=np.nan_to_num((v-np.nanmean(v))/(np.nanstd(v)+1e-6))
    gr=np.gradient(v); rs=pd.Series(v).rolling(11,min_periods=1,center=True).std().values
    sm=np.convolve(v,np.ones(15)/15,mode='same')
    return np.stack([v,gr,rs,sm],1)
# fit tokenizer on a pool of horizontal+typewell descriptors
pool=[]
files=sorted(glob.glob(f"{DATA}/*__horizontal_well.csv"))[:NW]
cache={}
for f in files:
    wid=f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    h=pd.read_csv(f); t=pd.read_csv(f.replace("__horizontal_well","__typewell"))
    GR=h['GR'].values.astype(float); Ht=h['TVT'].values.astype(float); known=h['TVT_input'].notna().values
    tw=t.dropna(subset=['TVT','GR']).sort_values('TVT'); tv=tw['TVT'].values.astype(float); gt=tw['GR'].values.astype(float)
    if len(tv)<50: continue
    cache[wid]=(h,GR,Ht,known,tv,gt)
    dh=desc(GR); pool.append(dh[::7])
POOL=np.concatenate(pool); km=MiniBatchKMeans(12,random_state=0,n_init=3).fit(POOL)
def dp_path(EM,s0,lam,cap,extra):
    N,S=EM.shape; INF=1e12; dd=np.arange(-cap,cap+1); trans=lam*(dd.astype(float)**2)
    cost=np.full(S,INF); cost[s0]=0.0; back=np.zeros((N,S),dtype=np.int32); E=EM if extra is None else EM+extra
    for n in range(N):
        best=np.full(S,INF); bd=np.zeros(S,dtype=np.int32)
        for k,dv in enumerate(dd):
            src=np.roll(cost,dv)
            if dv>0: src[:dv]=INF
            elif dv<0: src[dv:]=INF
            cand=src+trans[k]; u=cand<best; best[u]=cand[u]; bd[u]=dv
        cost=best+E[n]; back[n]=bd
    s=int(np.argmin(cost)); p=np.zeros(N,int)
    for n in range(N-1,-1,-1): p[n]=s; s=max(0,min(S-1,s-int(back[n,s])))
    return p
poolT=[];poolD=[];poolOR=[]
for wid,(h,GR,Ht,known,tv,gt) in cache.items():
    c=np.where(known)[0].max(); states=np.arange(tv.min(),tv.max(),1.0); S=len(states)
    if S<50: continue
    GRtw=np.interp(states,tv,gt); tok_tw=km.predict(desc(GRtw))          # typewell token per state
    tok_h=km.predict(desc(GR))                                          # horizontal token per row
    sub=g[wid]; toe=np.array([i for i in np.where(~known)[0] if i>c and i in sub.index and not np.isnan(GR[i])])
    if len(toe)<50: continue
    ds=toe[::4]
    # emission = token mismatch (0 if same facies token else 1) + centroid-distance soft term
    cen=km.cluster_centers_
    th=tok_h[ds]
    hard=(th[:,None]!=tok_tw[None,:]).astype(float)
    soft=np.linalg.norm(cen[th][:,None,:]-cen[tok_tw][None,:,:],axis=2)/ (np.linalg.norm(cen,axis=1).mean()+1e-6)
    EM=hard+0.3*soft
    s0=int(np.clip(round(Ht[c]-states[0]),0,S-1)); cap=8
    truth=sub.loc[toe,'yt'].values; dwt=sub.loc[toe,'oof'].values
    paths=[]; pen=np.zeros((len(ds),S))
    for kk in range(K):
        p=dp_path(EM,s0,LAM,cap,pen if kk>0 else None); paths.append(p)
        for n in range(len(ds)):
            lo=max(0,p[n]-12); hi=min(S,p[n]+13); pen[n,lo:hi]+=0.6
    ests=[np.interp(toe,ds,states[p]) for p in paths]; rm=[np.sqrt(np.mean((e-truth)**2)) for e in ests]
    poolT.append(truth);poolD.append(dwt);poolOR.append(ests[int(np.argmin(rm))])
T=np.concatenate(poolT);D=np.concatenate(poolD);OR=np.concatenate(poolOR)
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
print(f"\nC facies-token alignment ({len(poolT)} wells, {round(time.time()-t0,1)}s):")
print(f"   DWT={rmse(D,T):.3f}  ORACLE best-of-{K} (token)={rmse(OR,T):.3f}  beats-DWT={'YES' if rmse(OR,T)<rmse(D,T)-0.3 else 'no'}")
