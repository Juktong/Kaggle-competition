"""Combined L4 evaluation across both anisotropy sweeps, with well-level bootstrap."""
import os, numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
lo=np.load(f'{SH}/struct_aniso.npz',allow_pickle=True)
hi=np.load(f'{SH}/struct_aniso_hi.npz',allow_pickle=True)
assert (lo['well'].astype(str)==hi['well'].astype(str)).all() and (lo['ridx']==hi['ridx']).all(), "row order mismatch"
aw=lo['well'].astype(str)
fields={}
for src in (lo,hi):
    for k in src.files:
        if k.startswith('struct_a'): fields.setdefault(k[8:], src[k].astype(np.float32))
ANIS=sorted(fields, key=float)
nnb=dict(zip(lo['meta_well'].astype(str),lo['meta_nnb'].astype(int)))
cl=dict(zip(lo['meta_well'].astype(str),lo['meta_closest'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(aw): si[w].append(i)
Bl,Tl,Wl=[],[],[]; Sl={a:[] for a in ANIS}
for w in sorted(set(dw)&set(aw)):
    a_=np.array(di[w]); b_=np.array(si[w])
    if len(a_)!=len(b_): continue
    Bl.append(dc['blend'][a_].astype(float)); Tl.append(dc['truth'][a_].astype(float)); Wl.append(np.full(len(a_),w))
    for a in ANIS: Sl[a].append(fields[a][b_].astype(float))
base=np.concatenate(Bl); Y=np.concatenate(Tl); well=np.concatenate(Wl)
S={a:np.concatenate(Sl[a]) for a in ANIS}
nnbv=np.array([nnb.get(w,0) for w in well],float); clov=np.array([cl.get(w,np.nan) for w in well],float)
gate=(nnbv>=4)&(clov<1000)&np.isfinite(clov)
rmse=lambda p:float(np.sqrt(np.mean((p-Y)**2)))
uw=np.array(sorted(set(well)))
ref=base.copy(); ref[gate]=0.85*base[gate]+0.15*S['1'][gate]
print(f"rows={len(Y)} wells={len(uw)} gated={100*gate.mean():.1f}%  anisos={ANIS}")
print(f"  deployed (A=1, W=0.15) = {rmse(ref):.4f}\n")
def halves(seed):
    rg=np.random.RandomState(seed); sh=uw.copy(); rg.shuffle(sh)
    g0=set(sh[:len(sh)//2]); inA=np.array([w in g0 for w in well]); return [(inA,~inA),(~inA,inA)]
print(f"{'A':>4} | {'fixed W=.15':>12} | {'nested-W':>10} {'fitW':>6} | {'gain(fix)':>10} {'gain(nest)':>11}")
best=(None,np.inf)
for a in ANIS:
    pf=base.copy(); pf[gate]=0.85*base[gate]+0.15*S[a][gate]
    outs=[];ws=[]
    for seed in range(3):
        p=base.copy()
        for tr,te in halves(seed):
            m=tr&gate; d=(S[a]-base)[m]
            c=float(np.clip(np.dot(d,(Y-base)[m])/max(np.dot(d,d),1e-9),0,1)); ws.append(c)
            ap=te&gate; p[ap]=base[ap]+c*(S[a][ap]-base[ap])
        outs.append(rmse(p))
    nr=float(np.mean(outs))
    if nr<best[1]: best=(a,nr)
    print(f"{a:>4} | {rmse(pf):>12.4f} | {nr:>10.4f} {np.mean(ws):>6.3f} | {rmse(ref)-rmse(pf):>+10.4f} {rmse(ref)-nr:>+11.4f}")
ba,br=best
print(f"\nBEST single field: A={ba}  nested={br:.4f}  gain {rmse(ref)-br:+.4f}")
# conservative deployable form: best A at UNCHANGED W=0.15
pcons=base.copy(); pcons[gate]=0.85*base[gate]+0.15*S[ba][gate]
print(f"conservative (A={ba}, W unchanged 0.15): {rmse(pcons):.4f}  gain {rmse(ref)-rmse(pcons):+.4f}")
# bootstrap both
idxw={w:np.where(well==w)[0] for w in uw}
pb=base.copy()
for tr,te in halves(0):
    m=tr&gate; d=(S[ba]-base)[m]
    c=float(np.clip(np.dot(d,(Y-base)[m])/max(np.dot(d,d),1e-9),0,1))
    ap=te&gate; pb[ap]=base[ap]+c*(S[ba][ap]-base[ap])
for tag,cand in [(f"A={ba} nested-W",pb),(f"A={ba} fixed W=.15",pcons)]:
    rb=np.random.RandomState(7); g=[]
    for _ in range(400):
        samp=uw[rb.randint(0,len(uw),len(uw))]
        rows=np.concatenate([idxw[w] for w in samp])
        g.append(np.sqrt(np.mean((ref[rows]-Y[rows])**2))-np.sqrt(np.mean((cand[rows]-Y[rows])**2)))
    g=np.array(g)
    d_=np.array([np.sqrt(np.mean((ref[idxw[w]]-Y[idxw[w]])**2))-np.sqrt(np.mean((cand[idxw[w]]-Y[idxw[w]])**2)) for w in uw])
    print(f"  [{tag}] bootstrap(400): mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} frac>0={100*np.mean(g>0):.0f}%"
          f" | wells helped {100*np.mean(d_>0):.1f}% hurt {100*np.mean(d_<0):.1f}% median {np.median(d_):+.3f}")
print("\nGATE: >= +0.10 with stably positive bootstrap.")
