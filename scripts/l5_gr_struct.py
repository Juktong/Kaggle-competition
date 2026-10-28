"""L5 mini-smoke: GR-WEIGHTED cross-well structural field.

Data audit (2026-07-21) established the only test-available channels are {MD,X,Y,Z,GR,TVT_input} plus
typewell {TVT,GR}. So a third decorrelated forward model must be a DIFFERENT COMPUTATION over those,
not new data. The current structural field uses ONLY geometry: IDW over group-mates' r = TVT+Z at
matched XY. It never looks at the mates' GR.

Idea: two horizontal wells at the same structural level should read similar GR. Weight each mate point
by BOTH anisotropic XY proximity AND GR agreement with the target row:

    w = 1/(d_aniso + 1) * exp(-(gr_target - gr_mate)^2 / (2*sigma^2))

Honest: target GR is test-available; mate GR and mate TVT come from TRAIN wells. Same MIN_SEP guard,
same group key, same heel anchor.
Env: MAXW, ANISO, SIGMA, K, OUT.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
K=int(os.environ.get('K','12')); ANCHOR=100; MIN_SEP=150.0
MAXW=int(os.environ.get('MAXW','60')); ANISO=float(os.environ.get('ANISO','50'))
SIGMAS=[float(x) for x in os.environ.get('SIGMAS','10,20,40').split(',')]
OUT=os.environ.get('OUT', f'{SH}/l5_gr_struct_smoke.npz')
KSEL=int(os.environ.get('KSEL','60'))   # candidate pool before GR re-weighting

cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM=cs['is_toe']
dwell=cs['well'][tM].astype(str); dr=cs['ridx'][tM].astype(int)
toe=defaultdict(set)
for w,r in zip(dwell,dr): toe[w].add(int(r))
del cs
gkey={}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid=os.path.basename(f).split('__')[0]
    try: gkey[wid]=round(float(np.nanmax(pd.read_csv(f,usecols=['TVT'])['TVT'].values)),1)
    except Exception: pass
groups=defaultdict(list)
for w,k in gkey.items(): groups[k].append(w)
cache={}
def get(w):
    if w not in cache:
        cache[w]=pd.read_csv(f'{D}/{w}__horizontal_well.csv',usecols=['X','Y','Z','TVT','TVT_input','GR'])
    return cache[w]
_t={}
def tree_of(w):
    if w not in _t:
        h=get(w); _t[w]=cKDTree(np.column_stack([h['X'].values,h['Y'].values]))
    return _t[w]

targets=sorted(toe.keys())[:MAXW]
OW,OR=[],[]
OG={s:[] for s in SIGMAS}; OBASE=[]
for n,wid in enumerate(targets):
    if n%20==0: print(f'  [{n}/{len(targets)}]',flush=True)
    if wid not in gkey: continue
    try: hw=get(wid)
    except Exception: continue
    kn=hw['TVT_input'].notna().values
    if kn.sum()<ANCHOR: continue
    ridx=np.array(sorted(toe[wid]))
    if len(ridx)<10: continue
    X=hw['X'].values; Y=hw['Y'].values; Z=hw['Z'].values
    GRt=pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    txy=np.column_stack([X,Y])
    px,py,pr,pg=[],[],[],[]
    for m in groups.get(gkey[wid],[]):
        if m==wid: continue
        try: mh=get(m)
        except Exception: continue
        if len(mh)<5: continue
        d,_=tree_of(m).query(txy[::10],k=1)
        if float(np.median(d))<MIN_SEP: continue
        rr=mh['TVT'].values+mh['Z'].values
        gm=pd.Series(mh['GR'].values).interpolate(limit_direction='both').values.astype(float)
        ok=np.isfinite(rr)&np.isfinite(gm)
        px.append(mh['X'].values[ok][::4]); py.append(mh['Y'].values[ok][::4])
        pr.append(rr[ok][::4]); pg.append(gm[ok][::4])
    if not px: continue
    PX=np.concatenate(px); PY=np.concatenate(py); PR=np.concatenate(pr); PG=np.concatenate(pg)
    A=np.column_stack([np.ones(len(PX)),PX-PX.mean(),PY-PY.mean()])
    try:
        co=np.linalg.solve(A.T@A+1e-6*np.eye(3),A.T@PR); gx,gy=float(co[1]),float(co[2])
    except Exception: gx,gy=0.0,0.0
    gn=np.hypot(gx,gy); u=np.array([1.0,0.0]) if gn<1e-12 else np.array([gx,gy])/gn
    v=np.array([-u[1],u[0]]); P=np.column_stack([PX,PY])
    Pt=np.column_stack([P@u,(P@v)/ANISO]); Tt=np.column_stack([txy@u,(txy@v)/ANISO])
    kk=min(KSEL,len(PR))
    dd,ii=cKDTree(Pt).query(Tt,k=kk)
    if dd.ndim==1: dd=dd[:,None]; ii=ii[:,None]
    kn_idx=np.where(kn)[0][-ANCHOR:]
    # geometry-only baseline (== the L4 field, but with the KSEL pool truncated to K)
    wg=1.0/(dd[:,:K]+1.0); rb=(wg*PR[ii[:,:K]]).sum(1)/wg.sum(1)
    anc=float(np.nanmean(hw['TVT_input'].values[kn_idx]+Z[kn_idx]-rb[kn_idx]))
    OBASE.append((rb+anc-Z)[ridx].astype(np.float32))
    wgeo=1.0/(dd+1.0); grsel=PG[ii]; dg=grsel-GRt[:,None]
    for s in SIGMAS:
        wgr=wgeo*np.exp(-(dg**2)/(2.0*s*s))
        sw=wgr.sum(1); sw[sw<1e-12]=1e-12
        rg=(wgr*PR[ii]).sum(1)/sw
        bad=~np.isfinite(rg); rg[bad]=rb[bad]
        a2=float(np.nanmean(hw['TVT_input'].values[kn_idx]+Z[kn_idx]-rg[kn_idx]))
        OG[s].append((rg+a2-Z)[ridx].astype(np.float32))
    OW.append(np.full(len(ridx),wid)); OR.append(ridx)
out=dict(well=np.concatenate(OW).astype(str), ridx=np.concatenate(OR).astype(np.int32),
         geo=np.concatenate(OBASE))
for s in SIGMAS: out[f'gr_s{s:g}']=np.concatenate(OG[s])
np.savez_compressed(OUT,**out)
print(f"saved {OUT}: wells={len(OW)} rows={sum(len(x) for x in OR)} sigmas={SIGMAS}")
