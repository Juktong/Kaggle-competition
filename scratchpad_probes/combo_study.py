import numpy as np, pandas as pd, glob, os
from sklearn.metrics import root_mean_squared_error as rmse
OUT="/tmp/claude-1001/-home-ubuntu-workstation-JoeProject/4d8861e5-1123-46df-9acb-e09199721777/scratchpad/dwt_oof_out"
oof=np.load(f"{OUT}/dwt_oof.npy"); yt=np.load(f"{OUT}/dwt_ytrue.npy"); base=np.load(f"{OUT}/dwt_base.npy")
ids=pd.read_csv(f"{OUT}/dwt_ids.csv")['id'].values
print("rows",len(oof),"ids",len(ids))
# parse id -> well, rowidx
well=np.array([s.rsplit('_',1)[0] for s in ids])
ridx=np.array([int(s.rsplit('_',1)[1]) for s in ids])
print("distinct wells in train_df:", len(set(well.tolist())))
# per-well row counts vs raw
rawlen={}; cutmap={}
for f in glob.glob("data/rogii/train/*__horizontal_well.csv"):
    w=os.path.basename(f)[:8]
    d=pd.read_csv(f, usecols=['TVT_input'])
    ti=pd.to_numeric(d.TVT_input,errors='coerce').to_numpy(float); k=np.isfinite(ti)
    rawlen[w]=len(d)
    cutmap[w]=int(np.argmax(~k)) if (not k.all() and k.any()) else -1
# build toe mask for train_df rows
uw=set(well.tolist())
cut_arr=np.array([cutmap.get(w,-1) for w in well])
is_toe = (cut_arr>=0) & (ridx>=cut_arr)
is_heel= (cut_arr>=0) & (ridx< cut_arr)
print(f"toe rows: {is_toe.sum()}  heel rows: {is_heel.sum()}  neither: {(~is_toe&~is_heel).sum()}")
err=oof-yt
print(f"\n=== DWT RMSE ===")
print(f"  ALL train_df rows : {rmse(yt,oof):.4f}")
if is_toe.sum(): print(f"  TOE rows only     : {rmse(yt[is_toe],oof[is_toe]):.4f}   <-- the scored target")
if is_heel.sum(): print(f"  HEEL rows only    : {rmse(yt[is_heel],oof[is_heel]):.4f}")
# save intermediate for lever tests
np.savez(f"{OUT}/combo_state.npz", oof=oof, yt=yt, base=base, well=well, ridx=ridx, cut=cut_arr, is_toe=is_toe, is_heel=is_heel)
print("saved combo_state.npz")
