"""G2.2 — well-level selector smoke (local only, no Kaggle, no submission).

Question: can we choose, PER WELL, between the scored outputs (frontier overlap-OFF `54968060`,
frontier SP45-only `54990075`, honest `54844628`) using only test-available signals, and beat every
single output?

Honesty constraints:
  - Only 3 wells are scored, so a selector fitted on them would be fitting 3 points. We therefore
    measure the ORACLE gain first: if even a truth-selected per-well choice cannot beat the best single
    output by a useful margin, no honest selector can.
  - The evaluation target is the train-copy TVT proxy, which G1.2 showed SATURATES. So a proxy-measured
    selector gain must be treated as an upper bound, not a prediction.
  - Feature-based selection is only explored if the oracle margin is materially positive.
"""
import numpy as np, pandas as pd
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
TRAIN = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
OUTS = {
    '54968060_overlapOFF': (f'{SH}/a2full_out/submission.csv', 6.643),
    '54990075_sp45only':   (f'{SH}/sp45full_out/submission.csv', 6.690),
    '54844628_honest':     (f'{SH}/dep_out/submission.csv', 7.891),
}

truth = {}
for w in ['000d7d20', '00bbac68', '00e12e8b']:
    h = pd.read_csv(f'{TRAIN}/{w}__horizontal_well.csv')
    toe = h['TVT_input'].isna().values
    for i in np.where(toe)[0]:
        truth[f'{w}_{i}'] = h['TVT'].values[i]

pred = {}
for k, (p, _) in OUTS.items():
    s = pd.read_csv(p); pred[k] = dict(zip(s['id'], s['tvt']))
ids = [k for k in truth if all(k in pred[m] for m in pred)]
wells = sorted({k[:8] for k in ids})
byw = defaultdict(list)
for k in ids: byw[k[:8]].append(k)

def rmse(sel):
    """sel: well -> model name"""
    e = []
    for w, ks in byw.items():
        m = sel[w]
        e += [pred[m][k] - truth[k] for k in ks]
    e = np.array(e); return float(np.sqrt(np.mean(e ** 2)))

print(f"rows={len(ids)} wells={len(wells)}  (proxy = train-copy TVT; SATURATES, see G1.2)")
print("\n=== per-well proxy RMSE by model ===")
print(f"{'well':10s} " + " ".join(f"{m:22s}" for m in OUTS) + "  best")
per = {}
for w in wells:
    ks = byw[w]; row = {}
    for m in pred:
        e = np.array([pred[m][k] - truth[k] for k in ks]); row[m] = float(np.sqrt(np.mean(e ** 2)))
    per[w] = row
    best = min(row, key=row.get)
    print(f"{w:10s} " + " ".join(f"{row[m]:<22.3f}" for m in OUTS) + f"  {best}")

print("\n=== single-model pooled proxy RMSE ===")
for m in OUTS:
    print(f"  {m:22s} {rmse({w: m for w in wells}):.4f}   (public {OUTS[m][1]})")

oracle = {w: min(per[w], key=per[w].get) for w in wells}
r_or = rmse(oracle)
best_single = min(OUTS, key=lambda m: rmse({w: m for w in wells}))
r_bs = rmse({w: best_single for w in wells})
print(f"\n=== ORACLE per-well selection (upper bound) ===")
print(f"  choice: " + ", ".join(f"{w}->{oracle[w].split('_')[0]}" for w in wells))
print(f"  oracle proxy RMSE = {r_or:.4f}   best single = {r_bs:.4f} ({best_single})")
print(f"  ORACLE MARGIN = {r_bs - r_or:+.4f} ft")

print("\n=== verdict ===")
if r_bs - r_or < 0.10:
    print("  The oracle margin is small: even a truth-selected per-well choice barely beats the best")
    print("  single output, so an honest feature-based selector has almost nothing to capture.")
else:
    print("  Oracle margin is material -> a feature-based selector is worth exploring, BUT with only 3")
    print("  scored wells any fitted rule would be fitting 3 points; it would need train masked splits.")
