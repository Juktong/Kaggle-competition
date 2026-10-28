"""L5 follow-up: can the GR DIFFERENCE between two wells at matched XY estimate their TVT DIFFERENCE?

The structural field assumes a mate's r = TVT+Z transfers directly to the target at matched XY. It never
checks whether the two wells are actually at the same structural level. If the local GR-vs-TVT gradient
(available from the typewell, test-available) converts a GR difference into a TVT difference, that is a
correction the field currently ignores -- and it is a genuinely different computation.

Test on TRAIN pairs where BOTH true TVTs are known:
    predicted dTVT = (GR_A - GR_B) / (dGR/dTVT from the typewell at that level)
    true      dTVT =  TVT_A - TVT_B
Measure the correlation. If it is near zero, this mechanism does not exist and the line closes.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict
from scipy.spatial import cKDTree
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MIN_SEP=150.0; MAXW=int(os.environ.get('MAXW','50')); STEP=int(os.environ.get('STEP','20'))
gkey={}
for f in glob.glob(f'{D}/*__typewell.csv'):
    wid=os.path.basename(f).split('__')[0]
    try: gkey[wid]=round(float(np.nanmax(pd.read_csv(f,usecols=['TVT'])['TVT'].values)),1)
    except Exception: pass
groups=defaultdict(list)
for w,k in gkey.items(): groups[k].append(w)
hc={}; tc={}
def gh(w):
    if w not in hc: hc[w]=pd.read_csv(f'{D}/{w}__horizontal_well.csv',usecols=['X','Y','Z','TVT','GR'])
    return hc[w]
def gt(w):
    if w not in tc:
        t=pd.read_csv(f'{D}/{w}__typewell.csv',usecols=['TVT','GR']).sort_values('TVT')
        tv=t['TVT'].values.astype(float); gr=t['GR'].fillna(t['GR'].mean()).values.astype(float)
        grid=np.arange(np.nanmin(tv),np.nanmax(tv),0.5); prof=np.interp(grid,tv,gr)
        # local dGR/dTVT via a smoothed gradient
        k=41; ker=np.ones(k)/k
        sm=np.convolve(np.pad(prof,(k//2,k//2),mode='edge'),ker,mode='same')[k//2:k//2+len(prof)]
        tc[w]=(grid,np.gradient(sm,0.5))
    return tc[w]
_t={}
def tree_of(w):
    if w not in _t:
        h=gh(w); _t[w]=cKDTree(np.column_stack([h['X'].values,h['Y'].values]))
    return _t[w]
PD_,TD_,GD_,GRAD_=[],[],[],[]
targets=sorted(gkey.keys())[:MAXW]
for n,a in enumerate(targets):
    if n%20==0: print(f'  [{n}/{len(targets)}]',flush=True)
    try: ha=gh(a); grid,grad=gt(a)
    except Exception: continue
    XA=ha['X'].values; YA=ha['Y'].values; TA=ha['TVT'].values.astype(float)
    GA=pd.Series(ha['GR'].values).interpolate(limit_direction='both').values.astype(float)
    axy=np.column_stack([XA,YA])
    for b in groups.get(gkey[a],[]):
        if b==a: continue
        try: hb=gh(b)
        except Exception: continue
        if len(hb)<5: continue
        d,idx=tree_of(b).query(axy[::STEP],k=1)
        if float(np.median(d))<MIN_SEP: continue
        TB=hb['TVT'].values.astype(float)
        GB=pd.Series(hb['GR'].values).interpolate(limit_direction='both').values.astype(float)
        sel=np.arange(0,len(XA),STEP)
        m=(d<300)&np.isfinite(TA[sel])&np.isfinite(TB[idx])&np.isfinite(GA[sel])&np.isfinite(GB[idx])
        if m.sum()<20: continue
        tdiff=TA[sel][m]-TB[idx][m]
        gdiff=GA[sel][m]-GB[idx][m]
        lvl=0.5*(TA[sel][m]+TB[idx][m])
        gr_at=np.interp(lvl,grid,grad)
        ok=np.abs(gr_at)>1e-3
        if ok.sum()<20: continue
        PD_.append(gdiff[ok]/gr_at[ok]); TD_.append(tdiff[ok]); GD_.append(gdiff[ok]); GRAD_.append(gr_at[ok])
P=np.concatenate(PD_); T=np.concatenate(TD_); G=np.concatenate(GD_); GRD=np.concatenate(GRAD_)
ok=np.isfinite(P)&np.isfinite(T)&(np.abs(P)<200)
P,T,G,GRD=P[ok],T[ok],G[ok],GRD[ok]
print(f"\npairs sampled: {len(T)} matched points")
print(f"  true dTVT     : std={T.std():.2f} ft  mean={T.mean():+.2f}")
print(f"  GR diff       : std={G.std():.2f}     |dGR/dTVT| median={np.median(np.abs(GRD)):.3f} /ft")
print(f"  predicted dTVT: std={P.std():.2f} ft")
print(f"\n  corr(predicted dTVT, true dTVT) = {np.corrcoef(P,T)[0,1]:+.4f}")
print(f"  corr(raw GR diff, true dTVT)    = {np.corrcoef(G,T)[0,1]:+.4f}")
a=float(np.dot(P,T)/max(np.dot(P,P),1e-9))
res=T-a*P
print(f"  best scalar a={a:.4f}: residual std {res.std():.2f} vs baseline {T.std():.2f}"
      f"  -> variance explained {100*(1-res.var()/T.var()):.1f}%")
print("\nGATE: a materially non-zero correlation would mean the structural field is ignoring a usable,")
print("      test-available correction for level mismatch between a target and its mates.")
