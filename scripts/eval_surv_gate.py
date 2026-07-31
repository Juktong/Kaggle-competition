"""Re-validate the anisotropic candidate with the gate defined on the CLOSEST SURVIVING mate.

The deployed gate uses min(sep) over ALL candidate mates INCLUDING ones the MIN_SEP duplicate guard
drops. On train that affects 5.1% of wells; at inference every test well with a train near-twin gets
closest=0ft and passes the gate trivially (all 3 smoke wells did). Those wells are exactly where the
candidate loses (-0.4439 pooled). Defining the gate on the closest SURVIVING mate is semantically
correct ("is there a nearby USABLE mate?") and strictly more conservative, and makes OOF and inference
behave the same way.
"""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
sv=np.load(f'{SH}/struct_aniso_surv.npz',allow_pickle=True)
aw=sv['well'].astype(str)
a1=sv['struct_a1'].astype(np.float32); a50=sv['struct_a50'].astype(np.float32)
nnb=dict(zip(sv['meta_well'].astype(str),sv['meta_nnb'].astype(int)))
cl_all=dict(zip(sv['meta_well'].astype(str),sv['meta_closest'].astype(float)))
cl_srv=dict(zip(sv['meta_well'].astype(str),sv['meta_closest_surv'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(aw): si[w].append(i)
Bl,Tl,Wl,S1,S50=[],[],[],[],[]
for w in sorted(set(dw)&set(aw)):
    a_=np.array(di[w]); b_=np.array(si[w])
    if len(a_)!=len(b_): continue
    Bl.append(dc['blend'][a_].astype(float)); Tl.append(dc['truth'][a_].astype(float)); Wl.append(np.full(len(a_),w))
    S1.append(a1[b_].astype(float)); S50.append(a50[b_].astype(float))
base=np.concatenate(Bl); Y=np.concatenate(Tl); well=np.concatenate(Wl)
s1=np.concatenate(S1); s50=np.concatenate(S50)
nnbv=np.array([nnb.get(w,0) for w in well],float)
c_all=np.array([cl_all.get(w,np.nan) for w in well],float)
c_srv=np.array([cl_srv.get(w,np.nan) for w in well],float)
rmse=lambda p:float(np.sqrt(np.mean((p-Y)**2)))
uw=np.array(sorted(set(well))); idxw={w:np.where(well==w)[0] for w in uw}
gate_old=(nnbv>=4)&(c_all<1000)&np.isfinite(c_all)
gate_new=(nnbv>=4)&(c_srv<1000)&np.isfinite(c_srv)
print(f"rows={len(Y)} wells={len(uw)}")
print(f"  gate on ALL-mates min  : {100*gate_old.mean():.1f}% rows, {len(set(well[gate_old]))} wells")
print(f"  gate on SURVIVING min  : {100*gate_new.mean():.1f}% rows, {len(set(well[gate_new]))} wells")
print(f"  wells gated ON by old but OFF by new: {len(set(well[gate_old])-set(well[gate_new]))}\n")
ref=base.copy(); ref[gate_old]=0.85*base[gate_old]+0.15*s1[gate_old]
r0=rmse(ref); print(f"deployed (A=1,W=.15, old gate) = {r0:.4f}")
def halves(seed):
    rg=np.random.RandomState(seed); sh=uw.copy(); rg.shuffle(sh)
    g0=set(sh[:len(sh)//2]); inA=np.array([w in g0 for w in well]); return [(inA,~inA),(~inA,inA)]
def boot(cand,lab):
    rb=np.random.RandomState(7); g=[]
    for _ in range(1000):
        samp=uw[rb.randint(0,len(uw),len(uw))]
        rows=np.concatenate([idxw[w] for w in samp])
        g.append(np.sqrt(np.mean((ref[rows]-Y[rows])**2))-np.sqrt(np.mean((cand[rows]-Y[rows])**2)))
    g=np.array(g)
    d_=np.array([np.sqrt(np.mean((ref[idxw[w]]-Y[idxw[w]])**2))-np.sqrt(np.mean((cand[idxw[w]]-Y[idxw[w]])**2)) for w in uw])
    nz=np.abs(d_)>1e-9
    print(f"  [{lab}] rmse={rmse(cand):.4f} gain={r0-rmse(cand):+.4f} | boot mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} "
          f"1st={np.percentile(g,1):+.4f} frac>0={100*np.mean(g>0):.0f}% | helped={100*np.mean(d_>1e-9):.1f}% worst={d_.min():+.2f}")
    return r0-rmse(cand), float(np.percentile(g,5))
print("\nfixed A=50, W=0.25 under each gate:")
for lab,gt in [("old gate (all-mates min)",gate_old),("NEW gate (surviving min)",gate_new)]:
    c=base.copy(); c[gt]=0.75*base[gt]+0.25*s50[gt]
    boot(c,lab)
print("\nnested W (A=50) under the NEW gate, W grid capped at 0.25:")
outs=[];ws=[]
for seed in range(6):
    p=base.copy()
    for tr,te in halves(seed):
        m=tr&gate_new; best=(np.inf,0.15)
        for Wt in [0.15,0.20,0.25]:
            q=(1-Wt)*base[m]+Wt*s50[m]; s=float(np.mean((q-Y[m])**2))
            if s<best[0]: best=(s,Wt)
        ws.append(best[1]); ap=te&gate_new; p[ap]=(1-best[1])*base[ap]+best[1]*s50[ap]
    outs.append(rmse(p))
nested=float(np.mean(outs))
print(f"  nested W picks={sorted(set(ws))} mean={np.mean(ws):.3f}")
print(f"  NESTED = {nested:.4f}  gain {r0-nested:+.4f}")
shipW=max(set(ws),key=ws.count)
ship=base.copy(); ship[gate_new]=(1-shipW)*base[gate_new]+shipW*s50[gate_new]
print(f"\n  DEPLOYABLE: A=50, W={shipW}, gate on closest SURVIVING mate")
gn,b5=boot(ship,f"A=50 W={shipW} new gate")
print(f"\n  GATE (+0.10 AND stably positive bootstrap): {'MEETS' if (r0-nested)>=0.10 and b5>0 else 'DOES NOT MEET'}")
