#!/usr/bin/env python3
"""Probe the structure of the TVT target vs Z (elevation), which IS known in test.

Hypothesis: TVT is close to (-Z + c), so the real unknown is the small residual
r = TVT + Z. If so, projecting the toe TVT from its known Z beats last_value by a
lot, and the competition is really about modeling r (a ~small-range signal).
Native TVT_input mask = hidden split. CPU only.
"""
import glob, os
import numpy as np, pandas as pd

DATA = "data/rogii/train"

def main(n_wells=150):
    rows = []
    r_within_std = []
    for f in sorted(glob.glob(os.path.join(DATA, "*__horizontal_well.csv")))[:n_wells]:
        df = pd.read_csv(f)
        if not {"TVT", "Z", "TVT_input"}.issubset(df.columns):
            continue
        tvt = pd.to_numeric(df.TVT, errors="coerce").to_numpy(float)
        z = pd.to_numeric(df.Z, errors="coerce").to_numpy(float)
        ti = pd.to_numeric(df.TVT_input, errors="coerce").to_numpy(float)
        known = np.isfinite(ti)
        if not known.any() or known.all():
            continue
        cut = int(np.argmax(~known))
        if cut < 20 or len(df) - cut < 20:
            continue
        r = tvt + z                                   # residual r = TVT + Z
        r_within_std.append(float(np.nanstd(r[np.isfinite(r)])))
        anchor_tvt = float(ti[cut-1]); anchor_z = float(z[cut-1])
        r_anchor = anchor_tvt + anchor_z
        toe = slice(cut, len(df)); true = tvt[toe]; ok = np.isfinite(true)
        if ok.sum() < 20: continue
        z_toe = z[toe]
        pred_last = np.full(ok.sum(), anchor_tvt)                 # last_value
        pred_zproj = (r_anchor - z_toe)[ok]                      # -Z + c (slope -1)
        # r modeled as its own within-prefix linear trend vs MD (does r drift?)
        rmse = lambda p: float(np.sqrt(np.mean((p - true[ok])**2)))
        rows.append(dict(well=os.path.basename(f)[:8], rows=int(ok.sum()),
                         last=rmse(pred_last), zproj=rmse(pred_zproj),
                         r_mean=float(np.nanmean(r)), r_std=float(np.nanstd(r[np.isfinite(r)])),
                         r_toe_drift=float(np.nanmean(r[toe][ok]) - r_anchor)))
    d = pd.DataFrame(rows); w = d["rows"].to_numpy(float)
    wr = lambda c: float(np.sqrt(np.sum(w*d[c]**2)/w.sum()))
    print(f"wells: {len(d)}")
    print(f"\n=== predictor pooled RMSE on hidden toe ===")
    print(f"  last_value        = {wr('last'):.4f}")
    print(f"  Z-projection(-Z+c)= {wr('zproj'):.4f}   <-- uses known toe Z")
    print(f"  improvement       = {wr('last')-wr('zproj'):+.4f}")
    print(f"\n=== residual r = TVT+Z structure ===")
    print(f"  within-well r std : median={np.median(r_within_std):.2f}  mean={np.mean(r_within_std):.2f}")
    print(f"  cross-well r_mean : min={d.r_mean.min():.1f} max={d.r_mean.max():.1f} std={d.r_mean.std():.1f}")
    print(f"  r drift prefix->toe: mean|drift|={d.r_toe_drift.abs().mean():.2f}  max|drift|={d.r_toe_drift.abs().max():.2f}")
    print(f"\n=== interpretation ===")
    print(f"  Z-proj win_rate over last_value: {(d.zproj<d.last).mean():.2f}")
    print(f"  If Z-proj << last_value, TVT is mostly -Z+c and the real target is r (small).")

if __name__ == "__main__":
    main()
