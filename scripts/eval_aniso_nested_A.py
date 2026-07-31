"""Decisive honesty test for L4: nest the choice of ANISOTROPY A (and W) as well.

A=20 was picked by reading the full-data table -- the same 'a sweep is not a validation' failure that
was used to reject direction 2's lam=0.25. Here BOTH A and W are selected on training-half wells and
applied to the held-out half, so nothing is chosen using the rows it is scored on.
"""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
lo=np.load(f'{SH}/struct_aniso.npz',allow_pickle=True); hi=np.load(f'{SH}/struct_aniso_hi.npz',allow_pickle=True)
aw=lo['well'].astype(str)
fields={}
for src in (lo,hi):
    for k in src.files:
        if k.startswith('struct_a'): fields.setdefault(k[8:], src[k].astype(np.float32))
ANIS=sorted(fields,key=float)
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
uw=np.array(sorted(set(well))); idxw={w:np.where(well==w)[0] for w in uw}
ref=base.copy(); ref[gate]=0.85*base[gate]+0.15*S['1'][gate]
r0=rmse(ref); print(f"deployed (A=1,W=.15) = {r0:.4f}\n")
WGRID=[0.15,0.20,0.25,0.30,0.35]
def sse_of(a,Wt,mask):
    p=base[mask].copy(); g=gate[mask]
    p[g]=(1-Wt)*base[mask][g]+Wt*S[a][mask][g]
    return float(np.sum((p-Y[mask])**2)), int(mask.sum())
print("=== NESTED (A, W) selection: both chosen on training-half wells, applied to held-out half ===")
allouts=[]; picks=[]
for seed in range(6):
    rg=np.random.RandomState(seed); sh=uw.copy(); rg.shuffle(sh)
    half=set(sh[:len(sh)//2]); inA=np.array([w in half for w in well])
    tot=n=0.0
    for tr,te in [(inA,~inA),(~inA,inA)]:
        bs,bA,bW=np.inf,None,None
        for a in ANIS:
            for Wt in WGRID:
                s,m=sse_of(a,Wt,tr)
                if s/m<bs: bs,bA,bW=s/m,a,Wt
        picks.append((bA,bW))
        s,m=sse_of(bA,bW,te); tot+=s; n+=m
    allouts.append(np.sqrt(tot/n))
nested=float(np.mean(allouts))
from collections import Counter
print(f"  (A,W) picks: {Counter(picks).most_common()}")
print(f"  NESTED (A,W) result = {nested:.4f}   gain vs deployed {r0-nested:+.4f}")
print(f"  per-seed: {np.round(allouts,4)}")
shipA,shipW=Counter(picks).most_common(1)[0][0]
print(f"\n  deployable config: A={shipA}, W={shipW}")
ship=base.copy(); ship[gate]=(1-shipW)*base[gate]+shipW*S[shipA][gate]
print(f"  full-data RMSE of that fixed config = {rmse(ship):.4f}  gain {r0-rmse(ship):+.4f}")
rb=np.random.RandomState(7); g=[]
for _ in range(1000):
    samp=uw[rb.randint(0,len(uw),len(uw))]
    rows=np.concatenate([idxw[w] for w in samp])
    g.append(np.sqrt(np.mean((ref[rows]-Y[rows])**2))-np.sqrt(np.mean((ship[rows]-Y[rows])**2)))
g=np.array(g)
print(f"  bootstrap(1000): mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} 1st={np.percentile(g,1):+.4f} frac>0={100*np.mean(g>0):.0f}%")
d_=np.array([np.sqrt(np.mean((ref[idxw[w]]-Y[idxw[w]])**2))-np.sqrt(np.mean((ship[idxw[w]]-Y[idxw[w]])**2)) for w in uw])
print(f"  per-well: helped {100*np.mean(d_>1e-9):.1f}% hurt {100*np.mean(d_<-1e-9):.1f}% median(gated) {np.median(d_[np.abs(d_)>1e-9]):+.3f}")
print(f"  worst 5 wells: {np.round(np.sort(d_)[:5],2)}  best 5: {np.round(np.sort(d_)[-5:],2)}")
meets=(r0-nested)>=0.10 and np.percentile(g,5)>0
print(f"\n  GATE (+0.10 AND stably positive bootstrap): {'MEETS' if meets else 'DOES NOT MEET'}")
