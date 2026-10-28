from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_DATA_DIR = Path(r"D:\Codex\kaggle\rogii-wellbore\data")
DEFAULT_OUTPUT_DIR = Path("experiments")

REFERENCE_CANDIDATES = {
    "current_best_7p235": [
        Path("artifacts/sunny_physical_output/submission.csv"),
        Path("artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv"),
    ],
    "david_v12_7p263": Path("artifacts/david_v12_output/submission.csv"),
    "fleongg_w052_7p588": Path("artifacts/fleongg_v5_output/submission_sp45_fleongg_w0.52.csv"),
}

# Public scores we have actually observed from Kaggle submissions. These are
# intentionally path-specific because many notebooks write several variants.
KNOWN_PUBLIC_SCORES = {
    "artifacts/sunny_physical_output/submission.csv": 7.235,
    "artifacts/david_v12_output/submission.csv": 7.263,
    "artifacts/david_fastcpu_output/submission.csv": 7.703,
    "artifacts/fleongg_v5_output/submission_sp45_fleongg_w0.52.csv": 7.588,
    "artifacts/fleongg_v5_output/submission_sp45_fleongg_w0.55.csv": 7.599,
    "artifacts/fleongg_v5_output/submission_sp45_fleongg_w0.58.csv": 7.606,
    "artifacts/nickson_v5_artifact_output/submission.csv": 20.579,
    "artifacts/wellbore_direct_overlap_output/submission.csv": 11551.955,
    "artifacts/ourmatch_7159_output/submission.csv": 15357.198,
    "artifacts/kokinn_7159_ref_output/submission.csv": 15357.198,
    "artifacts/aevion_lb52_fixed_v4_output/submission.csv": math.nan,
}


def normalize_path(path: Path) -> str:
    return path.as_posix()


def parse_submission_ids(ids: pd.Series) -> pd.DataFrame:
    parts = ids.astype(str).str.rsplit("_", n=1, expand=True)
    if parts.shape[1] != 2:
        raise ValueError("submission ids must look like <well>_<row_idx>")
    return pd.DataFrame(
        {
            "id": ids.astype(str).to_numpy(),
            "well": parts[0].to_numpy(),
            "row_idx": parts[1].astype(int).to_numpy(),
        }
    )


def load_sample(data_dir: Path) -> pd.DataFrame:
    sample = pd.read_csv(data_dir / "sample_submission.csv")
    if list(sample.columns)[:1] != ["id"]:
        raise ValueError("sample_submission.csv must contain id column")
    sample["id"] = sample["id"].astype(str)
    parsed = parse_submission_ids(sample["id"])
    return sample[["id"]].merge(parsed, on="id", how="left")


