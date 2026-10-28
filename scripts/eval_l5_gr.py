"""Evaluate the L5 GR-weighted structural field against the geometry-only (L4) field on the smoke subset."""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/l5_gr_struct_smoke.npz',allow_pickle=True)
lw=z['well'].astype(str); geo=z['geo'].astype(float)
SIG=[k[4:] for k in z.files if k.startswith('gr_s')]
dz=np.load(f'{SH}/decomp_features.npz',allow_pickle=True)
dw=dz['well'].astype(str)
di=defaultdict(list); li=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(lw): li[w].append(i)
B,T,G,W={},{},{},{}
Bl,Tl,Gl,Wl=[],[],[],[]; Sl={s:[] for s in SIG}
for w in sorted(set(dw)&set(lw)):
    a=np.array(di[w]); b=np.array(li[w])
    if len(a)!=len(b): continue
    Bl.append(dz['blend'][a].astype(float)); Tl.append(dz['truth'][a].astype(float))
    Gl.append(geo[b]); Wl.append(np.full(len(a),w))
    for s in SIG: Sl[s].append(z[f'gr_s{s}'][b].astype(float))
base=np.concatenate(Bl); Y=np.concatenate(Tl); gv=np.concatenate(Gl); well=np.concatenate(Wl)
S={s:np.concatenate(Sl[s]) for s in SIG}
rmse=lambda p:float(np.sqrt(np.mean((p-Y)**2)))
uw=np.array(sorted(set(well)))
print(f"smoke subset: rows={len(Y)} wells={len(uw)}")
print(f"  base(DWT+PF)={rmse(base):.4f}  geo-only struct standalone={rmse(gv):.4f}")
for s in SIG: print(f"  GR-weighted sigma={s:>4} standalone={rmse(S[s]):.4f}")
def halves(seed):
    rg=np.random.RandomState(seed); sh=uw.copy(); rg.shuffle(sh)
    g0=set(sh[:len(sh)//2]); inA=np.array([w in g0 for w in well]); return [(inA,~inA),(~inA,inA)]
def nested(field,lab):
    outs=[]
    for seed in range(3):
        p=base.copy()
        for tr,te in halves(seed):
            d=(field-base)[tr]
            c=float(np.clip(np.dot(d,(Y-base)[tr])/max(np.dot(d,d),1e-9),0,1))
            p[te]=base[te]+c*(field[te]-base[te])
        outs.append(rmse(p))
    r=float(np.mean(outs)); print(f"  {lab:34s} nested={r:.4f}  gain vs base {rmse(base)-r:+.4f}")
    return r
print("\nnested weight fit (subset, 3 seeds):")
rg_=nested(gv,"geometry-only (L4 A=50)")
best=(None,np.inf)
for s in SIG:
    r=nested(S[s],f"GR-weighted sigma={s}")
    if r<best[1]: best=(s,r)
print(f"\n  best GR sigma={best[0]}  nested={best[1]:.4f}   INCREMENT vs geometry-only {rg_-best[1]:+.4f}")
# decorrelation: does GR weighting produce a DIFFERENT error direction?
eg=gv-Y; es=S[best[0]]-Y; eb=base-Y
print(f"\n  corr(err_geo, err_GRweighted) = {np.corrcoef(eg,es)[0,1]:+.4f}")
print(f"  corr(err_base, err_geo)       = {np.corrcoef(eb,eg)[0,1]:+.4f}")
print(f"  corr(err_base, err_GRweighted)= {np.corrcoef(eb,es)[0,1]:+.4f}")
print("\n  two-field nested (base + geo + GRweighted, 2 coefficients):")
outs=[]
for seed in range(3):
    p=base.copy()
    for tr,te in halves(seed):
        Xm=np.column_stack([(gv-base)[tr],(S[best[0]]-base)[tr]])
        try: c,_,_,_=np.linalg.lstsq(Xm,(Y-base)[tr],rcond=None)
        except Exception: c=np.zeros(2)
        c=np.clip(c,0,1)
        p[te]=base[te]+c[0]*(gv[te]-base[te])+c[1]*(S[best[0]][te]-base[te])
    outs.append(rmse(p))
print(f"     nested={np.mean(outs):.4f}   vs geometry-only {rg_-np.mean(outs):+.4f}")
print("\nHEADROOM CHECK: GR weighting must add materially over geometry-only to justify a full run.")
