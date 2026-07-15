"""B4' — guarded honest+overlap override (per-well, precision-first).

Self-contained so it can be (a) validated locally and (b) pasted verbatim into the DWT honest
notebook as a final post-processing cell. Mechanism:

  final = DWT everywhere, EXCEPT wells detected as high-confidence train duplicates, whose toe TVT
  is reconstructed from the matched train twin.

Two match tiers (both gated by the SAME proven-tight agreement test):
  1. same-id  : train/{well}__horizontal_well.csv exists (reused id) — the public-plateau mechanism.
  2. fingerprint : no same-id train file — scan train wells by heel location, accept only a unique
                   high-confidence geometric+TVT match (catches different-id duplicates).

Gate (adopted from the proven public guarded-recovery, david_v12): on the test well's KNOWN region,
interpolate the train twin's Z/GR/TVT onto the test MD grid and require
    tvt_rmse < TVT_RMSE_GATE (0.02 ft)  AND  z_mad < Z_MAD_GATE  AND  gr_mad < GR_MAD_GATE
    AND >= MIN_VISIBLE overlapping known rows.
Reconstruction = np.interp(test_toe_MD, train_MD, train_TVT). Everything failing the gate keeps DWT.

Per-well (NOT all-or-nothing): novel wells simply keep DWT, so on a novel-heavy private set B4' == DWT.
"""
import os, glob
import numpy as np
import pandas as pd

# ---- proven-tight gate ----
TVT_RMSE_GATE = 0.02   # ft: known-region TVT_input vs interp(train TVT) RMSE
Z_MAD_GATE = 0.02      # ft
GR_MAD_GATE = 0.50     # API
MIN_VISIBLE = 50       # overlapping known rows required
HEEL_GRID = 50.0       # ft cell for fingerprint-tier heel prefilter


def _interp(md_to, md_from, vals):
    return np.interp(md_to, md_from, vals, left=np.nan, right=np.nan)


def _gate(te, tr):
    """te: test well df (MD,X,Y,Z,GR,TVT_input). tr: train twin df (MD,Z,GR,TVT). Return (ok, rep)."""
    md = te["MD"].to_numpy(float)
    tr_md = tr["MD"].to_numpy(float)
    z_tr = _interp(md, tr_md, tr["Z"].to_numpy(float))
    m = np.isfinite(z_tr) & te["Z"].notna().to_numpy()
    if int(m.sum()) < MIN_VISIBLE:
        return False, {"reason": "no_overlap", "visible": int(m.sum())}
    gr_src = tr["GR"].interpolate(limit_direction="both").to_numpy(float)
    gr_tr = _interp(md, tr_md, gr_src)
    g = m & te["GR"].notna().to_numpy() & np.isfinite(gr_tr)
    tvt_tr = _interp(md, tr_md, tr["TVT"].to_numpy(float))
    v = te["TVT_input"].notna().to_numpy() & np.isfinite(tvt_tr)
    if int(v.sum()) < MIN_VISIBLE:
        return False, {"reason": "no_visible_tvt", "visible": int(v.sum())}
    z_mad = float(np.mean(np.abs(te["Z"].to_numpy(float)[m] - z_tr[m])))
    gr_mad = float(np.mean(np.abs(te["GR"].to_numpy(float)[g] - gr_tr[g]))) if g.any() else float("inf")
    tvt_rmse = float(np.sqrt(np.mean((te["TVT_input"].to_numpy(float)[v] - tvt_tr[v]) ** 2)))
    rep = {"reason": "ok", "tvt_rmse": tvt_rmse, "z_mad": z_mad, "gr_mad": gr_mad,
           "visible": int(v.sum()), "cover": float(m.mean())}
    ok = (tvt_rmse < TVT_RMSE_GATE) and (z_mad < Z_MAD_GATE) and (gr_mad < GR_MAD_GATE)
    return ok, rep


def _heel_cell(x, y):
    return (int(np.floor(x / HEEL_GRID)), int(np.floor(y / HEEL_GRID)))


def _load_train_index(train_dir):
    """Return (paths_by_id, heel_index). heel_index: cell -> [well_ids]. Reads only heel XY (cheap)."""
    paths = {os.path.basename(p).split("__")[0]: p
             for p in glob.glob(os.path.join(train_dir, "*__horizontal_well.csv"))}
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
        heel.setdefault(_heel_cell(d["X"].values[i0], d["Y"].values[i0]), []).append(wid)
    return paths, heel


