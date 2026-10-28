"""Task 2: does swapping the PF component for the K=96 likelihood-weighted mean add on top of L4?

The K=96 top-K RANKER did not pass the gate (bootstrap 5th negative, no constructible guard), but the
pure seeds-only effect (K24 -> K96 PF weighted mean, no ranker, no new model) was +0.0228 on the
isotropic deployed pipeline. This tests whether that seeds-only effect survives ON TOP of the
anisotropic field already submitted as 54878409.

Reference points (all on the same aligned row set):
  deployed 54844628 : 0.5*DWT + 0.5*PF_K24, isotropic struct W=0.15
  submitted 54878409: 0.5*DWT + 0.5*PF_K24, aniso A=50 struct W=0.25, gate closest_surv<1000
  candidate         : 0.5*DWT + 0.5*PF_K96, aniso A=50 struct W=0.25, same gate
"""
import os, glob, numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
sv=np.load(f'{SH}/struct_aniso_surv.npz',allow_pickle=True)
sw=sv['well'].astype(str); sr=sv['ridx'].astype(int)
s1=sv['struct_a1'].astype(np.float32); s50=sv['struct_a50'].astype(np.float32)
nnb=dict(zip(sv['meta_well'].astype(str),sv['meta_nnb'].astype(int)))
csv_=dict(zip(sv['meta_well'].astype(str),sv['meta_closest_surv'].astype(float)))
call=dict(zip(sv['meta_well'].astype(str),sv['meta_closest'].astype(float)))
si=defaultdict(list)
for i,w in enumerate(sw): si[w].append(i)

# K96 store: per-well arrays in toe order
store={}
for f in glob.glob(f'{SH}/topk96_paths/*.npz'):
    w=os.path.basename(f)[:-4]; z=np.load(f)
    store[w]=(z['mean'].astype(np.float64), z['dwt'].astype(np.float64), z['truth'].astype(np.float64))
print(f"K96 wells={len(store)}  struct wells={len(si)}",flush=True)

# K24 decomp (the pipeline actually deployed)
dz=np.load(f'{SH}/decomp_features.npz',allow_pickle=True)
dw=dz['well'].astype(str); ddwt=dz['dwt']; dpf=dz['pf']; dtru=dz['truth']
di=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)

W,PF24,PF96,DWT,Y,S1,S50=[],[],[],[],[],[],[]
skip_len=0
for w in sorted(set(si)&set(store)&set(di)):
    a=np.array(di[w]); b=np.array(si[w]); m96,d96,t96=store[w]
    if not (len(a)==len(b)==len(m96)):
        skip_len+=1; continue
    # consistency: the K96 dump's dwt/truth must match the decomp arrays for the same well
    if np.max(np.abs(d96-ddwt[a].astype(np.float64)))>1e-3: skip_len+=1; continue
    W.append(np.full(len(a),w)); PF24.append(dpf[a].astype(np.float64)); PF96.append(m96)
    DWT.append(ddwt[a].astype(np.float64)); Y.append(dtru[a].astype(np.float64))
    S1.append(s1[b].astype(np.float64)); S50.append(s50[b].astype(np.float64))
well=np.concatenate(W); pf24=np.concatenate(PF24); pf96=np.concatenate(PF96)
dwt=np.concatenate(DWT); Yv=np.concatenate(Y); st1=np.concatenate(S1); st50=np.concatenate(S50)
print(f"aligned rows={len(Yv)} wells={len(set(well))} skipped_wells={skip_len}",flush=True)
nnbv=np.array([nnb.get(w,0) for w in well],float)
csvv=np.array([csv_.get(w,np.nan) for w in well],float)
callv=np.array([call.get(w,np.nan) for w in well],float)
gate_new=(nnbv>=4)&(csvv<1000)&np.isfinite(csvv)
gate_old=(nnbv>=4)&(callv<1000)&np.isfinite(callv)
rmse=lambda p:float(np.sqrt(np.mean((p-Yv)**2)))
uw=np.array(sorted(set(well))); idxw={w:np.where(well==w)[0] for w in uw}
b24=0.5*dwt+0.5*pf24; b96=0.5*dwt+0.5*pf96
print(f"\nPF component alone: K24={rmse(pf24):.4f}  K96={rmse(pf96):.4f}")
print(f"base:               K24={rmse(b24):.4f}  K96={rmse(b96):.4f}  seeds-only {rmse(b24)-rmse(b96):+.4f}")
dep=b24.copy(); dep[gate_old]=0.85*b24[gate_old]+0.15*st1[gate_old]
sub=b24.copy(); sub[gate_new]=0.75*b24[gate_new]+0.25*st50[gate_new]
cnd=b96.copy(); cnd[gate_new]=0.75*b96[gate_new]+0.25*st50[gate_new]
r_dep,r_sub,r_cnd=rmse(dep),rmse(sub),rmse(cnd)
print(f"\ndeployed 54844628 (iso W.15, K24) = {r_dep:.4f}")
print(f"submitted 54878409 (A50 W.25, K24) = {r_sub:.4f}   gain vs deployed {r_dep-r_sub:+.4f}")
print(f"candidate  L4+K96  (A50 W.25, K96) = {r_cnd:.4f}   gain vs deployed {r_dep-r_cnd:+.4f}")
print(f"                                        INCREMENT vs 54878409 {r_sub-r_cnd:+.4f}")
def boot(cand,ref,lab,n=1000):
    rb=np.random.RandomState(7); g=[]
    for _ in range(n):
        samp=uw[rb.randint(0,len(uw),len(uw))]
        rows=np.concatenate([idxw[w] for w in samp])
        g.append(np.sqrt(np.mean((ref[rows]-Yv[rows])**2))-np.sqrt(np.mean((cand[rows]-Yv[rows])**2)))
    g=np.array(g)
    d_=np.array([np.sqrt(np.mean((ref[idxw[w]]-Yv[idxw[w]])**2))-np.sqrt(np.mean((cand[idxw[w]]-Yv[idxw[w]])**2)) for w in uw])
    print(f"  [{lab}] boot mean={g.mean():+.4f} 5th={np.percentile(g,5):+.4f} frac>0={100*np.mean(g>0):.0f}%"
          f" | helped={100*np.mean(d_>1e-9):.1f}% worst={d_.min():+.2f}")
    return float(np.percentile(g,5))
print("\nbootstrap:")
boot(cnd,dep,"L4+K96 vs deployed")
b5=boot(cnd,sub,"L4+K96 vs 54878409  <-- the decision-relevant one")
print(f"\nGATE for a NEW submission while 54878409 is pending:")
print(f"  needs stable increment over 54878409 (bootstrap 5th > 0): {'MEETS' if (r_sub-r_cnd)>0 and b5>0 else 'DOES NOT MEET'}")
