import numpy as np, pandas as pd
from sklearn.metrics import root_mean_squared_error as rmse
from scipy.signal import savgol_filter
OUT="/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out"
S=np.load(f"{OUT}/combo_state.npz", allow_pickle=True)
oof=S['oof']; yt=S['yt']; base=S['base']; well=S['well']; ridx=S['ridx']
d=oof-base            # DWT predicted residual-from-anchor
dt=yt-base            # true residual
base_rmse=rmse(yt,oof)
print(f"DWT toe baseline RMSE = {base_rmse:.4f}\n")

# ---- Lever A: global shrinkage lambda ----
print("[A] global shrink  pred=base+λ(oof-base)")
bestA=(1.0,base_rmse)
for lam in np.arange(0.80,1.06,0.02):
    r=rmse(yt, base+lam*d)
    if r<bestA[1]: bestA=(lam,r)
    print(f"   λ={lam:.2f}  RMSE={r:.4f}")
print(f"   best λ={bestA[0]:.2f} -> {bestA[1]:.4f}  Δ={bestA[1]-base_rmse:+.4f}")

# ---- Lever D: clip extreme predicted residual ----
print("\n[D] clip |oof-base| at percentile")
for q in (99.9,99.5,99,98):
    cap=np.percentile(np.abs(d),q)
    r=rmse(yt, base+np.clip(d,-cap,cap))
    print(f"   q={q}  cap={cap:.1f}  RMSE={r:.4f}  Δ={r-base_rmse:+.4f}")

# ---- Lever B: per-well smoothing of residual along MD ----
print("\n[B] per-well savgol smoothing of (oof-base) along row order")
order=np.lexsort((ridx, well))     # sort by well then ridx
inv=np.empty_like(order); inv[order]=np.arange(len(order))
w_s=well[order]; d_s=d[order]
# group boundaries
import itertools
sm=np.copy(d_s)
i=0; N=len(w_s)
for win in (0,):  # placeholder
    pass
def smooth_groups(dvec, wvec, wl, po):
    out=np.copy(dvec); i=0; n=len(wvec)
    while i<n:
        j=i
        while j<n and wvec[j]==wvec[i]: j+=1
        seg=dvec[i:j]
        if len(seg)>wl:
            wlen=wl if wl%2==1 else wl+1
            wlen=min(wlen, len(seg)-(1-len(seg)%2))
            if wlen>=3 and wlen>po:
                try: out[i:j]=savgol_filter(seg, wlen, po)
                except: pass
        i=j
    return out
for wl in (31,61,121,201):
    sm=smooth_groups(d_s, w_s, wl, 2)
    r=rmse(yt, base+sm[inv])
    print(f"   savgol win={wl}  RMSE={r:.4f}  Δ={r-base_rmse:+.4f}")
