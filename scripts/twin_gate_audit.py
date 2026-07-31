"""Does the A=50/W=0.25 field perform on wells whose 'closest' is a DROPPED near-twin?

At inference, a test well with a train near-twin gets closest=0ft, so the closest<1000ft gate passes
trivially. If such wells are ones the field handles badly, the gate is mis-firing and must be
recomputed from the closest SURVIVING mate. Measured here on the 39 train wells (5.1%) in that regime.
"""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
lo=np.load(f'{SH}/struct_aniso.npz',allow_pickle=True); hi=np.load(f'{SH}/struct_aniso_hi.npz',allow_pickle=True)
aw=lo['well'].astype(str)
a1=lo['struct_a1'].astype(np.float32); a50=hi['struct_a50'].astype(np.float32)
nnb=dict(zip(lo['meta_well'].astype(str),lo['meta_nnb'].astype(int)))
cl=dict(zip(lo['meta_well'].astype(str),lo['meta_closest'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(aw): si[w].append(i)
rows=[]
for w in sorted(set(dw)&set(aw)):
    a_=np.array(di[w]); b_=np.array(si[w])
    if len(a_)!=len(b_): continue
    base=dc['blend'][a_].astype(float); Y=dc['truth'][a_].astype(float)
    g=(nnb.get(w,0)>=4) and np.isfinite(cl.get(w,np.nan)) and cl.get(w,1e9)<1000
    if not g: continue
    dep=0.85*base+0.15*a1[b_].astype(float)
    cand=0.75*base+0.25*a50[b_].astype(float)
    rows.append((w, cl.get(w,np.nan), nnb.get(w,0),
                 float(np.sqrt(np.mean((dep-Y)**2))), float(np.sqrt(np.mean((cand-Y)**2))), len(a_)))
W=np.array([r[0] for r in rows]); C=np.array([r[1] for r in rows]); NB=np.array([r[2] for r in rows])
RD=np.array([r[3] for r in rows]); RC=np.array([r[4] for r in rows]); N=np.array([r[5] for r in rows])
gain=RD-RC
def rep(mask,lab):
    if mask.sum()==0: print(f"  {lab:34s} n=0"); return
    sd=np.sqrt(np.sum(RD[mask]**2*N[mask])/np.sum(N[mask])); sc=np.sqrt(np.sum(RC[mask]**2*N[mask])/np.sum(N[mask]))
    print(f"  {lab:34s} n={mask.sum():3d}  deployed={sd:7.4f} cand={sc:7.4f} pooled_gain={sd-sc:+.4f}"
          f"  helped={100*np.mean(gain[mask]>0):.0f}% worst={gain[mask].min():+.2f}")
print(f"gated wells={len(rows)}")
rep(np.ones(len(W),bool), "ALL gated")
rep(C<150,               "closest is a DROPPED mate (<150ft)")
rep(C==0,                "closest == 0ft (exact twin)")
rep((C>=150),            "closest is a SURVIVING mate")
rep((C>=150)&(C<400),    "  surviving, 150-400ft")
rep((C>=400)&(C<1000),   "  surviving, 400-1000ft")
