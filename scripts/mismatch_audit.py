"""Mismatch audit for 54878409: OOF +0.1802 and visible-well +0.181, but public 7.891 -> 7.953 (-0.062).

Central question: was the bootstrap measuring the right uncertainty? It resampled 760 wells, which gives
the sampling distribution of a 760-well MEAN. The actual evaluation is 3 wells / 14151 rows. The relevant
distribution is the gain over a 3-WELL draw, which is far wider.
"""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
sv=np.load(f'{SH}/struct_aniso_surv.npz',allow_pickle=True)
aw=sv['well'].astype(str); s1=sv['struct_a1']; s50=sv['struct_a50']
nnb=dict(zip(sv['meta_well'].astype(str),sv['meta_nnb'].astype(int)))
csv_=dict(zip(sv['meta_well'].astype(str),sv['meta_closest_surv'].astype(float)))
call=dict(zip(sv['meta_well'].astype(str),sv['meta_closest'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(aw): si[w].append(i)
Bl,Tl,Wl,S1,S5=[],[],[],[],[]
for w in sorted(set(dw)&set(aw)):
    a=np.array(di[w]); b=np.array(si[w])
    if len(a)!=len(b): continue
    Bl.append(dc['blend'][a].astype(float)); Tl.append(dc['truth'][a].astype(float)); Wl.append(np.full(len(a),w))
    S1.append(s1[b].astype(float)); S5.append(s50[b].astype(float))
base=np.concatenate(Bl); Y=np.concatenate(Tl); well=np.concatenate(Wl)
st1=np.concatenate(S1); st50=np.concatenate(S5)
nnbv=np.array([nnb.get(w,0) for w in well],float)
csvv=np.array([csv_.get(w,np.nan) for w in well],float)
callv=np.array([call.get(w,np.nan) for w in well],float)
gold=(nnbv>=4)&(callv<1000)&np.isfinite(callv)
gnew=(nnbv>=4)&(csvv<1000)&np.isfinite(csvv)
dep=base.copy(); dep[gold]=0.85*base[gold]+0.15*st1[gold]
cnd=base.copy(); cnd[gnew]=0.75*base[gnew]+0.25*st50[gnew]
uw=np.array(sorted(set(well))); idxw={w:np.where(well==w)[0] for w in uw}
rm=lambda p,r: float(np.sqrt(np.mean((p[r]-Y[r])**2)))
allr=np.arange(len(Y))
print(f"OOF over {len(uw)} wells: deployed {rm(dep,allr):.4f} -> candidate {rm(cnd,allr):.4f}  gain {rm(dep,allr)-rm(cnd,allr):+.4f}\n")
print("=== 1. THE BOOTSTRAP MEASURED THE WRONG THING ===")
for nw in [760,100,20,10,5,3,1]:
    rb=np.random.RandomState(7); g=[]
    for _ in range(4000):
        samp=uw[rb.randint(0,len(uw),nw)]
        rows=np.concatenate([idxw[w] for w in samp])
        g.append(rm(dep,rows)-rm(cnd,rows))
    g=np.array(g)
    print(f"  resample {nw:>3} wells: mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} "
          f"25th={np.percentile(g,25):+.4f} frac<0={100*np.mean(g<0):>4.1f}%")
print("\n  -> the reported 'bootstrap 5th +0.0490' was for a 760-well mean.")
print("     The competition evaluates 3 wells, where the gain distribution is far wider.")
print("\n=== 2. per-well gain distribution (what a 3-well draw samples from) ===")
d_=np.array([rm(dep,idxw[w])-rm(cnd,idxw[w]) for w in uw])
print(f"  mean={d_.mean():+.3f} median={np.median(d_):+.3f} std={d_.std():.3f}")
print(f"  wells hurt {100*np.mean(d_<-1e-9):.1f}%  helped {100*np.mean(d_>1e-9):.1f}%")
print(f"  percentiles: 5th {np.percentile(d_,5):+.2f} | 25th {np.percentile(d_,25):+.2f} | 75th {np.percentile(d_,75):+.2f} | 95th {np.percentile(d_,95):+.2f}")
print("\n=== 3. the 3 test wells (they are also train wells) ===")
VIS=['000d7d20','00bbac68','00e12e8b']
for w in VIS:
    if w not in idxw: print(f"  {w}: absent"); continue
    r=idxw[w]
    print(f"  {w}: n={len(r):5d} dep={rm(dep,r):6.3f} cand={rm(cnd,r):6.3f} gain={rm(dep,r)-rm(cnd,r):+.3f}"
          f" | nnb={nnb.get(w,0):3d} closest_all={call.get(w,np.nan):7.1f} closest_surv={csv_.get(w,np.nan):7.1f}")
vr=np.concatenate([idxw[w] for w in VIS if w in idxw])
print(f"  POOLED 3 wells (OOF): dep={rm(dep,vr):.4f} cand={rm(cnd,vr):.4f} gain={rm(dep,vr)-rm(cnd,vr):+.4f}")
print("\n=== 4. are the test wells in the weak twin subgroup? ===")
twin=np.array([call.get(w,np.nan)<150 for w in uw])
print(f"  train wells with closest_all<150ft: {twin.sum()} of {len(uw)}")
print(f"  the 3 test wells' closest_all: " + ", ".join(f"{w}={call.get(w,np.nan):.1f}" for w in VIS))
tm=np.concatenate([idxw[w] for w in uw[twin]])
print(f"  twin-subgroup pooled gain: {rm(dep,tm)-rm(cnd,tm):+.4f}")
