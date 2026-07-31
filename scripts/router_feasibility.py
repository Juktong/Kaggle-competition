import numpy as np, pandas as pd, os, glob
from collections import defaultdict
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
# DWT + PF per-well aligned
cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM=cs['is_toe']
dw=cs['well'][tM].astype(str); do=cs['oof'][tM].astype(np.float64); dy=cs['yt'][tM].astype(np.float64); dr=cs['ridx'][tM].astype(int)
dwt=defaultdict(dict)
for w,r,o,y in zip(dw,dr,do,dy): dwt[w][r]=(o,y)
pf=np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz',allow_pickle=True)
pw=pf['well'].astype(str); pp=pf['pred'].astype(np.float64); ptr=pf['truth'].astype(np.float64)
# pf npz has per-toe-row order matching hw toe order; rebuild per well
pfw=defaultdict(list)
# need pf row->ridx: pf npz stored well+pred+truth in toe order; reconstruct via hw toe indices
rows=[]
for wid in np.unique(pw):
    hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv')
    toe=hw['TVT_input'].isna().values; tidx=np.where(toe)[0]
    m=pw==wid; pr=pp[m]; tr=ptr[m]
    if len(pr)!=len(tidx): continue
    # test-available features from heel + trajectory
    kn=hw[hw['TVT_input'].notna()]; ev=hw[hw['TVT_input'].isna()]
    if len(kn)<10 or len(ev)<10: continue
    tail=kn.tail(30); dt=np.diff(tail['TVT_input'].values); dm=np.diff(tail['MD'].values); mm=dm>0
    heel_drift=float(np.median(np.abs(dt[mm]/dm[mm]))) if mm.sum()>=3 else 0.0
    z_span=float(np.nanmax(ev['Z'].values)-np.nanmin(ev['Z'].values))
    n_eval=int(toe.sum()); n_known=int(len(kn))
    gr_std=float(np.nanstd(hw['GR'].values))
    heel_zrange=float(kn['Z'].max()-kn['Z'].min())
    # per-well model errors on aligned toe rows
    keep=[(j,ii) for j,ii in enumerate(tidx) if ii in dwt[wid]]
    if len(keep)<10: continue
    Dv=np.array([dwt[wid][ii][0] for _,ii in keep]); Yv=np.array([dwt[wid][ii][1] for _,ii in keep]); Pv=np.array([pr[j] for j,_ in keep])
    dR=np.sqrt(np.mean((Dv-Yv)**2)); pR=np.sqrt(np.mean((Pv-Yv)**2))
    # per-well optimal blend weight a* (min RMSE of D+a(P-D))
    d=Pv-Dv; r=Yv-Dv; astar=float(np.dot(d,r)/np.dot(d,d)) if np.dot(d,d)>1e-9 else 0.0
    rows.append(dict(wid=wid,dR=dR,pR=pR,adv=dR-pR,astar=astar,heel_drift=heel_drift,z_span=z_span,n_eval=n_eval,n_known=n_known,gr_std=gr_std,heel_zrange=heel_zrange))
df=pd.DataFrame(rows)
print(f"wells={len(df)}")
print(f"PF advantage (dR-pR): median={df.adv.median():.2f} mean={df.adv.mean():.2f}  PF>DWT wells={int((df.adv>0).sum())} ({100*np.mean(df.adv>0):.0f}%)")
# correlation of test-available features with PF advantage and optimal weight
print("\ntest-available feature -> corr with PF-advantage (dR-pR) / corr with optimal a*:")
for f in ['heel_drift','z_span','n_eval','n_known','gr_std','heel_zrange']:
    print(f"  {f:12s} corr(adv)={np.corrcoef(df[f],df.adv)[0,1]:+.3f}  corr(a*)={np.corrcoef(df[f],df.astar)[0,1]:+.3f}")
df.to_csv(os.path.join(os.environ['CLAUDE_JOB_DIR'],'tmp/router_feat.csv'),index=False)
print("\nsaved router_feat.csv")
