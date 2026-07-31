#!/usr/bin/env python3
"""Evaluate a first multi-hypothesis geosteering router on pseudo-hidden splits."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_DATA_DIR = Path("data/sample")
DEFAULT_OUTPUT_DIR = Path("experiments")
DEFAULT_REPORT = Path("reports/multi_hypothesis_router_cv_report.md")
STRAT_COLUMNS = ["Z", "ANCC", "ASTNU", "ASTNL", "EGFDU", "EGFDL", "BUDA"]


@dataclass
class PathCandidate:
    method: str
    values: np.ndarray
    status: str = "ok"
    detail: str = ""
    diagnostics: dict[str, float] | None = None


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return "" if not np.isfinite(value) else f"{value:.6g}"
    if pd.isna(value):
        return ""
    return str(value)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows."
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def rmse(pred: np.ndarray, true: np.ndarray) -> float:
    pred = np.asarray(pred, dtype=float)
    true = np.asarray(true, dtype=float)
    mask = np.isfinite(pred) & np.isfinite(true)
    if int(mask.sum()) == 0:
        return float("nan")
    diff = pred[mask] - true[mask]
    return float(np.sqrt(np.mean(diff * diff)))


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


def safe_interp(x: np.ndarray, y: np.ndarray, target: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    target = np.asarray(target, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 5:
        return np.full(len(target), np.nan, dtype=float)
    x = x[mask]
    y = y[mask]
    order = np.argsort(x)
    x = x[order]
    y = y[order]
    keep = np.r_[True, np.diff(x) > 1e-9]
    x = x[keep]
    y = y[keep]
    if len(x) < 5:
        return np.full(len(target), np.nan, dtype=float)
    return np.interp(target, x, y, left=np.nan, right=np.nan)


def predict_line(x_train: np.ndarray, y_train: np.ndarray, x_eval: np.ndarray, fallback: float) -> np.ndarray:
    fit = finite_line_fit(x_train, y_train)
    if fit is None:
        return np.full(len(x_eval), float(fallback), dtype=float)
    slope, intercept = fit
    pred = slope * np.asarray(x_eval, dtype=float) + intercept
    pred[~np.isfinite(pred)] = float(fallback)
    return pred.astype(float)


def damp_toward(fallback: float, raw: np.ndarray, damp: float, max_move: float) -> np.ndarray:
    move = np.asarray(raw, dtype=float) - float(fallback)
    move = np.clip(damp * move, -max_move, max_move)
    return float(fallback) + move


def saturating_move(move: np.ndarray, max_move: float) -> np.ndarray:
    move = np.asarray(move, dtype=float)
    if max_move <= 0:
        return np.zeros_like(move, dtype=float)
    return max_move * np.tanh(move / max_move)


def interp_typewell_gr(tw: pd.DataFrame, tvt: np.ndarray) -> np.ndarray:
    if not {"TVT", "GR"}.issubset(tw.columns):
        return np.full(len(tvt), np.nan, dtype=float)
    work = tw[["TVT", "GR"]].copy()
    work["TVT"] = pd.to_numeric(work["TVT"], errors="coerce")
    work["GR"] = pd.to_numeric(work["GR"], errors="coerce")
    work = work.dropna().sort_values("TVT")
    return safe_interp(work["TVT"].to_numpy(float), work["GR"].to_numpy(float), np.asarray(tvt, dtype=float))


def robust_mae(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) < 20:
        return float("nan")
    return float(np.nanmedian(np.abs(a[mask] - b[mask])))


def normalized_corr(a: np.ndarray, b: np.ndarray, min_pairs: int = 20) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) < min_pairs:
        return float("nan")
    aa = a[mask] - float(np.nanmean(a[mask]))
    bb = b[mask] - float(np.nanmean(b[mask]))
    denom = float(np.sqrt(np.sum(aa * aa) * np.sum(bb * bb)))
    if denom <= 1e-12:
        return float("nan")
    return float(np.sum(aa * bb) / denom)


def best_gr_shift(gr: np.ndarray, tw: pd.DataFrame, tvt_path: np.ndarray, shifts: np.ndarray) -> tuple[float, float, float, float]:
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


def best_ncc_shift(gr: np.ndarray, tw: pd.DataFrame, tvt_path: np.ndarray, shifts: np.ndarray) -> tuple[float, float, float, float]:
    scores = np.asarray([normalized_corr(gr, interp_typewell_gr(tw, tvt_path + shift)) for shift in shifts], dtype=float)
    if not np.isfinite(scores).any():
        return 0.0, float("nan"), float("nan"), 0.0
    zero_idx = int(np.argmin(np.abs(shifts)))
    zero_score = float(scores[zero_idx])
    best_idx = int(np.nanargmax(scores))
    best_score = float(scores[best_idx])
    gain = 0.0
    if np.isfinite(zero_score):
        gain = float(best_score - zero_score)
    return float(shifts[best_idx]), zero_score, best_score, gain


def self_corr_prefix_shape_candidate(
    hw: pd.DataFrame,
    train_valid: np.ndarray,
    eval_idx: np.ndarray,
    true_tvt: np.ndarray,
    fallback: float,
    args: argparse.Namespace,
) -> PathCandidate | None:
    if "GR" not in hw.columns or len(train_valid) < args.self_corr_window * 2 or len(eval_idx) < args.self_corr_min_eval_rows:
        return None
    gr_full = pd.to_numeric(hw["GR"], errors="coerce").interpolate(limit_direction="both").to_numpy(float)
    window = int(min(args.self_corr_window, len(eval_idx), max(args.self_corr_min_eval_rows, len(train_valid) // 2)))
    if window < args.self_corr_min_eval_rows:
        return None
    eval_gr = gr_full[eval_idx[:window]]
    start_min = int(train_valid[0])
    start_max = int(train_valid[-1] - window + 1)
    if start_max <= start_min:
        return None

    best_corr = float("nan")
    best_start = -1
    for start in range(start_min, start_max + 1, max(1, args.self_corr_stride)):
        idx = np.arange(start, start + window, dtype=int)
        if not np.isfinite(true_tvt[idx]).all():
            continue
        corr = normalized_corr(eval_gr, gr_full[idx], min_pairs=args.self_corr_min_pairs)
        if np.isfinite(corr) and (not np.isfinite(best_corr) or corr > best_corr):
            best_corr = corr
            best_start = start

    if best_start < 0 or not np.isfinite(best_corr):
        return None
    if best_corr < args.self_corr_min_corr:
        return PathCandidate(
            "self_corr_prefix_shape",
            np.full(len(eval_idx), fallback, dtype=float),
            status="fallback",
            detail=f"corr_below_gate;corr={best_corr:.4f}",
            diagnostics={"self_corr": best_corr, "self_corr_start": float(best_start)},
        )

    match_idx = np.arange(best_start, best_start + window, dtype=int)
    delta = true_tvt[match_idx] - float(true_tvt[match_idx[0]])
    delta = np.clip(delta, -args.max_move, args.max_move)
    pred = np.full(len(eval_idx), fallback + float(delta[-1]), dtype=float)
    pred[:window] = fallback + delta
    return PathCandidate(
        "self_corr_prefix_shape",
        pred,
        detail=f"corr={best_corr:.4f};start={best_start};window={window}",
        diagnostics={"self_corr": best_corr, "self_corr_start": float(best_start)},
    )


def piecewise_tail_slope_candidate(
    method: str,
    x: np.ndarray,
    train_valid: np.ndarray,
    eval_idx: np.ndarray,
    true_tvt: np.ndarray,
    fallback: float,
    damp: float,
    max_move: float,
    min_feature_span: float,
) -> PathCandidate | None:
    tail_idx = train_valid[-min(len(train_valid), 256) :]
    if len(tail_idx) < 20:
        return None
    fit = finite_line_fit(x[tail_idx], true_tvt[tail_idx])
    span = float(np.nanmax(x[tail_idx]) - np.nanmin(x[tail_idx])) if len(tail_idx) else 0.0
    if fit is None or not np.isfinite(span) or abs(span) < min_feature_span:
        return PathCandidate(method, np.full(len(eval_idx), fallback, dtype=float), status="fallback", detail="insufficient_tail_span")
    slope, _ = fit
    raw_move = slope * (np.asarray(x[eval_idx], dtype=float) - float(x[train_valid[-1]]))
    move = np.clip(damp * saturating_move(raw_move, max_move), -max_move, max_move)
    pred = fallback + move
    pred[~np.isfinite(pred)] = fallback
    return PathCandidate(
        method,
        pred,
        detail=f"slope={slope:.6g};span={span:.3f};damp={damp:.3f}",
        diagnostics={"piecewise_slope": slope, "piecewise_span": span},
    )


def fault_step_recent_level_candidate(
    train_valid: np.ndarray,
    eval_idx: np.ndarray,
    true_tvt: np.ndarray,
    fallback: float,
    args: argparse.Namespace,
) -> PathCandidate | None:
    window = int(args.fault_window)
    if len(train_valid) < 2 * window:
        return None
    prev = true_tvt[train_valid[-2 * window : -window]]
    recent = true_tvt[train_valid[-window:]]
    prev_med = float(np.nanmedian(prev))
    recent_med = float(np.nanmedian(recent))
    step = recent_med - prev_med
    if not np.isfinite(step) or abs(step) < args.fault_min_step:
        return PathCandidate(
            "fault_step_recent_level",
            np.full(len(eval_idx), fallback, dtype=float),
            status="fallback",
            detail=f"step_below_gate;step={step:.4f}",
            diagnostics={"fault_step": step},
        )
    ramp = 1.0 - np.exp(-np.arange(len(eval_idx), dtype=float) / max(20.0, 0.08 * len(eval_idx)))
    move = np.clip(args.fault_damp * step * ramp, -args.max_move, args.max_move)
    return PathCandidate(
        "fault_step_recent_level",
        fallback + move,
        detail=f"step={step:.4f};window={window};damp={args.fault_damp:.3f}",
        diagnostics={"fault_step": step},
    )


def native_cut_index(hw: pd.DataFrame) -> int | None:
    if "TVT_input" not in hw.columns:
        return None
    tvt_input = pd.to_numeric(hw["TVT_input"], errors="coerce").to_numpy(float)
    finite = np.flatnonzero(np.isfinite(tvt_input))
    if len(finite) == 0:
        return None
    return int(finite[-1] + 1)


def split_specs(hw: pd.DataFrame, cut_fracs: list[float], include_native: bool) -> list[tuple[str, int]]:
    specs: list[tuple[str, int]] = []
    if include_native:
        cut = native_cut_index(hw)
        if cut is not None:
            specs.append(("native_prefix", cut))
    n = len(hw)
    for frac in cut_fracs:
        specs.append((f"frac_{frac:.2f}", int(round(n * frac))))
    deduped: dict[tuple[str, int], tuple[str, int]] = {}
    for name, cut in specs:
        deduped.setdefault((name, cut), (name, cut))
    return list(deduped.values())


def prefix_holdout_cut(prefix_idx: np.ndarray, args: argparse.Namespace) -> int | None:
    if len(prefix_idx) < args.min_prefix_rows + args.router_min_holdout_rows:
        return None
    holdout_n = max(args.router_min_holdout_rows, int(round(args.router_holdout_frac * len(prefix_idx))))
    holdout_n = min(holdout_n, max(args.router_min_holdout_rows, len(prefix_idx) // 2))
    cut = int(prefix_idx[-holdout_n])
    if cut < args.min_prefix_rows:
        return None
    return cut


# --- Minimal 1-D particle filter over typewell GR likelihood ------------------
# State (tvt, dip). Motion: dip random-walks (bounded) + rare fault jumps and an
# Ornstein-Uhlenbeck pull toward the anchor (kappa) that makes the estimate
# revert to last_value when GR is uninformative. Observation: typewell GR
# likelihood at each particle's tvt (GR-missing rows carry no update). sigma_gr
# and dip0 are calibrated from the KNOWN prefix only, so the candidate stays
# hidden-test compatible. Validated on real train wells: strong low-catastrophic
# rescue on high-drift wells, benefit concentrated so it is a routed candidate.

def _systematic_resample(weights: np.ndarray, u: float) -> np.ndarray:
    n = len(weights)
    positions = (u + np.arange(n)) / n
    return np.searchsorted(np.cumsum(weights), positions).clip(0, n - 1)


def _robust_std(values: np.ndarray, floor: float) -> float:
    values = values[np.isfinite(values)]
    if len(values) < 10:
        return floor
    mad = float(np.median(np.abs(values - np.median(values))))
    return max(floor, 1.4826 * mad)


def typewell_particle_filter_candidate(
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    train_valid: np.ndarray,
    eval_idx: np.ndarray,
    true_tvt: np.ndarray,
    fallback: float,
    args: argparse.Namespace,
) -> PathCandidate | None:
    if "GR" not in hw.columns or not {"TVT", "GR"}.issubset(tw.columns):
        return None
    twf = tw[["TVT", "GR"]].apply(pd.to_numeric, errors="coerce").dropna().sort_values("TVT")
    if len(twf) < 30:
        return None
    tw_tvt = twf["TVT"].to_numpy(float)
    tw_gr = twf["GR"].to_numpy(float)
    md = pd.to_numeric(hw["MD"], errors="coerce").to_numpy(float)
    gr = pd.to_numeric(hw["GR"], errors="coerce").to_numpy(float)

    n_particles = int(getattr(args, "pf_particles", 300))
    kappa = float(getattr(args, "pf_kappa", 0.02))
    q_tvt = float(getattr(args, "pf_q_tvt", 0.25))
    q_dip = float(getattr(args, "pf_q_dip", 0.002))
    dip_persist = float(getattr(args, "pf_dip_persist", 0.97))
    dip_cap = float(getattr(args, "pf_dip_cap", 0.15))
    dip_shrink = float(getattr(args, "pf_dip_shrink", 0.2))
    fault_p = float(getattr(args, "pf_fault_p", 0.02))
    fault_scale = float(getattr(args, "pf_fault_scale", 8.0))
    ess_frac = float(getattr(args, "pf_ess_frac", 0.5))
    sigma_floor = float(getattr(args, "pf_sigma_floor", 6.0))
    tail = int(getattr(args, "pf_dip_tail", 250))
    init_tvt = float(getattr(args, "pf_init_tvt", 1.0))
    seed = int(getattr(args, "pf_seed", 20260701))

    # calibrate sigma_gr and dip0 from the known prefix only
    md_p = md[train_valid]
    gr_p = gr[train_valid]
    tvt_p = true_tvt[train_valid]
    resid = gr_p - np.interp(tvt_p, tw_tvt, tw_gr, left=np.nan, right=np.nan)
    sigma_gr = _robust_std(resid, sigma_floor)
    dip0 = 0.0
    mask_p = np.isfinite(tvt_p) & np.isfinite(md_p)
    if int(mask_p.sum()) >= 30:
        k = min(tail, int(mask_p.sum()))
        xi = md_p[mask_p][-k:]
        yi = tvt_p[mask_p][-k:]
        if xi[-1] - xi[0] > 1e-6:
            dip0 = float(np.polyfit(xi, yi, 1)[0])
    dip0 = float(np.clip(dip0 * dip_shrink, -dip_cap, dip_cap))

    md_e = md[eval_idx]
    gr_e = gr[eval_idx]
    m = len(md_e)
    if m == 0 or not np.isfinite(md_e).any():
        return None
    rng = np.random.default_rng(seed)
    lo, hi = float(tw_tvt.min()), float(tw_tvt.max())
    step = float(np.median(np.diff(md_e))) if m > 1 else 1.0
    dmd = np.diff(md_e, prepend=md_e[0] - (step if step else 1.0))
    tvt = fallback + rng.normal(0, init_tvt, n_particles)
    dip = np.clip(dip0 + rng.normal(0, max(q_dip, 1e-6), n_particles), -dip_cap, dip_cap)
    w = np.full(n_particles, 1.0 / n_particles)
    pred = np.full(m, fallback, dtype=float)
    spread = np.zeros(m)
    for i in range(m):
        dip = np.clip(dip * dip_persist + rng.normal(0, q_dip, n_particles), -dip_cap, dip_cap)
        noise = rng.normal(0, q_tvt, n_particles)
        jump = rng.random(n_particles) < fault_p
        if jump.any():
            noise[jump] += rng.normal(0, fault_scale, int(jump.sum()))
        tvt = np.clip(tvt + dip * dmd[i] + kappa * (fallback - tvt) + noise, lo, hi)
        g = gr_e[i]
        if np.isfinite(g):
            gt = np.interp(tvt, tw_tvt, tw_gr)
            ll = -0.5 * ((g - gt) / sigma_gr) ** 2
            w = w * np.exp(ll - np.nanmax(ll))
            s = float(w.sum())
            w = np.full(n_particles, 1.0 / n_particles) if (not np.isfinite(s) or s <= 0) else w / s
        mean = float(np.sum(w * tvt))
        pred[i] = mean
        spread[i] = float(np.sqrt(max(0.0, np.sum(w * (tvt - mean) ** 2))))
        if 1.0 / float(np.sum(w ** 2)) < ess_frac * n_particles:
            idx = _systematic_resample(w, float(rng.random()))
            tvt = tvt[idx]
            dip = dip[idx]
            w = np.full(n_particles, 1.0 / n_particles)
    gr_cov = float(np.isfinite(gr_e).mean())
    return PathCandidate(
        "typewell_particle_filter",
        pred,
        detail=f"sigma_gr={sigma_gr:.2f};dip0={dip0:.4f};kappa={kappa:.3f};gr_cov={gr_cov:.2f}",
        diagnostics={
            "pf_sigma_gr": sigma_gr,
            "pf_dip0": dip0,
            "pf_post_std": float(np.mean(spread)),
            "pf_mean_abs_dev": float(np.mean(np.abs(pred - fallback))),
            "pf_gr_coverage": gr_cov,
        },
    )


def candidate_paths(
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    train_idx: np.ndarray,
    eval_idx: np.ndarray,
    true_tvt: np.ndarray,
    args: argparse.Namespace,
) -> list[PathCandidate]:
    md = pd.to_numeric(hw["MD"], errors="coerce").to_numpy(float)
    train_valid = train_idx[np.isfinite(true_tvt[train_idx])]
    if len(train_valid) == 0:
        return []
    fallback = float(true_tvt[train_valid[-1]])
    tail_idx = train_valid[-min(args.tail_rows, len(train_valid)) :]

    candidates: list[PathCandidate] = []
    candidates.append(PathCandidate("last_value", np.full(len(eval_idx), fallback, dtype=float)))

    raw_tail = predict_line(md[tail_idx], true_tvt[tail_idx], md[eval_idx], fallback)
    candidates.append(
        PathCandidate(
            "damped_tail_linear_md",
            damp_toward(fallback, raw_tail, args.tail_damp, args.max_move),
            detail=f"damp={args.tail_damp:.3f};max_move={args.max_move:.3f}",
        )
    )

    for col in STRAT_COLUMNS:
        if col not in hw.columns:
            continue
        x = pd.to_numeric(hw[col], errors="coerce").to_numpy(float)
        raw = predict_line(x[tail_idx], true_tvt[tail_idx], x[eval_idx], fallback)
        candidates.append(
            PathCandidate(
                f"damped_tail_linear_{col}",
                damp_toward(fallback, raw, args.strat_damp, args.max_move),
                detail=f"damp={args.strat_damp:.3f};max_move={args.max_move:.3f}",
            )
        )

    piecewise_md = piecewise_tail_slope_candidate(
        "piecewise_tail_slope_md",
        md,
        train_valid,
        eval_idx,
        true_tvt,
        fallback,
        args.piecewise_damp,
        args.max_move,
        args.piecewise_min_feature_span,
    )
    if piecewise_md is not None:
        candidates.append(piecewise_md)

    if "Z" in hw.columns:
        z = pd.to_numeric(hw["Z"], errors="coerce").to_numpy(float)
        piecewise_z = piecewise_tail_slope_candidate(
            "piecewise_tail_slope_Z",
            z,
            train_valid,
            eval_idx,
            true_tvt,
            fallback,
            args.piecewise_damp,
            args.max_move,
            args.piecewise_min_feature_span,
        )
        if piecewise_z is not None:
            candidates.append(piecewise_z)

    fault_step = fault_step_recent_level_candidate(train_valid, eval_idx, true_tvt, fallback, args)
    if fault_step is not None:
        candidates.append(fault_step)

    if len(train_valid) >= args.plateau_window:
        tail = true_tvt[train_valid[-min(args.plateau_window, len(train_valid)) :]]
        target = float(np.nanquantile(tail, args.plateau_quantile))
        move = np.clip(target - fallback, -args.max_move, args.max_move)
        candidates.append(
            PathCandidate(
                "recent_plateau_quantile",
                np.full(len(eval_idx), fallback + args.plateau_blend * move, dtype=float),
                detail=f"window={args.plateau_window};quantile={args.plateau_quantile:.3f};move={move:.3f}",
            )
        )

    self_corr = self_corr_prefix_shape_candidate(hw, train_valid, eval_idx, true_tvt, fallback, args)
    if self_corr is not None:
        candidates.append(self_corr)

    pf = typewell_particle_filter_candidate(hw, tw, train_valid, eval_idx, true_tvt, fallback, args)
    if pf is not None:
        candidates.append(pf)

    if "GR" in hw.columns:
        gr_full = pd.to_numeric(hw["GR"], errors="coerce").interpolate(limit_direction="both").to_numpy(float)
        shifts = np.arange(-args.max_gr_shift, args.max_gr_shift + 1e-9, args.gr_shift_step)
        prefix_gr = train_valid[np.isfinite(gr_full[train_valid])]
        eval_gr_mask = np.isfinite(gr_full[eval_idx])
        if len(prefix_gr) >= args.min_gr_rows and int(eval_gr_mask.sum()) >= args.min_gr_rows:
            prefix_shift, _, _, prefix_improvement = best_gr_shift(gr_full[prefix_gr], tw, true_tvt[prefix_gr], shifts)
            for base in list(candidates):
                eval_shift, _, _, eval_improvement = best_gr_shift(
                    gr_full[eval_idx][eval_gr_mask],
                    tw,
                    base.values[eval_gr_mask],
                    shifts,
                )
                if abs(prefix_shift) > args.max_prefix_shift_abs:
                    status = "fallback"
                    shifted = base.values.copy()
                    detail = "prefix_shift_unstable"
                elif eval_improvement < args.min_eval_improvement or abs(eval_shift) < 1e-9:
                    status = "fallback"
                    shifted = base.values.copy()
                    detail = "eval_shift_not_confident"
                else:
                    status = "ok"
                    ramp = 1.0 - np.exp(-np.arange(len(eval_idx), dtype=float) / max(30.0, 0.10 * len(eval_idx)))
                    shifted = base.values + np.clip(args.gr_alpha * eval_shift * ramp, -args.max_move, args.max_move)
                    detail = f"eval_shift={eval_shift:.3f};eval_improvement={eval_improvement:.4f}"
                candidates.append(
                    PathCandidate(
                        f"gr_shift__{base.method}",
                        shifted,
                        status=status,
                        detail=detail,
                        diagnostics={
                            "prefix_gr_shift": prefix_shift,
                            "prefix_gr_improvement": prefix_improvement,
                            "eval_gr_shift": eval_shift,
                            "eval_gr_improvement": eval_improvement,
                        },
                    )
                )
            ncc_prefix_shift, _, ncc_prefix_score, ncc_prefix_gain = best_ncc_shift(
                gr_full[prefix_gr],
                tw,
                true_tvt[prefix_gr],
                shifts,
            )
            for base in [candidate for candidate in candidates if candidate.method in {"last_value", "recent_plateau_quantile"}]:
                eval_shift, zero_corr, best_corr, corr_gain = best_ncc_shift(
                    gr_full[eval_idx][eval_gr_mask],
                    tw,
                    base.values[eval_gr_mask],
                    shifts,
                )
                if abs(ncc_prefix_shift) > args.max_prefix_shift_abs:
                    status = "fallback"
                    shifted = base.values.copy()
                    detail = "prefix_ncc_shift_unstable"
                elif (
                    not np.isfinite(best_corr)
                    or best_corr < args.min_ncc_corr
                    or corr_gain < args.min_ncc_gain
                    or abs(eval_shift) < 1e-9
                ):
                    status = "fallback"
                    shifted = base.values.copy()
                    detail = f"ncc_not_confident;corr={best_corr:.4f};gain={corr_gain:.4f}"
                else:
                    status = "ok"
                    ramp = 1.0 - np.exp(-np.arange(len(eval_idx), dtype=float) / max(30.0, 0.10 * len(eval_idx)))
                    shifted = base.values + np.clip(args.ncc_alpha * eval_shift * ramp, -args.max_move, args.max_move)
                    detail = f"eval_shift={eval_shift:.3f};corr={best_corr:.4f};gain={corr_gain:.4f}"
                candidates.append(
                    PathCandidate(
                        f"ncc_shift__{base.method}",
                        shifted,
                        status=status,
                        detail=detail,
                        diagnostics={
                            "prefix_ncc_shift": ncc_prefix_shift,
                            "prefix_ncc_score": ncc_prefix_score,
                            "prefix_ncc_gain": ncc_prefix_gain,
                            "eval_ncc_shift": eval_shift,
                            "eval_ncc_zero": zero_corr,
                            "eval_ncc_best": best_corr,
                            "eval_ncc_gain": corr_gain,
                        },
                    )
                )

    return candidates


def method_diagnostics(candidates: list[PathCandidate], true: np.ndarray) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        values = np.asarray(candidate.values, dtype=float)
        diff = values - true
        finite = np.isfinite(diff)
        rows.append(
            {
                "method": candidate.method,
                "status": candidate.status,
                "detail": candidate.detail,
                "eval_rows": int(finite.sum()),
                "rmse": rmse(values, true),
                "mae": float(np.mean(np.abs(diff[finite]))) if int(finite.sum()) else float("nan"),
                "bias": float(np.mean(diff[finite])) if int(finite.sum()) else float("nan"),
                "sse": float(np.sum(diff[finite] * diff[finite])) if int(finite.sum()) else float("nan"),
                "pred_std": float(np.nanstd(values)) if len(values) else float("nan"),
                **(candidate.diagnostics or {}),
            }
        )
    return rows


def is_guarded_candidate(method: str, allow_gr_shift: bool) -> bool:
    if method == "last_value":
        return True
    if method.startswith("gr_shift__") and not allow_gr_shift:
        return False
    if method in {"damped_tail_linear_md", "gr_shift__damped_tail_linear_md", "piecewise_tail_slope_md"}:
        return False
    if method.startswith("ncc_shift__"):
        return False
    if method == "damped_tail_linear_Z" or method in {"recent_plateau_quantile", "self_corr_prefix_shape"}:
        return True
    return False


def select_router_method(
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    prefix_idx: np.ndarray,
    true_tvt: np.ndarray,
    args: argparse.Namespace,
) -> dict[str, object]:
    holdout_cut = prefix_holdout_cut(prefix_idx, args)
    if holdout_cut is None:
        return {
            "router_method": "last_value",
            "router_status": "fallback",
            "router_detail": "short_prefix_for_holdout",
            "holdout_cut_idx": math.nan,
            "holdout_best_rmse": math.nan,
            "holdout_baseline_rmse": math.nan,
            "holdout_margin_rmse": math.nan,
            "holdout_improvement_rmse": math.nan,
            "guarded_method": "last_value",
            "guarded_status": "fallback",
            "guarded_detail": "short_prefix_for_holdout",
            "holdout_top2_methods": "",
        }

    train_idx = np.arange(0, holdout_cut, dtype=int)
    holdout_idx = np.arange(holdout_cut, int(prefix_idx[-1]) + 1, dtype=int)
    holdout_true = true_tvt[holdout_idx]
    holdout_candidates = candidate_paths(hw, tw, train_idx, holdout_idx, true_tvt, args)
    rows = method_diagnostics(holdout_candidates, holdout_true)
    valid = [row for row in rows if np.isfinite(float(row["rmse"]))]
    if not valid:
        return {
            "router_method": "last_value",
            "router_status": "fallback",
            "router_detail": "no_valid_holdout_candidate",
            "holdout_cut_idx": holdout_cut,
            "holdout_best_rmse": math.nan,
            "holdout_baseline_rmse": math.nan,
            "holdout_margin_rmse": math.nan,
            "holdout_improvement_rmse": math.nan,
            "guarded_method": "last_value",
            "guarded_status": "fallback",
            "guarded_detail": "no_valid_holdout_candidate",
            "holdout_top2_methods": "",
        }

    valid = sorted(valid, key=lambda row: (float(row["rmse"]), str(row["method"])))
    best = valid[0]
    baseline_rows = [row for row in valid if row["method"] == "last_value"]
    baseline_rmse = float(baseline_rows[0]["rmse"]) if baseline_rows else float("nan")
    second_rmse = float(valid[1]["rmse"]) if len(valid) > 1 else float("nan")
    margin = second_rmse - float(best["rmse"]) if np.isfinite(second_rmse) else float("nan")
    improvement = baseline_rmse - float(best["rmse"]) if np.isfinite(baseline_rmse) else float("nan")
    top2 = ";".join(str(row["method"]) for row in valid[:2])
    guarded_method = "last_value"
    guarded_status = "fallback"
    guarded_detail = "default_last_value"
    if str(best["method"]) == "last_value":
        guarded_status = "ok"
        guarded_detail = "holdout_selected_last_value"
    else:
        blocked_reasons = []
        for candidate in valid:
            candidate_method = str(candidate["method"])
            if candidate_method == "last_value":
                continue
            candidate_rmse = float(candidate["rmse"])
            candidate_improvement = baseline_rmse - candidate_rmse if np.isfinite(baseline_rmse) else float("nan")
            candidate_improvement_frac = (
                candidate_improvement / (abs(baseline_rmse) + 1e-6) if np.isfinite(candidate_improvement) else float("nan")
            )
            passes_improvement = (
                np.isfinite(candidate_improvement)
                and np.isfinite(candidate_improvement_frac)
                and candidate_improvement >= args.router_min_improvement_rmse
                and candidate_improvement_frac >= args.router_min_improvement_frac
            )
            passes_margin = np.isfinite(candidate_improvement) and candidate_improvement >= args.router_min_margin_rmse
            passes_family = is_guarded_candidate(candidate_method, args.router_allow_gr_shift)
            if passes_improvement and passes_margin and passes_family:
                guarded_method = candidate_method
                guarded_status = "ok"
                guarded_detail = (
                    f"passed_guarded_holdout_gate;ranked_candidate={candidate_method};"
                    f"improvement={candidate_improvement:.4f}"
                )
                break
            blocked_reasons.append(
                f"{candidate_method}:improvement={candidate_improvement:.4f},family_ok={passes_family}"
            )
        if guarded_method == "last_value":
            guarded_detail = "blocked_guard;" + ";".join(blocked_reasons[:3])
    return {
        "router_method": str(best["method"]),
        "router_status": "ok",
        "router_detail": "selected_by_prefix_holdout_rmse",
        "holdout_cut_idx": holdout_cut,
        "holdout_best_rmse": float(best["rmse"]),
        "holdout_baseline_rmse": baseline_rmse,
        "holdout_margin_rmse": margin,
        "holdout_improvement_rmse": improvement,
        "guarded_method": guarded_method,
        "guarded_status": guarded_status,
        "guarded_detail": guarded_detail,
        "holdout_top2_methods": top2,
    }


def select_confidence_guarded_method(candidates: list[PathCandidate], guarded_method: str, args: argparse.Namespace) -> tuple[str, str]:
    if guarded_method != "last_value":
        return guarded_method, "kept_prefix_holdout_guard"
    self_corr_candidates = [
        candidate
        for candidate in candidates
        if candidate.method == "self_corr_prefix_shape"
        and candidate.status == "ok"
        and candidate.diagnostics
        and float(candidate.diagnostics.get("self_corr", float("nan"))) >= args.router_self_corr_min_corr
    ]
    if self_corr_candidates:
        best = max(self_corr_candidates, key=lambda candidate: float(candidate.diagnostics.get("self_corr", float("nan"))))
        corr = float(best.diagnostics.get("self_corr", float("nan"))) if best.diagnostics else float("nan")
        return best.method, f"self_corr_confidence_gate;corr={corr:.4f}"
    return guarded_method, "default_last_value_after_confidence_gate"


def run_split(
    well: str,
    split_name: str,
    cut_idx: int,
    hw: pd.DataFrame,
    tw: pd.DataFrame,
    args: argparse.Namespace,
) -> tuple[list[dict[str, object]], dict[str, object] | None]:
    true_tvt = pd.to_numeric(hw["TVT"], errors="coerce").to_numpy(float)
    n = len(hw)
    if cut_idx < args.min_prefix_rows or n - cut_idx < args.min_eval_rows:
        return [], None

    prefix_idx = np.arange(0, cut_idx, dtype=int)
    eval_idx = np.arange(cut_idx, n, dtype=int)
    eval_true = true_tvt[eval_idx]
    candidates = candidate_paths(hw, tw, prefix_idx, eval_idx, true_tvt, args)
    if not candidates:
        return [], None

    router = select_router_method(hw, tw, prefix_idx, true_tvt, args)
    method_to_values = {candidate.method: candidate.values for candidate in candidates}
    chosen_method = str(router["router_method"])
    if chosen_method not in method_to_values:
        chosen_method = "last_value"
    chosen_values = method_to_values.get(chosen_method, candidates[0].values)
    candidates.append(PathCandidate("router_prefix_holdout_best", chosen_values, detail=f"selected={chosen_method}"))
    guarded_method = str(router.get("guarded_method", "last_value"))
    if guarded_method not in method_to_values:
        guarded_method = "last_value"
    guarded_values = method_to_values.get(guarded_method, candidates[0].values)
    candidates.append(PathCandidate("router_guarded_prefix_holdout", guarded_values, detail=f"selected={guarded_method}"))
    confidence_method, confidence_detail = select_confidence_guarded_method(candidates, guarded_method, args)
    if confidence_method not in method_to_values:
        confidence_method = guarded_method if guarded_method in method_to_values else "last_value"
    confidence_values = method_to_values.get(confidence_method, candidates[0].values)
    candidates.append(PathCandidate("router_confidence_guarded", confidence_values, detail=f"selected={confidence_method};{confidence_detail}"))

    rows = []
    for row in method_diagnostics(candidates, eval_true):
        rows.append(
            {
                "well": well,
                "split": split_name,
                "cut_idx": cut_idx,
                "prefix_rows": len(prefix_idx),
                **row,
            }
        )

    decision = {
        "well": well,
        "split": split_name,
        "cut_idx": cut_idx,
        "prefix_rows": len(prefix_idx),
        "eval_rows": len(eval_idx),
        "selected_eval_method": chosen_method,
        "guarded_eval_method": guarded_method,
        "confidence_eval_method": confidence_method,
        "confidence_detail": confidence_detail,
        **router,
    }
    return rows, decision


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
        rows.append(
            {
                "method": method,
                "splits": int(len(valid)),
                "eval_rows": int(valid["eval_rows"].sum()),
                "weighted_rmse": float(np.sqrt(valid["sse"].sum() / valid["eval_rows"].sum())),
                "mean_rmse": float(valid["rmse"].mean()),
                "median_rmse": float(valid["rmse"].median()),
                "mean_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].mean()),
                "median_delta_rmse_vs_baseline": float(valid["delta_rmse_vs_baseline"].median()),
                "win_rate_vs_baseline": float((valid["delta_rmse_vs_baseline"] < 0).mean()),
                "fallback_rate": float((valid["status"] != "ok").mean()) if "status" in valid.columns else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["weighted_rmse", "method"])


def write_report(scores: pd.DataFrame, summary: pd.DataFrame, decisions: pd.DataFrame, output: Path, baseline: str) -> None:
    best = summary.head(16).copy()
    router_rows = summary[summary["method"].astype(str).str.contains("router", regex=False, na=False)].copy()
    decision_counts = (
        decisions["selected_eval_method"].value_counts().rename_axis("selected_eval_method").reset_index(name="count")
        if not decisions.empty and "selected_eval_method" in decisions.columns
        else pd.DataFrame()
    )
    guarded_counts = (
        decisions["guarded_eval_method"].value_counts().rename_axis("guarded_eval_method").reset_index(name="count")
        if not decisions.empty and "guarded_eval_method" in decisions.columns
        else pd.DataFrame()
    )
    confidence_counts = (
        decisions["confidence_eval_method"].value_counts().rename_axis("confidence_eval_method").reset_index(name="count")
        if not decisions.empty and "confidence_eval_method" in decisions.columns
        else pd.DataFrame()
    )
    worst_router = scores[scores["method"] == "router_confidence_guarded"].sort_values("rmse", ascending=False).head(10)
    lines = [
        "# Multi-Hypothesis Router CV Report",
        "",
        "This report evaluates a first candidate-path matrix and prefix-holdout router on train pseudo-hidden splits.",
        "It is a diagnostic harness, not an official submission package.",
        "",
        f"Baseline comparator: `{baseline}`",
        "",
        "## Method Summary",
        "",
        markdown_table(best),
        "",
        "## Router Summary",
        "",
        markdown_table(router_rows),
        "",
        "## Router Selection Counts",
        "",
        markdown_table(decision_counts),
        "",
        "## Guarded Router Selection Counts",
        "",
        markdown_table(guarded_counts),
        "",
        "## Confidence Router Selection Counts",
        "",
        markdown_table(confidence_counts),
        "",
        "## Worst Router Splits",
        "",
        markdown_table(
            worst_router[
                [
                    "well",
                    "split",
                    "cut_idx",
                    "prefix_rows",
                    "eval_rows",
                    "rmse",
                    "baseline_rmse",
                    "delta_rmse_vs_baseline",
                    "detail",
                ]
            ]
            if not worst_router.empty
            else pd.DataFrame()
        ),
        "",
        "## Interpretation",
        "",
        "- `router_prefix_holdout_best` chooses a candidate family using only a holdout from the known prefix.",
        "- `router_guarded_prefix_holdout` falls back to `last_value` unless holdout improvement, margin, and family safety gates pass.",
        "- `router_confidence_guarded` starts from the guarded router, then allows high-confidence self-correlation evidence visible in the evaluation GR.",
        "- Piecewise slope and recent fault-step candidates are lightweight dynamic-dip probes; they are diagnostic unless the guarded router selects them without worsening worst-split risk.",
        "- A useful router should improve weighted RMSE or at least reduce worst-split risk versus `last_value`.",
        "- If the router underperforms, inspect `experiments/multi_hypothesis_router_cv_decisions.csv` to see which candidate families the prefix holdout over-selected.",
        "",
        "## Outputs",
        "",
        "- `experiments/multi_hypothesis_router_cv_scores.csv`",
        "- `experiments/multi_hypothesis_router_cv_summary.csv`",
        "- `experiments/multi_hypothesis_router_cv_decisions.csv`",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_cut_fracs(values: list[str]) -> list[float]:
    out: list[float] = []
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
    parser.add_argument("--self-corr-stride", type=int, default=16)
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
    parser.add_argument("--baseline-method", default="last_value")
    args = parser.parse_args()

    train_dir = args.data_dir / "train"
    if not train_dir.is_dir():
        raise FileNotFoundError(f"missing train directory: {train_dir}")

    cut_fracs = parse_cut_fracs(args.cut_fracs)
    score_rows: list[dict[str, object]] = []
    decision_rows: list[dict[str, object]] = []
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
            rows, decision = run_split(well, split_name, cut_idx, hw, tw, args)
            score_rows.extend(rows)
            if decision is not None:
                decision_rows.append(decision)

    scores = pd.DataFrame(score_rows)
    decisions = pd.DataFrame(decision_rows)
    if scores.empty:
        raise RuntimeError("no router CV rows generated")
    summary = summarize(scores, args.baseline_method)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scores_path = args.output_dir / "multi_hypothesis_router_cv_scores.csv"
    summary_path = args.output_dir / "multi_hypothesis_router_cv_summary.csv"
    decisions_path = args.output_dir / "multi_hypothesis_router_cv_decisions.csv"
    scores.to_csv(scores_path, index=False)
    summary.to_csv(summary_path, index=False)
    decisions.to_csv(decisions_path, index=False)
    write_report(scores, summary, decisions, args.report, args.baseline_method)

    print(f"wrote {scores_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {decisions_path}")
    print(f"wrote {args.report}")
    print(summary.head(16).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
