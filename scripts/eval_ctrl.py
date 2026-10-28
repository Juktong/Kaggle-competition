"""CONTROL: is anisotropy's ADVANTAGE OVER ISOTROPY preserved at stricter duplicate guards?

Comparing A=20/50 at MIN_SEP=400/800 against the deployed A=1/MIN_SEP=150 conflates two effects:
(a) losing real mates between 150 and 400 ft, which degrades ANY field, and
(b) anisotropy re-admitting near-twins the isotropic guard excluded (leakage).
The leakage question is answered only by comparing A>1 vs A=1 AT THE SAME MIN_SEP.
"""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
di=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
SETS={'150':(f'{SH}/struct_aniso.npz',f'{SH}/struct_aniso_hi.npz'),
      '400':(f'{SH}/struct_iso_sep400.npz',f'{SH}/struct_aniso_sep400.npz'),
      '800':(f'{SH}/struct_iso_sep800.npz',f'{SH}/struct_aniso_sep800.npz')}
print(f"{'MIN_SEP':>8} {'A':>4} {'W=0.15':>9} {'W=0.25':>9} | {'vs A=1 same sep (W=.25)':>24}")
for sep,(isof,anif) in SETS.items():
    iso=np.load(isof,allow_pickle=True); ani=np.load(anif,allow_pickle=True)
    sw=iso['well'].astype(str); si=defaultdict(list)
    for i,w in enumerate(sw): si[w].append(i)
    nnb=dict(zip(iso['meta_well'].astype(str),iso['meta_nnb'].astype(int)))
    cl=dict(zip(iso['meta_well'].astype(str),iso['meta_closest'].astype(float)))
    common=[w for w in sorted(set(dw)&set(sw)) if len(di[w])==len(si[w])]
    Bl,Tl,Wl=[],[],[]
    for w in common:
        a_=np.array(di[w]); Bl.append(dc['blend'][a_].astype(float)); Tl.append(dc['truth'][a_].astype(float)); Wl.append(np.full(len(a_),w))
    base=np.concatenate(Bl); Y=np.concatenate(Tl); well=np.concatenate(Wl)
    nnbv=np.array([nnb.get(w,0) for w in well],float); clov=np.array([cl.get(w,np.nan) for w in well],float)
    gate=(nnbv>=4)&(clov<1000)&np.isfinite(clov)
    rmse=lambda p:float(np.sqrt(np.mean((p-Y)**2)))
    vals={}
    for src in (iso,ani):
        sw2=src['well'].astype(str); si2=defaultdict(list)
        for i,w in enumerate(sw2): si2[w].append(i)
        for k in src.files:
            if not k.startswith('struct_a'): continue
            a=k[8:]
            if a in vals: continue
            v=src[k].astype(np.float32); parts=[]
            okall=True
            for w in common:
                if w not in si2 or len(si2[w])!=len(di[w]): okall=False; break
                parts.append(v[np.array(si2[w])].astype(float))
            if okall: vals[a]=np.concatenate(parts)
    if '1' not in vals: print(f"{sep:>8}  (A=1 control missing)"); continue
    r1=None
    for a in sorted(vals,key=float):
        p15=base.copy(); p15[gate]=0.85*base[gate]+0.15*vals[a][gate]
        p25=base.copy(); p25[gate]=0.75*base[gate]+0.25*vals[a][gate]
        if a=='1': r1=rmse(p25)
        delta=r1-rmse(p25) if r1 is not None else float('nan')
        print(f"{sep:>8} {a:>4} {rmse(p15):>9.4f} {rmse(p25):>9.4f} | {delta:>+24.4f}")
    print()
print("=> if 'vs A=1 same sep' stays clearly positive at 400/800, anisotropy itself is sound and the")
print("   earlier collapse was loss of real mates. If it vanishes/reverses, the advantage was leakage.")
