"""Direction F local preflight (decides whether external-data + Kaggle GPU is worth it).
Train a small SELF-SUPERVISED contrastive GR encoder (TS2Vec/SimCLR-lite) on ROGII GR only
(test-available), extract per-toe-row embeddings, fit a residual GBM, and check the nested blend
weight SIGN vs DWT. If the learned encoder embedding gives a POSITIVE-weight honest OOF improvement,
external-data pretraining + GPU is justified; if it lands on the blend-neutral frontier / negative
weight (like the ROCKET probe), external data is unlikely to help and GPU is not warranted.
"""
import numpy as np, pandas as pd, glob, time, torch
import torch.nn as nn, lightgbm as lgb
torch.set_num_threads(2); torch.manual_seed(0); np.random.seed(0)
DATA="/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
t0=time.time(); Wn=64; EMB=32
z=np.load("/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out/combo_state.npz",allow_pickle=True)
d=pd.DataFrame(dict(well=z['well'],ridx=z['ridx'].astype(int),oof=z['oof'],yt=z['yt'],base=z['base'],cut=z['cut']))
g={w:s for w,s in d.groupby('well')}
def rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))
# collect GR sequences
GRs={}
for f in sorted(glob.glob(f"{DATA}/*__horizontal_well.csv")):
    wid=f.split('/')[-1].split('__')[0]
    if wid not in g: continue
    GRs[wid]=pd.read_csv(f,usecols=['GR'])['GR'].values.astype(np.float32)
print(f"loaded {len(GRs)} GR seqs {round(time.time()-t0,1)}s",flush=True)
def win_at(gr, centers):
    n=len(gr); out=np.empty((len(centers),Wn),np.float32)
    for i,c in enumerate(centers):
        lo=c-Wn//2; hi=lo+Wn
        seg=gr[max(0,lo):min(n,hi)]
        if len(seg)<Wn: seg=np.pad(seg,(max(0,-lo),max(0,hi-n)),mode='edge')
        out[i]=seg[:Wn]
    m=np.nanmean(out,1,keepdims=True); s=np.nanstd(out,1,keepdims=True)+1e-6
    return np.nan_to_num((out-m)/s)
# sample training windows
wins=[]
for wid,gr in GRs.items():
    if len(gr)<Wn+5: continue
    cs=np.random.randint(Wn//2,len(gr)-Wn//2,size=90); wins.append(win_at(gr,cs))
Wtr=np.concatenate(wins); print(f"train windows {Wtr.shape} {round(time.time()-t0,1)}s",flush=True)
class Enc(nn.Module):
    def __init__(s):
        super().__init__()
        s.c=nn.Sequential(nn.Conv1d(1,32,7,padding=3),nn.ReLU(),nn.Conv1d(32,32,5,padding=2),nn.ReLU(),
                          nn.Conv1d(32,32,3,padding=1),nn.ReLU(),nn.AdaptiveAvgPool1d(1),nn.Flatten(),nn.Linear(32,EMB))
    def forward(s,x):
        e=s.c(x.unsqueeze(1)); return e/(e.norm(dim=1,keepdim=True)+1e-8)
def augment(x):
    x=x+torch.randn_like(x)*0.1
    sc=1.0+torch.randn(x.shape[0],1)*0.1; x=x*sc
    if np.random.rand()<0.5:
        L=np.random.randint(5,20); st=np.random.randint(0,Wn-L); x[:,st:st+L]=0.0
    return x
enc=Enc(); opt=torch.optim.Adam(enc.parameters(),lr=1e-3); T=torch.tensor(Wtr)
n=len(T); idx=np.arange(n); tau=0.2
for ep in range(10):
    np.random.shuffle(idx); tot=0;nb=0
    for b in range(0,n,256):
        bi=idx[b:b+256]; xb=T[bi]
        z1=enc(augment(xb.clone())); z2=enc(augment(xb.clone()))
        logits=z1@z2.T/tau; lab=torch.arange(len(bi))
        loss=(nn.functional.cross_entropy(logits,lab)+nn.functional.cross_entropy(logits.T,lab))/2
        opt.zero_grad(); loss.backward(); opt.step(); tot+=loss.item(); nb+=1
    if ep%3==0: print(f"  ep{ep} infonce {tot/nb:.3f} {round(time.time()-t0,1)}s",flush=True)
enc.eval()
# per-toe-row embeddings + residual GBM
XX=[];YY=[];OO=[];YT=[];BB=[];WW=[]
with torch.no_grad():
    for wid,gr in GRs.items():
        s=g[wid]; c=int(s.cut.iloc[0]); ri=s.ridx.values; keep=np.arange(0,len(ri),8); ri=ri[keep]
        o=s.oof.values[keep]; y=s.yt.values[keep]; b=s.base.values[keep]; dist=(ri-c).astype(float)
        emb=enc(torch.tensor(win_at(gr,ri))).numpy()
        XX.append(np.column_stack([emb,dist/1000.0,dist**0.5])); YY.append((y-b).astype(np.float32)); OO.append(o);YT.append(y);BB.append(b);WW.append(np.array([wid]*len(ri)))
X=np.concatenate(XX);Yd=np.concatenate(YY);O=np.concatenate(OO);Y=np.concatenate(YT);B=np.concatenate(BB);W=np.concatenate(WW)
print(f"emb rows {X.shape} {round(time.time()-t0,1)}s",flush=True)
uw=np.unique(W); rng=np.random.RandomState(0); perm=rng.permutation(len(uw)); f5={uw[perm[i]]:i%5 for i in range(len(uw))}
fold=np.array([f5[w] for w in W]); gp=np.zeros(len(X))
for fo in range(5):
    tr=fold!=fo; te=fold==fo
    m=lgb.LGBMRegressor(n_estimators=400,num_leaves=63,learning_rate=0.03,min_child_samples=50,subsample=0.8,colsample_bytree=0.8,n_jobs=2,verbose=-1)
    m.fit(X[tr],Yd[tr]); gp[te]=B[te]+m.predict(X[te])
c=np.corrcoef(gp-Y,O-Y)[0,1]; ws=[]; bl=np.zeros(len(X))
for fo in range(5):
    tr=fold!=fo; te=fold==fo; a=(gp-O)[tr]; b=(Y-O)[tr]; w=float(np.sum(a*b)/np.sum(a*a)); ws.append(w); wc=max(-0.1,min(0.7,w)); bl[te]=((1-wc)*O+wc*gp)[te]
print(f"\nF PREFLIGHT (SSL contrastive GR encoder, ROGII-only):")
print(f"   DWT={rmse(O,Y):.4f}  SSL-residual={rmse(gp,Y):.4f}  corr(err,DWT)={c:.3f}")
print(f"   mean nested blend weight={np.mean(ws):+.3f} ({'NEGATIVE = drift-amplification artifact (external data unlikely to help; GPU NOT warranted)' if np.mean(ws)<0.02 else 'POSITIVE = genuine signal (external+GPU justified)'})  nested-blend={rmse(bl,Y):.4f}")
