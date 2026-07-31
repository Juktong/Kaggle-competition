#!/usr/bin/env python3
"""Run pseudo-test CV on train wells by hiding suffixes with known TVT labels."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_DATA_DIR = Path(r"D:\Codex\kaggle\rogii-wellbore\data")
DEFAULT_OUTPUT_DIR = Path("experiments")
DEFAULT_REPORT = Path("reports/pseudo_test_cv_report.md")
STRAT_COLUMNS = ["Z", "ANCC", "ASTNU", "ASTNL", "EGFDU", "EGFDL", "BUDA"]


@dataclass
class Prediction:
    method: str
    values: np.ndarray
    status: str = "ok"
    detail: str = ""
    selected_feature: str = ""
    gr_shift: float = math.nan
    gr_improvement: float = math.nan


def finite_line_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float] | None:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 2:
        return None
    x = x[mask]
    y = y[mask]
    if float(np.ptp(x)) <= 1e-9:
        return None
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)


def predict_line(x_train: np.ndarray, y_train: np.ndarray, x_eval: np.ndarray, fallback: float) -> np.ndarray:
    fit = finite_line_fit(x_train, y_train)
    if fit is None:
        return np.full(len(x_eval), float(fallback), dtype=float)
    slope, intercept = fit
    pred = slope * np.asarray(x_eval, dtype=float) + intercept
    pred[~np.isfinite(pred)] = float(fallback)
    return pred.astype(float)


def interp_typewell_gr(tw: pd.DataFrame, tvt: np.ndarray) -> np.ndarray:
    if not {"TVT", "GR"}.issubset(tw.columns):
        return np.full(len(tvt), np.nan)
    work = tw[["TVT", "GR"]].copy()
    work["TVT"] = pd.to_numeric(work["TVT"], errors="coerce")
    work["GR"] = pd.to_numeric(work["GR"], errors="coerce")
    work = work.dropna().sort_values("TVT")
    if len(work) < 5:
        return np.full(len(tvt), np.nan)
    x = work["TVT"].to_numpy(float)
    y = work["GR"].to_numpy(float)
    keep = np.r_[True, np.diff(x) > 0]
    x = x[keep]
    y = y[keep]
    if len(x) < 5:
        return np.full(len(tvt), np.nan)
    return np.interp(np.asarray(tvt, dtype=float), x, y, left=np.nan, right=np.nan)


def robust_mae(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) < 20:
        return float("nan")
    return float(np.nanmedian(np.abs(a[mask] - b[mask])))


def best_gr_shift(
    gr: np.ndarray,
    tw: pd.DataFrame,
    tvt_path: np.ndarray,
    shifts: np.ndarray,
) -> tuple[float, float, float, float]:
    scores = np.asarray([robust_mae(gr, interp_typewell_gr(tw, tvt_path + shift)) for shift in shifts], dtype=float)
    if not np.isfinite(scores).any():
        return 0.0, float("nan"), float("nan"), 0.0
    zero_idx = int(np.argmin(np.abs(shifts)))
    zero_score = float(scores[zero_idx])
    best_idx = int(np.nanargmin(scores))
    best_score = float(scores[best_idx])
    improvement = 0.0
    if np.isfinite(zero_score):
        improvement = float((zero_score - best_score) / (abs(zero_score) + 1e-6))
    return float(shifts[best_idx]), zero_score, best_score, improvement


def smooth_move(n: int, shift: float, alpha: float, max_move: float) -> np.ndarray:
    if n <= 0:
        return np.empty(0, dtype=float)
    ramp = 1.0 - np.exp(-np.arange(n, dtype=float) / max(30.0, 0.10 * n))
    return np.clip(alpha * shift * ramp, -max_move, max_move)


def plateau_recent_quantile_prediction(
    prefix_idx: np.ndarray,
    eval_idx: np.ndarray,
    y: np.ndarray,
    args: argparse.Namespace,
) -> Prediction:
    prefix = prefix_idx[np.isfinite(y[prefix_idx])]
    fallback = float(y[prefix[-1]])
    if len(prefix) < args.plateau_window:
        return Prediction("plateau_recent_quantile", np.full(len(eval_idx), fallback), "fallback", "short_prefix")

    tail = y[prefix[-min(args.plateau_window, len(prefix)) :]]
    target = float(np.nanquantile(tail, args.plateau_quantile))
    raw_move = target - fallback
    if not np.isfinite(raw_move) or abs(raw_move) < args.plateau_min_move:
        detail = f"target={target:.4f};move={raw_move:.4f};min_move={args.plateau_min_move:.3f}"
        return Prediction("plateau_recent_quantile", np.full(len(eval_idx), fallback), "fallback", detail)

    move = float(np.clip(args.plateau_blend * raw_move, -args.max_move, args.max_move))
    pred = np.full(len(eval_idx), fallback + move, dtype=float)
    detail = (
        f"window={args.plateau_window};quantile={args.plateau_quantile:.3f};"
        f"target={target:.4f};move={move:.4f}"
    )
    return Prediction("plateau_recent_quantile", pred, "ok", detail)


def plateau_gated_tail_prediction(
    hw: pd.DataFrame,
    prefix_idx: np.ndarray,
    eval_idx: np.ndarray,
    y: np.ndarray,
    args: argparse.Namespace,
) -> Prediction:
    prefix = prefix_idx[np.isfinite(y[prefix_idx])]
    fallback = float(y[prefix[-1]])
    if len(prefix) < args.min_prefix_rows + args.gate_min_holdout_rows:
        return Prediction("plateau_gated_tail_linear", np.full(len(eval_idx), fallback), "fallback", "short_prefix")

    holdout_n = max(args.gate_min_holdout_rows, int(round(args.gate_holdout_frac * len(prefix))))
    holdout_n = min(holdout_n, max(args.gate_min_holdout_rows, len(prefix) // 2))
    train_idx = prefix[:-holdout_n]
    valid_idx = prefix[-holdout_n:]
    if len(train_idx) < args.min_prefix_rows or len(valid_idx) < args.gate_min_holdout_rows:
        return Prediction("plateau_gated_tail_linear", np.full(len(eval_idx), fallback), "fallback", "short_holdout")

    md = pd.to_numeric(hw["MD"], errors="coerce").to_numpy(float)
    train_tail = train_idx[-min(args.tail_rows, len(train_idx)) :]
    valid_fallback = float(y[train_idx[-1]])
    valid_last = np.full(len(valid_idx), valid_fallback, dtype=float)
    valid_line = predict_line(md[train_tail], y[train_tail], md[valid_idx], valid_fallback)

    valid_y = y[valid_idx]
    last_rmse = rmse(valid_last, valid_y)
    line_rmse = rmse(valid_line, valid_y)
    if not np.isfinite(line_rmse) or line_rmse + args.gate_margin_rmse >= last_rmse:
        detail = f"holdout_last={last_rmse:.4f};holdout_line={line_rmse:.4f}"
        return Prediction("plateau_gated_tail_linear", np.full(len(eval_idx), fallback), "fallback", detail)

    eval_tail = prefix[-min(args.tail_rows, len(prefix)) :]
    raw_eval_line = predict_line(md[eval_tail], y[eval_tail], md[eval_idx], fallback)
    movement = np.clip(args.gate_slope_damp * (raw_eval_line - fallback), -args.max_move, args.max_move)
    pred = fallback + movement
    detail = (
        f"holdout_last={last_rmse:.4f};holdout_line={line_rmse:.4f};"
        f"damp={args.gate_slope_damp:.3f};max_move={float(np.max(np.abs(movement))):.3f}"
    )
    return Prediction("plateau_gated_tail_linear", pred, "ok", detail)


def best_strat_prediction(hw: pd.DataFrame, prefix_idx: np.ndarray, eval_idx: np.ndarray, y: np.ndarray) -> Prediction:
    prefix = prefix_idx[np.isfinite(y[prefix_idx])]
    if len(prefix) < 80:
        return Prediction("best_strat_linear", np.full(len(eval_idx), y[prefix[-1]]), "fallback", "short_prefix")

    split = max(20, int(0.80 * len(prefix)))
    train_idx = prefix[:split]
    valid_idx = prefix[split:]
    candidates = []
    for col in STRAT_COLUMNS:
        if col not in hw.columns:
            continue
        x = pd.to_numeric(hw[col], errors="coerce").to_numpy(float)
        fallback = float(y[train_idx[-1]])
        valid_pred = predict_line(x[train_idx], y[train_idx], x[valid_idx], fallback)
        valid_y = y[valid_idx]
        mask = np.isfinite(valid_pred) & np.isfinite(valid_y)
        if int(mask.sum()) < 20:
            continue
        rmse = float(np.sqrt(np.mean((valid_pred[mask] - valid_y[mask]) ** 2)))
        candidates.append((rmse, col, x))

    if not candidates:
        x = pd.to_numeric(hw["MD"], errors="coerce").to_numpy(float)
        pred = predict_line(x[prefix], y[prefix], x[eval_idx], float(y[prefix[-1]]))
        return Prediction("best_strat_linear", pred, "fallback", "no_valid_strat_feature", "MD")

    _, col, x = sorted(candidates, key=lambda item: item[0])[0]
    pred = predict_line(x[prefix], y[prefix], x[eval_idx], float(y[prefix[-1]]))
    return Prediction("best_strat_linear", pred, "ok", "selected_by_prefix_holdout", col)


def gr_shift_prediction(
    method: str,
    base_pred: np.ndarray,
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    prefix_idx: np.ndarray,
    eval_idx: np.ndarray,
    true_tvt: np.ndarray,
    alpha: float,
    max_move: float,
    max_prefix_shift_abs: float,
    min_eval_improvement: float,
) -> Prediction:
    if "GR" not in hw.columns:
        return Prediction(method, base_pred, "fallback", "missing_gr")

    gr_full = pd.to_numeric(hw["GR"], errors="coerce").interpolate(limit_direction="both").to_numpy(float)
    shifts = np.arange(-30.0, 30.1, 5.0)
    prefix_finite = prefix_idx[np.isfinite(true_tvt[prefix_idx]) & np.isfinite(gr_full[prefix_idx])]
    eval_finite_mask = np.isfinite(base_pred) & np.isfinite(gr_full[eval_idx])

    if len(prefix_finite) < 50 or int(eval_finite_mask.sum()) < 50:
        return Prediction(method, base_pred, "fallback", "not_enough_gr")

    prefix_shift, _, _, prefix_improvement = best_gr_shift(
        gr_full[prefix_finite], tw, true_tvt[prefix_finite], shifts
    )
    eval_shift, _, _, eval_improvement = best_gr_shift(
        gr_full[eval_idx][eval_finite_mask], tw, base_pred[eval_finite_mask], shifts
    )

    if abs(prefix_shift) > max_prefix_shift_abs:
        return Prediction(method, base_pred, "fallback", "prefix_shift_unstable", gr_shift=eval_shift, gr_improvement=eval_improvement)
    if eval_improvement < min_eval_improvement or abs(eval_shift) < 1e-9:
        return Prediction(method, base_pred, "fallback", "eval_shift_not_confident", gr_shift=eval_shift, gr_improvement=eval_improvement)

    moved = base_pred + smooth_move(len(base_pred), eval_shift, alpha, max_move)
    detail = f"prefix_shift={prefix_shift:.3f};prefix_improvement={prefix_improvement:.4f}"
    return Prediction(method, moved, "ok", detail, gr_shift=eval_shift, gr_improvement=eval_improvement)


def rmse(pred: np.ndarray, true: np.ndarray) -> float:
    mask = np.isfinite(pred) & np.isfinite(true)
    if int(mask.sum()) == 0:
        return float("nan")
    diff = pred[mask] - true[mask]
    return float(np.sqrt(np.mean(diff * diff)))


def mae(pred: np.ndarray, true: np.ndarray) -> float:
    mask = np.isfinite(pred) & np.isfinite(true)
    if int(mask.sum()) == 0:
        return float("nan")
    return float(np.mean(np.abs(pred[mask] - true[mask])))


def p95_abs(pred: np.ndarray, true: np.ndarray) -> float:
    mask = np.isfinite(pred) & np.isfinite(true)
    if int(mask.sum()) == 0:
        return float("nan")
    return float(np.quantile(np.abs(pred[mask] - true[mask]), 0.95))


def native_cut_index(hw: pd.DataFrame) -> int | None:
    if "TVT_input" not in hw.columns:
        return None
    tvt_input = pd.to_numeric(hw["TVT_input"], errors="coerce").to_numpy(float)
    finite = np.flatnonzero(np.isfinite(tvt_input))
    if len(finite) == 0:
        return None
    return int(finite[-1] + 1)


def split_specs(hw: pd.DataFrame, cut_fracs: list[float], include_native: bool) -> list[tuple[str, int]]:
    specs = []
    if include_native:
        cut = native_cut_index(hw)
        if cut is not None:
            specs.append(("native_prefix", cut))
    n = len(hw)
    for frac in cut_fracs:
        cut = int(round(n * frac))
        specs.append((f"frac_{frac:.2f}", cut))
    unique = {}
    for name, cut in specs:
        unique.setdefault((name, cut), (name, cut))
    return list(unique.values())


def run_split(
    well: str,
    split_name: str,
    cut_idx: int,
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    args: argparse.Namespace,
) -> list[dict[str, object]]:
    true_tvt = pd.to_numeric(hw["TVT"], errors="coerce").to_numpy(float)
    md = pd.to_numeric(hw["MD"], errors="coerce").to_numpy(float)
    n = len(hw)
    if cut_idx < args.min_prefix_rows or n - cut_idx < args.min_eval_rows:
        return []

    prefix_idx = np.arange(0, cut_idx, dtype=int)
    eval_idx = np.arange(cut_idx, n, dtype=int)
    prefix_true = true_tvt[prefix_idx]
    eval_true = true_tvt[eval_idx]
    fallback = float(prefix_true[np.isfinite(prefix_true)][-1])

    tail_prefix_idx = prefix_idx[-min(args.tail_rows, len(prefix_idx)) :]
    tail_linear = predict_line(md[tail_prefix_idx], true_tvt[tail_prefix_idx], md[eval_idx], fallback)
    full_linear = predict_line(md[prefix_idx], true_tvt[prefix_idx], md[eval_idx], fallback)
    plateau_quantile = plateau_recent_quantile_prediction(prefix_idx, eval_idx, true_tvt, args)
    plateau_gated = plateau_gated_tail_prediction(hw, prefix_idx, eval_idx, true_tvt, args)
    strat = best_strat_prediction(hw, prefix_idx, eval_idx, true_tvt)

    predictions = [
        Prediction("last_value", np.full(len(eval_idx), fallback, dtype=float)),
        Prediction("tail_linear_md", tail_linear),
        Prediction("full_linear_md", full_linear),
        plateau_quantile,
        plateau_gated,
        strat,
        gr_shift_prediction(
            "gr_shift_tail_linear",
            tail_linear,
            hw,
            tw,
            prefix_idx,
            eval_idx,
            true_tvt,
            args.alpha,
            args.max_move,
            args.max_prefix_shift_abs,
            args.min_eval_improvement,
        ),
        gr_shift_prediction(
            "gr_shift_plateau_quantile",
            plateau_quantile.values,
            hw,
            tw,
            prefix_idx,
            eval_idx,
            true_tvt,
            args.alpha,
            args.max_move,
            args.max_prefix_shift_abs,
            args.min_eval_improvement,
        ),
        gr_shift_prediction(
            "gr_shift_plateau_gated",
            plateau_gated.values,
            hw,
            tw,
            prefix_idx,
            eval_idx,
            true_tvt,
            args.alpha,
            args.max_move,
            args.max_prefix_shift_abs,
            args.min_eval_improvement,
        ),
        gr_shift_prediction(
            "gr_shift_best_strat",
            strat.values,
            hw,
            tw,
            prefix_idx,
            eval_idx,
            true_tvt,
            args.alpha,
            args.max_move,
            args.max_prefix_shift_abs,
            args.min_eval_improvement,
        ),
    ]

    rows = []
    for pred in predictions:
        values = np.asarray(pred.values, dtype=float)
        diff = values - eval_true
        finite = np.isfinite(diff)
        score = rmse(values, eval_true)
        rows.append(
            {
                "well": well,
                "split": split_name,
                "cut_idx": cut_idx,
                "prefix_rows": len(prefix_idx),
                "eval_rows": int(finite.sum()),
                "method": pred.method,
                "status": pred.status,
                "detail": pred.detail,
                "selected_feature": pred.selected_feature,
                "gr_shift": pred.gr_shift,
                "gr_improvement": pred.gr_improvement,
                "rmse": score,
                "mae": mae(values, eval_true),
                "p95_abs_error": p95_abs(values, eval_true),
                "bias": float(np.mean(diff[finite])) if int(finite.sum()) else float("nan"),
                "sse": float(np.sum(diff[finite] * diff[finite])) if int(finite.sum()) else float("nan"),
            }
        )
    return rows


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows."
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                vals.append("" if not np.isfinite(val) else f"{val:.6g}")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def summarize(scores: pd.DataFrame, baseline: str) -> pd.DataFrame:
    if scores.empty:
        return pd.DataFrame()
    key = ["well", "split", "cut_idx"]
    base = scores[scores["method"] == baseline][key + ["rmse"]].rename(columns={"rmse": "baseline_rmse"})
    work = scores.merge(base, on=key, how="left")
    work["delta_rmse_vs_baseline"] = work["rmse"] - work["baseline_rmse"]
    scores["baseline_rmse"] = work["baseline_rmse"].to_numpy(float)
    scores["delta_rmse_vs_baseline"] = work["delta_rmse_vs_baseline"].to_numpy(float)

    rows = []
    for method, group in work.groupby("method", sort=False):
        valid = group[np.isfinite(group["sse"]) & (group["eval_rows"] > 0)].copy()
        if valid.empty:
            continue
        weighted_rmse = float(np.sqrt(valid["sse"].sum() / valid["eval_rows"].sum()))
        rows.append(
            {
                "method": method,
                "splits": int(len(valid)),
                "eval_rows": int(valid["eval_rows"].sum()),
                "weighted_rmse": weighted_rmse,
                "mean_rmse": float(valid["rmse"].mean()),
                "median_rmse": float(valid["rmse"].median()),
                "mean_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].mean()),
                "median_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].median()),
                "win_rate_vs_baseline": float((valid["delta_rmse_vs_baseline"] < 0).mean()),
                "fallback_rate": float((valid["status"] != "ok").mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["weighted_rmse", "method"])


def write_report(scores: pd.DataFrame, summary: pd.DataFrame, output: Path, baseline: str) -> None:
    best = summary.head(10).copy()
    worst = scores.sort_values("rmse", ascending=False).head(12).copy()
    cols_summary = [
        "method",
        "splits",
        "eval_rows",
        "weighted_rmse",
        "mean_delta_rmse_vs_baseline",
        "win_rate_vs_baseline",
        "fallback_rate",
    ]
    cols_worst = ["well", "split", "method", "status", "rmse", "baseline_rmse", "delta_rmse_vs_baseline", "detail"]
    cols_worst = [c for c in cols_worst if c in worst.columns]

    lines = [
        "# Pseudo-Test CV Report",
        "",
        "This report hides suffixes of training wells and scores simple hidden-zone inference strategies against known `TVT` labels.",
        "It is not a substitute for Kaggle Public LB, but it gives pre-submission evidence about method families before spending daily slots.",
        "",
        f"Baseline comparator: `{baseline}`",
        "",
        "## Method Summary",
        "",
        markdown_table(best[[c for c in cols_summary if c in best.columns]]),
        "",
        "Interpretation:",
        "",
        "- Negative `mean_delta_rmse_vs_baseline` means the method beat the baseline comparator on average.",
        "- High `fallback_rate` means a method's safety gate often refused to modify the baseline.",
        "- Treat this as directional evidence; full public/private hidden wells can differ.",
        "",
        "## Worst Split Rows",
        "",
        markdown_table(worst[cols_worst]),
        "",
        "## Outputs",
        "",
        "- `experiments/pseudo_test_cv_scores.csv`",
        "- `experiments/pseudo_test_cv_summary.csv`",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_cut_fracs(values: list[str]) -> list[float]:
    out = []
    for value in values:
        frac = float(value)
        if not 0.05 <= frac <= 0.90:
            raise argparse.ArgumentTypeError(f"cut fraction out of range: {value}")
        out.append(frac)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cut-fracs", nargs="*", default=["0.25", "0.35", "0.50", "0.65"])
    parser.add_argument("--no-native-prefix", action="store_true")
    parser.add_argument("--min-prefix-rows", type=int, default=200)
    parser.add_argument("--min-eval-rows", type=int, default=200)
    parser.add_argument("--tail-rows", type=int, default=256)
    parser.add_argument("--plateau-window", type=int, default=256)
    parser.add_argument("--plateau-quantile", type=float, default=0.50)
    parser.add_argument("--plateau-min-move", type=float, default=4.0)
    parser.add_argument("--plateau-blend", type=float, default=1.0)
    parser.add_argument("--gate-holdout-frac", type=float, default=0.20)
    parser.add_argument("--gate-min-holdout-rows", type=int, default=80)
    parser.add_argument("--gate-margin-rmse", type=float, default=0.25)
    parser.add_argument("--gate-slope-damp", type=float, default=0.35)
    parser.add_argument("--alpha", type=float, default=0.20)
    parser.add_argument("--max-move", type=float, default=12.0)
    parser.add_argument("--max-prefix-shift-abs", type=float, default=10.0)
    parser.add_argument("--min-eval-improvement", type=float, default=0.03)
    parser.add_argument("--baseline-method", default="last_value")
    args = parser.parse_args()

    train_dir = args.data_dir / "train"
    if not train_dir.is_dir():
        raise FileNotFoundError(f"missing train directory: {train_dir}")

    cut_fracs = parse_cut_fracs(args.cut_fracs)
    rows = []
    for hw_path in sorted(train_dir.glob("*__horizontal_well.csv")):
        well = hw_path.name.removesuffix("__horizontal_well.csv")
        tw_path = train_dir / f"{well}__typewell.csv"
        if not tw_path.exists():
            continue
        hw = pd.read_csv(hw_path)
        tw = pd.read_csv(tw_path)
        if not {"MD", "TVT"}.issubset(hw.columns):
            continue
        for split_name, cut_idx in split_specs(hw, cut_fracs, include_native=not args.no_native_prefix):
            rows.extend(run_split(well, split_name, cut_idx, hw, tw, args))

    scores = pd.DataFrame(rows)
    if scores.empty:
        raise RuntimeError("no pseudo-test rows generated")
    summary = summarize(scores, args.baseline_method)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scores_path = args.output_dir / "pseudo_test_cv_scores.csv"
    summary_path = args.output_dir / "pseudo_test_cv_summary.csv"
    scores.to_csv(scores_path, index=False)
    summary.to_csv(summary_path, index=False)
    write_report(scores, summary, args.report, args.baseline_method)

    print(f"wrote {scores_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {args.report}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
