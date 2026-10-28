"""V5 — Visible-well pre-submit audit tool (reusable mandatory gate).

The 3 visible test wells (000d7d20, 00bbac68, 00e12e8b) are ALSO in train/ with full TVT truth.
Any candidate submission.csv produced locally predicts those wells, so we can score it against
real truth BEFORE spending a Kaggle slot. This tool runs the standard pre-submit checks:

  1. FORMAT      — columns == {id, tvt}; row set / order match sample_submission.csv.
  2. FINITE      — every tvt is finite (no NaN / inf).
  3. RANGE       — tvt within a sane band (derived from visible-well truth, generous margin).
  4. DIFF-vs-DWT — if a baseline (DWT) submission is given: RMSE / max-abs / %rows-changed
                   (flags a no-op copy OR a wild divergence).
  5. VISIBLE-RMSE — per-well and pooled RMSE on the 3 visible wells vs train truth. This is the
                   only REAL-test signal available locally.

Usage
-----
  python3 scripts/visible_well_audit.py --candidate sub.csv [--baseline dwt_sub.csv]
  # programmatic:
  from scripts.visible_well_audit import audit; rep = audit("sub.csv", baseline="dwt_sub.csv")

Exit code 0 iff all HARD checks pass (format + finite). RANGE / DIFF / VISIBLE-RMSE are reported
as WARN/INFO — a large visible-RMSE or wild DWT divergence should block a submit by human judgement.
Truth is read from the local train/ dir; the id suffix `{well}_{ridx}` maps to train row `iloc[ridx]`.
"""
import argparse, os, sys
import numpy as np, pandas as pd

DEFAULT_TRAIN = "/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train"
DEFAULT_SAMPLE = "/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/sample_submission.csv"
VISIBLE = ["000d7d20", "00bbac68", "00e12e8b"]


def _load_sub(path):
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    if "id" not in cols or "tvt" not in cols:
        raise ValueError(f"{path}: expected columns id,tvt — got {list(df.columns)}")
    df = df.rename(columns={cols["id"]: "id", cols["tvt"]: "tvt"})[["id", "tvt"]]
    return df


def _well_of(ids):
    return ids.str.rsplit("_", n=1).str[0]


def _ridx_of(ids):
    return ids.str.rsplit("_", n=1).str[1].astype(int)


def truth_for_visible(train_dir=DEFAULT_TRAIN, wells=VISIBLE):
    """Map {well}_{ridx} -> train TVT truth for the visible wells (which live in train/)."""
    out = {}
    for w in wells:
        p = os.path.join(train_dir, f"{w}__horizontal_well.csv")
        if not os.path.exists(p):
            continue
        h = pd.read_csv(p, usecols=["TVT"])
        out[w] = h["TVT"].values.astype(float)
    return out


