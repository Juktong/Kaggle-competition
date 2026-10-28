"""Direction A: prediction-domain validation + robust selection.
Hypothesis: random GroupKFold overstates generalization; spatial/domain-blocked folds are a better
private proxy. Test whether (a) DWT error is worse on worst-domain folds, (b) any auxiliary residual
model / loss-diversity improves the WORST domain (not just pooled), (c) blend weights stay >=0
(not the disguised drift-rescaling), (d) adversarial validation reveals domain-drift features.
Inputs: all test-time available (GR/typewell/trajectory-derived). No train-only fields.
"""
import numpy as np, pandas as pd, glob, lightgbm as lgb
from sklearn.cluster import KMeans
from sklearn.metrics import roc_auc_score
TMP="/home/ubuntu/.claude/jobs/45a5eb5b/tmp"
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
d=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt'],base=z['base']))
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
F=pd.read_csv(f"{TMP}/well_feats.csv")
xy=[]
for f in sorted(glob.glob(f"{DATA}/*__horizontal_well.csv")):
    wid=f.split('/')[-1].split('__')[0]; h=pd.read_csv(f, usecols=['X','Y'])
    xy.append((wid,h['X'].mean(),h['Y'].mean()))
XY=pd.DataFrame(xy,columns=['wid','cx','cy']).merge(F,on='wid',how='inner')
XY['sblock']=KMeans(6,n_init=5,random_state=0).fit_predict((XY[['cx','cy']]-XY[['cx','cy']].mean())/XY[['cx','cy']].std())
rng=np.random.RandomState(0); XY['rfold']=rng.permutation(len(XY))%6
w2s={XY.wid.iloc[i]:XY.sblock.iloc[i] for i in range(len(XY))}
w2r={XY.wid.iloc[i]:XY.rfold.iloc[i] for i in range(len(XY))}
d['sblock']=d.well.map(w2s); d['rfold']=d.well.map(w2r)

print("== A1: DWT pooled RMSE by SPATIAL block vs RANDOM fold (domain sensitivity) ==")
sb=d.groupby('sblock').apply(lambda s:rmse(s.oof,s.yt)); rf=d.groupby('rfold').apply(lambda s:rmse(s.oof,s.yt))
print(f"   spatial blocks: {[round(x,2) for x in sb.values]}  worst={sb.max():.2f} spread={sb.max()-sb.min():.2f}")
print(f"   random folds  : {[round(x,2) for x in rf.values]}  worst={rf.max():.2f} spread={rf.max()-rf.min():.2f}")

print("\n== A2: adversarial validation — can test-available feats separate spatial blocks? ==")
FEATK=[c for c in F.columns if c not in ('wid','offset','aff0','aff1')]
aucs=[]
for b in range(6):
    y=(XY.sblock==b).astype(int).values
    p=np.zeros(len(XY)); rf6=rng.permutation(len(XY))%5
    for fo in range(5):
        tr=rf6!=fo; te=rf6==fo
        m=lgb.LGBMClassifier(n_estimators=150,num_leaves=15,learning_rate=0.05,min_child_samples=20,verbose=-1)
        m.fit(XY[FEATK][tr],y[tr]); p[te]=m.predict_proba(XY[FEATK][te])[:,1]
    aucs.append(roc_auc_score(y,p))
mf=lgb.LGBMClassifier(n_estimators=200,num_leaves=15,verbose=-1).fit(XY[FEATK],XY.sblock)
imp=sorted(zip(FEATK,mf.feature_importances_),key=lambda x:-x[1])[:6]
print(f"   mean block-vs-rest AUC = {np.mean(aucs):.3f} (0.5=no covariate shift). top drift feats: {[k for k,_ in imp]}")

print("\n== A3: loss-diversity + GroupDRO-lite under SPATIAL folds; blend-weight sign per block ==")
L=np.load(f"{TMP}/lgbm_feats.npz",allow_pickle=True); X=L['X'];Yd=L['Yd'];O=L['O'];Y=L['Y'];B=L['B'];W=L['W']
sfold=np.array([w2s.get(w,0) for w in W])
def eval_aux(objective, dro=False):
    gp=np.zeros(len(X))
    for fo in range(6):
        tr=sfold!=fo; te=sfold==fo
        sw=None
        if dro:
            aw=1.0+2.0*(np.abs(Yd[tr])>np.quantile(np.abs(Yd[tr]),0.7)); sw=aw
        par={'objective':objective}
        if objective=='huber': par['alpha']=0.9
        m=lgb.LGBMRegressor(n_estimators=400,num_leaves=63,learning_rate=0.03,min_child_samples=50,
                            subsample=0.8,colsample_bytree=0.8,n_jobs=2,verbose=-1,**par)
        m.fit(X[tr],Yd[tr],sample_weight=sw); gp[te]=B[te]+m.predict(X[te])
    ws=[]; bl=np.zeros(len(X))
    for fo in range(6):
        tr=sfold!=fo; te=sfold==fo; a=(gp-O)[tr]; b=(Y-O)[tr]
        w=float(np.sum(a*b)/np.sum(a*a)); ws.append(w); wc=max(-0.1,min(0.7,w)); bl[te]=((1-wc)*O+wc*gp)[te]
    wbD=max(rmse(O[sfold==fo],Y[sfold==fo]) for fo in range(6))
    wbB=max(rmse(bl[sfold==fo],Y[sfold==fo]) for fo in range(6))
    return rmse(gp,Y),np.corrcoef(gp-Y,O-Y)[0,1],np.mean(ws),rmse(bl,Y),wbD,wbB
for obj,dro,tag in [('regression',False,'l2       '),('huber',False,'huber    '),('huber',True,'huber+DRO')]:
    r,c,wm,blr,wbD,wbB=eval_aux(obj,dro)
    print(f"   {tag}: RMSE={r:.3f} corr={c:.3f} mean-blendW={wm:+.3f} pooled-blend={blr:.4f} | worstBlock DWT={wbD:.3f}->blend {wbB:.3f}")
print(f"   DWT pooled(spatial-grouped)={rmse(O,Y):.4f}")
