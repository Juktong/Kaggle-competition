"""Direct mechanism probe: where does the A=50 field's IDW weight come from?

If anisotropy is re-admitting near-twins, the weight should concentrate on mates whose ISOTROPIC
separation is just past MIN_SEP=150ft -- exactly the ones the guard was calibrated to sit next to.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
K=12; ANCHOR=100; MIN_SEP=150.0; NW=int(os.environ.get('NW','40'))
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
    if w not in cache: cache[w]=pd.read_csv(f'{D}/{w}__horizontal_well.csv',usecols=['X','Y','Z','TVT','TVT_input'])
    return cache[w]
_t={}
def tree_of(w):
    if w not in _t:
        h=get(w); _t[w]=cKDTree(np.column_stack([h['X'].values,h['Y'].values]))
    return _t[w]
res={1.0:[],50.0:[]}
targets=sorted(toe.keys())[:NW]
for wid in targets:
    if wid not in gkey: continue
    try: hw=get(wid)
    except Exception: continue
    if hw['TVT_input'].notna().values.sum()<ANCHOR: continue
    X=hw['X'].values; Y=hw['Y'].values; txy=np.column_stack([X,Y])
    px,py,pr,psep=[],[],[],[]
    for m in groups.get(gkey[wid],[]):
        if m==wid: continue
        try: mh=get(m)
        except Exception: continue
        if len(mh)<5: continue
        d,_=tree_of(m).query(txy[::10],k=1); sep=float(np.median(d))
        if sep<MIN_SEP: continue
        rr=mh['TVT'].values+mh['Z'].values; ok=np.isfinite(rr)
        n=ok.sum()//4+1
        px.append(mh['X'].values[ok][::4]); py.append(mh['Y'].values[ok][::4]); pr.append(rr[ok][::4])
        psep.append(np.full(len(mh['X'].values[ok][::4]),sep))
    if not px: continue
    PX=np.concatenate(px); PY=np.concatenate(py); PSEP=np.concatenate(psep)
    A_=np.column_stack([np.ones(len(PX)),PX-PX.mean(),PY-PY.mean()])
    try:
        co=np.linalg.solve(A_.T@A_+1e-6*np.eye(3),A_.T@np.concatenate(pr)); gx,gy=float(co[1]),float(co[2])
    except Exception: gx,gy=0.0,0.0
    gn=np.hypot(gx,gy); u=np.array([1.0,0.0]) if gn<1e-12 else np.array([gx,gy])/gn
    v=np.array([-u[1],u[0]]); P=np.column_stack([PX,PY])
    for a in (1.0,50.0):
        Pt=np.column_stack([P@u,(P@v)/a]); Tt=np.column_stack([txy@u,(txy@v)/a])
        dd,ii=cKDTree(Pt).query(Tt,k=min(K,len(PX)))
        if dd.ndim==1: dd=dd[:,None]; ii=ii[:,None]
        wg=1.0/(dd+1.0); wg=wg/wg.sum(1,keepdims=True)
        sep_sel=PSEP[ii]
        res[a].append((float(np.mean(np.sum(wg*(sep_sel<400),axis=1))), float(np.mean(np.sum(wg*(sep_sel<250),axis=1))),
                       float(np.median(sep_sel)), float(np.median(dd))))
for a in (1.0,50.0):
    arr=np.array(res[a])
    print(f"A={a:g}: weight share from mates with isotropic sep <400ft = {arr[:,0].mean():.1%}"
          f" | <250ft = {arr[:,1].mean():.1%}")
    print(f"        median isotropic sep of SELECTED mates = {np.median(arr[:,2]):.0f} ft"
          f" | median effective query distance = {np.median(arr[:,3]):.1f}")
print(f"\nwells sampled: {len(res[1.0])}  (MIN_SEP guard = {MIN_SEP:.0f} ft)")
