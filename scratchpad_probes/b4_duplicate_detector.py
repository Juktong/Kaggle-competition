"""B4' — precision-first train<->test duplicate detector + bounded TVT reconstruction.

Mechanism: at Kaggle scoring the hidden test wells are swapped in; some duplicate train wells
(this is the within-competition overlap that produces the public 7.2 plateau). This module detects
high-confidence duplicates from test-available fingerprints ONLY (MD,X,Y,Z,GR,TVT_input known-region)
and reconstructs the toe TVT from the matched train twin. Everything else falls back to DWT.

Precision is prioritized over recall: an accepted override must clear tight geometric agreement AND
be unique (2nd-best far worse) AND agree with the known-region TVT_input. Ambiguous/partial matches
return None (=> DWT fallback).

Reusable by both local validation (this file's __main__) and the Kaggle notebook.
"""
import os, glob
import numpy as np
import pandas as pd

TRAIN_DIR = "/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
TEST_DIR = "/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/test"

# ---- matching tolerances (tight; exact duplicates are byte-identical) ----
XYZ_TOL = 0.5      # ft: |dX|,|dY|,|dZ| per aligned row to count as agreeing
GR_TOL = 1.0       # API: |dGR| per aligned row
MD_ROUND = 2       # decimals to align MD
HEEL_GRID = 50.0   # ft cell for the fast heel-location prefilter (coarse; neighbours also scanned)
MIN_KNOWN = 20     # require at least this many known rows to attempt a match
ACCEPT_FRAC = 0.98 # >=98% of known rows must agree within tol
UNIQUE_MARGIN = 0.5  # best agree_frac must exceed 2nd-best by this (else ambiguous -> None)
TVT_INPUT_TOL = 1.0  # known-region TVT_input must agree within this on matched rows


def load_horizontal(path, with_truth=False):
    cols = ["MD", "X", "Y", "Z", "GR", "TVT_input"] + (["TVT"] if with_truth else [])
    df = pd.read_csv(path, usecols=lambda c: c in set(cols) or c in ("MD", "X", "Y", "Z", "GR", "TVT_input", "TVT"))
    return df


def load_train_wells(train_dir=TRAIN_DIR, limit=None):
    """well_id -> dict of arrays (md,x,y,z,gr,tvt,tvt_input, known_mask)."""
    paths = sorted(glob.glob(os.path.join(train_dir, "*__horizontal_well.csv")))
    if limit:
        paths = paths[:limit]
    wells = {}
    for p in paths:
        wid = os.path.basename(p).split("__")[0]
        df = pd.read_csv(p, usecols=["MD", "X", "Y", "Z", "GR", "TVT", "TVT_input"])
        ti = df["TVT_input"].values.astype(float)
        wells[wid] = dict(
            md=df["MD"].values.astype(float),
            x=df["X"].values.astype(float),
            y=df["Y"].values.astype(float),
            z=df["Z"].values.astype(float),
            gr=df["GR"].values.astype(float),
            tvt=df["TVT"].values.astype(float),
            tvt_input=ti,
            known=np.isfinite(ti),
        )
    return wells


def _heel_cell(x, y):
    return (int(np.floor(x / HEEL_GRID)), int(np.floor(y / HEEL_GRID)))


def build_index(wells):
    """heel-location prefilter: cell -> [well_ids]. Uses first known row (heel)."""
    index = {}
    for wid, w in wells.items():
        k = w["known"]
        if k.sum() == 0:
            continue
        i0 = np.argmax(k)  # first known row
        cell = _heel_cell(w["x"][i0], w["y"][i0])
        index.setdefault(cell, []).append(wid)
    return index


def _candidates(index, x0, y0):
    c0 = _heel_cell(x0, y0)
    out = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            out.extend(index.get((c0[0] + dx, c0[1] + dy), []))
    return out


def _agree_fraction(t_md, t_x, t_y, t_z, t_gr, cand):
    """Fraction of test known rows that MD-align to the candidate and agree geometrically.
    Returns (agree_frac, n_aligned, matched_row_index_map). Aligns by rounded MD."""
    md_key = {round(m, MD_ROUND): i for i, m in enumerate(cand["md"])}
    n = len(t_md)
    agree = 0
    aligned = 0
    for j in range(n):
        ci = md_key.get(round(t_md[j], MD_ROUND))
        if ci is None:
            continue
        aligned += 1
        if (abs(t_x[j] - cand["x"][ci]) <= XYZ_TOL and
                abs(t_y[j] - cand["y"][ci]) <= XYZ_TOL and
                abs(t_z[j] - cand["z"][ci]) <= XYZ_TOL and
                (not np.isfinite(t_gr[j]) or not np.isfinite(cand["gr"][ci]) or
                 abs(t_gr[j] - cand["gr"][ci]) <= GR_TOL)):
            agree += 1
    frac = agree / max(1, n)
    return frac, aligned


