import numpy as np, pandas as pd, os
from collections import defaultdict
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM=cs['is_toe']
dw=cs['well'][tM].astype(str); do=cs['oof'][tM].astype(np.float64); dy=cs['yt'][tM].astype(np.float64); dr=cs['ridx'][tM].astype(int)
dwt=defaultdict(dict)
for w,r,o,y in zip(dw,dr,do,dy): dwt[w][r]=(o,y)
pf=np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz',allow_pickle=True)
pw=pf['well'].astype(str); pp=pf['pred'].astype(np.float64)
def geom_pred(hw, xcol, tail=256, max_move=120.0, damp=0.8):
    kn=hw[hw['TVT_input'].notna()]; toe=hw['TVT_input'].isna().values
    if len(kn)<20: return None
    x=hw[xcol].values.astype(float); t=hw['TVT_input'].values.astype(float)
    ki=np.where(hw['TVT_input'].notna().values)[0]; ti=ki[-min(len(ki),tail):]
    xx=x[ti]; yy=t[ti]; m=np.isfinite(xx)&np.isfinite(yy)
    if m.sum()<20 or (np.nanmax(xx[m])-np.nanmin(xx[m]))<1e-6: return None
    slope=np.polyfit(xx[m],yy[m],1)[0]
    last_t=t[ki[-1]]; last_x=x[ki[-1]]
    move=np.clip(damp*slope*(x-last_x),-max_move,max_move)
    return last_t+move
Ds,Ps,Ys,Gmd,Gz=[],[],[],[],[]
for wid in np.unique(pw):
    hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv'); toe=hw['TVT_input'].isna().values; tidx=np.where(toe)[0]
    m=pw==wid; pr=pp[m]
    if len(pr)!=len(tidx) or wid not in dwt: continue
    gmd=geom_pred(hw,'MD'); gz=geom_pred(hw,'Z')
    if gmd is None or gz is None: continue
    keep=[(j,ii) for j,ii in enumerate(tidx) if ii in dwt[wid]]
    if len(keep)<10: continue
    for j,ii in keep:
        o,y=dwt[wid][ii]; Ds.append(o);Ps.append(pr[j]);Ys.append(y);Gmd.append(gmd[ii]);Gz.append(gz[ii])
D_=np.array(Ds);P=np.array(Ps);Y=np.array(Ys);Gmd=np.array(Gmd);Gz=np.array(Gz)
def rmse(x): return np.sqrt(np.mean((x-Y)**2))
eD=D_-Y;eP=P-Y;eGmd=Gmd-Y;eGz=Gz-Y
print(f"rows={len(Y)}")
print(f"standalone RMSE: DWT={rmse(D_):.3f} PF={rmse(P):.3f} geom_MD={rmse(Gmd):.3f} geom_Z={rmse(Gz):.3f}  (blend DWT+PF@0.5={rmse(0.5*D_+0.5*P):.3f})")
print(f"corr geom_MD: vs DWT={np.corrcoef(eGmd,eD)[0,1]:.3f} vs PF={np.corrcoef(eGmd,eP)[0,1]:.3f}")
print(f"corr geom_Z:  vs DWT={np.corrcoef(eGz,eD)[0,1]:.3f} vs PF={np.corrcoef(eGz,eP)[0,1]:.3f}")
# nested 3-way blend: DWT+PF+geom, weights fit on fold0 applied fold1 (well split)
uw=np.array(sorted(set(pw[np.isin(pw,list(dwt))]))) if False else None
# well-split via row hash
rng=np.random.RandomState(0); idx=np.arange(len(Y)); rng.shuffle(idx); h=idx[:len(idx)//2]; h2=idx[len(idx)//2:]
def fit3(mask, cols):
    X=np.column_stack([cols[c][mask]-D_[mask] for c in range(len(cols))]); r=Y[mask]-D_[mask]
    a,_,_,_=np.linalg.lstsq(X,r,rcond=None); return a
def apply3(mask,cols,a): 
    return D_[mask]+sum(a[c]*(cols[c][mask]-D_[mask]) for c in range(len(cols)))
# 2-way DWT+PF baseline (nested)
for name,cols in [("DWT+PF",[P]),("DWT+PF+geomMD",[P,Gmd]),("DWT+PF+geomZ",[P,Gz]),("DWT+PF+geomMD+geomZ",[P,Gmd,Gz])]:
    pred=np.empty(len(Y))
    a1=fit3(h,cols); a2=fit3(h2,cols)
    pred[h2]=apply3(h2,cols,a1); pred[h]=apply3(h,cols,a2)
    print(f"  nested {name:22s} RMSE={np.sqrt(np.mean((pred-Y)**2)):.4f}  weights(fold-avg)={np.round((a1+a2)/2,3)}")
