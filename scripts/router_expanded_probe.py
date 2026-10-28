import numpy as np, pandas as pd, os
from collections import defaultdict
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM=cs['is_toe']
dw=cs['well'][tM].astype(str); do=cs['oof'][tM].astype(np.float64); dy=cs['yt'][tM].astype(np.float64); dr=cs['ridx'][tM].astype(int)
dwt=defaultdict(dict)
for w,r,o,y in zip(dw,dr,do,dy): dwt[w][r]=(o,y)
pf=np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz',allow_pickle=True)
pw=pf['well'].astype(str); pp=pf['pred'].astype(np.float64)
Ds,Ps,Ys,DIS,ROWF,GRr,CURV,Wid=[],[],[],[],[],[],[],[]
for wid in np.unique(pw):
    hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv'); toe=hw['TVT_input'].isna().values; tidx=np.where(toe)[0]
    m=pw==wid; pr=pp[m]
    if len(pr)!=len(tidx) or wid not in dwt: continue
    gr=hw['GR'].values.astype(float); z=hw['Z'].values.astype(float); md=hw['MD'].values.astype(float)
    grough=pd.Series(gr).rolling(15,center=True,min_periods=1).std().values
    # curvature ~ 2nd diff of Z wrt MD
    curv=np.abs(np.gradient(np.gradient(z,md),md))
    keep=[(j,ii) for j,ii in enumerate(tidx) if ii in dwt[wid]]
    if len(keep)<10: continue
    n=len(keep)
    for k,(j,ii) in enumerate(keep):
        o,y=dwt[wid][ii]; p=pr[j]
        Ds.append(o);Ps.append(p);Ys.append(y);DIS.append(abs(p-o));ROWF.append(k/n)
        GRr.append(grough[ii] if np.isfinite(grough[ii]) else 0.0); CURV.append(curv[ii] if np.isfinite(curv[ii]) else 0.0); Wid.append(wid)
D_=np.array(Ds);P=np.array(Ps);Y=np.array(Ys);DIS=np.array(DIS);ROWF=np.array(ROWF);GRr=np.array(GRr);CURV=np.array(CURV)
eD=np.abs(D_-Y); eP=np.abs(P-Y)
better_pf=(eP<eD).astype(float)   # 1 if PF closer at this row
print(f"rows={len(Y)}  PF-better-per-row: {100*better_pf.mean():.1f}%")
# does any test-available feature predict which is better per row?
print("per-row feature -> corr with (eD-eP) [+ means feature high => PF better] and with |D-Y| [hard proxy]:")
for name,f in [('|PF-DWT| disagree',DIS),('row_frac(toe pos)',ROWF),('GR roughness',GRr),('Z curvature',CURV)]:
    c1=np.corrcoef(f,eD-eP)[0,1]; c2=np.corrcoef(f,eD)[0,1]
    print(f"  {name:20s} corr(eD-eP)={c1:+.3f}  corr(|D-Y|)={c2:+.3f}")
# KEY: does disagreement predict which model is right? split by disagreement quartile
print("\ndisagreement-quartile: is PF or DWT better where they disagree most?")
q=np.quantile(DIS,[0.25,0.5,0.75])
for lo,hi,lab in [(-1,q[0],'Q1 low-disagree'),(q[0],q[1],'Q2'),(q[1],q[2],'Q3'),(q[2],1e9,'Q4 high-disagree')]:
    m=(DIS>lo)&(DIS<=hi)
    print(f"  {lab:16s} n={m.sum():>8d}  DWT_rmse={np.sqrt(np.mean(eD[m]**2)):.2f}  PF_rmse={np.sqrt(np.mean(eP[m]**2)):.2f}  blend0.5={np.sqrt(np.mean((0.5*D_[m]+0.5*P[m]-Y[m])**2)):.2f}")
