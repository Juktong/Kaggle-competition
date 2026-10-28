"""Corrected 3-well-scale validation gate (reusable CLI + importable library).

The competition evaluates the WHOLE test set = 3 wells / 14,151 rows. A stability statistic computed by
resampling 760 wells (the sampling distribution of a 760-well mean) does NOT constrain the quantity that
decides the outcome. `54878409` passed a 760-well gate (5th +0.049) and lost on public; at 3-well scale
the same effect was negative in ~42% of draws. So: every submission gate must be evaluated at the number
of wells actually scored.

This tool takes any candidate + baseline per-row prediction and reports, over TRAIN wells used as the
population from which a 3-well test is drawn:
  - pooled RMSE gain vs baseline (default baseline = s_54844628, public 7.891)
  - per-well gain mean/median/std, helped/hurt fraction
  - 3-well bootstrap: 1/5/25/50/75/95 pct, P(gain>0), best/worst 3-well draw (named)
  - 760-well bootstrap (REFERENCE ONLY, not a gate)
  - the exact gain on the ACTUAL 3 test wells (000d7d20, 00bbac68, 00e12e8b) -- OOF proxy only
  - corrected-gate decision

Corrected gate (default): 3-well bootstrap 5th percentile > 0.
  If 5th <= 0 but 25th > 0: NOT auto-pass; requires a pre-public/test-available guard AND row-split
  stability (see scripts/row_split_gate.py) to be considered.

CLI:
  python3 scripts/eval_three_well_gate.py --candidate s_54878409 [--baseline s_54844628]
      [--frame .../aligned_preds.npz] [--nboot 20000] [--json out.json]
Library:
  from eval_three_well_gate import three_well_gate
  res = three_well_gate(pred_cand, pred_base, truth, well, nboot=20000)
"""
import os, json, argparse, numpy as np
from collections import defaultdict

TEST_WELLS = ['000d7d20', '00bbac68', '00e12e8b']
DEFAULT_FRAME = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/aligned_preds.npz'


def three_well_gate(pred_cand, pred_base, truth, well, nboot=20000, seed=7, ndraw=3):
    pred_cand = np.asarray(pred_cand, float); pred_base = np.asarray(pred_base, float)
    truth = np.asarray(truth, float); well = np.asarray(well).astype(str)
    uw = np.array(sorted(set(well)))
    idxw = {w: np.where(well == w)[0] for w in uw}
    # per-well squared-error sums (lets us pool any subset exactly)
    sse_c = {w: float(np.sum((pred_cand[idxw[w]] - truth[idxw[w]]) ** 2)) for w in uw}
    sse_b = {w: float(np.sum((pred_base[idxw[w]] - truth[idxw[w]]) ** 2)) for w in uw}
    n_w = {w: len(idxw[w]) for w in uw}

    def pooled_gain(ws):
        nb = sum(n_w[w] for w in ws)
        rb = np.sqrt(sum(sse_b[w] for w in ws) / nb)
        rc = np.sqrt(sum(sse_c[w] for w in ws) / nb)
        return rb - rc

    all_gain = pooled_gain(uw)
    per_well = np.array([np.sqrt(sse_b[w] / n_w[w]) - np.sqrt(sse_c[w] / n_w[w]) for w in uw])

    rng = np.random.RandomState(seed)
    draws = np.empty(nboot)
    best = (-1e9, None); worst = (1e9, None)
    for i in range(nboot):
        ws = uw[rng.randint(0, len(uw), ndraw)]
        g = pooled_gain(ws)
        draws[i] = g
        if g > best[0]: best = (g, list(ws))
        if g < worst[0]: worst = (g, list(ws))
    pct = {p: float(np.percentile(draws, p)) for p in [1, 5, 25, 50, 75, 95]}

    # 760-well reference bootstrap
    ref = np.empty(2000)
    for i in range(2000):
        ws = uw[rng.randint(0, len(uw), len(uw))]
        ref[i] = pooled_gain(ws)

    actual = [w for w in TEST_WELLS if w in idxw]
    actual_gain = pooled_gain(actual) if actual else float('nan')

    gate_pass = pct[5] > 0
    conditional = (not gate_pass) and pct[25] > 0
    return dict(
        all_gain=float(all_gain),
        per_well_mean=float(per_well.mean()), per_well_median=float(np.median(per_well)),
        per_well_std=float(per_well.std()),
        helped=float(np.mean(per_well > 1e-9)), hurt=float(np.mean(per_well < -1e-9)),
        n_wells=len(uw), ndraw=ndraw,
        boot3_pct=pct, boot3_prob_pos=float(np.mean(draws > 0)),
        boot3_best=best[1], boot3_best_gain=float(best[0]),
        boot3_worst=worst[1], boot3_worst_gain=float(worst[0]),
        ref760_mean=float(ref.mean()), ref760_5th=float(np.percentile(ref, 5)),
        ref760_prob_pos=float(np.mean(ref > 0)),
        actual_test_wells=actual, actual_test_gain=float(actual_gain),
        gate_pass=bool(gate_pass), gate_conditional=bool(conditional),
    )


def _print(name, base_name, r):
    print(f"=== 3-well gate: candidate={name}  baseline={base_name} ===")
    print(f"  pooled OOF gain (all {r['n_wells']} wells) = {r['all_gain']:+.4f}")
    print(f"  per-well gain: mean={r['per_well_mean']:+.4f} median={r['per_well_median']:+.4f} "
          f"std={r['per_well_std']:.4f} | helped={100*r['helped']:.1f}% hurt={100*r['hurt']:.1f}%")
    p = r['boot3_pct']
    print(f"  3-WELL bootstrap: 1st={p[1]:+.4f} 5th={p[5]:+.4f} 25th={p[25]:+.4f} "
          f"50th={p[50]:+.4f} 75th={p[75]:+.4f} 95th={p[95]:+.4f}")
    print(f"                    P(gain>0)={100*r['boot3_prob_pos']:.1f}%  "
          f"worst3={r['boot3_worst_gain']:+.3f} best3={r['boot3_best_gain']:+.3f}")
    print(f"  760-well ref (NOT a gate): mean={r['ref760_mean']:+.4f} 5th={r['ref760_5th']:+.4f} "
          f"P>0={100*r['ref760_prob_pos']:.1f}%")
    print(f"  actual 3 test wells {r['actual_test_wells']}: gain={r['actual_test_gain']:+.4f} (OOF proxy)")
    verdict = 'PASS (3-well 5th>0)' if r['gate_pass'] else (
        'CONDITIONAL (5th<=0 but 25th>0; needs pre-public guard + row-split stability)'
        if r['gate_conditional'] else 'FAIL (3-well 5th<=0 and 25th<=0)')
    print(f"  CORRECTED GATE: {verdict}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--baseline', default='s_54844628')
    ap.add_argument('--frame', default=DEFAULT_FRAME)
    ap.add_argument('--nboot', type=int, default=20000)
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    z = np.load(a.frame, allow_pickle=True)
    if a.candidate not in z.files:
        raise SystemExit(f"candidate '{a.candidate}' not in frame; columns: {[c for c in z.files]}")
    r = three_well_gate(z[a.candidate], z[a.baseline], z['truth'], z['well'], nboot=a.nboot)
    _print(a.candidate, a.baseline, r)
    if a.json:
        json.dump(r, open(a.json, 'w'), indent=1); print(f"  wrote {a.json}")


if __name__ == '__main__':
    main()