def _read_train(path):
    return pd.read_csv(path, usecols=["MD", "X", "Y", "Z", "GR", "TVT", "TVT_input"])


def apply_b4_override(sub, data_dir, dwt_col="tvt", verbose=True):
    """sub: DataFrame [id, tvt] (DWT base). data_dir: has train/ and test/. Returns (sub2, audit list)."""
    sub = sub.copy()
    sub["_well"] = sub["id"].str.rsplit("_", n=1).str[0]
    sub["_ridx"] = sub["id"].str.rsplit("_", n=1).str[1].astype(int)
    train_dir = os.path.join(data_dir, "train")
    test_dir = os.path.join(data_dir, "test")
    paths_by_id, heel = _load_train_index(train_dir)

    audit = []
    override_vals = {}  # id -> tvt
    wells = list(sub["_well"].drop_duplicates())
    for wid in wells:
        te_path = os.path.join(test_dir, f"{wid}__horizontal_well.csv")
        if not os.path.exists(te_path):
            audit.append({"well": wid, "tier": "-", "accepted": False, "reason": "no_test_file"})
            continue
        te = pd.read_csv(te_path)

        matched_id, rep, tier = None, None, None
        # tier 1: same-id
        if wid in paths_by_id:
            tr = _read_train(paths_by_id[wid])
            ok, r = _gate(te, tr)
            if ok:
                matched_id, rep, tier = wid, r, "same-id"
        # tier 2: fingerprint (only if same-id did not accept)
        if matched_id is None:
            k = te["TVT_input"].notna().to_numpy()
            if k.any():
                i0 = int(np.argmax(k))
                c0 = _heel_cell(te["X"].values[i0], te["Y"].values[i0])
                cand = []
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        cand.extend(heel.get((c0[0] + dx, c0[1] + dy), []))
                passers = []
                for cid in cand:
                    if cid == wid:
                        continue
                    ok, r = _gate(te, _read_train(paths_by_id[cid]))
                    if ok:
                        passers.append((r["tvt_rmse"], cid, r))
                if len(passers) == 1:  # unique high-confidence match
                    _, cid, r = passers[0]
                    matched_id, rep, tier = cid, r, "fingerprint"
                elif len(passers) > 1:
                    audit.append({"well": wid, "tier": "fingerprint", "accepted": False,
                                  "reason": "ambiguous", "n_pass": len(passers)})
                    continue

        if matched_id is None:
            audit.append({"well": wid, "tier": "-", "accepted": False, "reason": "no_match"})
            continue

        # reconstruct toe TVT from matched twin via MD interpolation
        tr = _read_train(paths_by_id[matched_id])
        g = sub[sub["_well"] == wid]
        te_md = te["MD"].to_numpy(float)
        recon_full = _interp(te_md, tr["MD"].to_numpy(float), tr["TVT"].to_numpy(float))
        n_ov = 0
        for rid, ri in zip(g["id"].values, g["_ridx"].values):
            if 0 <= ri < len(recon_full) and np.isfinite(recon_full[ri]):
                override_vals[rid] = float(recon_full[ri])
                n_ov += 1
        audit.append({"well": wid, "tier": tier, "matched": matched_id, "accepted": True,
                      "rows_overridden": n_ov, "n_rows": int(len(g)),
                      "tvt_rmse": rep["tvt_rmse"], "z_mad": rep["z_mad"], "gr_mad": rep["gr_mad"]})

    if override_vals:
        mask = sub["id"].isin(override_vals)
        sub.loc[mask, dwt_col] = sub.loc[mask, "id"].map(override_vals)
    n_acc = sum(1 for a in audit if a.get("accepted"))
    n_rows = sum(a.get("rows_overridden", 0) for a in audit)
    if verbose:
        print(f"[B4' override] wells={len(wells)}  accepted={n_acc}  rows_overridden={n_rows}")
        for a in audit:
            if a.get("accepted"):
                print(f"   OVERRIDE {a['well']} <-{a['tier']}- {a.get('matched')}  "
                      f"rows={a['rows_overridden']}/{a['n_rows']}  tvt_rmse={a['tvt_rmse']:.4g}")
    return sub.drop(columns=["_well", "_ridx"]), audit
