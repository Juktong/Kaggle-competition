#!/usr/bin/env python3
"""Prototype: typewell segment-NCC dip alignment vs last_value baseline.

Goal: test whether using the *shape* of the paired typewell GR<->TVT curve
(a non-constant warp) beats the current last_value / scalar-shift baseline on
real ROGII train wells, using the native TVT_input mask as the hidden split.

Not integrated into the framework yet. Pure diagnostic.
"""
from __future__ import annotations
import argparse, glob, os
import numpy as np, pandas as pd

DATA = "data/rogii/train"


def ncc(a, b, min_pairs=15):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if int(m.sum()) < min_pairs:
        return np.nan
    aa = a[m] - a[m].mean(); bb = b[m] - b[m].mean()
    d = np.sqrt((aa * aa).sum() * (bb * bb).sum())
    return float((aa * bb).sum() / d) if d > 1e-9 else np.nan


def tw_interp(tw_tvt, tw_gr, tvt):
    return np.interp(np.asarray(tvt, float), tw_tvt, tw_gr, left=np.nan, right=np.nan)


def align_path(md, gr, anchor, tw_tvt, tw_gr, seg_len, k_grid, slope_cap,
               dev_cap, min_ncc, min_cov, lam, blend, max_dev_step):
    """Anchor-relative, hard-bounded, penalized typewell warp (no runaway).

    Each segment's TVT = anchor + dev + slope*ramp, where `dev` is an ABSOLUTE
    deviation from the anchor (never accumulated from a drifting level, so it
    cannot run away) and is hard-clamped to |dev| <= dev_cap. We score with
    NCC minus a movement penalty (lam*|dev|/dev_cap), require the segment to
    clear an absolute NCC gate, limit dev change between consecutive segments
    (max_dev_step), and finally blend the warp toward last_value by `blend`.
    Returns predicted TVT for every eval row plus fraction of segments warped.
    """
    n = len(md)
    pred = np.full(n, anchor, float)
    prev_dev = 0.0
    applied = 0; total = 0
    i = 0
    devs = np.linspace(-dev_cap, dev_cap, k_grid)
    while i < n:
        j = min(i + seg_len, n)
        smd = md[i:j]; sgr = gr[i:j]
        span = float(smd[-1] - smd[0]) if j - i > 1 else 0.0
        cov = np.isfinite(sgr).mean() if j - i > 0 else 0.0
        total += 1
        if cov < min_cov or span <= 0:
            pred[i:j] = anchor; i = j; continue
        d_bound = min(dev_cap, abs(slope_cap * span) + 1e-6)
        ramp = (smd - smd[0]) / (span if span else 1.0)
        best_pen, best_ncc, best_dev, best_slope = -9.0, np.nan, 0.0, 0.0
        for dev in devs:
            if abs(dev - prev_dev) > max_dev_step:      # continuity across segments
                continue
            for sl in np.linspace(-d_bound, d_bound, max(3, k_grid // 2)):
                tvt_seg = anchor + dev + sl * ramp
                s = ncc(sgr, tw_interp(tw_tvt, tw_gr, tvt_seg))
                if not np.isfinite(s):
                    continue
                pen = s - lam * abs(dev) / dev_cap       # penalize large moves
                if pen > best_pen:
                    best_pen, best_ncc, best_dev, best_slope = pen, s, dev, sl
        # gate: only warp when the aligned segment genuinely correlates
        if np.isfinite(best_ncc) and best_ncc >= min_ncc:
            seg = anchor + best_dev + best_slope * ramp
            seg = np.clip(seg, anchor - dev_cap, anchor + dev_cap)
            pred[i:j] = (1 - blend) * anchor + blend * seg   # blend toward last_value
            prev_dev = best_dev; applied += 1
        else:
            pred[i:j] = anchor
        i = j
    return np.clip(pred, tw_tvt.min(), tw_tvt.max()), applied / max(1, total)


def eval_well(path, args):
    df = pd.read_csv(path)
    tw = pd.read_csv(path.replace("__horizontal_well", "__typewell"))
    if not {"TVT", "GR"}.issubset(tw.columns):
        return None
    tw = tw[["TVT", "GR"]].apply(pd.to_numeric, errors="coerce").dropna().sort_values("TVT")
    if len(tw) < 30:
        return None
    tw_tvt = tw["TVT"].to_numpy(float); tw_gr = tw["GR"].to_numpy(float)
    tvt = pd.to_numeric(df["TVT"], errors="coerce").to_numpy(float)
    ti = pd.to_numeric(df["TVT_input"], errors="coerce").to_numpy(float)
    md = pd.to_numeric(df["MD"], errors="coerce").to_numpy(float)
    gr = pd.to_numeric(df["GR"], errors="coerce").to_numpy(float)
    known = np.isfinite(ti)
    if not known.any() or known.all():
        return None
    cut = int(np.argmax(~known))  # first hidden row
    if cut < 20 or (len(df) - cut) < 20:
        return None
    anchor = float(ti[cut - 1]) if np.isfinite(ti[cut - 1]) else float(tvt[cut - 1])
    ev = slice(cut, len(df))
    true = tvt[ev]
    ap_args = (tw_tvt, tw_gr, args.seg_len, args.k_grid, args.slope_cap,
               args.dev_cap, args.min_ncc, args.min_cov, args.lam, args.blend,
               args.max_dev_step)

    def run(md_s, gr_s, true_s, anc):
        ok = np.isfinite(true_s)
        if ok.sum() < 20:
            return None
        base = np.full(len(true_s), anc)
        algn, appl = align_path(md_s, gr_s, anc, *ap_args)
        rmse = lambda p: float(np.sqrt(np.mean((p[ok] - true_s[ok]) ** 2)))
        return rmse(base), rmse(algn), appl

    # true hidden split (native TVT_input mask)
    r_eval = run(md[ev], gr[ev], tvt[ev], anchor)
    if r_eval is None:
        return None
    # prefix hold-out: hide the toe-side tail of the KNOWN prefix and score there
    hcut = int(cut * 0.6)
    hres = None
    if hcut >= 20 and (cut - hcut) >= 20 and np.isfinite(tvt[hcut - 1]):
        hs = slice(hcut, cut)
        hres = run(md[hs], gr[hs], tvt[hs], float(tvt[hcut - 1]))
    b_e, a_e, appl = r_eval
    row = dict(well=os.path.basename(path)[:8], rows=int(np.isfinite(tvt[ev]).sum()),
               base=b_e, algn=a_e, applied=appl,
               holdout_delta=(hres[1] - hres[0]) if hres else np.nan)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-wells", type=int, default=60)
    ap.add_argument("--seg-len", type=int, default=120)
    ap.add_argument("--k-grid", type=int, default=25)
    ap.add_argument("--slope-cap", type=float, default=0.3)
    ap.add_argument("--dev-cap", type=float, default=15.0)
    ap.add_argument("--max-dev-step", type=float, default=6.0)
    ap.add_argument("--lam", type=float, default=0.25)
    ap.add_argument("--blend", type=float, default=0.6)
    ap.add_argument("--min-ncc", type=float, default=0.7)
    ap.add_argument("--min-cov", type=float, default=0.35)
    ap.add_argument("--gate-tol", type=float, default=0.05)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(DATA, "*__horizontal_well.csv")))[: args.n_wells]
    rows = [r for r in (eval_well(f, args) for f in files) if r]
    d = pd.DataFrame(rows)
    d["delta"] = d["algn"] - d["base"]           # negative = alignment better
    w = d["rows"].to_numpy(float)
    wrmse = lambda c: float(np.sqrt(np.sum(w * d[c] ** 2) / w.sum()))
    print(f"wells={len(d)} seg={args.seg_len} k={args.k_grid} slope_cap={args.slope_cap} "
          f"dev_cap={args.dev_cap} step={args.max_dev_step} lam={args.lam} blend={args.blend} "
          f"min_ncc={args.min_ncc} min_cov={args.min_cov}")
    print(f"  mean fraction of segments warped = {d['applied'].mean():.2f}")
    print(f"  weighted RMSE  base(last_value) = {wrmse('base'):.4f}")
    print(f"  weighted RMSE  typewell_align   = {wrmse('algn'):.4f}")
    print(f"  mean per-well delta   = {d['delta'].mean():+.4f}")
    print(f"  median per-well delta = {d['delta'].median():+.4f}")
    print(f"  win rate (align<base) = {(d['delta'] < -1e-6).mean():.3f}")
    print(f"  catastrophic (>+5)    = {(d['delta'] > 5).mean():.3f}")
    # --- router-gate simulation: trust alignment only where prefix hold-out says so ---
    g = d[np.isfinite(d["holdout_delta"])].copy()
    gate = g["holdout_delta"] < -args.gate_tol      # holdout says align beats base
    print(f"\n  [router-gate sim] wells with holdout signal: {len(g)}  gate_tol={args.gate_tol}")
    for name, sub in [("GATE ON  (holdout: align better)", g[gate]),
                      ("GATE OFF (holdout: base better)", g[~gate])]:
        if len(sub):
            print(f"    {name}: n={len(sub):3d}  eval win_rate={ (sub['delta']<-1e-6).mean():.2f}  "
                  f"mean eval delta={sub['delta'].mean():+.4f}  catastrophic={ (sub['delta']>5).mean():.2f}")
    if len(g):
        wg = g["rows"].to_numpy(float)
        routed = np.where(gate, g["algn"], g["base"])      # apply align only when gated on
        base_g = float(np.sqrt(np.sum(wg * g["base"] ** 2) / wg.sum()))
        routed_g = float(np.sqrt(np.sum(wg * routed ** 2) / wg.sum()))
        print(f"    ROUTED weighted RMSE = {routed_g:.4f}   vs base {base_g:.4f}   "
              f"delta = {routed_g - base_g:+.4f}")
    # --- is the benefit concentrated on high-drift (high base-RMSE) wells? ---
    print("\n  [drift stratification]  base-RMSE quartile -> align benefit")
    q = d["base"].quantile([0.25, 0.5, 0.75]).to_list()
    for lo, hi, lbl in [(-1, q[0], "Q1 low-drift"), (q[0], q[1], "Q2"),
                        (q[1], q[2], "Q3"), (q[2], 1e9, "Q4 high-drift")]:
        sub = d[(d["base"] > lo) & (d["base"] <= hi)]
        if len(sub):
            print(f"    {lbl:14s} base<= {hi:6.1f}  n={len(sub):3d}  "
                  f"win_rate={(sub['delta']<-1e-6).mean():.2f}  mean delta={sub['delta'].mean():+.4f}")
    print("\n  best 8 improvements:")
    for _, r in d.sort_values("delta").head(8).iterrows():
        print(f"    {r.well}  base={r.base:7.3f} align={r.algn:7.3f} delta={r.delta:+7.3f} hold={r.holdout_delta:+.3f}")


if __name__ == "__main__":
    main()
