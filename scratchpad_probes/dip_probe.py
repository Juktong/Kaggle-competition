"""Honest toe-TVT prediction from structural surfaces (fully known in toe) vs
naive projection. Native TVT_input mask = hidden split. Leave-well-out via
GroupKFold LightGBM. CPU only."""
import glob, numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
import lightgbm as lgb

SURF=['ANCC','ASTNU','ASTNL','EGFDU','EGFDL','BUDA']
files=sorted(glob.glob("data/rogii/train/*__horizontal_well.csv"))

rows=[]; wells=[]; ytoe=[]; naive=[]; wid=[]
for wi,f in enumerate(files):
    d=pd.read_csv(f)
    ti=pd.to_numeric(d.TVT_input,errors='coerce').to_numpy(float)
    known=np.isfinite(ti)
    if known.all() or not known.any(): continue
    cut=int(np.argmax(~known))
    if cut<20 or len(d)-cut<20: continue
    tvt=pd.to_numeric(d.TVT,errors='coerce').to_numpy(float)
    z=pd.to_numeric(d.Z,errors='coerce').to_numpy(float)
    x=pd.to_numeric(d.X,errors='coerce').to_numpy(float)
    y=pd.to_numeric(d.Y,errors='coerce').to_numpy(float)
    md=pd.to_numeric(d.MD,errors='coerce').to_numpy(float)
    S={c:pd.to_numeric(d[c],errors='coerce').to_numpy(float) for c in SURF}
    # per-well heel anchor: r at cut (last known)
    r=tvt+z
    r_anchor=r[cut-1]
    for i in range(cut,len(d)):
        if not np.isfinite(tvt[i]): continue
        feat=dict(z=z[i],x=x[i],y=y[i],md=md[i],
                  dmd=md[i]-md[cut-1], zc=z[i]-z[cut-1],
                  r_anchor=r_anchor)
        for c in SURF:
            feat[c]=S[c][i]
            feat[c+'_mz']=S[c][i]-z[i]   # surface relative to wellbore
        rows.append(feat); ytoe.append(tvt[i]); wid.append(wi)
        naive.append(-z[i]+r_anchor)     # naive: carry last residual

X=pd.DataFrame(rows); y=np.array(ytoe); g=np.array(wid); naive=np.array(naive)
print("toe samples:",len(y),"wells:",len(set(g)),"features:",list(X.columns))
rmse=lambda a,b:float(np.sqrt(np.mean((a-b)**2)))
print(f"\nNAIVE projection (carry last r): RMSE={rmse(y,naive):.3f}")

oof=np.zeros(len(y))
gkf=GroupKFold(n_splits=5)
for tr,va in gkf.split(X,y,groups=g):
    m=lgb.LGBMRegressor(n_estimators=400,learning_rate=0.05,num_leaves=63,
                        min_child_samples=50,subsample=0.8,colsample_bytree=0.8,
                        n_jobs=4,verbose=-1)
    m.fit(X.iloc[tr],y[tr])
    oof[va]=m.predict(X.iloc[va])
print(f"LGBM surfaces (GroupKFold LOWO): RMSE={rmse(y,oof):.3f}")
# blend
for w in (0.3,0.5,0.7):
    bl=w*oof+(1-w)*naive
    print(f"  blend {w:.1f}*lgbm+{1-w:.1f}*naive: RMSE={rmse(y,bl):.3f}")
