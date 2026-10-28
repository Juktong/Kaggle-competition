#!/usr/bin/env python3
"""Pre-submit checks for ROGII submission.csv files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


JUMP_SLOPE_THRESHOLD = 3.0
WEAK_ANCHOR_GAP_THRESHOLD = 80.0
TYPEWELL_MARGIN = 250.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def safe_key(label: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in label.strip()).strip("_").lower() or "reference"


def parse_submission_ids(ids: pd.Series) -> pd.DataFrame:
    parts = ids.astype(str).str.rsplit("_", n=1, expand=True)
    if parts.shape[1] != 2:
        raise ValueError("submission ids must look like <well>_<row_idx>")
    return pd.DataFrame(
        {
            "id": ids.astype(str).to_numpy(),
            "well": parts[0].to_numpy(),
            "row_idx": pd.to_numeric(parts[1], errors="raise").astype(int).to_numpy(),
        }
    )


def load_reference_submission(path: Path, sample_ids: pd.Series) -> tuple[pd.DataFrame | None, str | None]:
    if not path.is_file():
        return None, f"reference not found: {path}"
    try:
        ref = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        return None, f"could not read reference {path}: {exc}"
    if not {"id", "tvt"}.issubset(ref.columns):
        return None, f"reference {path} must contain id,tvt columns"
    ref = ref[["id", "tvt"]].copy()
    ref["id"] = ref["id"].astype(str)
    if len(ref) != len(sample_ids):
        return None, f"reference row count mismatch for {path}: {len(ref)} vs {len(sample_ids)}"
    if not ref["id"].equals(sample_ids):
        return None, f"reference id order mismatch for {path}"
    vals = pd.to_numeric(ref["tvt"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(vals).all():
        return None, f"reference contains non-finite tvt values: {path}"
    ref["tvt"] = vals
    return ref, None


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    return float(np.sqrt(np.mean(d * d)))


def reference_distance_metrics(
    sub: pd.DataFrame,
    sample_ids: pd.Series,
    references: list[tuple[str, Path]],
    warnings: list[str],
) -> dict:
    distances = {}
    vals = sub["tvt"].to_numpy(dtype=float)
    for label, path in references:
        ref, warning = load_reference_submission(path, sample_ids)
        key = safe_key(label)
        if warning is not None:
            warnings.append(warning)
            distances[key] = {"path": str(path), "status": "SKIP", "reason": warning}
            continue
        assert ref is not None
        diff = vals - ref["tvt"].to_numpy(dtype=float)
        abs_diff = np.abs(diff)
        distances[key] = {
            "path": str(path),
            "status": "PASS",
            "rmse": rmse(vals, ref["tvt"].to_numpy(dtype=float)),
            "mae": float(np.mean(abs_diff)),
            "p95_abs_diff": float(np.quantile(abs_diff, 0.95)),
            "max_abs_diff": float(np.max(abs_diff)),
        }
    return distances


def shape_metrics(sub: pd.DataFrame, sample: pd.DataFrame, data_dir: Path, warnings: list[str]) -> dict:
    parsed = parse_submission_ids(sample["id"].astype(str))
    work = parsed.copy()
    work["tvt"] = sub["tvt"].to_numpy(dtype=float)

    first_gaps = []
    slope_gaps = []
    pred_slopes = []
    pred_curv = []
    weak_anchor_rows = 0
    jump_count = 0
    total_step_count = 0
    typewell_range_violations = 0
    wells_seen = 0
    wells_with_anchor = 0

    for well, group in work.groupby("well", sort=False):
        wells_seen += 1
        group = group.sort_values("row_idx")
        pred = group["tvt"].to_numpy(dtype=float)
        rows = group["row_idx"].to_numpy(dtype=int)

        hw_path = data_dir / "test" / f"{well}__horizontal_well.csv"
        if hw_path.is_file():
            hw = pd.read_csv(hw_path)
            if "TVT_input" in hw.columns:
                tvt_input = pd.to_numeric(hw["TVT_input"], errors="coerce").to_numpy(dtype=float)
                known_idx = np.flatnonzero(np.isfinite(tvt_input))
                if len(known_idx) > 0 and len(rows) > 0:
                    before = known_idx[known_idx < rows[0]]
                    if len(before) > 0:
                        wells_with_anchor += 1
                        last_idx = int(before[-1])
                        gap = float(pred[0] - tvt_input[last_idx])
                        first_gaps.append(gap)
                        if abs(gap) > WEAK_ANCHOR_GAP_THRESHOLD:
                            weak_anchor_rows += len(group)
                        if len(before) >= 8 and len(pred) >= 2:
                            tail = before[-8:]
                            x = tail.astype(float)
                            y = tvt_input[tail]
                            if np.ptp(x) > 0:
                                last_slope = float(np.polyfit(x, y, 1)[0])
                                n = min(8, len(pred))
                                first_slope = float(np.polyfit(rows[:n].astype(float), pred[:n], 1)[0])
                                slope_gaps.append(first_slope - last_slope)

        if len(pred) >= 2:
            slopes = np.diff(pred)
            pred_slopes.extend(slopes.tolist())
            total_step_count += len(slopes)
            jump_count += int(np.sum(np.abs(slopes) > JUMP_SLOPE_THRESHOLD))
        if len(pred) >= 3:
            pred_curv.extend(np.diff(pred, n=2).tolist())

        tw_path = data_dir / "test" / f"{well}__typewell.csv"
        if tw_path.is_file():
            try:
                tw = pd.read_csv(tw_path, usecols=["TVT"])
                lo = float(tw["TVT"].min()) - TYPEWELL_MARGIN
                hi = float(tw["TVT"].max()) + TYPEWELL_MARGIN
                typewell_range_violations += int(np.sum((pred < lo) | (pred > hi)))
            except Exception as exc:  # pragma: no cover - defensive CLI guard
                warnings.append(f"could not check typewell TVT range for {well}: {exc}")

    first_gap_arr = np.asarray(first_gaps, dtype=float)
    slope_gap_arr = np.asarray(slope_gaps, dtype=float)
    slopes_arr = np.asarray(pred_slopes, dtype=float)
    curv_arr = np.asarray(pred_curv, dtype=float)
    rows_total = max(1, len(work))
    step_total = max(1, total_step_count)

    metrics = {
        "wells_seen": int(wells_seen),
        "wells_with_anchor": int(wells_with_anchor),
        "anchor_first_abs_median": float(np.nanmedian(np.abs(first_gap_arr))) if len(first_gap_arr) else None,
        "anchor_first_abs_p90": float(np.nanquantile(np.abs(first_gap_arr), 0.90)) if len(first_gap_arr) else None,
        "anchor_weak_row_frac": weak_anchor_rows / rows_total,
        "slope_gap_abs_median": float(np.nanmedian(np.abs(slope_gap_arr))) if len(slope_gap_arr) else None,
        "slope_abs_p50": float(np.nanmedian(np.abs(slopes_arr))) if len(slopes_arr) else None,
        "slope_abs_p95": float(np.nanquantile(np.abs(slopes_arr), 0.95)) if len(slopes_arr) else None,
        "curvature_abs_p95": float(np.nanquantile(np.abs(curv_arr), 0.95)) if len(curv_arr) else None,
        "jump_rate_abs_slope_gt3": jump_count / step_total,
        "typewell_range_violation_frac": typewell_range_violations / rows_total,
    }

    p90_gap = metrics["anchor_first_abs_p90"]
    if p90_gap is not None and p90_gap > WEAK_ANCHOR_GAP_THRESHOLD:
        warnings.append(f"large anchor gap p90: {p90_gap:.3f}")
    if metrics["anchor_weak_row_frac"] > 0.10:
        warnings.append(f"weak anchor row fraction is high: {metrics['anchor_weak_row_frac']:.4f}")
    if metrics["jump_rate_abs_slope_gt3"] > 0.02:
        warnings.append(f"jump rate abs slope > {JUMP_SLOPE_THRESHOLD:g} is high: {metrics['jump_rate_abs_slope_gt3']:.4f}")
    if metrics["typewell_range_violation_frac"] > 0.02:
        warnings.append(f"typewell range violation fraction is high: {metrics['typewell_range_violation_frac']:.4f}")

    return metrics


def audit(
    submission_path: Path,
    sample_path: Path | None = None,
    data_dir: Path | None = None,
    references: list[tuple[str, Path]] | None = None,
) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    references = references or []

    if not submission_path.is_file():
        raise FileNotFoundError(f"submission not found: {submission_path}")

    sub = pd.read_csv(submission_path)
    if list(sub.columns) != ["id", "tvt"]:
        fail(errors, f"columns must be exactly ['id', 'tvt']; got {list(sub.columns)}")

    if "id" not in sub.columns:
        fail(errors, "missing id column")
    if "tvt" not in sub.columns:
        fail(errors, "missing tvt column")

    if "id" in sub.columns:
        sub["id"] = sub["id"].astype(str)
        duplicated = int(sub["id"].duplicated().sum())
        if duplicated:
            fail(errors, f"duplicate ids: {duplicated}")

    tvt_stats = {}
    if "tvt" in sub.columns:
        tvt = pd.to_numeric(sub["tvt"], errors="coerce").to_numpy(dtype=float)
        finite = np.isfinite(tvt)
        non_finite = int((~finite).sum())
        if non_finite:
            fail(errors, f"non-finite tvt values: {non_finite}")
        if len(tvt):
            tvt_stats = {
                "tvt_min": float(np.nanmin(tvt)),
                "tvt_max": float(np.nanmax(tvt)),
                "tvt_mean": float(np.nanmean(tvt)),
                "tvt_std": float(np.nanstd(tvt)),
            }
            if tvt_stats["tvt_std"] == 0:
                warnings.append("tvt has zero standard deviation")

    sample_info = {}
    sample = None
    if sample_path is None and data_dir is not None and (data_dir / "sample_submission.csv").is_file():
        sample_path = data_dir / "sample_submission.csv"
    if sample_path is not None:
        if not sample_path.is_file():
            raise FileNotFoundError(f"sample not found: {sample_path}")
        sample = pd.read_csv(sample_path)
        if "id" not in sample.columns:
            fail(errors, "sample is missing id column")
        else:
            sample_ids = sample["id"].astype(str)
            sample_info["sample_rows"] = int(len(sample))
            if len(sub) != len(sample):
                fail(errors, f"row count mismatch: submission={len(sub)} sample={len(sample)}")
            if "id" in sub.columns:
                order_match = bool(sub["id"].equals(sample_ids))
                sample_info["id_order_matches_sample"] = order_match
                if not order_match:
                    fail(errors, "id order does not match sample_submission.csv")

    deep_info = {}
    if sample is not None and "id" in sample.columns and "id" in sub.columns and "tvt" in sub.columns and not errors:
        if references:
            deep_info["reference_distances"] = reference_distance_metrics(
                sub,
                sample["id"].astype(str),
                references,
                warnings,
            )
        if data_dir is not None:
            try:
                deep_info["shape_metrics"] = shape_metrics(sub, sample, data_dir, warnings)
            except Exception as exc:  # pragma: no cover - defensive CLI guard
                warnings.append(f"shape metrics skipped: {exc}")

    risk_status = "WARN" if warnings else "PASS"
    return {
        "status": "PASS" if not errors else "FAIL",
        "risk_status": risk_status,
        "submission_path": str(submission_path),
        "sample_path": str(sample_path) if sample_path is not None else None,
        "data_dir": str(data_dir) if data_dir is not None else None,
        "rows": int(len(sub)),
        "columns": list(sub.columns),
        "sha256_submission_csv": sha256_file(submission_path),
        "errors": errors,
        "warnings": warnings,
        **sample_info,
        **tvt_stats,
        **deep_info,
    }


def parse_reference_args(values: list[str]) -> list[tuple[str, Path]]:
    out = []
    for value in values:
        if "=" in value:
            label, path = value.split("=", 1)
        else:
            path = value
            label = Path(path).parent.name or Path(path).stem
        out.append((label.strip(), Path(path)))
    return out


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def load_reference_registry(path: Path) -> list[tuple[str, Path]]:
    if not path.is_file():
        raise FileNotFoundError(f"reference registry not found: {path}")
    registry = pd.read_csv(path)
    required = {"label", "path"}
    missing = required - set(registry.columns)
    if missing:
        raise ValueError(f"reference registry missing columns: {sorted(missing)}")
    if "enabled" in registry.columns:
        registry = registry[registry["enabled"].map(truthy)]
    references = []
    for _, row in registry.iterrows():
        label = str(row["label"]).strip()
        ref_path = Path(str(row["path"]).strip())
        if label and str(ref_path):
            references.append((label, ref_path))
    return references


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path, help="Path to submission.csv")
    parser.add_argument("--sample", type=Path, default=None, help="Path to sample_submission.csv")
    parser.add_argument("--data-dir", type=Path, default=None, help="Optional data dir with sample_submission.csv and test/")
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Optional reference submission as LABEL=PATH. Can be passed multiple times.",
    )
    parser.add_argument(
        "--reference-registry",
        type=Path,
        default=None,
        help="Optional CSV with label,path,enabled columns for reference submissions.",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Optional audit JSON output path")
    args = parser.parse_args()

    references = []
    if args.reference_registry is not None:
        references.extend(load_reference_registry(args.reference_registry))
    references.extend(parse_reference_args(args.reference))

    result = audit(args.submission, args.sample, args.data_dir, references)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