def audit(candidate, baseline=None, train_dir=DEFAULT_TRAIN, sample=DEFAULT_SAMPLE,
          wells=VISIBLE, verbose=True):
    rep = {"hard_ok": True, "warnings": [], "checks": {}}
    def log(*a):
        if verbose: print(*a, flush=True)

    cand = _load_sub(candidate)
    log("=" * 78)
    log(f"V5 PRE-SUBMIT AUDIT  candidate={candidate}")
    log("=" * 78)

    # 1. FORMAT vs sample_submission
    smp = _load_sub(sample) if os.path.exists(sample) else None
    if smp is not None:
        same_set = set(cand["id"]) == set(smp["id"])
        same_order = len(cand) == len(smp) and (cand["id"].values == smp["id"].values).all()
        n_missing = len(set(smp["id"]) - set(cand["id"]))
        n_extra = len(set(cand["id"]) - set(smp["id"]))
        rep["checks"]["format"] = dict(rows=len(cand), sample_rows=len(smp),
                                       same_set=bool(same_set), same_order=bool(same_order),
                                       missing=n_missing, extra=n_extra)
        hard = same_set  # row SET must match; order is a warning (Kaggle joins on id)
        rep["hard_ok"] &= hard
        log(f"[1] FORMAT   rows={len(cand)} (sample {len(smp)})  same_set={same_set}  "
            f"same_order={same_order}  missing={n_missing} extra={n_extra}  "
            f"{'OK' if hard else 'FAIL(row set != sample)'}")
        if not same_order and same_set:
            rep["warnings"].append("row order differs from sample_submission (Kaggle joins on id, usually fine)")
    else:
        log("[1] FORMAT   sample_submission not found — skipped set/order check")
        rep["checks"]["format"] = dict(rows=len(cand), sample_rows=None)

    # 2. FINITE
    fin = np.isfinite(cand["tvt"].values)
    n_bad = int((~fin).sum())
    rep["checks"]["finite"] = dict(n_nonfinite=n_bad)
    rep["hard_ok"] &= (n_bad == 0)
    log(f"[2] FINITE   non-finite tvt = {n_bad}  {'OK' if n_bad == 0 else 'FAIL'}")

    # truth for visible wells (needed for range band + visible RMSE)
    truth = truth_for_visible(train_dir, wells)
    tvals = np.concatenate([v[np.isfinite(v)] for v in truth.values()]) if truth else np.array([])

    # 3. RANGE
    v = cand["tvt"].values
    v = v[np.isfinite(v)]
    if len(tvals):
        lo, hi = tvals.min() - 1000, tvals.max() + 1000
    else:
        lo, hi = -1e4, 5e4
    n_oor = int(((v < lo) | (v > hi)).sum())
    rep["checks"]["range"] = dict(min=float(v.min()) if len(v) else None,
                                  max=float(v.max()) if len(v) else None,
                                  mean=float(v.mean()) if len(v) else None,
                                  band=[float(lo), float(hi)], n_out_of_band=n_oor)
    log(f"[3] RANGE    tvt min/mean/max = {v.min():.1f}/{v.mean():.1f}/{v.max():.1f}  "
        f"sane band [{lo:.0f},{hi:.0f}]  out-of-band = {n_oor}"
        + ("  WARN" if n_oor else "  OK"))
    if n_oor:
        rep["warnings"].append(f"{n_oor} tvt values outside sane band")

    # 4. DIFF vs DWT baseline
    if baseline:
        base = _load_sub(baseline)
        m = cand.merge(base, on="id", suffixes=("_c", "_b"))
        d = m["tvt_c"].values - m["tvt_b"].values
        d = d[np.isfinite(d)]
        rmse_b = float(np.sqrt(np.mean(d**2)))
        maxabs = float(np.max(np.abs(d))) if len(d) else 0.0
        frac_ch = float(np.mean(np.abs(d) > 1e-6)) if len(d) else 0.0
        rep["checks"]["diff_vs_baseline"] = dict(rmse=rmse_b, max_abs=maxabs,
                                                 frac_changed=frac_ch, n_joined=len(m))
        log(f"[4] DIFF-DWT rmse-vs-baseline={rmse_b:.3f}  max|Δ|={maxabs:.2f}  "
            f"%rows changed={100*frac_ch:.1f}  (joined {len(m)})")
        if frac_ch == 0:
            rep["warnings"].append("candidate is identical to baseline (no-op)")
        if rmse_b > 50:
            rep["warnings"].append(f"candidate diverges strongly from DWT (rmse {rmse_b:.1f}) — inspect")
    else:
        log("[4] DIFF-DWT (no baseline given — skipped)")

    # 5. VISIBLE-WELL RMSE vs truth
    cw = _well_of(cand["id"])
    cr = _ridx_of(cand["id"])
    per = {}
    all_err = []
    for w in wells:
        if w not in truth:
            continue
        sel = (cw == w).values
        if sel.sum() == 0:
            continue
        ri = cr.values[sel]
        pv = cand["tvt"].values[sel]
        tr = truth[w]
        ok = ri < len(tr)
        e = pv[ok] - tr[ri[ok]]
        e = e[np.isfinite(e)]
        if len(e):
            per[w] = dict(n=int(len(e)), rmse=float(np.sqrt(np.mean(e**2))))
            all_err.append(e)
    pooled = float(np.sqrt(np.mean(np.concatenate(all_err)**2))) if all_err else None
    rep["checks"]["visible_rmse"] = dict(per_well=per, pooled=pooled)
    log("[5] VISIBLE-WELL RMSE vs train truth:")
    for w, s in per.items():
        log(f"       {w}  n={s['n']:6d}  RMSE={s['rmse']:.3f}")
    if pooled is not None:
        log(f"       POOLED (3 visible wells) RMSE = {pooled:.3f}")
    else:
        log("       (no visible wells found in candidate — cannot score)")

    log("-" * 78)
    log(f"HARD checks (format+finite): {'PASS' if rep['hard_ok'] else 'FAIL'}   "
        f"warnings: {len(rep['warnings'])}")
    for wmsg in rep["warnings"]:
        log(f"   WARN: {wmsg}")
    log("=" * 78)
    return rep


def main():
    ap = argparse.ArgumentParser(description="V5 visible-well pre-submit audit")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--baseline", default=None, help="DWT baseline submission.csv for diff-vs-DWT")
    ap.add_argument("--train-dir", default=DEFAULT_TRAIN)
    ap.add_argument("--sample", default=DEFAULT_SAMPLE)
    a = ap.parse_args()
    rep = audit(a.candidate, baseline=a.baseline, train_dir=a.train_dir, sample=a.sample)
    sys.exit(0 if rep["hard_ok"] else 1)


if __name__ == "__main__":
    main()
