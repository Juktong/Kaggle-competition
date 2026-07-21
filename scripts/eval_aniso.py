"""Evaluate the anisotropic structural field (L4) against the deployed isotropic one, nested by well."""
import os, numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
an=np.load(f'{SH}/struct_aniso.npz',allow_pickle=True)
aw=an['well'].astype(str); ar=an['ridx'].astype(int)
ANIS=[k[8:] for k in an.files if k.startswith('struct_a')]
nnb=dict(zip(an['meta_well'].astype(str),an['meta_nnb'].astype(int)))
cl=dict(zip(an['meta_well'].astype(str),an['meta_closest'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(aw): si[w].append(i)
B,T,W={},{},{}
common=sorted(set(dw)&set(aw))
Bl,Tl,Wl=[],[],[]
Sl={a:[] for a in ANIS}
for w in common:
    a_=np.array(di[w]); b_=np.array(si[w])
    if len(a_)!=len(b_): continue
    Bl.append(dc['blend'][a_].astype(float)); Tl.append(dc['truth'][a_].astype(float)); Wl.append(np.full(len(a_),w))
    for a in ANIS: Sl[a].append(an[f'struct_a{a}'][b_].astype(float))
base=np.concatenate(Bl); Y=np.concatenate(Tl); well=np.concatenate(Wl)
S={a:np.concatenate(Sl[a]) for a in ANIS}
nnbv=np.array([nnb.get(w,0) for w in well],float); clov=np.array([cl.get(w,np.nan) for w in well],float)
gate=(nnbv>=4)&(clov<1000)&np.isfinite(clov)
rmse=lambda p:float(np.sqrt(np.mean((p-Y)**2)))
uw=np.array(sorted(set(well)))
print(f"rows={len(Y)} wells={len(uw)} gated={100*gate.mean():.1f}%")
ref=base.copy(); ref[gate]=0.85*base[gate]+0.15*S['1'][gate]
print(f"  deployed (A=1, W=0.15) = {rmse(ref):.4f}\n")
print("fixed W=0.15, varying anisotropy:")
for a in ANIS:
    p=base.copy(); p[gate]=0.85*base[gate]+0.15*S[a][gate]
    print(f"  A={a:>2}: {rmse(p):.4f}   gain vs deployed {rmse(ref)-rmse(p):+.4f}")
print("\nnested-W refit per anisotropy (fit half the wells, apply to held-out half, 3 seeds):")
def halves(seed):
    rg=np.random.RandomState(seed); sh=uw.copy(); rg.shuffle(sh)
    g0=set(sh[:len(sh)//2]); inA=np.array([w in g0 for w in well]); return [(inA,~inA),(~inA,inA)]
for a in ANIS:
    outs=[]; ws=[]
    for seed in range(3):
        p=base.copy()
        for tr,te in halves(seed):
            m=tr&gate
            d=(S[a]-base)[m]
            c=float(np.clip(np.dot(d,(Y-base)[m])/max(np.dot(d,d),1e-9),0,1)); ws.append(c)
            ap=te&gate; p[ap]=base[ap]+c*(S[a][ap]-base[ap])
        outs.append(rmse(p))
    print(f"  A={a:>2}: nested={np.mean(outs):.4f}  fitted W={np.mean(ws):.3f}  gain vs deployed {rmse(ref)-np.mean(outs):+.4f}")
print("\ntwo-field combination (isotropic + anisotropic, 2 nested coefficients):")
for a in ANIS:
    if a=='1': continue
    outs=[]
    for seed in range(3):
        p=base.copy()
        for tr,te in halves(seed):
            m=tr&gate
            Xm=np.column_stack([(S['1']-base)[m],(S[a]-base)[m]])
            try: c,_,_,_=np.linalg.lstsq(Xm,(Y-base)[m],rcond=None)
            except Exception: c=np.zeros(2)
            c=np.clip(c,0,1); ap=te&gate
            p[ap]=base[ap]+c[0]*(S['1'][ap]-base[ap])+c[1]*(S[a][ap]-base[ap])
        outs.append(rmse(p))
    print(f"  A=1 + A={a:>2}: nested={np.mean(outs):.4f}   gain vs deployed {rmse(ref)-np.mean(outs):+.4f}")

print("\nwell-level bootstrap of the best single-field variant:")
best_a=None; best_r=np.inf
for a in ANIS:
    outs=[]
    for seed in range(3):
        p2=base.copy()
        for tr,te in halves(seed):
            m=tr&gate; d=(S[a]-base)[m]
            c=float(np.clip(np.dot(d,(Y-base)[m])/max(np.dot(d,d),1e-9),0,1))
            ap=te&gate; p2[ap]=base[ap]+c*(S[a][ap]-base[ap])
        outs.append(rmse(p2))
    if np.mean(outs)<best_r: best_r, best_a = float(np.mean(outs)), a
print(f"  best A={best_a} nested={best_r:.4f}")
pb=base.copy()
for tr,te in halves(0):
    m=tr&gate; d=(S[best_a]-base)[m]
    c=float(np.clip(np.dot(d,(Y-base)[m])/max(np.dot(d,d),1e-9),0,1))
    ap=te&gate; pb[ap]=base[ap]+c*(S[best_a][ap]-base[ap])
idxw={w:np.where(well==w)[0] for w in uw}
rb=np.random.RandomState(7); gains=[]
for _ in range(400):
    samp=uw[rb.randint(0,len(uw),len(uw))]
    rows=np.concatenate([idxw[w] for w in samp])
    gains.append(np.sqrt(np.mean((ref[rows]-Y[rows])**2))-np.sqrt(np.mean((pb[rows]-Y[rows])**2)))
g=np.array(gains)
print(f"  bootstrap(400): mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} frac>0={100*np.mean(g>0):.0f}%")
print("\nGATE: >= +0.10 vs deployed with stably positive bootstrap.")
