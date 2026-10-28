"""Direction G: synthetic geomodel -> domain-randomized SELECTOR training, validate on real OOF.
Hypothesis: the selection bottleneck (which candidate path is truth-like) can be learned from
UNLIMITED synthetic wells with known truth, then transfer to real. Feasibility: (1) does a selector
trained on synthetic pick truth-paths on synthetic? (2) does it transfer to real ROGII (beat best-cost
/ the B3 gate)? Report the synthetic->real domain gap. test-available inputs only at apply time.
"""
import numpy as np, pandas as pd, glob, time, lightgbm as lgb
from sklearn.metrics import accuracy_score
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
t0=time.time(); rs=np.random.RandomState(7); LAM=8.0; K=8; WIN=20
def dp_path(EM,s0,lam,cap,extra):
    N,S=EM.shape; INF=1e12; dd=np.arange(-cap,cap+1); trans=lam*(dd.astype(float)**2)
    cost=np.full(S,INF); cost[s0]=0.0; back=np.zeros((N,S),dtype=np.int32); E=EM if extra is None else EM+extra
    for n in range(N):
        best=np.full(S,INF); bd=np.zeros(S,dtype=np.int32)
        for k,dv in enumerate(dd):
            src=np.roll(cost,dv)
            if dv>0: src[:dv]=INF
            elif dv<0: src[dv:]=INF
            cand=src+trans[k]; u=cand<best; best[u]=cand[u]; bd[u]=dv
        cost=best+E[n]; back[n]=bd
    s=int(np.argmin(cost)); tot=float(cost[s]); p=np.zeros(N,int)
    for n in range(N-1,-1,-1): p[n]=s; s=max(0,min(S-1,s-int(back[n,s])))
    return p,tot
def norm_rows(A):
    A=A-A.mean(1,keepdims=True); n=np.sqrt((A*A).sum(1,keepdims=True))+1e-9; return A/n
def topk_paths(GRtw, states, GRh_ds, s0):
    offs=np.arange(-WIN,WIN+1); TW=norm_rows(np.interp(states[:,None]+offs[None,:],states,GRtw))
    # horizontal window features approximated: local GR pattern via +/-WIN in state units (use GRh as pseudo)
    Hn=norm_rows(np.stack([np.interp(np.arange(-WIN,WIN+1),[0],[GRh_ds[i]]) for i in range(len(GRh_ds))])) if False else None
    return None
def path_feats(p, states, s0, cost):
    tvt=states[p]; d=np.diff(tvt)
    return [cost, float(np.mean(np.abs(np.diff(d)))) if len(d)>1 else 0, float(np.sum(np.abs(d))),
            float(np.max(np.abs(d))) if len(d) else 0, float(abs(tvt[0]-states[s0])),
            float(tvt.max()-tvt.min()), float(np.mean((p<=3)|(p>=len(states)-4)))]

