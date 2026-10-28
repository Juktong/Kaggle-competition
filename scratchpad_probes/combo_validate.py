import numpy as np
from sklearn.metrics import root_mean_squared_error as rmse
from sklearn.model_selection import GroupKFold
from scipy.signal import savgol_filter
OUT="/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out"
S=np.load(f"{OUT}/combo_state.npz", allow_pickle=True)
oof=S['oof']; yt=S['yt']; base=S['base']; well=S['well']; ridx=S['ridx']
d=oof-base
base_rmse=rmse(yt,oof)
print(f"DWT baseline = {base_rmse:.4f}")

# extended lambda sweep (find true optimum on full data, for reference)
print("\n[extended λ sweep, full data]")
grid=np.arange(1.00,1.20,0.01)
for lam in grid:
    print(f"   λ={lam:.2f} RMSE={rmse(yt,base+lam*d):.4f}", end="  ")
    if abs((lam*100)%5)<1: print()
print()

# ---- HONEST GroupKFold: tune λ (and optional smoothing) on train folds, apply to held-out ----
gkf=GroupKFold(n_splits=5)
# precompute per-well savgol-smoothed residual (win=201, po=2)
order=np.lexsort((ridx,well)); inv=np.empty_like(order); inv[order]=np.arange(len(order))
w_s=well[order]; d_s=d[order]
def smooth_groups(dvec,wvec,wl,po=2):
    out=np.copy(dvec); i=0; n=len(wvec)
    while i<n:
        j=i
        while j<n and wvec[j]==wvec[i]: j+=1
        seg=dvec[i:j]
        if len(seg)>wl:
            wlen=wl if wl%2==1 else wl+1
            wlen=min(wlen,len(seg)-(1-len(seg)%2))
            if wlen>=3 and wlen>po:
                try: out[i:j]=savgol_filter(seg,wlen,po)
                except: pass
        i=j
    return out
d_smooth=smooth_groups(d_s,w_s,201)[inv]

lam_grid=np.arange(0.98,1.16,0.01)
oof_lam=np.zeros_like(yt); oof_lamsm=np.zeros_like(yt)
fold_base=[]; fold_lam=[]; fold_lamsm=[]
for tr,va in gkf.split(oof, yt, groups=well):
    # tune λ on train
    bl=min(lam_grid, key=lambda L: rmse(yt[tr], base[tr]+L*d[tr]))
    oof_lam[va]=base[va]+bl*d[va]
    # tune λ with smoothed residual on train
    bls=min(lam_grid, key=lambda L: rmse(yt[tr], base[tr]+L*d_smooth[tr]))
    oof_lamsm[va]=base[va]+bls*d_smooth[va]
    fold_base.append(rmse(yt[va],oof[va]))
    fold_lam.append(rmse(yt[va],oof_lam[va]))
    fold_lamsm.append(rmse(yt[va],oof_lamsm[va]))
print("\n=== HONEST held-out (GroupKFold, λ tuned on train folds) ===")
print(f"  DWT baseline      per-fold: {[f'{x:.3f}' for x in fold_base]}  pooled={rmse(yt,oof):.4f}")
print(f"  +λ scale          per-fold: {[f'{x:.3f}' for x in fold_lam]}  pooled={rmse(yt,oof_lam):.4f}  Δ={rmse(yt,oof_lam)-base_rmse:+.4f}")
print(f"  +λ scale +smooth  per-fold: {[f'{x:.3f}' for x in fold_lamsm]}  pooled={rmse(yt,oof_lamsm):.4f}  Δ={rmse(yt,oof_lamsm)-base_rmse:+.4f}")
