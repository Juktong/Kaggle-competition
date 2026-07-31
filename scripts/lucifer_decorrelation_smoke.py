import numpy as np, pandas as pd, os, glob
from collections import defaultdict
ns={}; exec(open('scripts/lucifer_honest_forward.py').read(), ns)
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
LOG=os.path.join(os.environ['CLAUDE_JOB_DIR'],'tmp/lucifer_serial.log')
cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM=cs['is_toe']
dw=cs['well'][tM].astype(str); do=cs['oof'][tM].astype(np.float64); dy=cs['yt'][tM].astype(np.float64); dr=cs['ridx'][tM].astype(int)
dwt=defaultdict(dict)
for w,r,o,y in zip(dw,dr,do,dy): dwt[w][r]=(o,y)
allw=sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng=np.random.RandomState(11); rng.shuffle(allw); wells=[w for w in allw if w in dwt][:15]
NS=8
def log(s):
    with open(LOG,'a') as f: f.write(s+'\n')
open(LOG,'w').close()
rows_all=[]
for k,wid in enumerate(wells):
    try:
        hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv'); tw=pd.read_csv(f'{D}/{wid}__typewell.csv')
        toe=hw['TVT_input'].isna().values
        tw_s=tw.sort_values('TVT'); tt=tw_s['TVT'].values.astype(float); tg=tw_s['GR'].fillna(tw_s['GR'].mean()).values.astype(float)
        def _full(pts):
            o=np.full(len(hw),np.nan); o[toe]=np.asarray(pts); return o
        pp=np.asarray(ns['run_pf_lik_ensemble'](hw,tw,n_particles=500,n_seeds=NS,scale=5.0))
        be=np.asarray(ns['run_beam_ensemble'](hw,tw))
        an=_full(ns['run_pf_ancc'](hw,tt,tg)[0]); zp=_full(ns['run_pf_z'](hw,tt,tg)[0])
        for i in [j for j in np.where(toe)[0] if j in dwt[wid]]:
            o,y=dwt[wid][i]; rows_all.append((o,y,pp[i],be[i],an[i],zp[i]))
        A=np.array(rows_all); Dp,Y,PP=A[:,0],A[:,1],A[:,2]; eD=Dp-Y; eP=PP-Y
        def cc(col):
            e=A[:,col]-Y; return np.sqrt(np.mean(e**2)), np.corrcoef(e,eD)[0,1], np.corrcoef(e,eP)[0,1]
        log(f"[{k+1}/{len(wells)}] {wid} rows={len(A)}  " + " ".join(
            f"{n}=R{cc(c)[0]:.1f}/cD{cc(c)[1]:.2f}/cP{cc(c)[2]:.2f}" for n,c in [('PF',2),('beam',3),('ancc',4),('zpf',5)]))
    except Exception as e:
        log(f"[{k+1}] {wid} ERR {e}")
A=np.array(rows_all); Dp,Y=A[:,0],A[:,1]; eD=Dp-Y; eP=A[:,2]-Y
log(f"\nFINAL wells={len(wells)} rows={len(A)} NS={NS}")
log(f"{'model':8s} {'RMSE':>7s} {'RMSE_p97trim':>12s} {'corrDWT':>8s} {'corrPF':>7s}")
for n,c in [('DWT',0),('PF',2),('beam',3),('ancc',4),('zpf',5)]:
    e=A[:,c]-Y; thr=np.percentile(np.abs(e),97); tr=np.sqrt(np.mean(e[np.abs(e)<=thr]**2))
    log(f"{n:8s} {np.sqrt(np.mean(e**2)):7.2f} {tr:12.2f} {np.corrcoef(e,eD)[0,1]:8.3f} {np.corrcoef(e,eP)[0,1]:7.3f}")
log("DONE")
