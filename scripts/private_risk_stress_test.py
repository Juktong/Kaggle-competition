import numpy as np, pandas as pd, os
from collections import defaultdict
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
feat=pd.read_csv(os.path.join(os.environ['CLAUDE_JOB_DIR'].replace('1a07ce3e','06dd2efb'),'tmp/router_feat.csv')) if os.path.exists(os.path.join(os.environ['CLAUDE_JOB_DIR'].replace('1a07ce3e','06dd2efb'),'tmp/router_feat.csv')) else None
# router_feat.csv may be under 06dd2efb job dir; fall back to recompute-free path
fp=None
for c in ['06dd2efb','1a07ce3e']:
    p=f'/home/ubuntu/.claude/jobs/{c}/tmp/router_feat.csv'
    if os.path.exists(p): fp=p
feat=pd.read_csv(fp) if fp else None
cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM=cs['is_toe']
dw=cs['well'][tM].astype(str); do=cs['oof'][tM].astype(np.float64); dy=cs['yt'][tM].astype(np.float64); dr=cs['ridx'][tM].astype(int)
dwt=defaultdict(dict)
for w,r,o,y in zip(dw,dr,do,dy): dwt[w][r]=(o,y)
pf=np.load('/home/ubuntu/.claude/jobs/06dd2efb/tmp/pf_oof_full773.npz',allow_pickle=True)
pw=pf['well'].astype(str); pp=pf['pred'].astype(np.float64)
# per-well aligned arrays
W={}
for wid in np.unique(pw):
    hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv'); toe=hw['TVT_input'].isna().values; tidx=np.where(toe)[0]
    m=pw==wid; pr=pp[m]
    if len(pr)!=len(tidx) or wid not in dwt: continue
    keep=[(j,ii) for j,ii in enumerate(tidx) if ii in dwt[wid]]
    if len(keep)<10: continue
    Dv=np.array([dwt[wid][ii][0] for _,ii in keep]); Yv=np.array([dwt[wid][ii][1] for _,ii in keep]); Pv=np.array([pr[j] for j,_ in keep])
    W[wid]=(Dv,Pv,Yv)
wids=sorted(W)
def pooled(sub, w):
    Ds=np.concatenate([W[x][0] for x in sub]); Ps=np.concatenate([W[x][1] for x in sub]); Ys=np.concatenate([W[x][2] for x in sub])
    return np.sqrt(np.mean(((1-w)*Ds+w*Ps-Ys)**2))
# ===== D: weight sweep on full OOF =====
print("=== D. DWT+PF weight sweep (full 773-well OOF, pooled RMSE) ===")
for w in [0.0,0.35,0.40,0.44,0.45,0.50,0.55,0.60,1.0]:
    tag='(DWT)' if w==0 else '(PF)' if w==1 else '(fitted~0.44)' if w==0.44 else '(current)' if w==0.5 else ''
    print(f"  W={w:.2f}: pooled RMSE={pooled(wids,w):.4f} {tag}")
# ===== B: private-composition stress test =====
print("\n=== B. private-risk stress test (subset RMSE; DWT vs PF vs blend@0.5 vs blend@fitted) ===")
if feat is not None:
    fmap={r.wid:r for _,r in feat.iterrows()}
    perD={x:np.sqrt(np.mean((W[x][0]-W[x][2])**2)) for x in wids}
    toe_ct={x:len(W[x][2]) for x in wids}
    def report(name, sub):
        if not sub: print(f"  {name}: (empty)"); return
        print(f"  {name:22s} n={len(sub):3d}  DWT={pooled(sub,0):.3f}  PF={pooled(sub,1):.3f}  blend0.5={pooled(sub,0.5):.3f}  blend0.44={pooled(sub,0.44):.3f}")
    report("ALL (novel proxy)", wids)
    # hard-well-heavy (top tercile DWT per-well RMSE)
    dr_sorted=sorted(wids,key=lambda x:perD[x])
    report("hard-well-heavy(top33%)", dr_sorted[int(len(wids)*0.67):])
    report("easy-well-heavy(bot33%)", dr_sorted[:int(len(wids)*0.33)])
    # long-well-heavy (top tercile toe count)
    tc_sorted=sorted(wids,key=lambda x:toe_ct[x])
    report("long-well-heavy(top33%)", tc_sorted[int(len(wids)*0.67):])
    report("short-well-heavy(bot33%)", tc_sorted[:int(len(wids)*0.33)])
    # high-drift-heavy (top tercile heel_drift)
    hd=sorted([x for x in wids if x in fmap],key=lambda x:fmap[x].heel_drift)
    report("high-drift-heavy(top33%)", hd[int(len(hd)*0.67):])
    report("low-drift-heavy(bot33%)", hd[:int(len(hd)*0.33)])
    # high z-span (structural change)
    zs=sorted([x for x in wids if x in fmap],key=lambda x:fmap[x].z_span)
    report("high-zspan-heavy(top33%)", zs[int(len(zs)*0.67):])
else:
    print("  (router_feat.csv not found — recompute needed)")
print("\n=> if blend beats DWT AND PF across all stress subsets, DWT+PF is robust for the honest slot.")
