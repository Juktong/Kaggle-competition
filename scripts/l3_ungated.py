"""Proposal L3: a separate, conservative structural path for the 12.7% currently-UNGATED rows.

Deployed: gated rows get 0.85*base + 0.15*struct; ungated rows get base only (no structural info).
A blanket weight was previously shown to be harmful (<=3-mate wells 10.19 -> 15.61), which is why the
gate exists. This tests a SEPARATELY tuned, nested-fit weight applied only to ungated rows, so the
gated majority is untouched by construction and the downside is bounded.
"""
import os, numpy as np
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/decomp_features.npz',allow_pickle=True); dc={k:z[k] for k in z.files}
dw=dc['well'].astype(str)
rd=np.load(f'{SH}/struct_oof_rowdist.npz',allow_pickle=True)
rw=rd['well'].astype(str); rs=rd['struct'].astype(float); nn=rd['nn_dist'].astype(float)
nnb=dict(zip(rd['meta_well'].astype(str),rd['meta_nnb'].astype(int)))
cl=dict(zip(rd['meta_well'].astype(str),rd['meta_closest'].astype(float)))
di=defaultdict(list); si=defaultdict(list)
for i,w in enumerate(dw): di[w].append(i)
for i,w in enumerate(rw): si[w].append(i)
B,S,T,W,N=[],[],[],[],[]
for w in sorted(set(dw)&set(rw)):
    a=np.array(di[w]); b=np.array(si[w])
    if len(a)!=len(b): continue
    B.append(dc['blend'][a].astype(float)); S.append(rs[b]); T.append(dc['truth'][a].astype(float))
    W.append(np.full(len(a),w)); N.append(nn[b])
base=np.concatenate(B); st=np.concatenate(S); Y=np.concatenate(T); well=np.concatenate(W); nnd=np.concatenate(N)
nnbv=np.array([nnb.get(w,0) for w in well],float); clov=np.array([cl.get(w,np.nan) for w in well],float)
gate=(nnbv>=4)&(clov<1000)&np.isfinite(clov)
cur=base.copy(); cur[gate]=0.85*base[gate]+0.15*st[gate]
rmse=lambda a:float(np.sqrt(np.mean((a-Y)**2)))
ung=~gate
uw=np.array(sorted(set(well)))
print(f"rows={len(Y)} ungated={100*ung.mean():.1f}% ({ung.sum()} rows, {len(set(well[ung]))} wells)")
print(f"deployed={rmse(cur):.4f}")
print(f"  on UNGATED rows only: base RMSE={np.sqrt(np.mean((base[ung]-Y[ung])**2)):.4f}  struct RMSE={np.sqrt(np.mean((st[ung]-Y[ung])**2)):.4f}")
def halves(seed):
    rg=np.random.RandomState(seed); sh=uw.copy(); rg.shuffle(sh)
    g0=set(sh[:len(sh)//2]); inA=np.array([w in g0 for w in well])
    return [(inA,~inA),(~inA,inA)]
print("\nfixed small weights on ungated rows (full-data, for shape):")
for Wt in [0.02,0.05,0.10,0.15]:
    p=cur.copy(); p[ung]=(1-Wt)*base[ung]+Wt*st[ung]
    print(f"  W={Wt:.2f}: {rmse(p):.4f}  gain {rmse(cur)-rmse(p):+.4f}")
print("\nNESTED weight fit on ungated rows only (fit half the wells, apply to held-out half):")
outs=[];lams=[]
for seed in range(3):
    p=cur.copy()
    for tr,te in halves(seed):
        m=tr&ung
        if m.sum()<500: continue
        d=(st-base)[m]; a=float(np.clip(np.dot(d,(Y-base)[m])/max(np.dot(d,d),1e-9),0,1))
        lams.append(a); ap=te&ung; p[ap]=base[ap]+a*(st[ap]-base[ap])
    outs.append(rmse(p))
print(f"  fitted weight (mean) = {np.mean(lams):.4f}")
print(f"  NESTED = {np.mean(outs):.4f}   gain {rmse(cur)-np.mean(outs):+.4f}")
print("\nsub-gate refinement: ungated rows that are still reasonably close to a mate")
for T2 in [1500,2000,3000]:
    sub=ung&(clov<T2)&np.isfinite(clov)
    if sub.sum()<1000: continue
    outs=[]
    for seed in range(3):
        p=cur.copy()
        for tr,te in halves(seed):
            m=tr&sub
            if m.sum()<500: continue
            d=(st-base)[m]; a=float(np.clip(np.dot(d,(Y-base)[m])/max(np.dot(d,d),1e-9),0,1))
            ap=te&sub; p[ap]=base[ap]+a*(st[ap]-base[ap])
        outs.append(rmse(p))
    print(f"  closest<{T2}: rows={100*sub.mean():.1f}%  NESTED={np.mean(outs):.4f}  gain {rmse(cur)-np.mean(outs):+.4f}")
print("\nGATE: >= +0.10 with stably positive bootstrap.")
