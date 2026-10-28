"""Direction B: self-supervised / deterministic multi-scale GR representation, then residual model.
Hypothesis: a richer learned/random representation of GR shape (ROCKET random-conv PPV + multi-scale
bands) may capture GR structure DWT's hand-crafted 195 features miss, giving a decorrelated or
stronger residual signal. Uses only test-available GR/typewell/trajectory. NOT raw NCC/matcher.
"""
import numpy as np, pandas as pd, glob, lightgbm as lgb
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
d=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt'],base=z['base'],cut=z['cut']))
g={w:s for w,s in d.groupby('well')}
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
rs=np.random.RandomState(42)
NK=48
kernels=[]
for _ in range(NK):
    L=rs.choice([7,9,11]); w=rs.randn(L); w-=w.mean(); dil=rs.choice([1,2,4]); bias=rs.uniform(-1,1)
    kernels.append((w,dil,bias))
def ppv_maxpool(gr, win=30):
    z=(gr-np.nanmean(gr))/(np.nanstd(gr)+1e-6); z=np.nan_to_num(z)
    feats=[]
    for w,dil,bias in kernels:
        k=np.repeat(w,1); # dilation via strided kernel
        kk=np.zeros((len(w)-1)*dil+1); kk[::dil]=w
        c=np.convolve(z,kk,mode='same')
        pos=(c>bias).astype(np.float32)
        cs=np.cumsum(np.insert(pos,0,0)); half=win
        lo=np.maximum(0,np.arange(len(pos))-half); hi=np.minimum(len(pos),np.arange(len(pos))+half+1)
        ppv=(cs[hi]-cs[lo])/(hi-lo)
        feats.append(ppv)
    return np.stack(feats,1)  # (n, NK)
XX=[];YY=[];OO=[];YT=[];BB=[];WW=[]
for k,f in enumerate(sorted(glob.glob(f"{DATA}/*__horizontal_well.csv"))):
    wid=f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    h=pd.read_csv(f, usecols=['MD','GR']); GR=h['GR'].values.astype(float); MD=h['MD'].values.astype(float)
    P=ppv_maxpool(GR)
    s=g[wid]; c=int(s.cut.iloc[0]); ri=s.ridx.values; keep=np.arange(0,len(ri),4); ri=ri[keep]
    o=s.oof.values[keep]; y=s.yt.values[keep]; b=s.base.values[keep]; dist=(ri-c).astype(float)
    feat=np.column_stack([P[ri], dist/1000.0, dist**0.5])
    XX.append(feat); YY.append((y-b).astype(np.float32)); OO.append(o);YT.append(y);BB.append(b);WW.append(np.array([wid]*len(ri)))
    if k%150==0: print("  rocket",k,flush=True)
X=np.concatenate(XX);Yd=np.concatenate(YY);O=np.concatenate(OO);Y=np.concatenate(YT);B=np.concatenate(BB);W=np.concatenate(WW)
print(f"rows={len(X)} feats={X.shape[1]}",flush=True)
uw=np.unique(W); rng=np.random.RandomState(0); perm=rng.permutation(len(uw)); f5={uw[perm[i]]:i%5 for i in range(len(uw))}
fold=np.array([f5[w] for w in W])
gp=np.zeros(len(X))
for fo in range(5):
    tr=fold!=fo; te=fold==fo
    m=lgb.LGBMRegressor(n_estimators=400,num_leaves=63,learning_rate=0.03,min_child_samples=50,subsample=0.8,colsample_bytree=0.8,n_jobs=2,verbose=-1)
    m.fit(X[tr],Yd[tr]); gp[te]=B[te]+m.predict(X[te])
c=np.corrcoef(gp-Y,O-Y)[0,1]; ws=[]; bl=np.zeros(len(X))
for fo in range(5):
    tr=fold!=fo; te=fold==fo; a=(gp-O)[tr]; b=(Y-O)[tr]; w=float(np.sum(a*b)/np.sum(a*a)); ws.append(w); wc=max(-0.1,min(0.7,w)); bl[te]=((1-wc)*O+wc*gp)[te]
print(f"\nB (ROCKET-repr residual GBM): RMSE={rmse(gp,Y):.4f}  DWT={rmse(O,Y):.4f}  corr(err,DWT)={c:.3f}")
print(f"   mean blend weight={np.mean(ws):+.3f} ({'NEGATIVE=drift-amplification artifact' if np.mean(ws)<0 else 'positive'})  nested-blend={rmse(bl,Y):.4f}")