def match_test_well(test_arrays, wells, index, exclude=None):
    """Return (best_wid, info) for a high-confidence duplicate, else (None, info).

    test_arrays: dict with md,x,y,z,gr and known (bool mask of the test well's known rows).
    Only the known-region rows are used for matching (test-available)."""
    k = test_arrays["known"]
    if k.sum() < MIN_KNOWN:
        return None, dict(reason="too_few_known", n_known=int(k.sum()))
    t_md = test_arrays["md"][k]
    t_x = test_arrays["x"][k]
    t_y = test_arrays["y"][k]
    t_z = test_arrays["z"][k]
    t_gr = test_arrays["gr"][k]
    i0 = np.argmax(k)
    cand_ids = _candidates(index, test_arrays["x"][i0], test_arrays["y"][i0])
    scored = []
    for cid in cand_ids:
        if exclude is not None and cid == exclude:
            continue
        frac, aligned = _agree_fraction(t_md, t_x, t_y, t_z, t_gr, wells[cid])
        if aligned >= MIN_KNOWN:
            scored.append((frac, cid, aligned))
    if not scored:
        return None, dict(reason="no_candidate", n_cand=len(cand_ids))
    scored.sort(reverse=True)
    best_frac, best_cid, best_aligned = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    info = dict(best_frac=float(best_frac), second_frac=float(second), best=best_cid,
                n_aligned=int(best_aligned), n_cand=len(cand_ids), reason="ok")
    if best_frac < ACCEPT_FRAC:
        info["reason"] = "below_accept"
        return None, info
    if (best_frac - second) < UNIQUE_MARGIN and second >= ACCEPT_FRAC:
        info["reason"] = "ambiguous"
        return None, info
    # confirm known-region TVT_input agreement (extra guard)
    cand = wells[best_cid]
    md_key = {round(m, MD_ROUND): i for i, m in enumerate(cand["md"])}
    ti_test = test_arrays.get("tvt_input")
    if ti_test is not None:
        ok = bad = 0
        kb = np.isfinite(ti_test)
        for j in np.where(kb)[0]:
            ci = md_key.get(round(test_arrays["md"][j], MD_ROUND))
            if ci is None or not np.isfinite(cand["tvt_input"][ci]):
                continue
            if abs(ti_test[j] - cand["tvt_input"][ci]) <= TVT_INPUT_TOL:
                ok += 1
            else:
                bad += 1
        if ok + bad > 0 and bad / (ok + bad) > 0.02:
            info["reason"] = "tvt_input_mismatch"
            info["ti_bad_frac"] = bad / (ok + bad)
            return None, info
    return best_cid, info


def reconstruct_toe(test_arrays, cand):
    """Copy the matched train twin's TVT onto the test well's toe rows (MD-aligned).
    Returns (pred_full array aligned to test rows, n_filled, n_toe)."""
    md_key = {round(m, MD_ROUND): i for i, m in enumerate(cand["md"])}
    n = len(test_arrays["md"])
    out = np.full(n, np.nan)
    toe = ~test_arrays["known"]
    filled = 0
    for j in np.where(toe)[0]:
        ci = md_key.get(round(test_arrays["md"][j], MD_ROUND))
        if ci is not None and np.isfinite(cand["tvt"][ci]):
            out[j] = cand["tvt"][ci]
            filled += 1
    return out, filled, int(toe.sum())


