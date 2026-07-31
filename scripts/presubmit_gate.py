"""Pre-submit gate — one command that runs every local check before a Kaggle submission and writes a
reproducible audit record (JSON + markdown).

Wraps the V5 visible-well audit (`visible_well_audit.py`) and adds an explicit PASS/FAIL decision plus
a written record so every submission is reproducible and auditable.

Checks (HARD = must pass to submit):
  HARD  format   : columns id,tvt; row SET matches sample_submission.
  HARD  finite   : all tvt finite.
  SOFT  range    : tvt within a sane band derived from visible-well truth.
  SOFT  diff-DWT : rmse / max|Δ| / %rows changed vs a DWT baseline (localized-diff sanity).
  INFO  visible  : per-well + pooled RMSE on the 3 visible wells vs train truth (the only real-test
                   local signal). For an honest candidate this should be ~DWT-level; for a guarded
                   overlap candidate (B4′) it should be ~0 on the visible duplicates.

Usage:
  python3 scripts/presubmit_gate.py --candidate sub.csv [--baseline dwt.csv] \
      --name "B4' guarded" --out-dir experiments/presubmit

Exit 0 iff HARD checks pass. Writes <out-dir>/<name>_presubmit.json and .md.
"""
import argparse, json, os, sys, datetime
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visible_well_audit import audit  # noqa: E402


def run_gate(candidate, baseline=None, name="candidate", out_dir="experiments/presubmit",
             train_dir=None, sample=None, ts=None):
    kw = {}
    if train_dir:
        kw["train_dir"] = train_dir
    if sample:
        kw["sample"] = sample
    rep = audit(candidate, baseline=baseline, verbose=True, **kw)

    # decision logic
    hard_ok = rep["hard_ok"]
    warns = list(rep["warnings"])
    vis = rep["checks"].get("visible_rmse", {}).get("pooled")
    decision = "PASS" if hard_ok else "FAIL"

    record = {
        "name": name,
        "timestamp": ts or "unset",  # pass ts in from caller; Date.now unavailable in some envs
        "candidate": os.path.abspath(candidate),
        "baseline": os.path.abspath(baseline) if baseline else None,
        "decision": decision,
        "hard_ok": hard_ok,
        "visible_pooled_rmse": vis,
        "warnings": warns,
        "checks": rep["checks"],
    }
    os.makedirs(out_dir, exist_ok=True)
    slug = name.replace(" ", "_").replace("'", "").replace("/", "_")
    jpath = os.path.join(out_dir, f"{slug}_presubmit.json")
    mpath = os.path.join(out_dir, f"{slug}_presubmit.md")
    json.dump(record, open(jpath, "w"), indent=2)

    fmt = rep["checks"].get("format", {})
    fin = rep["checks"].get("finite", {})
    rng = rep["checks"].get("range", {})
    dvb = rep["checks"].get("diff_vs_baseline", {})
    lines = [
        f"# Pre-submit audit — {name}",
        "",
        f"- decision: **{decision}**",
        f"- candidate: `{candidate}`",
        f"- baseline: `{baseline}`" if baseline else "- baseline: (none)",
        f"- rows: {fmt.get('rows')} (sample {fmt.get('sample_rows')}), "
        f"same_set={fmt.get('same_set')}, same_order={fmt.get('same_order')}",
        f"- finite: non-finite={fin.get('n_nonfinite')}",
        f"- range: [{rng.get('min')}, {rng.get('max')}] mean={rng.get('mean')} "
        f"out-of-band={rng.get('n_out_of_band')}",
    ]
    if dvb:
        lines.append(f"- diff-vs-DWT: rmse={dvb.get('rmse'):.3f} max|Δ|={dvb.get('max_abs'):.2f} "
                     f"%changed={100*dvb.get('frac_changed', 0):.1f}")
    if vis is not None:
        lines.append(f"- visible-well pooled RMSE: **{vis:.4f}**")
        per = rep["checks"]["visible_rmse"]["per_well"]
        for w, s in per.items():
            lines.append(f"    - {w}: n={s['n']} RMSE={s['rmse']:.4f}")
    if warns:
        lines.append("- warnings:")
        lines += [f"    - {w}" for w in warns]
    open(mpath, "w").write("\n".join(lines) + "\n")
    print(f"\n[presubmit] decision={decision}  record -> {jpath} , {mpath}")
    return record


def main():
    ap = argparse.ArgumentParser(description="Pre-submit gate (V5 audit + audit record)")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--name", default="candidate")
    ap.add_argument("--out-dir", default="experiments/presubmit")
    ap.add_argument("--train-dir", default=None)
    ap.add_argument("--sample", default=None)
    ap.add_argument("--timestamp", default=None, help="ISO timestamp string (caller supplies)")
    a = ap.parse_args()
    rec = run_gate(a.candidate, baseline=a.baseline, name=a.name, out_dir=a.out_dir,
                   train_dir=a.train_dir, sample=a.sample, ts=a.timestamp)
    sys.exit(0 if rec["hard_ok"] else 1)


if __name__ == "__main__":
    main()
