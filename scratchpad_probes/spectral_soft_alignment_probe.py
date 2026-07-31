"""Direction E: multi-resolution spectral/trend alignment, top-K posterior (not raw-GR NCC/DTW).
Hypothesis: aligning in a multi-scale trend/band representation (instead of raw GR) is more robust to
cycle-skipping/repeated lithology; test whether the ORACLE best-of-K path ceiling beats DWT (the
raw-GR heatmap oracle only TIED DWT). Non-monotonic allowed via smoothness DP. test-available inputs.
"""
import numpy as np, pandas as pd, glob, sys, time
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
NW=int(sys.argv[1]) if len(sys.argv)>1 else 120; LAM=8.0; K=8
t0=time.time()
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
df=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt']))
g={w:s.set_index('ridx') for w,s in df.groupby('well')}
def msfeat(v):
    v=np.nan_to_num((v-np.nanmean(v))/(np.nanstd(v)+1e-6)); out=[]
    for s in (5,15,40):
        k=np.ones(s)/s; sm=np.convolve(v,k,mode='same'); out.append(sm)
    out.append(np.gradient(out[0]))  # local slope of finest smooth
    return np.stack(out,1)  # (n,4)
def dp_path(EM,s0,lam,cap,extra):
    N,S=EM.shape; INF=1e12; dd=np.arange(-cap,cap+1); trans=lam*(dd.astype(float)**2)
    cost=np.full(S,INF); cost[s0]=0.0; back=np.zeros((N,S),dtype=np.int32); E=EM if extra is None else EM+extra
    for n in range(N):
        best=np.full(S,INF); bestd=np.zeros(S,dtype=np.int32)
        for k,dv in enumerate(dd):
            src=np.roll(cost,dv)
            if dv>0: src[:dv]=INF
            elif dv<0: src[dv:]=INF
            cand=src+trans[k]; u=cand<best; best[u]=cand[u]; bestd[u]=dv
        cost=best+E[n]; back[n]=bestd
    s=int(np.argmin(cost)); p=np.zeros(N,int)
    for n in range(N-1,-1,-1): p[n]=s; s=max(0,min(S-1,s-int(back[n,s])))
    return p
poolT=[];poolD=[];poolOR=[];poolBC=[]
for k,f in enumerate(sorted(glob.glob(f"{DATA}/*__horizontal_well.csv"))[:NW]):
    wid=f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    h=pd.read_csv(f); t=pd.read_csv(f.replace("__horizontal_well","__typewell"))
    MD=h['MD'].values.astype(float); GR=h['GR'].values.astype(float); Ht=h['TVT'].values.astype(float); known=h['TVT_input'].notna().values
    c=np.where(known)[0].max()
    tw=t.dropna(subset=['TVT','GR']).sort_values('TVT'); tv=tw['TVT'].values.astype(float); gt=tw['GR'].values.astype(float)
    if len(tv)<50: continue
    states=np.arange(tv.min(),tv.max(),1.0); S=len(states)
    if S<50: continue
    GRtw=np.interp(states,tv,gt); TWf=msfeat(GRtw)                     # (S,4) typewell multi-scale
    sub=g[wid]; toe=np.array([i for i in np.where(~known)[0] if i>c and i in sub.index and not np.isnan(GR[i])])
    if len(toe)<50: continue
    ds=toe[::4]
    Hf_full=msfeat(GR)                                                 # (len,4) horizontal multi-scale
    Hf=Hf_full[ds]                                                     # (n,4)
    # emission = squared multi-scale feature distance (n x S)
    EM=((Hf[:,None,:]-TWf[None,:,:])**2).sum(2)
    s0=int(np.clip(round(Ht[c]-states[0]),0,S-1)); cap=8
    truth=sub.loc[toe,'yt'].values; dwt=sub.loc[toe,'oof'].values
    paths=[]; pen=np.zeros((len(ds),S))
    for kk in range(K):
        p=dp_path(EM,s0,LAM,cap,pen if kk>0 else None); paths.append(p)
        for n in range(len(ds)):
            lo=max(0,p[n]-12); hi=min(S,p[n]+13); pen[n,lo:hi]+=0.5
    ests=[np.interp(toe,ds,states[p]) for p in paths]
    rm=[np.sqrt(np.mean((e-truth)**2)) for e in ests]
    poolT.append(truth);poolD.append(dwt);poolOR.append(ests[int(np.argmin(rm))]);poolBC.append(ests[0])
    if k%40==0: print("  ..",k,round(time.time()-t0,1),"s",flush=True)
T=np.concatenate(poolT);D=np.concatenate(poolD);OR=np.concatenate(poolOR);BC=np.concatenate(poolBC)
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
print(f"\nE spectral-alignment ({len(poolT)} wells, {round(time.time()-t0,1)}s):")
print(f"   DWT={rmse(D,T):.3f}  best-cost path={rmse(BC,T):.3f}  ORACLE best-of-{K}={rmse(OR,T):.3f}")
print(f"   (raw-GR oracle previously only TIED DWT; does spectral oracle beat it? {'YES' if rmse(OR,T)<rmse(D,T)-0.3 else 'no'})")
