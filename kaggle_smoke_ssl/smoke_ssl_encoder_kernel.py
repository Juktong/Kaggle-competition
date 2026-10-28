# ROGII GR-only SSL encoder — Kaggle GPU SMOKE kernel (skeleton)
# ---------------------------------------------------------------------------------------------
# PURPOSE: offline-load ROGII competition data + an external public GR dataset (FORCE-2020),
#          pretrain a small GR-only SSL encoder on GPU, and EXPORT per-window/per-well embeddings
#          to /kaggle/working. The residual-blend GATE against DWT OOF is done LOCALLY afterward
#          (this kernel does NOT ship the DWT OOF, and does NOT produce a competition submission).
#
# GATING (do not run the FULL version until all hold):
#   - ROGII external-data host-specific rule manually confirmed to allow external public data.
#   - A local preflight shows the embedding gives a POSITIVE-weight honest OOF blend vs DWT
#     (the ROGII-only SSL + facies preflights to date are NEGATIVE-weight; see report).
# Kaggle settings (kernel-metadata.json): enable_gpu=true (T4 x2 or P100), enable_internet=false.
# SMOKE = small sample + few epochs to verify the pipeline end-to-end cheaply on GPU.
# ---------------------------------------------------------------------------------------------
import os, glob, time, numpy as np, pandas as pd, torch, torch.nn as nn
t0=time.time(); SMOKE=True                      # SMOKE: cap wells/epochs; set False for full run
Wn=64; EMB=32; BATCH=512

def find_dir(patterns):
    for p in patterns:
        hits=glob.glob(p)
        if hits: return hits[0]
    return None
COMP=find_dir(["/kaggle/input/**/rogii-wellbore-geology-prediction",
               "/kaggle/input/competitions/rogii-wellbore-geology-prediction"]) or "/kaggle/input"
FORCE=find_dir(["/kaggle/input/**/force*2020*","/kaggle/input/*force*"])   # external GR dataset (attach)
print("COMP=",COMP," FORCE=",FORCE," gpu=",torch.cuda.is_available(),flush=True)

def gr_windows_from_csv(path, gr_col_candidates=("GR","GR_MEDIAN","GAMMA")):
    df=pd.read_csv(path)
    col=next((c for c in gr_col_candidates if c in df.columns), None)
    if col is None: return None
    gr=df[col].values.astype(np.float32); gr=gr[~np.isnan(gr)]
    if len(gr)<Wn+5: return None
    n= 40 if SMOKE else 120
    cs=np.random.randint(Wn//2,len(gr)-Wn//2,size=n)
    out=np.empty((n,Wn),np.float32)
    for i,c in enumerate(cs):
        seg=gr[c-Wn//2:c-Wn//2+Wn]; out[i]=seg[:Wn]
    m=out.mean(1,keepdims=True); s=out.std(1,keepdims=True)+1e-6
    return (out-m)/s

# ---- gather GR windows from external FORCE + ROGII (offline) ----
wins=[]
force_files = (glob.glob(f"{FORCE}/**/*.csv",recursive=True) if FORCE else [])[: (30 if SMOKE else 100000)]
for p in force_files:
    w=gr_windows_from_csv(p)
    if w is not None: wins.append(w)
rogii_files = glob.glob(f"{COMP}/train/*__horizontal_well.csv")[: (60 if SMOKE else 100000)]
for p in rogii_files:
    w=gr_windows_from_csv(p, gr_col_candidates=("GR",))
    if w is not None: wins.append(w)
W=np.concatenate(wins) if wins else np.zeros((0,Wn),np.float32)
print("pretrain windows:",W.shape," from force+rogii",round(time.time()-t0,1),"s",flush=True)
assert len(W)>1000, "not enough GR windows — check dataset attachment/paths"

dev="cuda" if torch.cuda.is_available() else "cpu"
class Enc(nn.Module):
    def __init__(s):
        super().__init__()
        s.c=nn.Sequential(nn.Conv1d(1,32,7,padding=3),nn.ReLU(),nn.Conv1d(32,32,5,padding=2),nn.ReLU(),
                          nn.Conv1d(32,32,3,padding=1),nn.ReLU(),nn.AdaptiveAvgPool1d(1),nn.Flatten(),nn.Linear(32,EMB))
    def forward(s,x):
        e=s.c(x.unsqueeze(1)); return e/(e.norm(dim=1,keepdim=True)+1e-8)
enc=Enc().to(dev); opt=torch.optim.Adam(enc.parameters(),lr=1e-3)
T=torch.tensor(W,device=dev); tau=0.2
def aug(x):
    x=x+torch.randn_like(x)*0.1; x=x*(1+torch.randn(x.shape[0],1,device=x.device)*0.1)
    return x
EPOCHS=3 if SMOKE else 30
for ep in range(EPOCHS):
    idx=torch.randperm(len(T),device=dev)
    for b in range(0,len(T),BATCH):
        bi=idx[b:b+BATCH]; xb=T[bi]
        z1=enc(aug(xb.clone())); z2=enc(aug(xb.clone()))
        logits=z1@z2.T/tau; lab=torch.arange(len(bi),device=dev)
        loss=(nn.functional.cross_entropy(logits,lab)+nn.functional.cross_entropy(logits.T,lab))/2
        opt.zero_grad(); loss.backward(); opt.step()
    print(f"  ep{ep} infonce {loss.item():.3f} {round(time.time()-t0,1)}s",flush=True)

# ---- export per-toe-row embeddings for ROGII train wells (for LOCAL blend gate) ----
enc.eval(); out_rows=[]
def win_at(gr, centers):
    n=len(gr); o=np.empty((len(centers),Wn),np.float32)
    for i,c in enumerate(centers):
        lo=c-Wn//2; seg=gr[max(0,lo):max(0,lo)+Wn]
        if len(seg)<Wn: seg=np.pad(seg,(0,Wn-len(seg)),mode='edge')
        o[i]=seg[:Wn]
    m=o.mean(1,keepdims=True); s=o.std(1,keepdims=True)+1e-6; return (o-m)/s
emb_recs=[]
with torch.no_grad():
    for p in rogii_files:
        wid=p.split('/')[-1].split('__')[0]; gr=pd.read_csv(p,usecols=['GR'])['GR'].values.astype(np.float32)
        if len(gr)<Wn+5: continue
        ri=np.arange(Wn//2,len(gr)-Wn//2, 8 if SMOKE else 4)
        e=enc(torch.tensor(win_at(gr,ri),device=dev)).cpu().numpy()
        emb_recs.append((wid,ri.astype(np.int32),e.astype(np.float32)))
np.savez_compressed("/kaggle/working/gr_ssl_embeddings.npz",
                    wids=np.array([r[0] for r in emb_recs],dtype=object),
                    ridx=np.array([r[1] for r in emb_recs],dtype=object),
                    emb=np.array([r[2] for r in emb_recs],dtype=object))
print("SMOKE OK. exported /kaggle/working/gr_ssl_embeddings.npz for", len(emb_recs), "wells",round(time.time()-t0,1),"s")
# NEXT (local): load this npz, build residual GBM on embeddings + distance, honest well-OOF,
#               check nested blend weight SIGN vs DWT OOF. Proceed to FULL run only if POSITIVE.
