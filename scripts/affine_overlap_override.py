"""DWT + bounded affine-overlap override (hedge candidate for final-2 slot-2).

Unlike B4' (exact `tvt_rmse<0.02`, which captured no hidden overlap because the overlap is affine
near-duplicates, not byte-identical), this matches train wells by trajectory geometry on the known
region and fits an AFFINE map `TVT_test_known ≈ a·TVT_train + b`, then reconstructs the toe as
`a·TVT_train_toe + b`. This captures datum-shifted / lightly-scaled duplicates (the plateau overlap).

IMPORTANT (validated on train): the known region does NOT reliably predict the toe — some geometric
matches with a near-perfect affine fit still diverge in the toe (heel↔toe wall). So this override has
irreducible false-positive risk (~15-30% of matches) and is a HEDGE, not a precision-safe upgrade.
It is meant to be paired with pure DWT under best-of-2 (DWT floors novel-heavy private; this captures
overlap-heavy private on a stronger base than the weak-base Gate-Safe hedge).

Two tightness presets: `conservative` (fewer, higher-confidence overrides) and `balanced` (more
coverage). Bounded: override falls back to DWT on any gate failure / ambiguity.
"""
import os, glob
import numpy as np
import pandas as pd

PRESETS = {
    # xz_tol: median |dX|,|dZ| over known rows;  gr_tol: median |dGR|;  aff_res: known-region affine residual RMSE (ft)
    # a_tol: |a-1|;  b_max: |b| (ft);  min_known: overlapping known rows;  uniq_margin: best aff_res must beat 2nd by this
    "conservative": dict(xz_tol=0.5, gr_tol=3.0, aff_res=1.5, a_tol=0.03, b_max=250.0, min_known=100, uniq_margin=1.0),
    "balanced":     dict(xz_tol=0.5, gr_tol=8.0, aff_res=3.0, a_tol=0.06, b_max=800.0, min_known=60,  uniq_margin=0.5),
}
HEEL_GRID = 50.0


def _cell(x, y):
    return (int(np.floor(x / HEEL_GRID)), int(np.floor(y / HEEL_GRID)))


def _load_index(train_dir):
    paths = {os.path.basename(p).split("__")[0]: p for p in glob.glob(os.path.join(train_dir, "*__horizontal_well.csv"))}
    heel = {}
    for wid, p in paths.items():
        try:
            d = pd.read_csv(p, usecols=["X", "Y", "TVT_input"])
        except Exception:
            continue
        k = d["TVT_input"].notna().to_numpy()
        if not k.any():
            continue
        i0 = int(np.argmax(k))
        heel.setdefault(_cell(d["X"].values[i0], d["Y"].values[i0]), []).append(wid)
    return paths, heel


def _read(path):
    return pd.read_csv(path, usecols=["MD", "X", "Y", "Z", "GR", "TVT", "TVT_input"])


def _match_affine(te, cand, P):
    """te: test well df; cand: train df. Return (ok, info) with affine a,b and residual if it passes the gate."""
    kn = te["TVT_input"].notna().to_numpy()
    if kn.sum() < P["min_known"]:
        return False, None
    kmd = te["MD"].values[kn]
    mdc = {round(m, 2): i for i, m in enumerate(cand["MD"].values)}
    ci = np.array([mdc.get(round(m, 2), -1) for m in kmd])
    ok = ci >= 0
    if ok.sum() < P["min_known"]:
        return False, None
    cig = ci[ok]
    dx = np.abs(te["X"].values[kn][ok] - cand["X"].values[cig])
    dz = np.abs(te["Z"].values[kn][ok] - cand["Z"].values[cig])
    dgr = np.abs(te["GR"].values[kn][ok] - cand["GR"].values[cig])
    if not (np.median(dx) < P["xz_tol"] and np.median(dz) < P["xz_tol"]):
        return False, None
    if not (np.nanmedian(dgr) < P["gr_tol"]):
        return False, None
    x = cand["TVT"].values[cig]
    y = te["TVT_input"].values[kn][ok]
    a, b = np.polyfit(x, y, 1)
    res = float(np.sqrt(np.mean((y - (a * x + b)) ** 2)))
    if res > P["aff_res"] or abs(a - 1.0) > P["a_tol"] or abs(b) > P["b_max"]:
        return False, dict(res=res, a=a, b=b)
    return True, dict(res=res, a=float(a), b=float(b), n=int(ok.sum()))


