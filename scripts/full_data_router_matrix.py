#!/usr/bin/env python3
"""Build a full-train candidate-path matrix and a first learned-prior router CV."""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from multi_hypothesis_router_cv import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT,
    PathCandidate,
    candidate_paths,
    fmt,
    markdown_table,
    method_diagnostics,
    native_cut_index,
    prefix_holdout_cut,
    rmse,
    split_specs,
)


DEFAULT_DATA_DIR = Path("data/rogii")
DEFAULT_FULL_REPORT = Path("reports/full_data_router_matrix_report.md")
ROUTER_ELIGIBLE_METHODS = {
    "last_value",
    "damped_tail_linear_Z",
    "recent_plateau_quantile",
    "self_corr_prefix_shape",
    "typewell_particle_filter",
}
TRAIN_ONLY_TOKENS = ("ANCC", "ASTNU", "ASTNL", "EGFDU", "EGFDL", "BUDA")


def is_hidden_compatible_method(method: str) -> bool:
    return not any(token in method for token in TRAIN_ONLY_TOKENS)


def stable_fold(well: str, n_folds: int) -> int:
    digest = hashlib.md5(well.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % n_folds


def split_prefix_holdout(
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    prefix_idx: np.ndarray,
    true_tvt: np.ndarray,
    args: argparse.Namespace,
) -> dict[str, dict[str, float | str]]:
    holdout_cut = prefix_holdout_cut(prefix_idx, args)
    if holdout_cut is None:
        return {}

    train_idx = np.arange(0, holdout_cut, dtype=int)
    holdout_idx = np.arange(holdout_cut, int(prefix_idx[-1]) + 1, dtype=int)
    holdout_true = true_tvt[holdout_idx]
    candidates = candidate_paths(hw, tw, train_idx, holdout_idx, true_tvt, args)
    rows = method_diagnostics(candidates, holdout_true)
    baseline = next((row for row in rows if row["method"] == "last_value"), None)
    baseline_rmse = float(baseline["rmse"]) if baseline and np.isfinite(float(baseline["rmse"])) else float("nan")
    out: dict[str, dict[str, float | str]] = {}
    for row in rows:
        method = str(row["method"])
        candidate_rmse = float(row["rmse"])
        out[method] = {
            "holdout_rmse": candidate_rmse,
            "holdout_delta_rmse_vs_baseline": candidate_rmse - baseline_rmse
            if np.isfinite(candidate_rmse) and np.isfinite(baseline_rmse)
            else float("nan"),
            "holdout_status": str(row.get("status", "")),
            "holdout_detail": str(row.get("detail", "")),
        }
    return out


def path_shape_metrics(values: np.ndarray, fallback: float) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    if len(finite) == 0:
        return {
            "pred_std": float("nan"),
            "pred_move_abs_p90": float("nan"),
            "pred_jump_abs_p99": float("nan"),
            "pred_range": float("nan"),
        }
    jumps = np.abs(np.diff(finite)) if len(finite) > 1 else np.array([0.0])
    return {
        "pred_std": float(np.nanstd(finite)),
        "pred_move_abs_p90": float(np.nanpercentile(np.abs(finite - fallback), 90)),
        "pred_jump_abs_p99": float(np.nanpercentile(jumps, 99)),
        "pred_range": float(np.nanmax(finite) - np.nanmin(finite)),
    }


def candidate_matrix_for_split(
    well: str,
    split_name: str,
    cut_idx: int,
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    true_tvt = pd.to_numeric(hw["TVT"], errors="coerce").to_numpy(float)
    n = len(hw)
    if cut_idx < args.min_prefix_rows or n - cut_idx < args.min_eval_rows:
        return [], None

    prefix_idx = np.arange(0, cut_idx, dtype=int)
    eval_idx = np.arange(cut_idx, n, dtype=int)
    eval_true = true_tvt[eval_idx]
    train_valid = prefix_idx[np.isfinite(true_tvt[prefix_idx])]
    if len(train_valid) == 0:
        return [], None
    fallback = float(true_tvt[train_valid[-1]])
    candidates = candidate_paths(hw, tw, prefix_idx, eval_idx, true_tvt, args)
    if not candidates:
        return [], None

    holdout = split_prefix_holdout(hw, tw, prefix_idx, true_tvt, args)
    diag_rows = method_diagnostics(candidates, eval_true)
    baseline = next((row for row in diag_rows if row["method"] == "last_value"), None)
    baseline_rmse = float(baseline["rmse"]) if baseline and np.isfinite(float(baseline["rmse"])) else float("nan")
    gr = pd.to_numeric(hw["GR"], errors="coerce") if "GR" in hw.columns else pd.Series(np.nan, index=hw.index)
    prefix_gr_finite = int(gr.iloc[prefix_idx].notna().sum())
    eval_gr_finite = int(gr.iloc[eval_idx].notna().sum())
    native_cut = native_cut_index(hw)

    rows = []
    method_to_candidate = {candidate.method: candidate for candidate in candidates}
    for row in diag_rows:
        method = str(row["method"])
        candidate = method_to_candidate.get(method)
        values = candidate.values if candidate is not None else np.full(len(eval_idx), np.nan)
        holdout_row = holdout.get(method, {})
        eval_rmse = float(row["rmse"])
        shape = path_shape_metrics(values, fallback)
        rows.append(
            {
                "well": well,
                "fold": stable_fold(well, args.n_folds),
                "split": split_name,
                "cut_idx": cut_idx,
                "native_cut_idx": native_cut if native_cut is not None else math.nan,
                "prefix_rows": len(prefix_idx),
                "eval_rows": len(eval_idx),
                "prefix_frac": cut_idx / max(1, n),
                "prefix_gr_coverage": prefix_gr_finite / max(1, len(prefix_idx)),
                "eval_gr_coverage": eval_gr_finite / max(1, len(eval_idx)),
                "fallback_tvt": fallback,
                "method": method,
                "hidden_compatible_method": is_hidden_compatible_method(method),
                "router_eligible_method": method in ROUTER_ELIGIBLE_METHODS,
                "status": str(row.get("status", "")),
                "detail": str(row.get("detail", "")),
                "eval_rmse": eval_rmse,
                "baseline_rmse": baseline_rmse,
                "delta_rmse_vs_baseline": eval_rmse - baseline_rmse
                if np.isfinite(eval_rmse) and np.isfinite(baseline_rmse)
                else float("nan"),
                "holdout_rmse": holdout_row.get("holdout_rmse", float("nan")),
                "holdout_delta_rmse_vs_baseline": holdout_row.get("holdout_delta_rmse_vs_baseline", float("nan")),
                "holdout_status": holdout_row.get("holdout_status", ""),
                "holdout_detail": holdout_row.get("holdout_detail", ""),
                **shape,
            }
        )

    split_meta = {
        "well": well,
        "fold": stable_fold(well, args.n_folds),
        "split": split_name,
        "cut_idx": cut_idx,
        "prefix_rows": len(prefix_idx),
        "eval_rows": len(eval_idx),
        "baseline_rmse": baseline_rmse,
    }
    return rows, split_meta


def summarize_methods(matrix: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for method, group in matrix.groupby("method", sort=False):
        valid = group[np.isfinite(group["eval_rmse"])].copy()
        if valid.empty:
            continue
        weights = valid["eval_rows"].to_numpy(float)
        rmse_values = valid["eval_rmse"].to_numpy(float)
        sse = np.sum(weights * rmse_values * rmse_values)
        rows.append(
            {
                "method": method,
                "splits": int(len(valid)),
                "eval_rows": int(valid["eval_rows"].sum()),
                "weighted_rmse": float(np.sqrt(sse / np.sum(weights))),
                "mean_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].mean()),
                "median_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].median()),
                "win_rate_vs_baseline": float((valid["delta_rmse_vs_baseline"] < 0).mean()),
                "catastrophic_rate_plus5": float((valid["delta_rmse_vs_baseline"] > 5.0).mean()),
                "hidden_compatible": bool(valid["hidden_compatible_method"].all()),
                "router_eligible": bool(valid["router_eligible_method"].all()),
            }
        )
    return pd.DataFrame(rows).sort_values(["weighted_rmse", "method"])


def build_method_priors(matrix: pd.DataFrame, train_folds: set[int], args: argparse.Namespace) -> pd.DataFrame:
    train = matrix[
        matrix["fold"].isin(train_folds)
        & matrix["router_eligible_method"]
        & np.isfinite(matrix["delta_rmse_vs_baseline"])
    ].copy()
    rows = []
    for method, group in train.groupby("method"):
        rows.append(
            {
                "method": method,
                "prior_mean_delta": float(group["delta_rmse_vs_baseline"].mean()),
                "prior_median_delta": float(group["delta_rmse_vs_baseline"].median()),
                "prior_win_rate": float((group["delta_rmse_vs_baseline"] < 0).mean()),
                "prior_catastrophic_rate_plus5": float((group["delta_rmse_vs_baseline"] > 5.0).mean()),
                "prior_splits": int(len(group)),
            }
        )
    priors = pd.DataFrame(rows)
    if priors.empty:
        return priors
    priors["prior_allowed"] = (
        (priors["prior_splits"] >= args.min_prior_splits)
        & (priors["prior_mean_delta"] <= args.max_prior_mean_delta)
        & (priors["prior_catastrophic_rate_plus5"] <= args.max_prior_catastrophic_rate)
    )
    return priors


def learned_prior_router(matrix: pd.DataFrame, split_meta: pd.DataFrame, args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame]:
    choices = []
    prior_rows = []
    all_folds = sorted(int(fold) for fold in matrix["fold"].dropna().unique())
    key = ["well", "split", "cut_idx"]

    for fold in all_folds:
        train_folds = set(all_folds) - {fold}
        priors = build_method_priors(matrix, train_folds, args)
        if not priors.empty:
            prior_rows.append(priors.assign(validation_fold=fold))
        prior_by_method = priors.set_index("method").to_dict("index") if not priors.empty else {}
        val = matrix[matrix["fold"] == fold].copy()
        for split_key, group in val.groupby(key, sort=False):
            baseline_row = group[group["method"] == "last_value"].head(1)
            if baseline_row.empty:
                continue
            baseline_rmse = float(baseline_row["eval_rmse"].iloc[0])
            selected = baseline_row.iloc[0]
            selected_reason = "fallback_last_value"
            eligible_rows = []
            for _, row in group.iterrows():
                method = str(row["method"])
                if method == "last_value" or not bool(row["router_eligible_method"]):
                    continue
                if str(row["status"]) != "ok":
                    continue
                holdout_delta = float(row["holdout_delta_rmse_vs_baseline"])
                if not np.isfinite(holdout_delta) or holdout_delta > -args.router_min_holdout_improvement:
                    continue
                prior = prior_by_method.get(method)
                if not prior or not bool(prior.get("prior_allowed", False)):
                    continue
                score = holdout_delta + args.prior_weight * float(prior["prior_mean_delta"])
                eligible_rows.append((score, row, prior))
            if eligible_rows:
                _, selected, prior = sorted(eligible_rows, key=lambda item: (item[0], str(item[1]["method"])))[0]
                selected_reason = (
                    f"learned_prior;holdout_delta={float(selected['holdout_delta_rmse_vs_baseline']):.4f};"
                    f"prior_mean_delta={float(prior['prior_mean_delta']):.4f}"
                )
            selected_rmse = float(selected["eval_rmse"])
            choices.append(
                {
                    "validation_fold": fold,
                    "well": split_key[0],
                    "split": split_key[1],
                    "cut_idx": split_key[2],
                    "selected_method": str(selected["method"]),
                    "selected_reason": selected_reason,
                    "router_rmse": selected_rmse,
                    "baseline_rmse": baseline_rmse,
                    "delta_rmse_vs_baseline": selected_rmse - baseline_rmse,
                    "eval_rows": int(selected["eval_rows"]),
                }
            )

    return pd.DataFrame(choices), pd.concat(prior_rows, ignore_index=True) if prior_rows else pd.DataFrame()


def summarize_router(router: pd.DataFrame) -> pd.DataFrame:
    if router.empty:
        return pd.DataFrame()
    valid = router[np.isfinite(router["router_rmse"])].copy()
    if valid.empty:
        return pd.DataFrame()
    weights = valid["eval_rows"].to_numpy(float)
    rmse_values = valid["router_rmse"].to_numpy(float)
    base_values = valid["baseline_rmse"].to_numpy(float)
    return pd.DataFrame(
        [
            {
                "router": "learned_prior_router",
                "splits": int(len(valid)),
                "eval_rows": int(valid["eval_rows"].sum()),
                "weighted_rmse": float(np.sqrt(np.sum(weights * rmse_values * rmse_values) / np.sum(weights))),
                "baseline_weighted_rmse": float(np.sqrt(np.sum(weights * base_values * base_values) / np.sum(weights))),
                "mean_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].mean()),
                "median_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].median()),
                "win_rate_vs_baseline": float((valid["delta_rmse_vs_baseline"] < 0).mean()),
                "catastrophic_rate_plus5": float((valid["delta_rmse_vs_baseline"] > 5.0).mean()),
            }
        ]
    )


def write_report(
    matrix: pd.DataFrame,
    method_summary: pd.DataFrame,
    router_choices: pd.DataFrame,
    router_summary: pd.DataFrame,
    priors: pd.DataFrame,
    output: Path,
    args: argparse.Namespace,
) -> None:
    selected_counts = (
        router_choices["selected_method"].value_counts().rename_axis("selected_method").reset_index(name="count")
        if not router_choices.empty
        else pd.DataFrame()
    )
    worst_router = (
        router_choices.sort_values("delta_rmse_vs_baseline", ascending=False).head(16)
        if not router_choices.empty
        else pd.DataFrame()
    )
    prior_view = (
        priors.sort_values(["validation_fold", "prior_mean_delta", "method"]).head(40)
        if not priors.empty
        else pd.DataFrame()
    )
    lines = [
        "# Full-Data Router Matrix Report",
        "",
        "This is the first full-train candidate-path matrix and learned-prior router CV.",
        "It is not a submission package.",
        "",
        "## Run Config",
        "",
        f"- data_dir: `{args.data_dir}`",
        f"- splits: native prefix plus `{', '.join(args.cut_fracs)}`",
        f"- folds: `{args.n_folds}` stable well-hash folds",
        f"- max_wells: `{args.max_wells if args.max_wells else 'all'}`",
        "",
        "## Method Summary",
        "",
        markdown_table(method_summary.head(20)),
        "",
        "## Router Summary",
        "",
        markdown_table(router_summary),
        "",
        "## Router Selection Counts",
        "",
        markdown_table(selected_counts),
        "",
        "## Worst Router Decisions",
        "",
        markdown_table(
            worst_router[
                [
                    "validation_fold",
                    "well",
                    "split",
                    "selected_method",
                    "router_rmse",
                    "baseline_rmse",
                    "delta_rmse_vs_baseline",
                    "selected_reason",
                ]
            ]
            if not worst_router.empty
            else pd.DataFrame()
        ),
        "",
        "## Learned Method Priors",
        "",
        markdown_table(prior_view),
        "",
        "## Interpretation",
        "",
        "- This run uses all available train wells unless `--max-wells` is set.",
        "- The router is intentionally simple: out-of-fold method priors plus prefix-holdout evidence.",
        "- Hidden-incompatible train-only formation columns are allowed as diagnostics in the matrix, but labeled explicitly.",
        "- The learned-prior router is stricter than hidden compatibility: it currently allows only conservative release-eligible methods.",
        "- A useful next router should beat `last_value` on weighted RMSE and keep catastrophic-rate low.",
        "",
        "## Outputs",
        "",
        "- `experiments/full_data_router_candidate_matrix.csv`",
        "- `experiments/full_data_router_method_summary.csv`",
        "- `experiments/full_data_router_choices.csv`",
        "- `experiments/full_data_router_summary.csv`",
        "- `experiments/full_data_router_method_priors.csv`",
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
    parser.add_argument("--report", type=Path, default=DEFAULT_FULL_REPORT)
    parser.add_argument("--cut-fracs", nargs="*", default=["0.35", "0.50", "0.65"])
    parser.add_argument("--no-native-prefix", action="store_true")
    parser.add_argument("--max-wells", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--n-folds", type=int, default=5)
    parser.add_argument("--min-prior-splits", type=int, default=40)
    parser.add_argument("--max-prior-mean-delta", type=float, default=0.0)
    parser.add_argument("--max-prior-catastrophic-rate", type=float, default=0.05)
    parser.add_argument("--router-min-holdout-improvement", type=float, default=0.75)
    parser.add_argument("--prior-weight", type=float, default=0.35)

    # Candidate generator args shared with multi_hypothesis_router_cv.py.
    parser.add_argument("--min-prefix-rows", type=int, default=200)
    parser.add_argument("--min-eval-rows", type=int, default=200)
    parser.add_argument("--tail-rows", type=int, default=256)
    parser.add_argument("--tail-damp", type=float, default=0.25)
    parser.add_argument("--strat-damp", type=float, default=0.20)
    parser.add_argument("--max-move", type=float, default=12.0)
    parser.add_argument("--plateau-window", type=int, default=256)
    parser.add_argument("--plateau-quantile", type=float, default=0.50)
    parser.add_argument("--plateau-blend", type=float, default=1.0)
    parser.add_argument("--piecewise-damp", type=float, default=0.30)
    parser.add_argument("--piecewise-min-feature-span", type=float, default=1e-6)
    parser.add_argument("--fault-window", type=int, default=128)
    parser.add_argument("--fault-min-step", type=float, default=3.0)
    parser.add_argument("--fault-damp", type=float, default=0.35)
    parser.add_argument("--self-corr-window", type=int, default=256)
    parser.add_argument("--self-corr-stride", type=int, default=32)
    parser.add_argument("--self-corr-min-eval-rows", type=int, default=80)
    parser.add_argument("--self-corr-min-pairs", type=int, default=50)
    parser.add_argument("--self-corr-min-corr", type=float, default=0.72)
    parser.add_argument("--router-holdout-frac", type=float, default=0.20)
    parser.add_argument("--router-min-holdout-rows", type=int, default=80)
    parser.add_argument("--router-min-improvement-rmse", type=float, default=0.75)
    parser.add_argument("--router-min-improvement-frac", type=float, default=0.15)
    parser.add_argument("--router-min-margin-rmse", type=float, default=0.10)
    parser.add_argument("--router-allow-gr-shift", action="store_true")
    parser.add_argument("--router-self-corr-min-corr", type=float, default=0.75)
    parser.add_argument("--min-gr-rows", type=int, default=50)
    parser.add_argument("--max-gr-shift", type=float, default=30.0)
    parser.add_argument("--gr-shift-step", type=float, default=5.0)
    parser.add_argument("--gr-alpha", type=float, default=0.20)
    parser.add_argument("--ncc-alpha", type=float, default=0.15)
    parser.add_argument("--min-ncc-corr", type=float, default=0.35)
    parser.add_argument("--min-ncc-gain", type=float, default=0.05)
    parser.add_argument("--max-prefix-shift-abs", type=float, default=10.0)
    parser.add_argument("--min-eval-improvement", type=float, default=0.03)
    # typewell particle-filter candidate (tuned on real train-well prototype)
    parser.add_argument("--pf-particles", type=int, default=300)
    parser.add_argument("--pf-kappa", type=float, default=0.02)
    parser.add_argument("--pf-q-tvt", type=float, default=0.25)
    parser.add_argument("--pf-q-dip", type=float, default=0.002)
    parser.add_argument("--pf-dip-persist", type=float, default=0.97)
    parser.add_argument("--pf-dip-cap", type=float, default=0.15)
    parser.add_argument("--pf-dip-shrink", type=float, default=0.2)
    parser.add_argument("--pf-fault-p", type=float, default=0.02)
    parser.add_argument("--pf-fault-scale", type=float, default=8.0)
    parser.add_argument("--pf-ess-frac", type=float, default=0.5)
    parser.add_argument("--pf-sigma-floor", type=float, default=6.0)
    parser.add_argument("--pf-dip-tail", type=int, default=250)
    parser.add_argument("--pf-init-tvt", type=float, default=1.0)
    parser.add_argument("--pf-seed", type=int, default=20260701)
    args = parser.parse_args()

    train_dir = args.data_dir / "train"
    if not train_dir.is_dir():
        raise FileNotFoundError(f"missing train directory: {train_dir}")
    cut_fracs = parse_cut_fracs(args.cut_fracs)

    score_rows: list[dict[str, Any]] = []
    split_rows: list[dict[str, Any]] = []
    hw_paths = sorted(train_dir.glob("*__horizontal_well.csv"))
    if args.max_wells:
        hw_paths = hw_paths[: args.max_wells]
    for i, hw_path in enumerate(hw_paths, start=1):
        well = hw_path.name.removesuffix("__horizontal_well.csv")
        tw_path = train_dir / f"{well}__typewell.csv"
        if not tw_path.exists():
            continue
        hw = pd.read_csv(hw_path)
        tw = pd.read_csv(tw_path)
        if not {"MD", "TVT"}.issubset(hw.columns):
            continue
        for split_name, cut_idx in split_specs(hw, cut_fracs, include_native=not args.no_native_prefix):
            rows, meta = candidate_matrix_for_split(well, split_name, cut_idx, hw, tw, args)
            score_rows.extend(rows)
            if meta is not None:
                split_rows.append(meta)
        if args.progress_every > 0 and i % args.progress_every == 0:
            print(f"processed wells={i} candidate_rows={len(score_rows)}", flush=True)

    matrix = pd.DataFrame(score_rows)
    split_meta = pd.DataFrame(split_rows)
    if matrix.empty:
        raise RuntimeError("no candidate matrix rows generated")

    method_summary = summarize_methods(matrix)
    router_choices, method_priors = learned_prior_router(matrix, split_meta, args)
    router_summary = summarize_router(router_choices)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(args.output_dir / "full_data_router_candidate_matrix.csv", index=False)
    method_summary.to_csv(args.output_dir / "full_data_router_method_summary.csv", index=False)
    router_choices.to_csv(args.output_dir / "full_data_router_choices.csv", index=False)
    router_summary.to_csv(args.output_dir / "full_data_router_summary.csv", index=False)
    method_priors.to_csv(args.output_dir / "full_data_router_method_priors.csv", index=False)
    write_report(matrix, method_summary, router_choices, router_summary, method_priors, args.report, args)

    print(f"wrote {args.output_dir / 'full_data_router_candidate_matrix.csv'}", flush=True)
    print(f"wrote {args.output_dir / 'full_data_router_method_summary.csv'}", flush=True)
    print(f"wrote {args.output_dir / 'full_data_router_choices.csv'}", flush=True)
    print(f"wrote {args.output_dir / 'full_data_router_summary.csv'}", flush=True)
    print(f"wrote {args.output_dir / 'full_data_router_method_priors.csv'}", flush=True)
    print(f"wrote {args.report}", flush=True)
    print(method_summary.head(12).to_string(index=False), flush=True)
    print(router_summary.to_string(index=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
