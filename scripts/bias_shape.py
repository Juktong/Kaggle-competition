import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
rd=np.load(f'{SH}/struct_oof_rowdist.npz',allow_pickle=True)
rw=rd['well'].astype(str); rs=rd['struct'].astype(float)
nnb=dict(zip(rd['meta_well'].astype(str),rd['meta_nnb'].astype(int)))
cl=dict(zip(rd['meta_well'].astype(str),rd['meta_closest'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(rw): si[w].append(i)
wells=[]
for w in sorted(set(dw)&set(rw)):
    a=np.array(di[w]); b=np.array(si[w])
    if len(a)!=len(b) or len(a)<300: continue
    base=dc['blend'][a].astype(float); tr=dc['truth'][a].astype(float)
    g=(nnb.get(w,0)>=4) and np.isfinite(cl.get(w,np.nan)) and cl.get(w,1e9)<1000
    wells.append((w, 0.85*base+0.15*rs[b] if g else base, tr))
print(f"wells={len(wells)}",flush=True)
lev,slo,r2=[],[],[]
for w,c,t in wells:
    r=t-c; x=np.linspace(0,1,len(r))
    A=np.column_stack([np.ones(len(r)),x])
    co,_,_,_=np.linalg.lstsq(A,r,rcond=None)
    lev.append(co[0]); slo.append(co[1])
    ss=np.sum((r-A@co)**2); st=np.sum((r-r.mean())**2)
    r2.append(1-ss/max(st,1e-9))
lev=np.array(lev); slo=np.array(slo); r2=np.array(r2)
print(f"  intercept (toe-start level): std={lev.std():.2f} ft")
print(f"  slope (start->end drift)   : std={slo.std():.2f} ft, median|slope|={np.median(abs(slo)):.2f}")
print(f"  linear fit explains median R2={np.median(r2):.3f} of within-well residual variance")
print(f"  corr(level, slope) = {np.corrcoef(lev,slo)[0,1]:+.3f}")
early=np.array([np.mean((t-c)[:100]) for w,c,t in wells])
full =np.array([np.mean(t-c) for w,c,t in wells])
cc=np.corrcoef(early,full)[0,1]
print(f"\n  corr(first-100-row bias, whole-well bias) = {cc:+.3f}  -> explains {100*cc**2:.0f}% of variance")
for n in [50,200,500]:
    e=np.array([np.mean((t-c)[:n]) for w,c,t in wells]); c2=np.corrcoef(e,full)[0,1]
    print(f"  corr(first-{n}-row bias, whole-well bias) = {c2:+.3f}")
