"""Probe 1: row-level structural weighting (deployed gate is per-WELL only). Saved artifacts only."""
import numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
st=np.load(f'{SH}/struct_oof.npz',allow_pickle=True)
sw=st['well'].astype(str); ss=st['struct'].astype(np.float64)
nnb=dict(zip(st['meta_well'].astype(str),st['meta_nnb'].astype(int)))
cl=dict(zip(st['meta_well'].astype(str),st['meta_closest'].astype(float)))
dc=np.load(f'{SH}/decomp_features.npz',allow_pickle=True)
dw=dc['well'].astype(str)
dcidx=defaultdict(list); sidx=defaultdict(list)
for i,w in enumerate(dw): dcidx[w].append(i)
for i,w in enumerate(sw): sidx[w].append(i)
D_,P_,B_,Y_,S_,TD_,RF_,W_=[],[],[],[],[],[],[],[]
for w in sorted(set(sw)&set(dw)):
    di=np.array(dcidx[w]); si=np.array(sidx[w])
    if len(di)!=len(si): continue
    B_.append(dc['blend'][di].astype(float)); Y_.append(dc['truth'][di].astype(float))
    S_.append(ss[si]); TD_.append(dc['toe_dist_md'][di].astype(float)); RF_.append(dc['row_frac'][di].astype(float))
    W_.append(np.full(len(di),w))
B_=np.concatenate(B_);Y_=np.concatenate(Y_);S_=np.concatenate(S_)
TD_=np.concatenate(TD_);RF_=np.concatenate(RF_);W_=np.concatenate(W_)
base=B_; rmse=lambda a: float(np.sqrt(np.mean((a-Y_)**2)))
gate=np.array([(nnb.get(w,0)>=4) and np.isfinite(cl.get(w,np.nan)) and cl.get(w,1e9)<1000 for w in W_])
print(f"rows={len(Y_)} wells={len(set(W_))} gated={100*gate.mean():.1f}%",flush=True)
flat=base.copy(); flat[gate]=0.85*base[gate]+0.15*S_[gate]
print(f"  deployed flat W=0.15 : {rmse(flat):.4f}",flush=True)
eS=np.abs(S_-Y_); eB=np.abs(base-Y_)
print("  struct vs base error by row_frac quartile (gated):",flush=True)
for lo,hi in [(0,.25),(.25,.5),(.5,.75),(.75,1.01)]:
    m=gate&(RF_>=lo)&(RF_<hi)
    if m.sum()>1000: print(f"    rf[{lo:.2f},{hi:.2f}) n={m.sum():>8d} struct={np.sqrt(np.mean(eS[m]**2)):6.2f} base={np.sqrt(np.mean(eB[m]**2)):6.2f}",flush=True)
uw=np.array(sorted(set(W_)))
def nested(wv,label):
    outs=[]
    for seed in range(3):
        rng=np.random.RandomState(seed); sh=uw.copy(); rng.shuffle(sh)
        g0=set(sh[:len(sh)//2]); inA=np.array([w in g0 for w in W_])
        pred=base.copy()
        for tr,te in [(inA,~inA),(~inA,inA)]:
            m=tr&gate
            if m.sum()<500: continue
            d=(S_-base)*wv
            a=float(np.clip(np.dot(d[m],(Y_-base)[m])/max(np.dot(d[m],d[m]),1e-9),0,3))
            ap=te&gate; pred[ap]=base[ap]+a*wv[ap]*(S_[ap]-base[ap])
        outs.append(rmse(pred))
    print(f"    {label:44s} {np.mean(outs):.4f}",flush=True)
print("  row-level schedules (nested scalar per schedule):",flush=True)
nested(np.full(len(Y_),0.15),'flat 0.15 (refit scalar)')
nested(np.clip(1.0-RF_,0,1)*0.3,'decay with row_frac (heavier near heel)')
nested(np.clip(RF_,0,1)*0.3,'grow with row_frac (heavier at toe)')
nested(np.full(len(Y_),0.15)*(1.0/(1.0+TD_/5000.0)),'decay with toe MD distance')
print("\n=> a schedule must beat the flat refit materially to justify a row-level gate.",flush=True)
