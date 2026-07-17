import numpy as np
s=np.load('/home/ubuntu/.claude/jobs/276bd506/tmp/smk/sunny_oof.npz',allow_pickle=True)
sw=s['well'].astype(str); s_pred=s['oof_drift'].astype(np.float64); s_y=s['y_drift'].astype(np.float64)
cs=np.load('/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz')
toe=cs['is_toe']; dw=cs['well'][toe].astype(str); d_pred=(cs['oof'][toe]-cs['base'][toe]).astype(np.float64); d_y=(cs['yt'][toe]-cs['base'][toe]).astype(np.float64)
# align by (well, position-within-well). Verify per-well counts + truth match.
from collections import defaultdict
def by_well(w): 
    idx=defaultdict(list)
    for i,x in enumerate(w): idx[x].append(i)
    return idx
si=by_well(sw); di=by_well(dw)
common=sorted(set(si)&set(di))
S_pred=[];S_y=[];D_pred=[];D_y=[];WELL=[]
n_match=n_mismatch=0
for w in common:
    a=np.array(si[w]); b=np.array(di[w])
    if len(a)!=len(b): n_mismatch+=1; continue
    # align by position (both toe rows in file/MD order); sanity: truth drift should match
    ty_s=s_y[a]; ty_d=d_y[b]
    if np.sqrt(np.mean((ty_s-ty_d)**2))>2.0:  # truth mismatch -> misaligned well, skip
        n_mismatch+=1; continue
    n_match+=1
    S_pred.append(s_pred[a]); S_y.append(ty_s); D_pred.append(d_pred[b]); D_y.append(ty_d); WELL.append(np.full(len(a),w))
S_pred=np.concatenate(S_pred);D_pred=np.concatenate(D_pred);TRUTH=np.concatenate(S_y);WELL=np.concatenate(WELL)
print(f"aligned wells={n_match} (mismatch/skip={n_mismatch}); rows={len(TRUTH)}")
cvD=np.sqrt(np.mean((D_pred-TRUTH)**2)); cvS=np.sqrt(np.mean((S_pred-TRUTH)**2))
print(f"row-level pooled: DWT drift RMSE={cvD:.4f}  Sunny drift RMSE={cvS:.4f}  corr(errD,errS)={np.corrcoef(D_pred-TRUTH,S_pred-TRUTH)[0,1]:.3f}")
# nested well-split blend: blended=DWT + a*(Sunny-DWT); fit a on group0, eval pooled RMSE on group1
uw=np.array(sorted(set(WELL))); rng=np.random.RandomState(0); rng.shuffle(uw)
g0=set(uw[:len(uw)//2]); m0=np.array([w in g0 for w in WELL]); m1=~m0
def fit_a(m):
    d=S_pred[m]-D_pred[m]; r=TRUTH[m]-D_pred[m]; v=np.dot(d,d)
    return float(np.dot(d,r)/v) if v>1e-9 else 0.0
def rmse(m,a): return np.sqrt(np.mean((TRUTH[m]-(D_pred[m]+a*(S_pred[m]-D_pred[m])))**2))
a0=fit_a(m0); a1=fit_a(m1)
# out-of-sample: fit on m0 apply m1, and vice versa
r1_base=rmse(m1,0); r1_bl=rmse(m1,a0); r0_base=rmse(m0,0); r0_bl=rmse(m0,a1)
print(f"nested blend weight a: fold0={a0:.3f} fold1={a1:.3f}  (stable & positive? {np.sign(a0)==np.sign(a1) and a0>0.03 and a1>0.03})")
print(f"OOS pooled RMSE: fold1 base={r1_base:.4f}->blend={r1_bl:.4f} ({r1_bl-r1_base:+.4f}) | fold0 base={r0_base:.4f}->blend={r0_bl:.4f} ({r0_bl-r0_base:+.4f})")
gain=((r1_base-r1_bl)*m1.sum()+(r0_base-r0_bl)*m0.sum())/len(TRUTH)
print(f"NET out-of-sample pooled RMSE gain = {gain:+.4f}  (positive=blend helps DWT)")