def load_submission(path: Path, sample: pd.DataFrame) -> pd.DataFrame | None:
    try:
        sub = pd.read_csv(path)
    except Exception:
        return None
    if not {"id", "tvt"}.issubset(sub.columns):
        return None
    sub = sub[["id", "tvt"]].copy()
    sub["id"] = sub["id"].astype(str)
    if len(sub) != len(sample):
        return None
    if not sub["id"].equals(sample["id"]):
        return None
    vals = pd.to_numeric(sub["tvt"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(vals).all():
        return None
    sub["tvt"] = vals
    return sub


def iter_submission_files(root: Path) -> list[Path]:
    paths = []
    for pattern in ("artifacts/**/*.csv", "submissions/**/*.csv"):
        paths.extend(root.glob(pattern))
    return sorted(set(paths), key=lambda p: normalize_path(p).lower())


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    return float(np.sqrt(np.mean(d * d)))


def mae(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))


def load_test_cache(data_dir: Path, sample: pd.DataFrame) -> dict[str, pd.DataFrame]:
    cache: dict[str, pd.DataFrame] = {}
    for well in sorted(sample["well"].unique()):
        path = data_dir / "test" / f"{well}__horizontal_well.csv"
        if path.exists():
            cache[well] = pd.read_csv(path)
    return cache


def anchor_and_shape_metrics(
    sub: pd.DataFrame,
    sample: pd.DataFrame,
    test_cache: dict[str, pd.DataFrame],
    data_dir: Path,
) -> dict[str, float]:
    work = sample[["id", "well", "row_idx"]].copy()
    work["tvt"] = sub["tvt"].to_numpy(dtype=float)

    first_gaps = []
    slope_gaps = []
    pred_slopes = []
    pred_curv = []
    jump_count = 0
    total_step_count = 0
    weak_anchor_rows = 0
    range_violations = 0

    for well, g in work.groupby("well", sort=False):
        hw = test_cache.get(well)
        if hw is None or len(g) == 0:
            continue
        g = g.sort_values("row_idx")
        pred = g["tvt"].to_numpy(dtype=float)
        rows = g["row_idx"].to_numpy(dtype=int)

        tvt_input = pd.to_numeric(hw.get("TVT_input"), errors="coerce").to_numpy(dtype=float)
        known_idx = np.flatnonzero(np.isfinite(tvt_input))
        if len(known_idx) > 0:
            before = known_idx[known_idx < rows[0]]
            if len(before) > 0:
                last_idx = int(before[-1])
                last_tvt = float(tvt_input[last_idx])
                first_gaps.append(float(pred[0] - last_tvt))
                if len(before) >= 8:
                    tail = before[-8:]
                    x = tail.astype(float)
                    y = tvt_input[tail]
                    if np.ptp(x) > 0:
                        last_slope = float(np.polyfit(x, y, 1)[0])
                        if len(pred) >= 8:
                            n = min(8, len(pred))
                            first_slope = float(np.polyfit(rows[:n].astype(float), pred[:n], 1)[0])
                            slope_gaps.append(first_slope - last_slope)
                if abs(pred[0] - last_tvt) > 80:
                    weak_anchor_rows += len(g)

        if len(pred) >= 2:
            slopes = np.diff(pred)
            pred_slopes.extend(slopes.tolist())
            total_step_count += len(slopes)
            jump_count += int(np.sum(np.abs(slopes) > 3.0))
        if len(pred) >= 3:
            pred_curv.extend(np.diff(pred, n=2).tolist())

        tw_path = data_dir / "test" / f"{well}__typewell.csv"
        if tw_path.exists():
            try:
                tw = pd.read_csv(tw_path, usecols=["TVT"])
                lo, hi = float(tw["TVT"].min()) - 250.0, float(tw["TVT"].max()) + 250.0
                range_violations += int(np.sum((pred < lo) | (pred > hi)))
            except Exception:
                pass

    slopes_arr = np.asarray(pred_slopes, dtype=float)
    curv_arr = np.asarray(pred_curv, dtype=float)
    first_gap_arr = np.asarray(first_gaps, dtype=float)
    slope_gap_arr = np.asarray(slope_gaps, dtype=float)

    return {
        "anchor_first_abs_median": float(np.nanmedian(np.abs(first_gap_arr))) if len(first_gap_arr) else np.nan,
        "anchor_first_abs_p90": float(np.nanquantile(np.abs(first_gap_arr), 0.90)) if len(first_gap_arr) else np.nan,
        "anchor_weak_row_frac": weak_anchor_rows / max(1, len(work)),
        "slope_gap_abs_median": float(np.nanmedian(np.abs(slope_gap_arr))) if len(slope_gap_arr) else np.nan,
        "slope_abs_p50": float(np.nanmedian(np.abs(slopes_arr))) if len(slopes_arr) else np.nan,
        "slope_abs_p95": float(np.nanquantile(np.abs(slopes_arr), 0.95)) if len(slopes_arr) else np.nan,
        "curvature_abs_p95": float(np.nanquantile(np.abs(curv_arr), 0.95)) if len(curv_arr) else np.nan,
        "jump_rate_abs_slope_gt3": jump_count / max(1, total_step_count),
        "typewell_range_violation_frac": range_violations / max(1, len(work)),
    }


def risk_grade(row: pd.Series) -> str:
    if row.get("known_public_score", np.nan) >= 20:
        return "reject_known_bad"
    if row.get("rmse_to_current_best_7p235", 0) > 80:
        return "reject_far_from_best"
    if row.get("anchor_weak_row_frac", 0) > 0.10 or row.get("jump_rate_abs_slope_gt3", 0) > 0.02:
        return "high_shape_risk"
    if row.get("rmse_to_current_best_7p235", 0) <= 1.0:
        return "near_duplicate_low_upside"
    if row.get("rmse_to_current_best_7p235", 0) <= 8.0:
        return "plausible_submit_candidate"
    return "medium_unknown"


def estimated_band(row: pd.Series) -> str:
    risk = str(row.get("risk_grade", ""))
    if risk.startswith("reject") or risk == "high_shape_risk":
        return "do_not_submit"
    nearest = row.get("nearest_known_public_score", np.nan)
    nearest_rmse = row.get("rmse_to_nearest_known", np.nan)
    current_rmse = row.get("rmse_to_current_best_7p235", np.nan)
    if np.isfinite(nearest) and np.isfinite(nearest_rmse) and nearest_rmse < 0.05:
        return f"near_known_{nearest:.3f}"
    if np.isfinite(current_rmse) and current_rmse < 1.0:
        return "likely_around_7p235_low_upside"
    if np.isfinite(current_rmse) and current_rmse < 4.0:
        return "plausible_7p2_to_7p8_band"
    if np.isfinite(current_rmse) and current_rmse < 12.0:
        return "unknown_possible_but_risky"
    return "unknown_high_variance"


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Score ROGII submission candidates with local surrogate metrics.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    sample = load_sample(args.data_dir)
    test_cache = load_test_cache(args.data_dir, sample)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(parents=True, exist_ok=True)

    refs: dict[str, pd.DataFrame] = {}
    for name, path_or_paths in REFERENCE_CANDIDATES.items():
        paths = path_or_paths if isinstance(path_or_paths, list) else [path_or_paths]
        for path in paths:
            if not path.exists():
                continue
            sub = load_submission(path, sample)
            if sub is not None:
                refs[name] = sub
                break

    rows = []
    valid_subs: dict[str, pd.DataFrame] = {}
    for path in iter_submission_files(args.root):
        sub = load_submission(path, sample)
        if sub is None:
            continue
        rel = normalize_path(path.relative_to(args.root))
        valid_subs[rel] = sub
        vals = sub["tvt"].to_numpy(dtype=float)
        row = {
            "path": rel,
            "known_public_score": KNOWN_PUBLIC_SCORES.get(rel, np.nan),
            "rows": int(len(sub)),
            "pred_min": float(np.min(vals)),
            "pred_max": float(np.max(vals)),
            "pred_mean": float(np.mean(vals)),
            "pred_std": float(np.std(vals)),
        }
        for ref_name, ref_sub in refs.items():
            ref_vals = ref_sub["tvt"].to_numpy(dtype=float)
            row[f"rmse_to_{ref_name}"] = rmse(vals, ref_vals)
            row[f"mae_to_{ref_name}"] = mae(vals, ref_vals)
            row[f"p95_abs_diff_to_{ref_name}"] = float(np.quantile(np.abs(vals - ref_vals), 0.95))
        row.update(anchor_and_shape_metrics(sub, sample, test_cache, args.data_dir))
        rows.append(row)

    metrics = pd.DataFrame(rows)
    if metrics.empty:
        raise RuntimeError("No valid submission files found.")

    known_paths = [
        p
        for p in valid_subs
        if p in KNOWN_PUBLIC_SCORES
        and np.isfinite(KNOWN_PUBLIC_SCORES[p])
        and KNOWN_PUBLIC_SCORES[p] < 100.0
    ]
    nearest_rows = []
    for path, sub in valid_subs.items():
        vals = sub["tvt"].to_numpy(dtype=float)
        best = (np.inf, None, np.nan)
        for known_path in known_paths:
            if known_path == path:
                continue
            known_vals = valid_subs[known_path]["tvt"].to_numpy(dtype=float)
            d = rmse(vals, known_vals)
            if d < best[0]:
                best = (d, known_path, KNOWN_PUBLIC_SCORES[known_path])
        nearest_rows.append(
            {
                "path": path,
                "rmse_to_nearest_known": float(best[0]) if np.isfinite(best[0]) else np.nan,
                "nearest_known_path": best[1],
                "nearest_known_public_score": best[2],
            }
        )
    metrics = metrics.merge(pd.DataFrame(nearest_rows), on="path", how="left")

    metrics["risk_grade"] = metrics.apply(risk_grade, axis=1)
    metrics["estimated_public_band"] = metrics.apply(estimated_band, axis=1)
    sort_cols = [c for c in ["known_public_score", "rmse_to_current_best_7p235"] if c in metrics.columns]
    if sort_cols:
        metrics = metrics.sort_values(sort_cols, na_position="last")
    metrics.to_csv(args.output_dir / "local_surrogate_scores.csv", index=False)

    pair_rows = []
    keys = list(valid_subs)
    for i, a in enumerate(keys):
        av = valid_subs[a]["tvt"].to_numpy(dtype=float)
        for b in keys[i + 1 :]:
            bv = valid_subs[b]["tvt"].to_numpy(dtype=float)
            pair_rows.append({"path_a": a, "path_b": b, "rmse": rmse(av, bv), "mae": mae(av, bv)})
    pairwise = pd.DataFrame(pair_rows).sort_values("rmse") if pair_rows else pd.DataFrame()
    pairwise.to_csv(args.output_dir / "local_surrogate_pairwise_distance.csv", index=False)

    known = metrics[np.isfinite(metrics["known_public_score"])].copy()
    report_lines = [
        "# ROGII Local Surrogate Score Report",
        "",
        "This report scores already-generated submission CSV files without using hidden labels.",
        "It cannot replace Kaggle Public LB, but it helps reject implausible candidates before spending limited submissions.",
        "",
        "## Inputs",
        f"- Data dir: `{args.data_dir}`",
        f"- Valid submission files scored: `{len(metrics)}`",
        f"- Known public-score calibration rows: `{len(known)}`",
        "",
        "## Important Limitation",
        "",
        "A submission CSV only contains hidden-row predictions, so true prefix RMSE cannot be computed from a CSV alone.",
        "Instead, the script computes visible-prefix compatibility: first hidden prediction vs last `TVT_input`, slope continuity, jump rate, typewell range checks, and distances to known scored references.",
        "",
        "## Best Known Public Scores In This Scan",
        "",
    ]
    if len(known):
        cols = ["path", "known_public_score", "risk_grade"]
        for col in ["rmse_to_current_best_7p235", "anchor_first_abs_p90", "jump_rate_abs_slope_gt3"]:
            if col in known.columns:
                cols.append(col)
        report_lines.append(markdown_table(known[cols].head(20)))
    else:
        report_lines.append("No known public-score rows were matched.")

    unknown = metrics[metrics["known_public_score"].isna()].copy()
    unknown_sort_cols = [c for c in ["risk_grade", "rmse_to_current_best_7p235"] if c in unknown.columns]
    if unknown_sort_cols:
        unknown = unknown.sort_values(unknown_sort_cols, na_position="last")
    unknown_cols = [
        "path",
        "risk_grade",
        "estimated_public_band",
        "rmse_to_current_best_7p235",
        "nearest_known_public_score",
        "rmse_to_nearest_known",
        "anchor_first_abs_p90",
        "jump_rate_abs_slope_gt3",
    ]
    unknown_cols = [c for c in unknown_cols if c in unknown.columns]
    report_lines.extend(
        [
            "",
            "## Top Unknown Candidates By Surrogate",
            "",
            markdown_table(unknown[unknown_cols].head(25)),
        ]
    )

    report_lines.extend(
        [
            "",
            "## Recommended Use",
            "",
            "1. Run this script after every new kernel output is downloaded.",
            "2. Do not submit candidates marked `reject_known_bad`, `reject_far_from_best`, or `high_shape_risk` unless there is a specific reason.",
            "3. Treat `near_duplicate_low_upside` as safe but unlikely to improve public LB.",
            "4. Prioritize `plausible_submit_candidate` candidates that are not too far from the current best and have low jump/anchor risk.",
            "",
            "## Output Files",
            "",
            "- `experiments/local_surrogate_scores.csv`",
            "- `experiments/local_surrogate_pairwise_distance.csv`",
        ]
    )
    Path("reports/local_surrogate_score_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    print(f"wrote {args.output_dir / 'local_surrogate_scores.csv'}")
    print(f"wrote {args.output_dir / 'local_surrogate_pairwise_distance.csv'}")
    print("wrote reports/local_surrogate_score_report.md")


if __name__ == "__main__":
    main()
