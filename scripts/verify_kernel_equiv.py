"""Equivalence check: does the PATCHED KERNEL cell-27 logic reproduce the validated producer?

Runs the kernel's inference code path on TRAIN wells used as pseudo-targets (self excluded from mates,
exactly as the producer does) and compares against struct_aniso_hi.npz A=50, row for row.
"""
import os, glob, json, numpy as np, pandas as pd
from collections import defaultdict as _dd
from scipy.spatial import cKDTree as _cKDTree
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
STRUCT_W=0.25; MIN_NB=4; MAX_CLOSEST=1000.0; MIN_SEP=150.0; K_NB=12; ANCHOR_N=100; ANISO=50.0
NW=int(os.environ.get('NW','25'))

def _gkey(p):
    t=pd.read_csv(p,usecols=['TVT']); return round(float(np.nanmax(t['TVT'].values)),1)
_tr_gkey={}
for _f in sorted(glob.glob(f'{D}/*__typewell.csv')):
    try: _tr_gkey[os.path.basename(_f).split('__')[0]]=_gkey(_f)
    except Exception: pass
_tr_groups=_dd(list)
for _w,_k in _tr_gkey.items(): _tr_groups[_k].append(_w)
_trc={}
def _tr(w):
    if w not in _trc: _trc[w]=pd.read_csv(f'{D}/{w}__horizontal_well.csv',usecols=['X','Y','Z','TVT'])
    return _trc[w]
_trtree={}
def _tr_tree(w):
    if w not in _trtree:
        h=_tr(w); _trtree[w]=_cKDTree(np.column_stack([h['X'].values,h['Y'].values]))
    return _trtree[w]

ref=np.load(f'{SH}/struct_aniso_hi.npz',allow_pickle=True)
rw=ref['well'].astype(str); rr=ref['ridx'].astype(int); rv=ref['struct_a50'].astype(float)
refmap=_dd(dict)
for w,r,v in zip(rw,rr,rv): refmap[w][int(r)]=v

targets=sorted(refmap.keys())[:NW]
maxdiff=0.0; nrows=0; nwells=0; gated_off=0
for wid in targets:
    hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv')
    gk=_tr_gkey.get(wid)
    mates=[m for m in _tr_groups.get(gk,[]) if m!=wid]      # self excluded, as the producer does
    kn=hw['TVT_input'].notna().values
    if kn.sum()<ANCHOR_N or not mates: continue
    X=hw['X'].values; Y=hw['Y'].values; Z=hw['Z'].values; txy=np.column_stack([X,Y])
    px,py,pr,seps,surv_seps=[],[],[],[],[]
    for m in mates:
        try: mh=_tr(m)
        except Exception: continue
        if len(mh)<5: continue
        d,_=_tr_tree(m).query(txy[::10],k=1); sep=float(np.median(d)); seps.append(sep)
        if sep<MIN_SEP: continue
        rrv=mh['TVT'].values+mh['Z'].values; ok=np.isfinite(rrv)
        px.append(mh['X'].values[ok][::4]); py.append(mh['Y'].values[ok][::4]); pr.append(rrv[ok][::4]); surv_seps.append(sep)
    _closest=float(min(surv_seps)) if surv_seps else float('nan')
    if not px: continue
    if len(px)<MIN_NB or not np.isfinite(_closest) or _closest>=MAX_CLOSEST:
        gated_off+=1; continue
    PX=np.concatenate(px); PY=np.concatenate(py); PR=np.concatenate(pr)
    _Amat=np.column_stack([np.ones(len(PX)),PX-PX.mean(),PY-PY.mean()])
    try:
        _co=np.linalg.solve(_Amat.T@_Amat+1e-6*np.eye(3),_Amat.T@PR); _gx,_gy=float(_co[1]),float(_co[2])
    except Exception: _gx,_gy=0.0,0.0
    _gn=np.hypot(_gx,_gy)
    _u=np.array([1.0,0.0]) if _gn<1e-12 else np.array([_gx,_gy])/_gn
    _v=np.array([-_u[1],_u[0]]); _P=np.column_stack([PX,PY])
    _Pt=np.column_stack([_P@_u,(_P@_v)/ANISO]); _Tt=np.column_stack([txy@_u,(txy@_v)/ANISO])
    dd,ii=_cKDTree(_Pt).query(_Tt,k=min(K_NB,len(PR)))
    if dd.ndim==1: dd=dd[:,None]; ii=ii[:,None]
    wg=1.0/(dd+1.0); r_pred=(wg*PR[ii]).sum(1)/wg.sum(1)
    kn_idx=np.where(kn)[0][-ANCHOR_N:]
    anchor=float(np.nanmean(hw['TVT_input'].values[kn_idx]+Z[kn_idx]-r_pred[kn_idx]))
    pred=r_pred+anchor-Z
    common=[r for r in refmap[wid] if r<len(pred)]
    if not common: continue
    dv=np.array([abs(np.float32(pred[r])-np.float32(refmap[wid][r])) for r in common])  # producer stores float32
    maxdiff=max(maxdiff,float(dv.max())); nrows+=len(common); nwells+=1
print(f"wells compared={nwells}  rows={nrows}  gated_off={gated_off}")
print(f"MAX |kernel_logic - validated_producer| = {maxdiff:.8f} ft")
print("EQUIVALENT (float32-exact)" if maxdiff==0.0 else ("EQUIVALENT within float32 storage precision" if maxdiff<2e-3 else "MISMATCH -- do not submit"))
print(f"  float32 resolution at TVT~8000ft = {8000*2**-23:.6f} ft")
