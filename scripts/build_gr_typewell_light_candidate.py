#!/usr/bin/env python3
"""Build a gated light GR/typewell correction candidate from a baseline submission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_ids(ids: pd.Series) -> pd.DataFrame:
    parts = ids.astype(str).str.rsplit("_", n=1, expand=True)
    if parts.shape[1] != 2:
        raise ValueError("ids must look like <well>_<row_idx>")
    return pd.DataFrame({
        "id": ids.astype(str).to_numpy(),
        "well": parts[0].to_numpy(),
        "row_idx": parts[1].astype(int).to_numpy(),
    })


def data_file(data_dir: Path, split: str, well: str, suffix: str) -> Path:
    nested = data_dir / split / f"{well}__{suffix}.csv"
    if nested.exists():
        return nested
    flat = data_dir / f"{well}__{suffix}.csv"
    if flat.exists():
        return flat
    raise FileNotFoundError(f"missing {split}/{well}__{suffix}.csv under {data_dir}")


def read_submission(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if list(df.columns) != ["id", "tvt"]:
        raise ValueError(f"{path} must have columns ['id', 'tvt']; got {list(df.columns)}")
    df["id"] = df["id"].astype(str)
    df["tvt"] = pd.to_numeric(df["tvt"], errors="raise").astype(float)
    if df["id"].duplicated().any():
        raise ValueError(f"{path} has duplicate ids")
    if not np.isfinite(df["tvt"].to_numpy(float)).all():
        raise ValueError(f"{path} has non-finite tvt")
    return df


def interp_typewell_gr(tw: pd.DataFrame, tvt: np.ndarray) -> np.ndarray:
    tw = tw[["TVT", "GR"]].copy()
    tw["TVT"] = pd.to_numeric(tw["TVT"], errors="coerce")
    tw["GR"] = pd.to_numeric(tw["GR"], errors="coerce")
    tw = tw.dropna().sort_values("TVT")
    if len(tw) < 5:
        return np.full(len(tvt), np.nan)
    x = tw["TVT"].to_numpy(float)
    y = tw["GR"].to_numpy(float)
    uniq = np.r_[True, np.diff(x) > 0]
    x = x[uniq]
    y = y[uniq]
    if len(x) < 5:
        return np.full(len(tvt), np.nan)
    return np.interp(tvt, x, y, left=np.nan, right=np.nan)


def robust_mae(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if int(m.sum()) < 10:
        return float("nan")
    d = a[m] - b[m]
    return float(np.nanmedian(np.abs(d)))


def best_shift(
    hw_gr: np.ndarray,
    tw: pd.DataFrame,
    tvt_path: np.ndarray,
    shifts: np.ndarray,
) -> tuple[float, float, float, float]:
    scores = []
    for shift in shifts:
        tw_gr = interp_typewell_gr(tw, tvt_path + float(shift))
        scores.append(robust_mae(hw_gr, tw_gr))
    scores_arr = np.asarray(scores, dtype=float)
    if not np.isfinite(scores_arr).any():
        return 0.0, float("nan"), float("nan"), 0.0
    zero_idx = int(np.argmin(np.abs(shifts)))
    zero_score = float(scores_arr[zero_idx])
    best_idx = int(np.nanargmin(scores_arr))
    best_score = float(scores_arr[best_idx])
    denom = abs(zero_score) + 1e-6
    improvement = float((zero_score - best_score) / denom) if np.isfinite(zero_score) else 0.0
    return float(shifts[best_idx]), zero_score, best_score, improvement


def smooth_move(n: int, shift: float, alpha: float, max_move: float) -> np.ndarray:
    if n <= 0:
        return np.empty(0, dtype=float)
    ramp = 1.0 - np.exp(-np.arange(n, dtype=float) / max(30.0, 0.10 * n))
    return np.clip(alpha * shift * ramp, -max_move, max_move)


def build_candidate(
    baseline: pd.DataFrame,
    data_dir: Path,
    alpha: float,
    max_move: float,
    min_eval_improvement: float,
    max_known_shift_abs: float,
    min_eval_gr_points: int,
    min_known_gr_points: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    parsed = parse_ids(baseline["id"])
    work = parsed.merge(baseline, on="id", how="left")
    out = baseline.copy()
    out_values = dict(zip(out["id"], out["tvt"]))
    shifts = np.arange(-20.0, 20.1, 5.0)
    report_rows = []

    for well, g in work.groupby("well", sort=False):
        g = g.sort_values("row_idx")
        row_idx = g["row_idx"].to_numpy(int)
        base_tvt = g["tvt"].to_numpy(float)
        try:
            hw = pd.read_csv(data_file(data_dir, "test", well, "horizontal_well"))
            tw = pd.read_csv(data_file(data_dir, "test", well, "typewell"))
        except Exception as exc:
            report_rows.append({
                "well": well,
                "status": "skip_missing_files",
                "reason": str(exc),
                "rows": int(len(g)),
            })
            continue

        if "GR" not in hw.columns or "TVT_input" not in hw.columns:
            report_rows.append({"well": well, "status": "skip_missing_columns", "rows": int(len(g))})
            continue

        gr_full = pd.to_numeric(hw["GR"], errors="coerce").interpolate(limit_direction="both")
        gr_full = gr_full.to_numpy(float)
        eval_gr = gr_full[row_idx]
        eval_finite = np.isfinite(eval_gr) & np.isfinite(base_tvt)
        eval_gr_points = int(eval_finite.sum())

        tvt_input = pd.to_numeric(hw["TVT_input"], errors="coerce").to_numpy(float)
        known_idx = np.flatnonzero(np.isfinite(tvt_input) & np.isfinite(gr_full))
        known_gr_points = int(len(known_idx))

        if eval_gr_points < min_eval_gr_points:
            status = "keep_baseline"
            reason = "not_enough_eval_gr"
            known_shift = float("nan")
            eval_shift = float("nan")
            eval_improvement = 0.0
            max_abs_move = 0.0
        elif known_gr_points < min_known_gr_points:
            status = "keep_baseline"
            reason = "not_enough_known_gr"
            known_shift = float("nan")
            eval_shift = float("nan")
            eval_improvement = 0.0
            max_abs_move = 0.0
        else:
            known_shift, known_zero, known_best, known_improvement = best_shift(
                gr_full[known_idx], tw, tvt_input[known_idx], shifts
            )
            eval_shift, eval_zero, eval_best, eval_improvement = best_shift(
                eval_gr[eval_finite], tw, base_tvt[eval_finite], shifts
            )
            if abs(known_shift) > max_known_shift_abs:
                status = "keep_baseline"
                reason = "known_prefix_alignment_unstable"
                max_abs_move = 0.0
            elif eval_improvement < min_eval_improvement:
                status = "keep_baseline"
                reason = "eval_shift_not_confident"
                max_abs_move = 0.0
            elif abs(eval_shift) < 1e-9:
                status = "keep_baseline"
                reason = "best_shift_zero"
                max_abs_move = 0.0
            else:
                move = smooth_move(len(g), eval_shift, alpha, max_move)
                corrected = base_tvt + move
                for rid, value in zip(g["id"].astype(str), corrected):
                    out_values[rid] = float(value)
                status = "corrected"
                reason = "passed_gate"
                max_abs_move = float(np.max(np.abs(move))) if len(move) else 0.0

        report_rows.append({
            "well": well,
            "status": status,
            "reason": reason,
            "rows": int(len(g)),
            "eval_gr_points": eval_gr_points,
            "known_gr_points": known_gr_points,
            "known_best_shift": known_shift,
            "eval_best_shift": eval_shift,
            "eval_improvement_frac": eval_improvement,
            "alpha": alpha,
            "max_abs_move": max_abs_move,
        })

    out["tvt"] = out["id"].map(out_values).astype(float)
    return out, pd.DataFrame(report_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True, help="Baseline submission.csv")
    parser.add_argument("--data-dir", type=Path, required=True, help="Competition data dir")
    parser.add_argument("--output-dir", type=Path, required=True, help="Candidate output dir")
    parser.add_argument("--alpha", type=float, default=0.10, help="Fraction of selected GR shift to apply")
    parser.add_argument("--max-move", type=float, default=8.0, help="Absolute movement clip in TVT units")
    parser.add_argument("--min-eval-improvement", type=float, default=0.03)
    parser.add_argument("--max-known-shift-abs", type=float, default=5.0)
    parser.add_argument("--min-eval-gr-points", type=int, default=100)
    parser.add_argument("--min-known-gr-points", type=int, default=50)
    args = parser.parse_args()

    baseline = read_submission(args.baseline)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidate, report = build_candidate(
        baseline=baseline,
        data_dir=args.data_dir,
        alpha=args.alpha,
        max_move=args.max_move,
        min_eval_improvement=args.min_eval_improvement,
        max_known_shift_abs=args.max_known_shift_abs,
        min_eval_gr_points=args.min_eval_gr_points,
        min_known_gr_points=args.min_known_gr_points,
    )

    out_path = args.output_dir / "submission.csv"
    report_path = args.output_dir / "gr_typewell_correction_report.csv"
    audit_path = args.output_dir / "candidate_audit.json"
    candidate.to_csv(out_path, index=False)
    report.to_csv(report_path, index=False)

    diff = candidate["tvt"].to_numpy(float) - baseline["tvt"].to_numpy(float)
    audit = {
        "candidate": "gr_light_typewell_alpha",
        "baseline": str(args.baseline),
        "rows": int(len(candidate)),
        "corrected_wells": int((report["status"] == "corrected").sum()) if len(report) else 0,
        "alpha": float(args.alpha),
        "max_move": float(args.max_move),
        "rmse_delta_vs_baseline": float(np.sqrt(np.mean(diff * diff))) if len(diff) else 0.0,
        "mean_abs_delta_vs_baseline": float(np.mean(np.abs(diff))) if len(diff) else 0.0,
        "p95_abs_delta_vs_baseline": float(np.quantile(np.abs(diff), 0.95)) if len(diff) else 0.0,
        "max_abs_delta_vs_baseline": float(np.max(np.abs(diff))) if len(diff) else 0.0,
    }
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(audit, indent=2, sort_keys=True))
    print(report.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