# ------------------------------- validation -------------------------------
def _validate():
    print("Loading train wells ...", flush=True)
    wells = load_train_wells()
    index = build_index(wells)
    ids = list(wells.keys())
    print(f"  {len(wells)} wells; heel-index cells={len(index)}; "
          f"max wells/cell={max(len(v) for v in index.values())}")

    # (A) heel-key collision: how many wells share a heel cell (prefilter selectivity)
    coll = sum(len(v) - 1 for v in index.values() if len(v) > 1)
    print(f"[A] wells sharing a heel cell with >=1 other: {coll}")

    # (B) genuine train-train duplicate PAIRS (two ids, same trajectory) using the same detector
    print("[B] scanning for genuine train-train duplicate pairs ...", flush=True)
    dup_pairs = []
    for wid in ids:
        w = wells[wid]
        ta = dict(md=w["md"], x=w["x"], y=w["y"], z=w["z"], gr=w["gr"],
                  known=w["known"], tvt_input=w["tvt_input"])
        m, info = match_test_well(ta, wells, index, exclude=wid)  # exclude self => any match is a TWIN
        if m is not None:
            dup_pairs.append((wid, m, info["best_frac"]))
    print(f"    genuine twin matches (excl self): {len(dup_pairs)}")
    for a, b, f in dup_pairs[:20]:
        print(f"      {a} <-> {b}   agree_frac={f:.3f}")

    # (C) FALSE-POSITIVE test: each well as pseudo-test, matched against all OTHERS (exclude self).
    #     A match here to a DIFFERENT well is a false positive (unless it's a genuine twin from (B)).
    twin_set = set(a for a, b, f in dup_pairs) | set(b for a, b, f in dup_pairs)
    fp = 0
    for wid in ids:
        if wid in twin_set:
            continue  # genuine twins handled separately
        w = wells[wid]
        ta = dict(md=w["md"], x=w["x"], y=w["y"], z=w["z"], gr=w["gr"],
                  known=w["known"], tvt_input=w["tvt_input"])
        m, info = match_test_well(ta, wells, index, exclude=wid)
        if m is not None:
            fp += 1
            print(f"    FALSE POSITIVE: {wid} -> {m}  frac={info['best_frac']:.3f}")
    print(f"[C] FALSE POSITIVES on {len(ids)-len(twin_set)} non-twin wells: {fp}")

    # (D) TRUE-POSITIVE / reconstruction: each well matched against ALL incl self -> recover self,
    #     reconstruct toe, RMSE vs truth. (Self-match simulates an exact hidden duplicate.)
    tp = 0
    recon_rmses = []
    n_test = 0
    for wid in ids:
        w = wells[wid]
        # simulate a "test view": known region only; toe TVT hidden
        ta = dict(md=w["md"], x=w["x"], y=w["y"], z=w["z"], gr=w["gr"],
                  known=w["known"], tvt_input=w["tvt_input"])
        m, info = match_test_well(ta, wells, index, exclude=None)
        n_test += 1
        if m is None:
            continue
        tp += 1
        pred, filled, ntoe = reconstruct_toe(ta, wells[m])
        toe = ~w["known"]
        e = pred[toe] - w["tvt"][toe]
        e = e[np.isfinite(e)]
        if len(e):
            recon_rmses.append(np.sqrt(np.mean(e**2)))
    recon = np.array(recon_rmses)
    print(f"[D] TRUE POSITIVES (self-incl match): {tp}/{n_test}  "
          f"recon RMSE: mean={recon.mean():.4g} max={recon.max():.4g} "
          f">1ft={int((recon>1).sum())}")

    # (E) visible test wells: run the REAL test files through the detector
    print("[E] visible test wells (real test/ files):")
    for wid in ["000d7d20", "00bbac68", "00e12e8b"]:
        p = os.path.join(TEST_DIR, f"{wid}__horizontal_well.csv")
        df = pd.read_csv(p)
        ti = df["TVT_input"].values.astype(float)
        ta = dict(md=df["MD"].values.astype(float), x=df["X"].values.astype(float),
                  y=df["Y"].values.astype(float), z=df["Z"].values.astype(float),
                  gr=df["GR"].values.astype(float), known=np.isfinite(ti), tvt_input=ti)
        m, info = match_test_well(ta, wells, index, exclude=None)
        truth = wells[wid]["tvt"] if wid in wells else None
        if m is not None:
            pred, filled, ntoe = reconstruct_toe(ta, wells[m])
            toe = ~ta["known"]
            rmse = np.nan
            if truth is not None:
                e = pred[toe] - truth[toe]
                e = e[np.isfinite(e)]
                rmse = np.sqrt(np.mean(e**2)) if len(e) else np.nan
            print(f"    {wid} -> {m}  frac={info['best_frac']:.3f}  filled={filled}/{ntoe}  "
                  f"recon_RMSE_vs_truth={rmse:.4g}")
        else:
            print(f"    {wid} -> NO MATCH ({info['reason']})")


if __name__ == "__main__":
    _validate()