# ---------- synthetic generator ----------
def gen_synth():
    # typewell: layered GR vs TVT
    S=rs.randint(500,900); base_tvt=rs.uniform(10000,12000)
    tvt_states=np.arange(base_tvt,base_tvt+S,1.0)
    nl=rs.randint(6,14); bnds=np.sort(rs.choice(S,nl,replace=False)); vals=rs.uniform(40,180,nl+1)
    GRtw=np.zeros(S); idx=0
    for i,bn in enumerate(list(bnds)+[S]):
        GRtw[idx:bn]=vals[i]; idx=bn
    GRtw=np.convolve(GRtw,np.ones(7)/7,mode='same')+rs.randn(S)*4
    # horizontal trajectory TVT(MD): dip + curvature + occasional jump + stretch
    N=rs.randint(1500,3500); MD=np.arange(N,dtype=float)
    dip=rs.uniform(-0.02,0.02); curv=rs.uniform(-1e-5,1e-5)
    tvt=base_tvt+rs.uniform(20,S-40)+dip*MD+0.5*curv*MD**2
    if rs.rand()<0.4:  # a fault jump
        j=rs.randint(N//3,2*N//3); tvt[j:]+=rs.uniform(-25,25)
    tvt=np.clip(tvt,tvt_states[WIN+1],tvt_states[-WIN-2])
    GRh=np.interp(tvt,tvt_states,GRtw)+rs.randn(N)*rs.uniform(3,10)  # observed horizontal GR + noise
    cut=int(N*rs.uniform(0.2,0.35))
    return GRtw,tvt_states,GRh,tvt,cut
def build_candidates(GRtw,states,GRh,tvt_true,cut):
    offs=np.arange(-WIN,WIN+1); TW=norm_rows(np.interp(states[:,None]+offs[None,:],states,GRtw))
    toe=np.arange(cut+1,len(GRh)); ds=toe[::4]
    # horizontal windows in index space mapped by a nominal dip (use finite diff of known heel)
    sl=(tvt_true[cut]-tvt_true[max(0,cut-100)])/(100+1e-9); sl=sl if abs(sl)>1e-4 else 1e-4
    Hw=np.stack([np.interp(np.arange(-WIN,WIN+1)/sl+i,np.arange(len(GRh)),GRh) for i in ds])
    EM=1.0-(norm_rows(Hw)@TW.T); s0=int(np.clip(round(tvt_true[cut]-states[0]),0,len(states)-1))
    paths=[];pen=np.zeros_like(EM)
    for kk in range(K):
        p,c=dp_path(EM,s0,LAM,8,pen if kk>0 else None); paths.append((p,c))
        for n in range(len(ds)):
            lo=max(0,p[n]-12); hi=min(len(states),p[n]+13); pen[n,lo:hi]+=0.4
    ests=[np.interp(toe,ds,states[p]) for p,_ in paths]; tt=tvt_true[toe]
    rm=[np.sqrt(np.mean((e-tt)**2)) for e in ests]
    feats=[path_feats(p,states,s0,c) for p,c in paths]
    return feats,rm,int(np.argmin(rm))

print("== G1: synthetic feasibility — can a selector pick truth-path on synthetic? ==",flush=True)
Xs=[];ys=[];grp=[];rmss=[]
for w in range(220):
    try:
        GRtw,states,GRh,tvt,cut=gen_synth(); feats,rm,best=build_candidates(GRtw,states,GRh,tvt,cut)
    except Exception: continue
    for ki in range(len(feats)):
        Xs.append(feats[ki]); ys.append(1 if ki==best else 0); grp.append(w); rmss.append(rm[ki])
    if w%60==0: print("  synth",w,round(time.time()-t0,1),"s",flush=True)
Xs=np.array(Xs);ys=np.array(ys);grp=np.array(grp);rmss=np.array(rmss)
gu=np.unique(grp); tr_g=set(gu[:int(len(gu)*0.7)])
trm=np.array([x in tr_g for x in grp]); tem=~trm
m=lgb.LGBMClassifier(n_estimators=300,num_leaves=15,learning_rate=0.05,min_child_samples=20,verbose=-1)
m.fit(Xs[trm],ys[trm])
# eval per synthetic held-out well: does selector pick best vs best-cost(=lowest cost feature[0])
def eval_group(Xg,rmg,proba):
    sel=int(np.argmax(proba)); bc=int(np.argmin(Xg[:,0])); orc=int(np.argmin(rmg))
    return rmg[sel],rmg[bc],rmg[orc]
selR=[];bcR=[];orR=[]
for w in gu:
    if w in tr_g: continue
    mask=grp==w; pr=m.predict_proba(Xs[mask])[:,1]
    s,b,o=eval_group(Xs[mask],rmss[mask],pr); selR.append(s);bcR.append(b);orR.append(o)
print(f"   synthetic held-out: selector-path RMSE={np.mean(selR):.2f}  best-cost={np.mean(bcR):.2f}  oracle={np.mean(orR):.2f}")
print(f"   => selector {'BEATS' if np.mean(selR)<np.mean(bcR)-0.2 else 'does NOT beat'} best-cost on synthetic (feasibility)")

# ---------- G2: transfer to REAL ROGII (apply synth-trained selector) ----------
print("\n== G2: transfer to REAL ROGII wells (60), synth-trained selector vs best-cost ==",flush=True)
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
dfo=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt'])); go={w:s.set_index('ridx') for w,s in dfo.groupby('well')}
selR=[];bcR=[];dwtR=[];orR=[]
for f in sorted(glob.glob(f"{DATA}/*__horizontal_well.csv"))[:60]:
    wid=f.split('/')[-1].split('__')[0]
    if wid not in go: continue
    h=pd.read_csv(f); t=pd.read_csv(f.replace("__horizontal_well","__typewell"))
    GR=h['GR'].values.astype(float); Ht=h['TVT'].values.astype(float); known=h['TVT_input'].notna().values
    tw=t.dropna(subset=['TVT','GR']).sort_values('TVT'); tv=tw['TVT'].values.astype(float); gt=tw['GR'].values.astype(float)
    if len(tv)<50: continue
    states=np.arange(tv.min(),tv.max(),1.0); GRtw=np.interp(states,tv,gt); c=np.where(known)[0].max()
    if len(states)<50: continue
    try: feats,rm,best=build_candidates(GRtw,states,GR,Ht,c)
    except Exception: continue
    sub=go[wid]; toe=np.array([i for i in np.where(~known)[0] if i>c and i in sub.index]);
    if len(toe)<50: continue
    dwt_rmse=np.sqrt(np.mean((sub.loc[toe,'oof'].values-sub.loc[toe,'yt'].values)**2))
    Xg=np.array(feats); pr=m.predict_proba(Xg)[:,1]
    selR.append(rm[int(np.argmax(pr))]); bcR.append(rm[int(np.argmin(Xg[:,0]))]); orR.append(rm[int(np.argmin(rm))]); dwtR.append(dwt_rmse)
print(f"   REAL: synth-selector path RMSE={np.mean(selR):.2f}  best-cost={np.mean(bcR):.2f}  oracle={np.mean(orR):.2f}  DWT={np.mean(dwtR):.2f}")
print(f"   => transfer: selector {'beats' if np.mean(selR)<np.mean(bcR)-0.2 else 'does NOT beat'} best-cost on REAL; both {'>' if np.mean(selR)>np.mean(dwtR) else '<'} DWT")
