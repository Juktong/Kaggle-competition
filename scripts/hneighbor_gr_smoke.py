"""Direction 5: horizontal-neighbour GR SEQUENCE alignment (the remaining L5 shape).

The structural field transfers a neighbour's r=TVT+Z geometrically at matched XY. This tests whether
aligning the target's GR SEQUENCE to a neighbour horizontal well's GR sequence (windowed NCC along MD)
picks a better TVT than geometry alone -- and whether its error decorrelates from struct/PF.

Smoke: for each target toe row, take the geometrically-nearest surviving group-mate; slide a GR window
to find the best local GR match; transfer that matched point's r. Compare to geometric IDW.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MIN_SEP=150.0; ANCHOR=100; MAXW=int(os.environ.get('MAXW','40')); WIN=int(os.environ.get('WIN','30'))
gkey={}
for f in glob.glob(f'{D}/*__typewell.csv'):
    w=os.path.basename(f).split('__')[0]
    try: gkey[w]=round(float(np.nanmax(pd.read_csv(f,usecols=['TVT'])['TVT'].values)),1)
    except Exception: pass
groups=defaultdict(list)
for w,k in gkey.items(): groups[k].append(w)
hc={}
def get(w):
    if w not in hc: hc[w]=pd.read_csv(f'{D}/{w}__horizontal_well.csv',usecols=['X','Y','Z','TVT','TVT_input','GR'])
    return hc[w]
_t={}
def tree(w):
    if w not in _t:
        h=get(w); _t[w]=cKDTree(np.column_stack([h['X'].values,h['Y'].values]))
    return _t[w]
cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz'); tM=cs['is_toe']
dwell=cs['well'][tM].astype(str); dr=cs['ridx'][tM].astype(int)
toe=defaultdict(set)
for w,r in zip(dwell,dr): toe[w].add(int(r))
del cs
GEO,SEQ,TRU=[],[],[]
targets=[w for w in sorted(toe) if w in gkey][:MAXW]
for n,wid in enumerate(targets):
    if n%10==0: print(f'  [{n}/{len(targets)}]',flush=True)
    try: hw=get(wid)
    except Exception: continue
    kn=hw['TVT_input'].notna().values
    if kn.sum()<ANCHOR: continue
    ridx=np.array(sorted(toe[wid]))
    X=hw['X'].values; Y=hw['Y'].values; Z=hw['Z'].values; TV=hw['TVT'].values.astype(float)
    GR=pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    txy=np.column_stack([X,Y])
    mates=[]
    for m in groups.get(gkey[wid],[]):
        if m==wid: continue
        try: mh=get(m)
        except Exception: continue
        if len(mh)<WIN+5: continue
        d,_=tree(m).query(txy[::10],k=1)
        if float(np.median(d))<MIN_SEP: continue
        mates.append(m)
    if not mates: continue
    kn_idx=np.where(kn)[0][-ANCHOR:]
    MR={}; MGR={}
    for m in mates:
        mh=get(m); MR[m]=mh['TVT'].values+mh['Z'].values
        MGR[m]=pd.Series(mh['GR'].values).interpolate(limit_direction='both').values.astype(float)
    # geometry anchor
    for i in ridx[::8]:
        # nearest mate point (geometry)
        best_geo=None; best_seq=None; best_ncc=-2
        gr_t=GR[max(0,i-WIN//2):i+WIN//2]
        if len(gr_t)<WIN: continue
        gr_t=(gr_t-gr_t.mean())/(gr_t.std()+1e-6)
        for m in mates[:3]:
            mr=MR[m]; mgr=MGR[m]
            j0=int(tree(m).query([X[i],Y[i]],k=1)[1])
            if best_geo is None: best_geo=mr[j0]
            lo=max(WIN//2,j0-40); hi=min(len(mgr)-WIN//2,j0+40)
            for j in range(lo,hi,3):
                wv=mgr[j-WIN//2:j+WIN//2]
                if len(wv)<WIN: continue
                wv=(wv-wv.mean())/(wv.std()+1e-6)
                ncc=float(np.mean(gr_t*wv))
                if ncc>best_ncc: best_ncc=ncc; best_seq=mr[j]
        if best_geo is None or best_seq is None: continue
        # anchor both
        GEO.append(best_geo-Z[i]); SEQ.append(best_seq-Z[i]); TRU.append((wid,i,TV[i],Z[i]))
# anchor per well: level-match on known heel using geometry
import numpy as np
byw=defaultdict(list)
for k,(w,i,tv,z) in enumerate(TRU): byw[w].append((k,i,tv,z))
geo=np.array(GEO); seq=np.array(SEQ)
# simple global anchor (smoke): shift so mean matches truth
tv=np.array([t[2] for t in TRU]); zz=np.array([t[3] for t in TRU])
ga=geo+ (tv-geo).mean(); sa=seq+(tv-seq).mean()
rmse=lambda p:float(np.sqrt(np.mean((p-tv)**2)))
print(f"\nrows={len(tv)}")
print(f"  geometry-nearest transfer RMSE={rmse(ga):.4f}")
print(f"  GR-sequence-matched transfer RMSE={rmse(sa):.4f}")
eg=ga-tv; es=sa-tv
print(f"  corr(err_geo, err_seq)={np.corrcoef(eg,es)[0,1]:+.4f}")
print("GATE: GR-sequence must beat geometry AND decorrelate to be a candidate. (smoke, crude anchor)")
