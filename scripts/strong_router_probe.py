#!/usr/bin/env python3
"""OOF diagnostic router probes for strong geosteering candidates.

This script is deliberately lightweight: it reads a full-data candidate matrix
and learns fold-held-out gates that decide when to select one method over the
anchor baseline. It is meant to answer whether a candidate's own diagnostics
make its wins predictable before we build a heavier LightGBM/CatBoost router.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DEFAULT_MATRIX = Path("experiments/full_data_router_candidate_matrix.csv")
DEFAULT_REPORT = Path("reports/strong_router_probe.md")
DEFAULT_OUTPUT = Path("experiments/strong_router_probe.csv")


def pooled_rmse(rmse_values: np.ndarray, weights: np.ndarray) -> float:
    rmse_values = np.asarray(rmse_values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    return float(np.sqrt(np.sum(weights * rmse_values * rmse_values) / np.sum(weights)))


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows."
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def candidate_rules(train: pd.DataFrame, features: list[str], quantiles: Iterable[float]) -> list[dict[str, object]]:
    rules: list[dict[str, object]] = [{"rule": "always_on", "clauses": []}]
    for feature in features:
        if feature not in train.columns:
            continue
        values = pd.to_numeric(train[feature], errors="coerce")
        if not np.isfinite(values).any():
            continue
        for q in quantiles:
            thr = float(values.quantile(q))
            rules.append({"rule": f"{feature}>q{q:.2f}", "clauses": [(feature, ">", thr)]})
            rules.append({"rule": f"{feature}<q{q:.2f}", "clauses": [(feature, "<", thr)]})

    # High-move, low-uncertainty gates are the first geologically sensible
    # two-feature pattern for PF-style candidates.
    if {"pred_move_abs_p90", "pf_post_std_p90"}.issubset(train.columns):
        move = pd.to_numeric(train["pred_move_abs_p90"], errors="coerce")
        spread = pd.to_numeric(train["pf_post_std_p90"], errors="coerce")
        if np.isfinite(move).any() and np.isfinite(spread).any():
            for mq in quantiles:
                for sq in quantiles:
                    rules.append(
                        {
                            "rule": f"pred_move_abs_p90>q{mq:.2f}&pf_post_std_p90<q{sq:.2f}",
                            "clauses": [
                                ("pred_move_abs_p90", ">", float(move.quantile(mq))),
                                ("pf_post_std_p90", "<", float(spread.quantile(sq))),
                            ],
                        }
                    )
    return rules


def apply_rule(df: pd.DataFrame, clauses: list[tuple[str, str, float]]) -> np.ndarray:
    gate = np.ones(len(df), dtype=bool)
    for feature, op, threshold in clauses:
        values = pd.to_numeric(df[feature], errors="coerce").to_numpy(float)
        if op == ">":
            gate &= values > threshold
        elif op == "<":
            gate &= values < threshold
        else:
            raise ValueError(f"unknown op: {op}")
        gate &= np.isfinite(values)
    return gate


def evaluate_rule(df: pd.DataFrame, clauses: list[tuple[str, str, float]]) -> tuple[float, int, float]:
    gate = apply_rule(df, clauses)
    routed = np.where(gate, df["eval_rmse"].to_numpy(float), df["baseline_rmse"].to_numpy(float))
    delta = routed - df["baseline_rmse"].to_numpy(float)
    return (
        pooled_rmse(routed, df["eval_rows"].to_numpy(float)),
        int(gate.sum()),
        float(np.mean(delta > 5.0)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--method", default="typewell_particle_filter")
    parser.add_argument(
        "--features",
        nargs="*",
        default=[
            "pred_move_abs_p90",
            "pred_range",
            "pf_post_std",
            "pf_post_std_p90",
            "pf_sigma_gr",
            "pf_gr_coverage",
            "pf_ess_mean",
            "pf_ess_min",
            "pf_resample_rate",
        ],
    )
    parser.add_argument("--quantiles", nargs="*", type=float, default=[0.2, 0.4, 0.6, 0.8])
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    matrix = pd.read_csv(args.matrix)
    data = matrix[matrix["method"] == args.method].copy()
    data = data[
        np.isfinite(pd.to_numeric(data["eval_rmse"], errors="coerce"))
        & np.isfinite(pd.to_numeric(data["baseline_rmse"], errors="coerce"))
        & np.isfinite(pd.to_numeric(data["eval_rows"], errors="coerce"))
    ].reset_index(drop=True)
    if data.empty:
        raise RuntimeError(f"no usable rows for method={args.method}")

    folds = sorted(int(fold) for fold in data["fold"].dropna().unique())
    weights = data["eval_rows"].to_numpy(float)
    base_pool = pooled_rmse(data["baseline_rmse"].to_numpy(float), weights)
    always_pool = pooled_rmse(data["eval_rmse"].to_numpy(float), weights)

    routed = np.full(len(data), np.nan)
    fold_rows = []
    for fold in folds:
        train = data[data["fold"] != fold].copy()
        val = data[data["fold"] == fold].copy()
        rules = candidate_rules(train, args.features, args.quantiles)
        best: dict[str, object] | None = None
        for rule in rules:
            train_pool, selected, catastrophic = evaluate_rule(train, rule["clauses"])
            candidate = {
                "rule": rule["rule"],
                "clauses": rule["clauses"],
                "train_pool": train_pool,
                "train_selected": selected,
                "train_catastrophic": catastrophic,
            }
            if best is None or (train_pool, catastrophic, -selected) < (
                float(best["train_pool"]),
                float(best["train_catastrophic"]),
                -int(best["train_selected"]),
            ):
                best = candidate
        assert best is not None
        gate = apply_rule(val, best["clauses"])
        routed[val.index] = np.where(gate, val["eval_rmse"].to_numpy(float), val["baseline_rmse"].to_numpy(float))
        val_pool = pooled_rmse(routed[val.index], val["eval_rows"].to_numpy(float))
        fold_rows.append(
            {
                "fold": fold,
                "rule": best["rule"],
                "train_rmse": round(float(best["train_pool"]), 4),
                "val_rmse": round(val_pool, 4),
                "selected": int(gate.sum()),
                "val_splits": int(len(val)),
            }
        )

    router_pool = pooled_rmse(routed, weights)
    selected_total = int(np.sum(routed != data["baseline_rmse"].to_numpy(float)))
    catastrophic = float(np.mean((routed - data["baseline_rmse"].to_numpy(float)) > 5.0))
    summary = pd.DataFrame(
        [
            {
                "router": "baseline_last_value",
                "pooled_rmse": round(base_pool, 4),
                "delta_vs_baseline": 0.0,
                "selected_splits": 0,
                "catastrophic_rate_plus5": 0.0,
            },
            {
                "router": f"always_on_{args.method}",
                "pooled_rmse": round(always_pool, 4),
                "delta_vs_baseline": round(always_pool - base_pool, 4),
                "selected_splits": int(len(data)),
                "catastrophic_rate_plus5": round(float(np.mean(data["delta_rmse_vs_baseline"] > 5.0)), 4)
                if "delta_rmse_vs_baseline" in data.columns
                else "",
            },
            {
                "router": f"oof_diag_gated_{args.method}",
                "pooled_rmse": round(router_pool, 4),
                "delta_vs_baseline": round(router_pool - base_pool, 4),
                "selected_splits": selected_total,
                "catastrophic_rate_plus5": round(catastrophic, 4),
            },
        ]
    )
    folds_df = pd.DataFrame(fold_rows)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_csv, index=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        "\n".join(
            [
                "# Strong Router Probe",
                "",
                f"Method: `{args.method}`",
                f"Matrix: `{args.matrix}`",
                "",
                "This OOF probe learns simple diagnostic gates on training folds and applies",
                "the selected gate to the held-out fold. It is a lightweight precursor to a",
                "larger learned geosteering router.",
                "",
                "## Summary",
                "",
                md_table(summary),
                "",
                "## Fold Rules",
                "",
                md_table(folds_df),
                "",
                "## Interpretation",
                "",
                "- A useful result must improve the baseline on held-out folds, not merely on",
                "  the training folds used to pick a gate.",
                "- If this probe beats the existing move-only gate, promote the selected",
                "  diagnostics into the full router feature set.",
                "- If it fails, the next candidate generator should be constrained alignment",
                "  rather than more PF threshold search.",
            ]
        )
        + "\n"
    )

    print(summary.to_string(index=False))
    print(f"\nwrote {args.output_csv}\nwrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
