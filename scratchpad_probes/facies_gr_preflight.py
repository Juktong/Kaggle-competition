"""Direction F local preflight, FACIES branch (the part the SSL preflight does not test).
Train a GR->facies(formation) classifier on ROGII TRAIN typewell (GR, Geology) pairs (proxy for an
external-facies-pretrained encoder; at real test the classifier is applied to test-available
horizontal GR, Geology labels are never read at test). Use predicted-facies probabilities +
facies-transition features as a residual model, honest well-OOF, check blend weight SIGN vs DWT.
Pass = stable POSITIVE-weight honest OOF improvement (not the negative-weight lambda artifact).
"""
import numpy as np, pandas as pd, glob, time, lightgbm as lgb
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
t0=time.time()
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
d=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt'],base=z['base'],cut=z['cut']))
g={w:s for w,s in d.groupby('well')}
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
def grfeat(gr):
    gr=np.asarray(gr,float); z=(gr-np.nanmean(gr))/(np.nanstd(gr)+1e-6)
    sm=np.convolve(np.nan_to_num(z),np.ones(9)/9,mode='same'); gd=np.gradient(sm)
    rs=pd.Series(z).rolling(11,min_periods=1,center=True).std().values
    return np.column_stack([np.nan_to_num(z),sm,gd,np.nan_to_num(rs)])
# ---- build facies training set from train typewells (GR, Geology) ----
Xf=[];yf=[]
for f in sorted(glob.glob(f"{DATA}/*__typewell.csv")):
    t=pd.read_csv(f)
    if 'Geology' not in t.columns: continue
    m=t['Geology'].notna() & t['GR'].notna()
    if m.sum()<30: continue
    ff=grfeat(t['GR'].values)[m.values]; Xf.append(ff); yf.append(t['Geology'].values[m.values])
Xf=np.concatenate(Xf); yf=np.concatenate(yf)
classes=sorted(pd.unique(yf)); c2i={c:i for i,c in enumerate(classes)}; yi=np.array([c2i[c] for c in yf])
print(f"facies train rows={len(Xf)} classes={len(classes)} ({classes[:6]}...) {round(time.time()-t0,1)}s",flush=True)
clf=lgb.LGBMClassifier(n_estimators=300,num_leaves=31,learning_rate=0.05,min_child_samples=50,n_jobs=2,verbose=-1)
clf.fit(Xf,yi)
K=len(classes)
# ---- apply to horizontal toe rows -> predicted facies probs + transition features ----
XX=[];YY=[];OO=[];YT=[];BB=[];WW=[]
for f in sorted(glob.glob(f"{DATA}/*__horizontal_well.csv")):
    wid=f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    h=pd.read_csv(f,usecols=['GR']); GR=h['GR'].values.astype(float)
    prob_all=clf.predict_proba(grfeat(GR))                      # (n,K)
    s=g[wid]; c=int(s.cut.iloc[0]); ri=s.ridx.values; keep=np.arange(0,len(ri),4); ri=ri[keep]
    o=s.oof.values[keep]; y=s.yt.values[keep]; b=s.base.values[keep]; dist=(ri-c).astype(float)
    pr=prob_all[ri]                                             # facies probs per toe row
    top=pr.argmax(1)
    # transition feature: cumulative facies changes from the cut, entropy
    ent=-(pr*np.log(pr+1e-9)).sum(1)
    XX.append(np.column_stack([pr, ent, dist/1000.0, dist**0.5])); YY.append((y-b).astype(np.float32))
    OO.append(o);YT.append(y);BB.append(b);WW.append(np.array([wid]*len(ri)))
X=np.concatenate(XX);Yd=np.concatenate(YY);O=np.concatenate(OO);Y=np.concatenate(YT);B=np.concatenate(BB);W=np.concatenate(WW)
print(f"facies-feature rows {X.shape} {round(time.time()-t0,1)}s",flush=True)
uw=np.unique(W); rng=np.random.RandomState(0); perm=rng.permutation(len(uw)); f5={uw[perm[i]]:i%5 for i in range(len(uw))}
fold=np.array([f5[w] for w in W]); gp=np.zeros(len(X))
for fo in range(5):
    tr=fold!=fo; te=fold==fo
    m=lgb.LGBMRegressor(n_estimators=400,num_leaves=63,learning_rate=0.03,min_child_samples=50,subsample=0.8,colsample_bytree=0.8,n_jobs=2,verbose=-1)
    m.fit(X[tr],Yd[tr]); gp[te]=B[te]+m.predict(X[te])
c=np.corrcoef(gp-Y,O-Y)[0,1]; ws=[]; bl=np.zeros(len(X))
for fo in range(5):
    tr=fold!=fo; te=fold==fo; a=(gp-O)[tr]; b=(Y-O)[tr]; w=float(np.sum(a*b)/np.sum(a*a)); ws.append(w); wc=max(-0.1,min(0.7,w)); bl[te]=((1-wc)*O+wc*gp)[te]
print(f"\nF PREFLIGHT (FACIES branch, predicted-facies features):")
print(f"   DWT={rmse(O,Y):.4f}  facies-residual={rmse(gp,Y):.4f}  corr(err,DWT)={c:.3f}")
print(f"   mean nested blend weight={np.mean(ws):+.3f} ({'NEGATIVE = lambda artifact -> facies-branch external GPU NOT warranted' if np.mean(ws)<0.02 else 'POSITIVE = genuine -> facies-branch worth external+GPU'})  nested-blend={rmse(bl,Y):.4f}")
