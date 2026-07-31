"""Preflight gate for the 'supervised formation-marker' direction (B2).
Compliance: Geology is train-only, so it may ONLY be used to TRAIN a classifier whose INPUTS are
test-available GR; at test we predict the marker from GR (never read Geology). This gate asks:
(1) can GR-window features even predict the typewell formation label (foundation; near-chance would
mean GR can't identify formation = the cycle-skipping problem in supervised form)?
(2) do the predicted-marker probability features give a POSITIVE-weight honest OOF blend vs DWT?
"""
import numpy as np, pandas as pd, glob, time, lightgbm as lgb
from sklearn.metrics import accuracy_score
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
t0=time.time()
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
dfo=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt'],base=z['base'],cut=z['cut']))
g={w:s for w,s in dfo.groupby('well')}
def grfeat(gr, idx):
    n=len(gr); out=[]
    for i in idx:
        w1=gr[max(0,i-10):i+11]; w2=gr[max(0,i-30):i+31]
        w1=w1[~np.isnan(w1)]; w2=w2[~np.isnan(w2)]
        gi=gr[i] if not np.isnan(gr[i]) else (np.nanmean(w2) if len(w2) else 0)
        out.append([gi, np.mean(w1) if len(w1) else gi, np.std(w1) if len(w1) else 0,
                    np.mean(w2) if len(w2) else gi, np.std(w2) if len(w2) else 0,
                    np.max(w1)-np.min(w1) if len(w1) else 0])
    return np.array(out,np.float32)
# ---- build typewell training set (GR-window -> formation) ----
Xtw=[];ytw=[];gtw=[]
files=sorted(glob.glob(f"{DATA}/*__typewell.csv"))
for k,f in enumerate(files):
    wid=f.split('/')[-1].split('__')[0]
    t=pd.read_csv(f)
    if 'Geology' not in t.columns: continue
    tt=t.dropna(subset=['GR','Geology']).reset_index(drop=True)
    if len(tt)<50: continue
    gr=tt['GR'].values.astype(float); lab=tt['Geology'].values.astype(str)
    idx=np.arange(len(gr))
    Xtw.append(grfeat(gr,idx)); ytw.append(lab); gtw.append(np.array([wid]*len(gr)))
Xtw=np.concatenate(Xtw); ytw=np.concatenate(ytw); gtw=np.concatenate(gtw)
labs,ycode=np.unique(ytw,return_inverse=True)
print(f"typewell rows {len(Xtw)}  #formations {len(labs)}  majority={pd.Series(ytw).value_counts(normalize=True).iloc[0]:.3f}  {round(time.time()-t0,1)}s",flush=True)
# GroupKFold-by-well accuracy
uw=np.unique(gtw); rng=np.random.RandomState(0); perm=rng.permutation(len(uw)); f5={uw[perm[i]]:i%5 for i in range(len(uw))}
fold=np.array([f5[w] for w in gtw]); pred=np.zeros(len(Xtw),int)
for fo in range(5):
    tr=fold!=fo; te=fold==fo
    m=lgb.LGBMClassifier(n_estimators=300,num_leaves=31,learning_rate=0.05,min_child_samples=30,verbose=-1)
    m.fit(Xtw[tr],ycode[tr]); pred[te]=m.predict(Xtw[te])
print(f"(1) GR-window -> formation OOF accuracy = {accuracy_score(ycode,pred):.3f}  (majority {pd.Series(ytw).value_counts(normalize=True).iloc[0]:.3f})",flush=True)
# train final classifier on all typewell rows for horizontal application
clf=lgb.LGBMClassifier(n_estimators=300,num_leaves=31,learning_rate=0.05,min_child_samples=30,verbose=-1).fit(Xtw,ycode)
# ---- apply to horizontal toe rows -> predicted-formation prob features -> residual blend ----
XX=[];YY=[];OO=[];YT=[];BB=[];WW=[]
for f in sorted(glob.glob(f"{DATA}/*__horizontal_well.csv")):
    wid=f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    h=pd.read_csv(f,usecols=['GR']); gr=h['GR'].values.astype(float)
    s=g[wid]; c=int(s.cut.iloc[0]); ri=s.ridx.values; keep=np.arange(0,len(ri),8); ri=ri[keep]
    o=s.oof.values[keep]; y=s.yt.values[keep]; b=s.base.values[keep]; dist=(ri-c).astype(float)
    prob=clf.predict_proba(grfeat(gr,ri))
    XX.append(np.column_stack([prob,dist/1000.0])); YY.append((y-b).astype(np.float32)); OO.append(o);YT.append(y);BB.append(b);WW.append(np.array([wid]*len(ri)))
X=np.concatenate(XX);Yd=np.concatenate(YY);O=np.concatenate(OO);Y=np.concatenate(YT);B=np.concatenate(BB);W=np.concatenate(WW)
uw=np.unique(W); perm=rng.permutation(len(uw)); f5={uw[perm[i]]:i%5 for i in range(len(uw))}
fold=np.array([f5[w] for w in W]); gp=np.zeros(len(X))
for fo in range(5):
    tr=fold!=fo; te=fold==fo
    m=lgb.LGBMRegressor(n_estimators=300,num_leaves=31,learning_rate=0.03,min_child_samples=50,n_jobs=2,verbose=-1)
    m.fit(X[tr],Yd[tr]); gp[te]=B[te]+m.predict(X[te])
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
c=np.corrcoef(gp-Y,O-Y)[0,1]; ws=[]
for fo in range(5):
    tr=fold!=fo; a=(gp-O)[tr]; b=(Y-O)[tr]; ws.append(float(np.sum(a*b)/np.sum(a*a)))
print(f"(2) predicted-marker residual: RMSE={rmse(gp,Y):.3f} DWT={rmse(O,Y):.3f} corr(err,DWT)={c:.3f} blendW={np.mean(ws):+.3f} ({'NEG=no independent info' if np.mean(ws)<0.02 else 'POS=worth pursuing B2'})",flush=True)
