#!/usr/bin/env python3
"""Sweep plateau recent-quantile parameters on pseudo-test splits."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

import pseudo_test_cv as cv


DEFAULT_SUMMARY = Path("experiments/plateau_quantile_sweep.csv")
DEFAULT_SPLITS = Path("experiments/plateau_quantile_sweep_split_scores.csv")
DEFAULT_REPORT = Path("reports/plateau_quantile_sweep_report.md")


@dataclass(frozen=True)
class SplitRecord:
    well: str
    split: str
    cut_idx: int
    prefix_rows: int
    eval_rows_total: int
    prefix_values: np.ndarray
    eval_true: np.ndarray
    fallback: float
    baseline_rmse: float
    baseline_mae: float
    baseline_p95_abs_error: float
    baseline_bias: float
    baseline_sse: float
    eval_rows: int


def parse_float_list(values: list[str]) -> list[float]:
    return [float(v) for v in values]


def parse_int_list(values: list[str]) -> list[int]:
    return [int(v) for v in values]


def split_records(
    data_dir: Path,
    cut_fracs: list[float],
    include_native: bool,
    min_prefix_rows: int,
    min_eval_rows: int,
) -> list[SplitRecord]:
    train_dir = data_dir / "train"
    if not train_dir.is_dir():
        raise FileNotFoundError(f"missing train directory: {train_dir}")

    records: list[SplitRecord] = []
    for hw_path in sorted(train_dir.glob("*__horizontal_well.csv")):
        well = hw_path.name.removesuffix("__horizontal_well.csv")
        tw_path = train_dir / f"{well}__typewell.csv"
        if not tw_path.exists():
            continue
        hw = pd.read_csv(hw_path)
        if not {"MD", "TVT"}.issubset(hw.columns):
            continue

        true_tvt = pd.to_numeric(hw["TVT"], errors="coerce").to_numpy(float)
        n = len(hw)
        for split_name, cut_idx in cv.split_specs(hw, cut_fracs, include_native=include_native):
            if cut_idx < min_prefix_rows or n - cut_idx < min_eval_rows:
                continue

            prefix_idx = np.arange(0, cut_idx, dtype=int)
            eval_idx = np.arange(cut_idx, n, dtype=int)
            prefix_values = true_tvt[prefix_idx]
            prefix_values = prefix_values[np.isfinite(prefix_values)]
            if len(prefix_values) == 0:
                continue

            eval_true = true_tvt[eval_idx]
            fallback = float(prefix_values[-1])
            baseline = np.full(len(eval_true), fallback, dtype=float)
            diff = baseline - eval_true
            finite = np.isfinite(diff)
            if int(finite.sum()) == 0:
                continue

            records.append(
                SplitRecord(
                    well=well,
                    split=split_name,
                    cut_idx=int(cut_idx),
                    prefix_rows=int(len(prefix_idx)),
                    eval_rows_total=int(len(eval_idx)),
                    prefix_values=prefix_values,
                    eval_true=eval_true,
                    fallback=fallback,
                    baseline_rmse=cv.rmse(baseline, eval_true),
                    baseline_mae=cv.mae(baseline, eval_true),
                    baseline_p95_abs_error=cv.p95_abs(baseline, eval_true),
                    baseline_bias=float(np.mean(diff[finite])),
                    baseline_sse=float(np.sum(diff[finite] * diff[finite])),
                    eval_rows=int(finite.sum()),
                )
            )
    if not records:
        raise RuntimeError("no pseudo-test split records generated")
    return records


def plateau_value(
    record: SplitRecord,
    window: int,
    quantile: float,
    min_move: float,
    blend: float,
    max_move: float,
) -> tuple[float, str, str]:
    if len(record.prefix_values) < window:
        return record.fallback, "fallback", "short_prefix"

    tail = record.prefix_values[-min(window, len(record.prefix_values)) :]
    target = float(np.nanquantile(tail, quantile))
    raw_move = target - record.fallback
    if not np.isfinite(raw_move) or abs(raw_move) < min_move:
        detail = f"target={target:.4f};move={raw_move:.4f};min_move={min_move:.3f}"
        return record.fallback, "fallback", detail

    move = float(np.clip(blend * raw_move, -max_move, max_move))
    detail = f"window={window};quantile={quantile:.3f};target={target:.4f};move={move:.4f}"
    return record.fallback + move, "ok", detail


def evaluate_combo(
    combo_id: int,
    records: list[SplitRecord],
    window: int,
    quantile: float,
    min_move: float,
    blend: float,
    max_move: float,
) -> tuple[dict[str, object], pd.DataFrame]:
    split_rows: list[dict[str, object]] = []
    for record in records:
        value, status, detail = plateau_value(record, window, quantile, min_move, blend, max_move)
        pred = np.full(len(record.eval_true), value, dtype=float)
        diff = pred - record.eval_true
        finite = np.isfinite(diff)
        sse = float(np.sum(diff[finite] * diff[finite]))
        rmse = cv.rmse(pred, record.eval_true)
        delta = rmse - record.baseline_rmse
        split_rows.append(
            {
                "combo_id": combo_id,
                "window": int(window),
                "quantile": float(quantile),
                "min_move": float(min_move),
                "blend": float(blend),
                "well": record.well,
                "split": record.split,
                "cut_idx": record.cut_idx,
                "prefix_rows": record.prefix_rows,
                "eval_rows": record.eval_rows,
                "method": "plateau_recent_quantile",
                "status": status,
                "detail": detail,
                "rmse": rmse,
                "mae": cv.mae(pred, record.eval_true),
                "p95_abs_error": cv.p95_abs(pred, record.eval_true),
                "bias": float(np.mean(diff[finite])),
                "sse": sse,
                "baseline_rmse": record.baseline_rmse,
                "baseline_mae": record.baseline_mae,
                "baseline_p95_abs_error": record.baseline_p95_abs_error,
                "baseline_bias": record.baseline_bias,
                "baseline_sse": record.baseline_sse,
                "delta_rmse_vs_baseline": delta,
            }
        )

    split_df = pd.DataFrame(split_rows)
    eval_rows = int(split_df["eval_rows"].sum())
    weighted_rmse = float(np.sqrt(split_df["sse"].sum() / eval_rows))
    baseline_weighted_rmse = float(np.sqrt(split_df["baseline_sse"].sum() / eval_rows))
    summary_row = {
        "combo_id": combo_id,
        "window": int(window),
        "quantile": float(quantile),
        "min_move": float(min_move),
        "blend": float(blend),
        "splits": int(len(split_df)),
        "eval_rows": eval_rows,
        "weighted_rmse": weighted_rmse,
        "last_value_weighted_rmse": baseline_weighted_rmse,
        "delta_weighted_rmse_vs_last_value": weighted_rmse - baseline_weighted_rmse,
        "mean_rmse": float(split_df["rmse"].mean()),
        "median_rmse": float(split_df["rmse"].median()),
        "mean_delta_rmse_vs_last_value": float(split_df["delta_rmse_vs_baseline"].mean()),
        "median_delta_rmse_vs_last_value": float(split_df["delta_rmse_vs_baseline"].median()),
        "win_rate_vs_last_value": float((split_df["delta_rmse_vs_baseline"] < 0).mean()),
        "fallback_rate": float((split_df["status"] != "ok").mean()),
        "ok_splits": int((split_df["status"] == "ok").sum()),
        "fallback_splits": int((split_df["status"] != "ok").sum()),
        "is_default": bool(
            window == 256
            and abs(quantile - 0.50) < 1e-12
            and abs(min_move - 4.0) < 1e-12
            and abs(blend - 1.0) < 1e-12
        ),
    }
    return summary_row, split_df


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


def grouped_summary(summary: pd.DataFrame, group_col: str) -> pd.DataFrame:
    return (
        summary.groupby(group_col, as_index=False)
        .agg(
            combos=("combo_id", "count"),
            best_weighted_rmse=("weighted_rmse", "min"),
            mean_delta=("delta_weighted_rmse_vs_last_value", "mean"),
            beat_rate=("delta_weighted_rmse_vs_last_value", lambda s: float((s < 0).mean())),
        )
        .sort_values("best_weighted_rmse")
    )


def write_report(
    summary: pd.DataFrame,
    split_scores: pd.DataFrame,
    report_path: Path,
    summary_path: Path,
    split_scores_path: Path,
) -> None:
    ranked = summary.sort_values(["weighted_rmse", "window", "quantile", "min_move", "blend"]).reset_index(drop=True)
    default_rows = ranked[ranked["is_default"]].copy()
    default_rank = int(default_rows.index[0] + 1) if len(default_rows) else None
    beat_count = int((summary["delta_weighted_rmse_vs_last_value"] < 0).sum())
    beat_rate = float(beat_count / max(1, len(summary)))

    top_cols = [
        "combo_id",
        "window",
        "quantile",
        "min_move",
        "blend",
        "weighted_rmse",
        "delta_weighted_rmse_vs_last_value",
        "win_rate_vs_last_value",
        "fallback_rate",
        "ok_splits",
    ]
    best_combo = ranked.iloc[0]["combo_id"] if len(ranked) else None
    best_splits = split_scores[split_scores["combo_id"] == best_combo].sort_values("delta_rmse_vs_baseline")
    split_focus_cols = [
        "combo_id",
        "well",
        "split",
        "status",
        "rmse",
        "baseline_rmse",
        "delta_rmse_vs_baseline",
        "detail",
    ]

    lines = [
        "# Plateau Quantile Sweep Report",
        "",
        "This report checks whether the plateau recent-quantile rule is stable across nearby local-validation parameters.",
        "It uses pseudo-test splits only and does not consume official Kaggle submissions.",
        "",
        "## Stability Summary",
        "",
        f"- Parameter combos tested: `{len(summary)}`",
        f"- Combos beating `last_value` weighted RMSE: `{beat_count}`",
        f"- Beat rate: `{beat_rate:.3f}`",
        f"- Default combo rank: `{default_rank if default_rank is not None else 'not tested'}`",
        "",
        "## Top Combos",
        "",
        markdown_table(ranked[top_cols].head(12)),
        "",
        "## By Window",
        "",
        markdown_table(grouped_summary(summary, "window")),
        "",
        "## By Quantile",
        "",
        markdown_table(grouped_summary(summary, "quantile")),
        "",
        "## By Min Move",
        "",
        markdown_table(grouped_summary(summary, "min_move")),
        "",
        "## Best Combo Split Detail",
        "",
        markdown_table(best_splits[split_focus_cols].head(20)),
        "",
        "## Interpretation",
        "",
        "- A high beat rate across nearby parameters supports a structural rule.",
        "- A single narrow winner suggests local overfit and should stay on hold.",
        "- Use this report to decide whether plateau candidates deserve an official information slot after pending scores resolve.",
        "",
        "## Outputs",
        "",
        f"- `{summary_path}`",
        f"- `{split_scores_path}`",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=cv.DEFAULT_DATA_DIR)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--split-scores", type=Path, default=DEFAULT_SPLITS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cut-fracs", nargs="*", default=["0.25", "0.35", "0.50", "0.65"])
    parser.add_argument("--no-native-prefix", action="store_true")
    parser.add_argument("--windows", nargs="*", default=["128", "256", "512"])
    parser.add_argument("--quantiles", nargs="*", default=["0.35", "0.50", "0.65"])
    parser.add_argument("--min-moves", nargs="*", default=["2.0", "4.0", "6.0", "8.0"])
    parser.add_argument("--blends", nargs="*", default=["1.0"])
    parser.add_argument("--min-prefix-rows", type=int, default=200)
    parser.add_argument("--min-eval-rows", type=int, default=200)
    parser.add_argument("--max-move", type=float, default=12.0)
    args = parser.parse_args()

    cut_fracs = cv.parse_cut_fracs(args.cut_fracs)
    windows = parse_int_list(args.windows)
    quantiles = parse_float_list(args.quantiles)
    min_moves = parse_float_list(args.min_moves)
    blends = parse_float_list(args.blends)

    records = split_records(
        data_dir=args.data_dir,
        cut_fracs=cut_fracs,
        include_native=not args.no_native_prefix,
        min_prefix_rows=args.min_prefix_rows,
        min_eval_rows=args.min_eval_rows,
    )

    summary_rows: list[dict[str, object]] = []
    split_frames: list[pd.DataFrame] = []
    combo_id = 0
    for window, quantile, min_move, blend in product(windows, quantiles, min_moves, blends):
        combo_id += 1
        summary_row, split_df = evaluate_combo(combo_id, records, window, quantile, min_move, blend, args.max_move)
        summary_rows.append(summary_row)
        split_frames.append(split_df)

    summary_df = pd.DataFrame(summary_rows).sort_values(["weighted_rmse", "window", "quantile", "min_move", "blend"])
    split_df = pd.concat(split_frames, ignore_index=True) if split_frames else pd.DataFrame()

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(args.summary, index=False)
    split_df.to_csv(args.split_scores, index=False)
    write_report(summary_df, split_df, args.report, args.summary, args.split_scores)

    print(f"wrote {args.summary}")
    print(f"wrote {args.split_scores}")
    print(f"wrote {args.report}")
    print(summary_df.head(12).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