def apply_affine_override(sub, data_dir, preset="conservative", verbose=True):
    P = PRESETS[preset]
    sub = sub.copy()
    well = sub["id"].str.rsplit("_", n=1).str[0]
    ridx = sub["id"].str.rsplit("_", n=1).str[1].astype(int)
    train_dir = os.path.join(str(data_dir), "train")
    test_dir = os.path.join(str(data_dir), "test")
    paths, heel = _load_index(train_dir)
    audit = []
    override = {}
    for wid in pd.unique(well):
        tep = os.path.join(test_dir, f"{wid}__horizontal_well.csv")
        if not os.path.exists(tep):
            continue
        te = pd.read_csv(tep)
        kn = te["TVT_input"].notna().to_numpy()
        if kn.sum() < P["min_known"]:
            continue
        i0 = int(np.argmax(kn))
        c0 = _cell(te["X"].values[i0], te["Y"].values[i0])
        passers = []
        # tier 1: same-id affine (hidden well reuses a train id but may be datum-shifted)
        if wid in paths:
            ok, info = _match_affine(te, _read(paths[wid]), P)
            if ok:
                passers.append((info["res"], wid, info))
        # tier 2: fingerprint affine (different-id near-duplicates, heel-indexed)
        cand_ids = [c for dx in (-1, 0, 1) for dy in (-1, 0, 1) for c in heel.get((c0[0] + dx, c0[1] + dy), []) if c != wid]
        for cid in cand_ids:
            ok, info = _match_affine(te, _read(paths[cid]), P)
            if ok:
                passers.append((info["res"], cid, info))
        if not passers:
            continue
        passers.sort(key=lambda z: z[0])
        best_res, best_cid, best_info = passers[0]
        second = passers[1][0] if len(passers) > 1 else 1e9
        if len(passers) > 1 and (second - best_res) < P["uniq_margin"]:
            audit.append(dict(well=wid, accepted=False, reason="ambiguous", n_pass=len(passers)))
            continue
        cand = _read(paths[best_cid])
        mdc = {round(m, 2): i for i, m in enumerate(cand["MD"].values)}
        a, b = best_info["a"], best_info["b"]
        ov_ids = sub["id"][well == wid].values
        ov_ri = ridx[well == wid].values
        n_ov = 0
        for rid, ri in zip(ov_ids, ov_ri):
            if 0 <= ri < len(te):
                cj = mdc.get(round(te["MD"].values[ri], 2), -1)
                if cj >= 0 and np.isfinite(cand["TVT"].values[cj]):
                    override[rid] = float(a * cand["TVT"].values[cj] + b)
                    n_ov += 1
        audit.append(dict(well=wid, accepted=True, matched=best_cid, a=a, b=b, res=best_info["res"],
                          rows=n_ov, n=int((well == wid).sum())))
    if override:
        m = sub["id"].isin(override)
        sub.loc[m, "tvt"] = sub.loc[m, "id"].map(override)
    n_acc = sum(1 for a in audit if a.get("accepted"))
    if verbose:
        print(f"[affine override / {preset}] wells overridden={n_acc}, rows={sum(a.get('rows',0) for a in audit)}")
        for a in audit:
            if a.get("accepted"):
                print(f"   {a['well']} <- {a['matched']}  a={a['a']:.3f} b={a['b']:.1f} res={a['res']:.2f} rows={a['rows']}")
    return sub, audit
