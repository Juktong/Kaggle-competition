"""Task 1: is 54878409's (A=50, W=0.25, gate closest_surv<1000) a stable plateau or a lucky point?

Grid: A in {20,50,100} x W in {0.20,0.25,0.30} x gate in {800,1000,1200}. All nested by well.
Also runs a joint nested (A,W,gate) selection so the honest procedure -- not the table -- picks.
Visible-well RMSE uses the 3 real test wells, which are also train wells, via their OOF rows.
"""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
s1f=np.load(f'{SH}/struct_aniso_surv.npz',allow_pickle=True)
s2f=np.load(f'{SH}/struct_aniso_surv2.npz',allow_pickle=True)
assert (s1f['well'].astype(str)==s2f['well'].astype(str)).all(), "row order mismatch"
aw=s1f['well'].astype(str)
F={'1':s1f['struct_a1'],'50':s1f['struct_a50'],'20':s2f['struct_a20'],'100':s2f['struct_a100']}
nnb=dict(zip(s1f['meta_well'].astype(str),s1f['meta_nnb'].astype(int)))
csv_=dict(zip(s1f['meta_well'].astype(str),s1f['meta_closest_surv'].astype(float)))
call=dict(zip(s1f['meta_well'].astype(str),s1f['meta_closest'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(aw): si[w].append(i)
Bl,Tl,Wl={},{},{}; Bl,Tl,Wl=[],[],[]; Sl={k:[] for k in F}
for w in sorted(set(dw)&set(aw)):
    a=np.array(di[w]); b=np.array(si[w])
    if len(a)!=len(b): continue
    Bl.append(dc['blend'][a].astype(float)); Tl.append(dc['truth'][a].astype(float)); Wl.append(np.full(len(a),w))
    for k in F: Sl[k].append(F[k][b].astype(float))
base=np.concatenate(Bl); Y=np.concatenate(Tl); well=np.concatenate(Wl)
S={k:np.concatenate(Sl[k]) for k in F}
nnbv=np.array([nnb.get(w,0) for w in well],float)
csvv=np.array([csv_.get(w,np.nan) for w in well],float)
callv=np.array([call.get(w,np.nan) for w in well],float)
rmse=lambda p:float(np.sqrt(np.mean((p-Y)**2)))
uw=np.array(sorted(set(well))); idxw={w:np.where(well==w)[0] for w in uw}
dep=base.copy(); gdep=(nnbv>=4)&(callv<1000)&np.isfinite(callv)
dep[gdep]=0.85*base[gdep]+0.15*S['1'][gdep]
r0=rmse(dep)
VIS=['000d7d20','00bbac68','00e12e8b']
visrows=np.concatenate([idxw[w] for w in VIS if w in idxw])
print(f"rows={len(Y)} wells={len(uw)}  deployed(A=1,W=.15)={r0:.4f}  visible wells present={sum(w in idxw for w in VIS)}")
print(f"deployed visible-well pooled RMSE = {np.sqrt(np.mean((dep[visrows]-Y[visrows])**2)):.4f}\n")
def build(A,W,GT):
    g=(nnbv>=4)&(csvv<GT)&np.isfinite(csvv)
    p=base.copy(); p[g]=(1-W)*base[g]+W*S[A][g]
    return p,g
def boot(p,n=400):
    rb=np.random.RandomState(7); gg=[]
    for _ in range(n):
        samp=uw[rb.randint(0,len(uw),len(uw))]
        rows=np.concatenate([idxw[w] for w in samp])
        gg.append(np.sqrt(np.mean((dep[rows]-Y[rows])**2))-np.sqrt(np.mean((p[rows]-Y[rows])**2)))
    return np.array(gg)
print(f"{'A':>4} {'W':>5} {'gate':>5} | {'OOF':>8} {'gain':>8} | {'boot5th':>8} {'frac>0':>6} | {'cov%':>5} {'vis':>7} {'twin39':>8}")
rows=[]
twin=(callv<150)
for A in ['20','50','100']:
    for W in [0.20,0.25,0.30]:
        for GT in [800.,1000.,1200.]:
            p,g=build(A,W,GT); r=rmse(p); gg=boot(p)
            vis=float(np.sqrt(np.mean((p[visrows]-Y[visrows])**2)))
            tw_m=g&twin
            tgain=(np.sqrt(np.mean((dep[tw_m]-Y[tw_m])**2))-np.sqrt(np.mean((p[tw_m]-Y[tw_m])**2))) if tw_m.sum()>0 else float('nan')
            rows.append((A,W,GT,r,r0-r,float(np.percentile(gg,5)),float(np.mean(gg>0)),100*g.mean(),vis,tgain))
            mark=' <== 54878409' if (A=='50' and abs(W-0.25)<1e-9 and GT==1000.) else ''
            print(f"{A:>4} {W:>5.2f} {GT:>5.0f} | {r:>8.4f} {r0-r:>+8.4f} | {np.percentile(gg,5):>+8.4f} {100*np.mean(gg>0):>5.0f}% | {100*g.mean():>4.1f} {vis:>7.4f} {tgain:>+8.4f}{mark}",flush=True)
print("\n=== joint NESTED (A,W,gate) selection: chosen on training-half wells, applied to held-out half ===")
outs=[];picks=[]
for seed in range(6):
    rg=np.random.RandomState(seed); sh=uw.copy(); rg.shuffle(sh)
    half=set(sh[:len(sh)//2]); inA=np.array([w in half for w in well])
    tot=n=0.0
    for tr,te in [(inA,~inA),(~inA,inA)]:
        best=(np.inf,None)
        for A in ['20','50','100']:
            for W in [0.20,0.25,0.30]:
                for GT in [800.,1000.,1200.]:
                    p,_=build(A,W,GT); s=float(np.mean((p[tr]-Y[tr])**2))
                    if s<best[0]: best=(s,(A,W,GT))
        picks.append(best[1])
        p,_=build(*best[1]); tot+=float(np.sum((p[te]-Y[te])**2)); n+=int(te.sum())
    outs.append(np.sqrt(tot/n))
from collections import Counter
print(f"  picks: {Counter(picks).most_common(4)}")
print(f"  NESTED (A,W,gate) = {np.mean(outs):.4f}   gain vs deployed {r0-np.mean(outs):+.4f}")
sub=[r for r in rows if r[0]=='50' and abs(r[1]-0.25)<1e-9 and r[2]==1000.][0]
bестgrid=min(rows,key=lambda r:r[3])
print(f"\n  54878409 config  : OOF {sub[3]:.4f} gain {sub[4]:+.4f} boot5th {sub[5]:+.4f} frac>0 {100*sub[6]:.0f}%")
print(f"  best grid config : A={bестgrid[0]} W={bестgrid[1]} gate={bестgrid[2]:.0f} OOF {bестgrid[3]:.4f} gain {bестgrid[4]:+.4f} boot5th {bестgrid[5]:+.4f}")
print(f"  spread of gain across all 27 configs: {min(r[4] for r in rows):+.4f} .. {max(r[4] for r in rows):+.4f}")
