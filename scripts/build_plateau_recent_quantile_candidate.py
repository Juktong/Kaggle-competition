#!/usr/bin/env python3
"""Build a sparse plateau recent-quantile candidate from a baseline submission."""

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
    return pd.DataFrame(
        {
            "id": ids.astype(str).to_numpy(),
            "well": parts[0].to_numpy(),
            "row_idx": parts[1].astype(int).to_numpy(),
        }
    )


def read_submission(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if list(df.columns) != ["id", "tvt"]:
        raise ValueError(f"{path} must have columns ['id', 'tvt']; got {list(df.columns)}")
    df["id"] = df["id"].astype(str)
    df["tvt"] = pd.to_numeric(df["tvt"], errors="raise").astype(float)
    if df["id"].duplicated().any():
        raise ValueError(f"{path} has duplicate ids")
    if not np.isfinite(df["tvt"].to_numpy(float)).all():
        raise ValueError(f"{path} contains non-finite tvt")
    return df


def horizontal_path(data_dir: Path, well: str) -> Path:
    nested = data_dir / "test" / f"{well}__horizontal_well.csv"
    if nested.exists():
        return nested
    flat = data_dir / f"{well}__horizontal_well.csv"
    if flat.exists():
        return flat
    raise FileNotFoundError(f"missing test horizontal well for {well} under {data_dir}")


def build_candidate(
    baseline: pd.DataFrame,
    data_dir: Path,
    window: int,
    quantile: float,
    min_move: float,
    blend: float,
    max_move: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    parsed = parse_ids(baseline["id"])
    work = parsed.merge(baseline, on="id", how="left")
    out = baseline.copy()
    out_values = dict(zip(out["id"], out["tvt"]))
    report_rows = []

    for well, group in work.groupby("well", sort=False):
        group = group.sort_values("row_idx")
        try:
            hw = pd.read_csv(horizontal_path(data_dir, well))
        except Exception as exc:
            report_rows.append({"well": well, "status": "keep_baseline", "reason": f"missing_hw:{exc}", "rows": len(group)})
            continue

        if "TVT_input" not in hw.columns:
            report_rows.append({"well": well, "status": "keep_baseline", "reason": "missing_TVT_input", "rows": len(group)})
            continue

        tvt_input = pd.to_numeric(hw["TVT_input"], errors="coerce").to_numpy(float)
        known = np.flatnonzero(np.isfinite(tvt_input))
        if len(known) < window:
            report_rows.append(
                {"well": well, "status": "keep_baseline", "reason": "short_prefix", "rows": len(group), "known_rows": len(known)}
            )
            continue

        tail = tvt_input[known[-min(window, len(known)) :]]
        last_value = float(tvt_input[known[-1]])
        target = float(np.nanquantile(tail, quantile))
        raw_move = target - last_value
        if not np.isfinite(raw_move) or abs(raw_move) < min_move:
            report_rows.append(
                {
                    "well": well,
                    "status": "keep_baseline",
                    "reason": "below_min_move",
                    "rows": len(group),
                    "known_rows": len(known),
                    "last_value": last_value,
                    "target": target,
                    "raw_move": raw_move,
                }
            )
            continue

        move = float(np.clip(blend * raw_move, -max_move, max_move))
        plateau_value = last_value + move
        for rid in group["id"].astype(str):
            out_values[rid] = plateau_value

        report_rows.append(
            {
                "well": well,
                "status": "plateau_replaced",
                "reason": "passed_min_move",
                "rows": len(group),
                "known_rows": len(known),
                "last_value": last_value,
                "target": target,
                "raw_move": raw_move,
                "applied_move": move,
                "plateau_value": plateau_value,
            }
        )

    out["tvt"] = out["id"].map(out_values).astype(float)
    return out, pd.DataFrame(report_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--window", type=int, default=256)
    parser.add_argument("--quantile", type=float, default=0.50)
    parser.add_argument("--min-move", type=float, default=4.0)
    parser.add_argument("--blend", type=float, default=1.0)
    parser.add_argument("--max-move", type=float, default=12.0)
    args = parser.parse_args()

    baseline = read_submission(args.baseline)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    candidate, report = build_candidate(
        baseline=baseline,
        data_dir=args.data_dir,
        window=args.window,
        quantile=args.quantile,
        min_move=args.min_move,
        blend=args.blend,
        max_move=args.max_move,
    )

    out_path = args.output_dir / "submission.csv"
    report_path = args.output_dir / "plateau_recent_quantile_report.csv"
    audit_path = args.output_dir / "candidate_audit.json"
    candidate.to_csv(out_path, index=False)
    report.to_csv(report_path, index=False)

    diff = candidate["tvt"].to_numpy(float) - baseline["tvt"].to_numpy(float)
    audit = {
        "candidate": "plateau_recent_quantile",
        "baseline": str(args.baseline),
        "rows": int(len(candidate)),
        "changed_wells": int((report["status"] == "plateau_replaced").sum()) if len(report) else 0,
        "window": int(args.window),
        "quantile": float(args.quantile),
        "min_move": float(args.min_move),
        "blend": float(args.blend),
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
