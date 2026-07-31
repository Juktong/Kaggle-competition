#!/usr/bin/env python3
"""Spatial geology model (leave-one-well-out): predict a well's hidden toe TVT
from OTHER wells' r = TVT+Z field via KNN in (X,Y), then TVT = r(X,Y) - Z_toe.
Tests whether spatial structure carries GR-independent signal. CPU only."""
import glob, os
import numpy as np, pandas as pd
from scipy.spatial import cKDTree

DATA = "data/rogii/train"

def load(n):
    W = []
    for f in sorted(glob.glob(os.path.join(DATA, "*__horizontal_well.csv")))[:n]:
        df = pd.read_csv(f)
        if not {"TVT","Z","X","Y","TVT_input"}.issubset(df.columns): continue
        tvt=pd.to_numeric(df.TVT,errors="coerce").to_numpy(float)
        z=pd.to_numeric(df.Z,errors="coerce").to_numpy(float)
        x=pd.to_numeric(df.X,errors="coerce").to_numpy(float)
        y=pd.to_numeric(df.Y,errors="coerce").to_numpy(float)
        ti=pd.to_numeric(df.TVT_input,errors="coerce").to_numpy(float)
        known=np.isfinite(ti)
        if not known.any() or known.all(): continue
        cut=int(np.argmax(~known))
        if cut<20 or len(df)-cut<20: continue
        m=np.isfinite(tvt)&np.isfinite(z)&np.isfinite(x)&np.isfinite(y)
        if m.sum()<50: continue
        W.append(dict(well=os.path.basename(f)[:8],x=x,y=y,z=z,tvt=tvt,ti=ti,cut=cut,m=m))
    return W

def main(n=150, k=12, sub=6):
    W=load(n)
    # pooled reference points (subsampled) tagged by well index
    RX,RY,RR,RW=[],[],[],[]
    for i,w in enumerate(W):
        idx=np.where(w["m"])[0][::sub]
        RX.append(w["x"][idx]);RY.append(w["y"][idx]);RR.append((w["tvt"]+w["z"])[idx]);RW.append(np.full(len(idx),i))
    RX=np.concatenate(RX);RY=np.concatenate(RY);RR=np.concatenate(RR);RW=np.concatenate(RW)
    xy=np.c_[RX,RY]
    rows=[]
    for i,w in enumerate(W):
        toe=slice(w["cut"],len(w["tvt"]))
        true=w["tvt"][toe]; ok=np.isfinite(true)&np.isfinite(w["z"][toe])&np.isfinite(w["x"][toe])
        if ok.sum()<20: continue
        anchor=float(w["ti"][w["cut"]-1])
        # leave-one-well-out KNN spatial r
        mask=RW!=i
        tree=cKDTree(xy[mask]); rr=RR[mask]
        q=np.c_[w["x"][toe][ok],w["y"][toe][ok]]
        dist,nn=tree.query(q,k=k)
        wgt=1.0/(dist+1.0); r_pred=np.sum(rr[nn]*wgt,axis=1)/np.sum(wgt,axis=1)
        pred_sp=r_pred - w["z"][toe][ok]
        pred_last=np.full(ok.sum(),anchor)
        rmse=lambda p:float(np.sqrt(np.mean((p-true[ok])**2)))
        # simple ensemble: average spatial with last_value
        pred_ens=0.5*pred_sp+0.5*pred_last
        rows.append(dict(well=w["well"],rows=int(ok.sum()),last=rmse(pred_last),
                         spatial=rmse(pred_sp),ens=rmse(pred_ens),
                         nbr_dist_med=float(np.median(dist))))
    d=pd.DataFrame(rows); wt=d["rows"].to_numpy(float)
    wr=lambda c:float(np.sqrt(np.sum(wt*d[c]**2)/wt.sum()))
    print(f"wells: {len(d)}  (k={k}, subsample={sub})")
    print(f"  last_value        pooled RMSE = {wr('last'):.4f}")
    print(f"  spatial(r(X,Y))   pooled RMSE = {wr('spatial'):.4f}   Δ={wr('spatial')-wr('last'):+.4f}")
    print(f"  0.5*spatial+0.5*last (ensemble)= {wr('ens'):.4f}   Δ={wr('ens')-wr('last'):+.4f}")
    print(f"  spatial win_rate vs last = {(d.spatial<d.last).mean():.2f}")
    print(f"  neighbor dist median (X,Y units): {d.nbr_dist_med.median():.1f}")
    print(f"  --- best spatial wells ---")
    for _,r in d.assign(g=d.spatial-d.last).sort_values('g').head(6).iterrows():
        print(f"    {r.well} last={r.last:7.2f} spatial={r.spatial:7.2f} Δ={r.spatial-r.last:+7.2f} nbrdist={r.nbr_dist_med:.0f}")

if __name__=="__main__":
    main()
