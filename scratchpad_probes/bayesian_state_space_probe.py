"""Direction D: Bayesian/state-space structural POSTERIOR (particle smoother), not a single DP path.
State = (TVT offset, dip, curvature); obs = horizontal-GR vs typewell-GR-at-state + trajectory
smoothness; occasional jump. Output posterior mean + posterior std (uncertainty) + top-K, not MAP.
Test: (1) posterior-mean RMSE / corr / blend-weight sign vs DWT; (2) does posterior uncertainty
predict DWT-failure better than the B4 classifier (AUC 0.573)? test-available inputs only.
"""
import numpy as np, pandas as pd, glob, sys, time
from sklearn.metrics import roc_auc_score
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
NW=int(sys.argv[1]) if len(sys.argv)>1 else 120; NP=160
t0=time.time(); rs=np.random.RandomState(3)
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
df=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt']))
g={w:s.set_index('ridx') for w,s in df.groupby('well')}
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
def pf(GRtw, states, GRh, ds, tvt0, dip0):
    S0=states[0]; Send=states[-1]
    tvt=tvt0+rs.randn(NP)*2.0; dip=dip0+rs.randn(NP)*0.005
    means=[]; stds=[]
    for i,row in enumerate(ds):
        # propagate
        dip=dip+rs.randn(NP)*0.004
        jump=(rs.rand(NP)<0.01)*rs.randn(NP)*15
        tvt=tvt+dip*(ds[i]-ds[i-1] if i>0 else 1)+jump
        tvt=np.clip(tvt,S0+1,Send-1)
        # weight by GR match
        gr_pred=np.interp(tvt,states,GRtw); w=np.exp(-0.5*((GRh[row]-gr_pred)/12.0)**2)+1e-9
        w/=w.sum()
        means.append(np.sum(w*tvt)); stds.append(np.sqrt(np.sum(w*(tvt-means[-1])**2)))
        # resample
        idx=rs.choice(NP,NP,p=w); tvt=tvt[idx]; dip=dip[idx]
    return np.array(means),np.array(stds)
poolT=[];poolD=[];poolPF=[]; per=[]
for k,f in enumerate(sorted(glob.glob(f"{DATA}/*__horizontal_well.csv"))[:NW]):
    wid=f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    h=pd.read_csv(f); t=pd.read_csv(f.replace("__horizontal_well","__typewell"))
    GR=h['GR'].values.astype(float); MD=h['MD'].values.astype(float); Ht=h['TVT'].values.astype(float); known=h['TVT_input'].notna().values
    tw=t.dropna(subset=['TVT','GR']).sort_values('TVT'); tv=tw['TVT'].values.astype(float); gt=tw['GR'].values.astype(float)
    if len(tv)<50: continue
    states=np.arange(tv.min(),tv.max(),1.0); GRtw=np.interp(states,tv,gt); c=np.where(known)[0].max()
    if len(states)<50: continue
    kmd=MD[known][-100:]; ktv=Ht[known][-100:]; dip0=np.polyfit(kmd,ktv,1)[0] if len(kmd)>20 else 0.0
    sub=g[wid]; toe=np.array([i for i in np.where(~known)[0] if i>c and i in sub.index and not np.isnan(GR[i])])
    if len(toe)<50: continue
    ds=toe[::4]
    try: means,stds=pf(GRtw,states,GR,ds,Ht[c],dip0)
    except Exception: continue
    est=np.interp(toe,ds,means); truth=sub.loc[toe,'yt'].values; dwt=sub.loc[toe,'oof'].values
    poolT.append(truth);poolD.append(dwt);poolPF.append(est)
    per.append((np.mean(stds), rmse(dwt,truth)))
    if k%40==0: print("  ..",k,round(time.time()-t0,1),"s",flush=True)
T=np.concatenate(poolT);D=np.concatenate(poolD);PF=np.concatenate(poolPF)
per=np.array(per)
c=np.corrcoef(PF-T,D-T)[0,1]
# blend weight sign
a=PF-D;b=T-D; wg=float(np.sum(a*b)/np.sum(a*a))
print(f"\nD Bayesian PF ({len(poolT)} wells, {round(time.time()-t0,1)}s):")
print(f"   DWT={rmse(D,T):.3f}  PF-posterior-mean={rmse(PF,T):.3f}  corr(err,DWT)={c:.3f}  blendW={wg:+.3f} ({'neg=artifact' if wg<0 else 'pos'})")
auc=roc_auc_score((per[:,1]>np.median(per[:,1])).astype(int), per[:,0])
print(f"   posterior-uncertainty predicts DWT-failure: AUC={auc:.3f} (vs B4 classifier 0.573)")
