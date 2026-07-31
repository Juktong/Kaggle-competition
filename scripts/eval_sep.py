"""Does the anisotropic gain survive a STRICTER duplicate guard?

A=50 divides strike distance by 50, so a mate just past MIN_SEP=150ft along strike has an effective
distance of ~3ft and could dominate the IDW -- potentially re-admitting the near-twins the guard was
calibrated (isotropically) to exclude. If the gain is real geology it should survive MIN_SEP=400/800.
If it collapses, it was duplicate leakage.
"""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
ref_src=np.load(f'{SH}/struct_aniso.npz',allow_pickle=True)     # A=1 baseline, MIN_SEP=150
runs={'150':np.load(f'{SH}/struct_aniso_hi.npz',allow_pickle=True),
      '400':np.load(f'{SH}/struct_aniso_sep400.npz',allow_pickle=True),
      '800':np.load(f'{SH}/struct_aniso_sep800.npz',allow_pickle=True)}
di=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
def build(src, key):
    sw=src['well'].astype(str); si=defaultdict(list)
    for i,w in enumerate(sw): si[w].append(i)
    return sw, si, src[key].astype(np.float32)
rw0, si0, a1 = build(ref_src,'struct_a1')
nnb=dict(zip(ref_src['meta_well'].astype(str),ref_src['meta_nnb'].astype(int)))
cl=dict(zip(ref_src['meta_well'].astype(str),ref_src['meta_closest'].astype(float)))
common=sorted(set(dw)&set(rw0))
Bl,Tl,Wl,S1=[],[],[],[]
for w in common:
    a_=np.array(di[w]); b_=np.array(si0[w])
    if len(a_)!=len(b_): continue
    Bl.append(dc['blend'][a_].astype(float)); Tl.append(dc['truth'][a_].astype(float))
    Wl.append(np.full(len(a_),w)); S1.append(a1[b_].astype(float))
base=np.concatenate(Bl); Y=np.concatenate(Tl); well=np.concatenate(Wl); s1=np.concatenate(S1)
nnbv=np.array([nnb.get(w,0) for w in well],float); clov=np.array([cl.get(w,np.nan) for w in well],float)
gate=(nnbv>=4)&(clov<1000)&np.isfinite(clov)
rmse=lambda p:float(np.sqrt(np.mean((p-Y)**2)))
ref=base.copy(); ref[gate]=0.85*base[gate]+0.15*s1[gate]
r0=rmse(ref)
print(f"deployed (A=1,W=.15,MIN_SEP=150) = {r0:.4f}")
print(f"\n{'MIN_SEP':>8} {'A':>4} {'nnb>=4 wells':>13} {'W=0.25':>10} {'gain':>9}")
for sep,src in runs.items():
    sw=src['well'].astype(str); si=defaultdict(list)
    for i,w in enumerate(sw): si[w].append(i)
    n2=dict(zip(src['meta_well'].astype(str),src['meta_nnb'].astype(int)))
    for a in ['20','50']:
        k=f'struct_a{a}'
        if k not in src.files: continue
        v=src[k].astype(np.float32); Sl=[]
        keep=[]
        for w in common:
            a_=np.array(di[w])
            if w not in si or len(si[w])!=len(a_): Sl.append(np.full(len(a_),np.nan)); continue
            Sl.append(v[np.array(si[w])].astype(float))
        S=np.concatenate(Sl)
        g2=gate & np.isfinite(S) & np.array([n2.get(w,0)>=4 for w in well])
        p=base.copy(); p[g2]=0.75*base[g2]+0.25*S[g2]
        nw=len(set(well[g2]))
        print(f"{sep:>8} {a:>4} {nw:>13} {rmse(p):>10.4f} {r0-rmse(p):>+9.4f}")
print("\n=> if the gain persists at MIN_SEP=400/800 it is geology, not duplicate leakage.")
