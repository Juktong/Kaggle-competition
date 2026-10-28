"""Direction 6: PF variant smoke. Do alternative PF parameterisations DECORRELATE from the deployed PF?
A variant only helps if its errors are decorrelated AND it is comparably strong. Smoke on a subset."""
import os, numpy as np, pandas as pd
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
code=open('/home/ubuntu/.claude/jobs/06dd2efb/tmp/SUNNY_CODE.py').read()
cut=code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
funcs=code[:cut].replace("INPUT_DIR = find_input_dir()","INPUT_DIR='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii'")
ns={}; exec(funcs,ns)
base_pf=ns['run_particle_filter']
MAXW=int(os.environ.get('MAXW','24')); NS=int(os.environ.get('NS','16'))

def pf_variant(hw,tw,n_particles=500,seed=42,gs_mult=1.0,PN=0.005,init=2.0,trim=False):
    """copy of run_particle_filter with tunable emission width / process noise / init / robust aggregation"""
    tw_s=tw.sort_values('TVT'); tw_tvt=tw_s['TVT'].values.astype(float); tw_gr=tw_s['GR'].fillna(tw_s['GR'].mean()).values.astype(float)
    kn=hw[hw['TVT_input'].notna()]; ev=hw[hw['TVT_input'].isna()]
    if len(ev)==0: return hw['TVT_input'].values.astype(float).copy(),0.0
    last=kn.iloc[-1]; last_tvt=float(last['TVT_input']); last_Z=float(last['Z']); last_MD=float(last['MD'])
    tw_at_k=np.interp(kn['TVT_input'].values,tw_tvt,tw_gr)
    gs=float(np.clip(np.nanstd(kn['GR'].fillna(0).values-tw_at_k),10.,60.))*gs_mult
    tail=kn.tail(30); dt=np.diff(tail['TVT_input'].values); dz=np.diff(tail['Z'].values); dm=np.diff(tail['MD'].values); m=dm>0
    ir=float(np.median((dt+dz)[m]/dm[m])) if m.sum()>=3 else 0.0
    N=n_particles; rng=np.random.default_rng(seed); ls=last_tvt+last_Z
    pos=ls+init*rng.standard_normal(N); rate=ir+0.01*rng.standard_normal(N); w=np.ones(N)/N
    MOM=0.998; VN=0.002; RP=0.1; RR=0.001; RESAMP=0.5
    md_v=ev['MD'].values.astype(float); z_v=ev['Z'].values.astype(float)
    gr_interp=hw['GR'].interpolate(limit_direction='both').fillna(tw_gr.mean()); gr_v=gr_interp.values.astype(float)[ev.index]
    out=hw['TVT_input'].values.astype(float).copy(); res=np.empty(len(ev)); prev=last_MD; ll=0.0
    for i in range(len(ev)):
        dms=max(md_v[i]-prev,1.0); rate=MOM*rate+VN*rng.standard_normal(N); pos=pos+rate*dms+PN*rng.standard_normal(N)
        tvt_p=np.clip(pos-z_v[i],tw_tvt[0]-100,tw_tvt[-1]+100); pos=tvt_p+z_v[i]
        eg=np.interp(tvt_p,tw_tvt,tw_gr); d=(gr_v[i]-eg)/gs; lk=np.maximum(np.exp(-0.5*np.minimum(d**2,600.)),1e-300)
        ll+=np.log(max(float((w*lk).sum()),1e-300)); w=w*lk; ws=w.sum(); w=w/ws if ws>0 else np.ones(N)/N
        neff=1.0/(w**2).sum()
        if neff<RESAMP*N:
            cum=np.cumsum(w); u0=rng.uniform(0,1.0/N); idx=np.clip(np.searchsorted(cum,u0+np.arange(N)/N),0,N-1)
            pos=pos[idx]+RP*rng.standard_normal(N); rate=rate[idx]+RR*rng.standard_normal(N); w=np.ones(N)/N
        if trim:
            tvtp=pos-z_v[i]; o=np.argsort(tvtp); k=int(0.1*N); keep=o[k:N-k]
            res[i]=float(np.average(tvtp[keep],weights=w[keep])) if w[keep].sum()>0 else float(np.dot(w,pos-z_v[i]))
        else:
            res[i]=float(np.dot(w,pos-z_v[i]))
        prev=md_v[i]
    out[list(ev.index)]=res; return out,ll

def ens(fn,hw,tw,ns_,**kw):
    ps=[]; ls=[]
    for s in range(ns_):
        p,ll=fn(hw,tw,seed=s,**kw); ps.append(p); ls.append(ll)
    l=np.array(ls); l-=l.max(); w=np.exp(l/5.0); w/=w.sum()
    return (w[:,None]*np.stack(ps,0)).sum(0)

import glob
allw=sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng=np.random.RandomState(11); rng.shuffle(allw); wids=allw[:MAXW]
D_base,D_v1,D_v2,D_tru=[],[],[],[]
for n,wid in enumerate(wids):
    try:
        hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv'); tw=pd.read_csv(f'{D}/{wid}__typewell.csv')
    except Exception: continue
    ev=hw['TVT_input'].isna().values
    if ev.sum()<10 or hw['TVT_input'].notna().sum()<50: continue
    tru=hw['TVT'].values.astype(float)
    b=ens(lambda hw,tw,seed: base_pf(hw,tw,seed=seed),hw,tw,NS)
    v1=ens(pf_variant,hw,tw,NS,gs_mult=float(os.environ.get('GSM','1.6')))
    v2=ens(pf_variant,hw,tw,NS,trim=True,PN=0.010)     # robust trim + more process noise
    D_base.append(b[ev]); D_v1.append(v1[ev]); D_v2.append(v2[ev]); D_tru.append(tru[ev])
    if n%8==0: print(f'  [{n}/{len(wids)}]',flush=True)
b=np.concatenate(D_base); v1=np.concatenate(D_v1); v2=np.concatenate(D_v2); y=np.concatenate(D_tru)
rmse=lambda p:float(np.sqrt(np.mean((p-y)**2)))
eb=b-y; e1=v1-y; e2=v2-y
print(f"\nrows={len(y)}  deployed-PF RMSE={rmse(b):.4f}")
print(f"  variant1 wider-emission RMSE={rmse(v1):.4f}  corr(err,baseErr)={np.corrcoef(e1,eb)[0,1]:.4f}")
print(f"  variant2 trim+procnoise RMSE={rmse(v2):.4f}  corr(err,baseErr)={np.corrcoef(e2,eb)[0,1]:.4f}")
for nm,v in [('v1',v1),('v2',v2)]:
    for a in [0.3,0.5]:
        bl=(1-a)*b+a*v; print(f"  blend base+{a}*({nm}-base): RMSE={rmse(bl):.4f} gain vs PF {rmse(b)-rmse(bl):+.4f}")
print("\nGATE: a variant helps only if corr(err) is materially <1 AND blending lowers RMSE.")
