"""Feasibility test for proposal L1 (heel-residual bias carry), before spending 2-4 h regenerating
DWT predictions on heel rows.

Direction 6 found the residual is a smooth per-well bias with a 500-2000 row coherence length. L1 asks:
can a bias MEASURED on rows where truth is known be carried into rows where it is not?

Direct measurement is not possible on heel rows without re-running the model: on heel rows TVT_input is
KNOWN and is an input, so a naive heel residual would be near zero and not comparable to a toe residual.
The honest cheap proxy is a WITHIN-WELL TOE SPLIT: measure the bias on the first fraction f of a well's
toe rows and carry it into the remainder. The carry strength lambda is fit NESTED by well.

This is an UPPER BOUND on L1 for two reasons, both stated in the report:
  (a) real heel rows sit further from the far toe than an early-toe segment does, and
  (b) the model's regime on heel rows differs (truth is available there as input).
If even this upper bound is small, L1 is not worth the run.
"""
import os, numpy as np
from collections import defaultdict

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
_z = np.load(os.path.join(SH, 'decomp_features.npz'), allow_pickle=True)
dc = {k: _z[k] for k in _z.files}
dw = dc['well'].astype(str)
rd = np.load(os.path.join(SH, 'struct_oof_rowdist.npz'), allow_pickle=True)
rw = rd['well'].astype(str); rs = rd['struct'].astype(np.float64)
nnb = dict(zip(rd['meta_well'].astype(str), rd['meta_nnb'].astype(int)))
cl = dict(zip(rd['meta_well'].astype(str), rd['meta_closest'].astype(float)))
di = defaultdict(list); si = defaultdict(list)
for i, w in enumerate(dw): di[w].append(i)
for i, w in enumerate(rw): si[w].append(i)

wells = []
for w in sorted(set(dw) & set(rw)):
    a = np.array(di[w]); b = np.array(si[w])
    if len(a) != len(b) or len(a) < 200: continue
    base = dc['blend'][a].astype(np.float64); truth = dc['truth'][a].astype(np.float64)
    g = (nnb.get(w, 0) >= 4) and np.isfinite(cl.get(w, np.nan)) and cl.get(w, 1e9) < 1000
    cur = 0.85 * base + 0.15 * rs[b] if g else base
    wells.append((w, cur, truth))
print(f"wells={len(wells)} rows={sum(len(c) for _,c,_ in wells)}", flush=True)
uw = np.array([w for w, _, _ in wells])

for f in [0.10, 0.20, 0.30]:
    # correlation between the early-segment bias and the later-segment bias
    eb, lb, ln = [], [], []
    for w, c, t in wells:
        k = max(10, int(len(c) * f))
        r = t - c
        eb.append(r[:k].mean()); lb.append(r[k:].mean()); ln.append(len(c) - k)
    eb = np.array(eb); lb = np.array(lb)
    corr = float(np.corrcoef(eb, lb)[0, 1])

    # nested carry: lambda fit on half the wells, applied to the other half's LATER rows only
    outs_base, outs_carry = [], []
    for seed in range(3):
        rg = np.random.RandomState(seed); sh = uw.copy(); rg.shuffle(sh)
        half = set(sh[:len(sh)//2])
        for tr_set in [half, set(uw) - half]:
            te_set = set(uw) - tr_set
            num = den = 0.0
            for (w, c, t) in wells:
                if w not in tr_set: continue
                k = max(10, int(len(c) * f)); r = t - c
                b = r[:k].mean(); num += b * r[k:].sum(); den += b * b * len(r[k:])
            lam = float(np.clip(num / max(den, 1e-9), 0, 2))
            se_b = se_c = n = 0.0
            for (w, c, t) in wells:
                if w not in te_set: continue
                k = max(10, int(len(c) * f)); r = t - c
                b = r[:k].mean()
                se_b += float(np.sum(r[k:] ** 2)); se_c += float(np.sum((r[k:] - lam * b) ** 2)); n += len(r[k:])
            outs_base.append((se_b, n)); outs_carry.append((se_c, n, lam))
    rb = np.sqrt(sum(a for a, _ in outs_base) / sum(b for _, b in outs_base))
    rc = np.sqrt(sum(a for a, _, _ in outs_carry) / sum(b for _, b, _ in outs_carry))
    lam_m = np.mean([l for _, _, l in outs_carry])
    print(f"\nf={f:.2f}  (bias measured on first {100*f:.0f}% of toe rows, carried into the rest)")
    print(f"  corr(early bias, later bias) = {corr:+.4f}")
    print(f"  nested lambda = {lam_m:.3f}")
    print(f"  later-rows RMSE: no carry {rb:.4f} -> with carry {rc:.4f}   gain {rb-rc:+.4f}", flush=True)

print("\nNOTE: this is an UPPER BOUND on L1 -- real heel rows are further from the far toe, and the")
print("      model's heel regime differs (TVT_input is known there and used as an input).")
print("GATE: if this upper bound is well under +0.10, L1 does not justify its 2-4 h run.")
