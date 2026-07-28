"""N1 — geometry-bounded monotonic alignment: a per-transition admissible band on the G3.2 DP.

G3.2 (`reports/g32_learned_alignment_smoke_2026-07-28.md`) produced the alignment line's first positive
result: learned scorer AUC 0.7242 vs NCC 0.5010, and its beam DP beat the flat anchor (12.527 vs 13.103
at lam=60). It stayed ~42% above the deployed ~8.86, so the formulation needs a constraint.

THE CONSTRAINT IS NOT A HYPER-PARAMETER. TVT is a stratigraphic thickness, so along a known path

    dTVT = -dZ + tan(delta) * dH

with dZ and dH known EXACTLY at every row from X/Y/Z (test-available) and delta the local apparent dip.
Between two consecutive evaluated rows this gives a hard admissible interval for the state change:

    t - s  in  [ (-dZ - tan(dmax)*dH)/STEP , (-dZ + tan(dmax)*dH)/STEP ]

Two distinct things follow, and this script separates them instead of lumping them together:

  CENTRING.  G3.2's regulariser is lam*|t - s|, which pulls toward NO TVT change. That prior is
             geometrically wrong whenever the well changes TVD: if the wellbore climbs or drops, TVT
             MUST change. The geometric centre of the transition is c = -dZ/STEP, so the correctly
             referenced regulariser is lam*|t - s - c| -- it penalises DIP, not TVT movement.
  BOUNDING.  The hard interval above, which forbids implausible dip.

Arms: `unbounded` (exact G3.2 behaviour, the control), `centred` (centring only, no hard bound), and
`bounded(dmax)` (centring + hard bound) over a dip sweep.

The emission matrix C[row, state] does not depend on the band, so it is computed once per well and
reused across all arms -- the arms differ ONLY in the transition rule.

Measured local dip (10-row step, 80 train wells, truth): |dip| p50 1.97 deg, p90 3.59, p95 5.43,
p99 27.05. A 4 deg band admits 92.1% of true transitions, 8 deg admits 96.4%.

Env: MAXW_TRAIN, MAXW_EVAL, EPOCHS, LAM, DMAXES.
"""
import os
import glob
from collections import defaultdict  # noqa: F401

import numpy as np
import pandas as pd

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MAXW_TRAIN = int(os.environ.get('MAXW_TRAIN', '60'))
MAXW_EVAL = int(os.environ.get('MAXW_EVAL', '12'))
EPOCHS = int(os.environ.get('EPOCHS', '8'))
LAM = float(os.environ.get('LAM', '60'))
DMAXES = [float(x) for x in os.environ.get('DMAXES', '1,2,4,8,16').split(',')]
LAMS = [float(x) for x in os.environ.get('LAMS', '20,60,150').split(',')]
STEP = 1.0
HW = 16
TWH = 8
BAND = 60          # symmetric search half-width for the unconstrained arms
K = 6
SUB = 10

np.random.seed(11)


def load(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv',
                     usecols=['MD', 'X', 'Y', 'Z', 'GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR']).sort_values('TVT')
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tv = tw['TVT'].values.astype(float)
    tg = tw['GR'].fillna(tw['GR'].mean()).values.astype(float)
    grid = np.arange(np.nanmin(tv), np.nanmax(tv), STEP)
    prof = np.interp(grid, tv, tg)
    return hw, gr, grid, prof


def hfeat(gr, i):
    a, b = max(0, i - HW), min(len(gr), i + HW + 1)
    w = gr[a:b]
    return np.array([w.mean(), w.std(), gr[i], w.max() - w.min(),
                     (w[len(w) // 2:].mean() - w[:len(w) // 2].mean())], float)


def tfeat(prof, s):
    a, b = max(0, s - TWH), min(len(prof), s + TWH + 1)
    w = prof[a:b]
    if len(w) < 3:
        w = prof[max(0, s - 1):s + 2]
    g = np.gradient(w) if len(w) > 2 else np.zeros(len(w))
    return np.array([w.mean(), w.std(), prof[min(s, len(prof) - 1)], w.max() - w.min(), g.mean()], float)


def pairfeat(fh, ft):
    d = fh - ft
    return np.concatenate([fh, ft, d, [abs(d[0]), abs(d[2])]])


# ---------------- training (identical design to G3.2) ----------------
wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng = np.random.RandomState(11)
rng.shuffle(wids)
train_w, eval_w = wids[:MAXW_TRAIN], wids[MAXW_TRAIN:MAXW_TRAIN + MAXW_EVAL]

X, Y = [], []
for wid in train_w:
    try:
        hw, gr, grid, prof = load(wid)
    except Exception:
        continue
    tvt = hw['TVT'].values.astype(float)
    n = len(gr)
    for i in np.arange(HW, n - HW, max(1, (n - 2 * HW) // 40)):
        if not np.isfinite(tvt[i]):
            continue
        s_true = int((tvt[i] - grid[0]) / STEP)
        if s_true < TWH or s_true >= len(grid) - TWH:
            continue
        fh = hfeat(gr, i)
        s_neg = s_true + int(np.random.choice([-1, 1]) * np.random.randint(8, 60))
        if s_neg < TWH or s_neg >= len(grid) - TWH:
            continue
        for s, y in ((s_true, 1.0), (s_neg, 0.0)):
            X.append(pairfeat(fh, tfeat(prof, s)))
            Y.append(y)
X = np.array(X, np.float32)
Y = np.array(Y, np.float32)
mu, sd = X.mean(0), X.std(0) + 1e-6
Xn = (X - mu) / sd
perm = np.random.RandomState(0).permutation(len(Y))
tr, va = perm[:int(0.8 * len(Y))], perm[int(0.8 * len(Y)):]

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

torch.manual_seed(0)
torch.set_num_threads(2)
model = nn.Sequential(nn.Linear(X.shape[1], 64), nn.ReLU(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
opt = torch.optim.Adam(model.parameters(), 1e-3)
lossf = nn.BCEWithLogitsLoss()
Xt, Yt = torch.tensor(Xn), torch.tensor(Y)
print(f'pairs={len(Y)}  train_wells={len(train_w)}  eval_wells={len(eval_w)}', flush=True)
for ep in range(EPOCHS):
    model.train()
    p = torch.randperm(len(tr))
    for k in range(0, len(tr), 512):
        b = torch.tensor(tr)[p[k:k + 512]]
        opt.zero_grad()
        loss = lossf(model(Xt[b]).squeeze(-1), Yt[b])
        loss.backward()
        opt.step()
model.eval()
with torch.no_grad():
    auc = roc_auc_score(Y[va], model(Xt[torch.tensor(va)]).squeeze(-1).numpy())
print(f'scorer val AUC = {auc:.4f}   (G3.2 recorded 0.7242)', flush=True)


# ---------------- per-well preparation: emission + geometry (band-independent) ----------------
def prep(wid):
    hw, gr, grid, prof = load(wid)
    kn = hw['TVT_input'].notna().values
    if kn.sum() < 100 or (~kn).sum() < 200:
        return None
    toe = np.where(~kn)[0][::SUB]
    if len(toe) < 20:
        return None
    tru = hw['TVT'].values.astype(float)[toe]
    anchor = float(hw['TVT_input'].values[kn][-1])
    a_row = int(np.where(kn)[0][-1])
    S = len(grid)
    TF = np.stack([tfeat(prof, s) for s in range(S)])
    C = np.empty((len(toe), S), float)
    with torch.no_grad():
        for j, i in enumerate(toe):
            fh = hfeat(gr, i)
            F = np.concatenate([np.repeat(fh[None], S, 0), TF, fh[None] - TF,
                                np.abs(fh[0] - TF[:, 0])[:, None],
                                np.abs(fh[2] - TF[:, 2])[:, None]], 1)
            sc = model(torch.tensor(((F - mu) / sd).astype(np.float32))).squeeze(-1).numpy()
            c = -sc
            C[j] = (c - c.mean()) / (c.std() + 1e-9)
    # geometry of each transition: previous evaluated row -> this evaluated row
    x, y, z = (hw[c].values.astype(float) for c in ['X', 'Y', 'Z'])
    rows = np.concatenate([[a_row], toe])
    dz = np.diff(z[rows])
    dh = np.hypot(np.diff(x[rows]), np.diff(y[rows]))
    return dict(wid=wid, grid=grid, C=C, tru=tru, anchor=anchor, S=S,
                centre=-dz / STEP, dh=dh)


def run_dp(P, mode, dmax=None, lam=LAM):
    """mode: 'unbounded' (G3.2), 'centred' (geometric centre, no hard bound), 'bounded' (both)."""
    C, S, grid = P['C'], P['S'], P['grid']
    s0 = int(np.clip((P['anchor'] - grid[0]) / STEP, 0, S - 1))
    beams = [([s0], 0.0)]
    clipped = 0
    total = 0
    for j in range(len(C)):
        c_j = P['centre'][j] if mode != 'unbounded' else 0.0
        h_j = np.tan(np.radians(dmax)) * P['dh'][j] / STEP if mode == 'bounded' else None
        cand = []
        for path, cost in beams:
            s = path[-1]
            if mode == 'bounded':
                lo = int(np.floor(s + c_j - h_j))
                hi = int(np.ceil(s + c_j + h_j)) + 1
                if hi - lo < 1:
                    hi = lo + 1
                lo, hi = max(0, lo), min(S, hi)
                if hi <= lo:
                    lo, hi = max(0, min(S - 1, int(round(s + c_j)))), min(S, max(1, int(round(s + c_j)) + 1))
            else:
                lo, hi = max(0, s - BAND), min(S, s + BAND + 1)
            states = np.arange(lo, hi)
            # penalty scale is IDENTICAL in every arm (always /BAND) so the band is the only change;
            # normalising by the band width would silently make a narrow band 60x more regularised.
            step = C[j, lo:hi] + lam * np.abs(states - s - c_j) / BAND
            # binding = does the hard bound exclude the state the EMISSION alone would pick?
            ulo, uhi = max(0, s - BAND), min(S, s + BAND + 1)
            ubest = ulo + int(np.argmin(C[j, ulo:uhi]))
            total += 1
            if mode == 'bounded' and not (lo <= ubest < hi):
                clipped += 1
            for t in np.argsort(step)[:K]:
                cand.append((path + [int(states[t])], cost + float(step[t])))
        cand.sort(key=lambda v: v[1])
        seen, beams = set(), []
        for p_, c_ in cand:
            if p_[-1] in seen:
                continue
            seen.add(p_[-1])
            beams.append((p_, c_))
            if len(beams) >= K:
                break
    top1 = grid[np.clip(np.array(beams[0][0][1:]), 0, S - 1)]
    return (float(np.sqrt(np.mean((top1 - P['tru']) ** 2))),
            float(np.sqrt(np.mean((P['anchor'] - P['tru']) ** 2))),
            clipped / max(total, 1))


def main():
    P = [p for p in (prep(w) for w in eval_w) if p is not None]
    print(f'\nprepared {len(P)} eval wells (emission computed once, reused by every arm)', flush=True)
    # Each arm is swept over lam and judged at ITS OWN optimum: centring changes what the penalty
    # means, so holding lam at the unbounded arm's optimum would handicap the new arms.
    print(f'\n=== transition-rule x lam sweep (same scorer, same emission, same penalty scale) ===')
    print('%-22s %s %12s %12s' % ('arm', ''.join('%10s' % f'lam={l:g}' for l in LAMS),
                                  'best', 'band binding'))
    rows = []
    for mode, dmax in [('unbounded', None), ('centred', None)] + [('bounded', d) for d in DMAXES]:
        name = mode if dmax is None else f'bounded {dmax:g} deg'
        per_lam, cl, fl = [], 0.0, 0.0
        for l in LAMS:
            rs = [run_dp(p, mode, dmax, lam=l) for p in P]
            per_lam.append(np.sqrt(np.mean([r[0] ** 2 for r in rs])))
            fl = np.sqrt(np.mean([r[1] ** 2 for r in rs]))
            cl = float(np.mean([r[2] for r in rs]))
        dp = float(min(per_lam))
        rows.append((name, dp, fl, cl))
        print('%-22s %s %12.3f %11.1f%%'
              % (name, ''.join('%10.3f' % v for v in per_lam), dp, 100 * cl), flush=True)
    print('flat-anchor on these wells: %.3f' % fl)

    # ---- NESTED validation. The table above SELECTS (arm, lam) on the same wells it reports, which is
    # a sweep, not a validation (project rule: nest the choice of every hyper-parameter). Here the
    # config is chosen on one half of the eval wells and scored on the disjoint other half, both ways.
    print('\n=== NESTED 2-fold: config chosen on one half, scored on the disjoint half ===')
    CONFIGS = [('unbounded', None), ('centred', None)] + [('bounded', d) for d in DMAXES]
    per_well = {}
    for mode, dmax in CONFIGS:
        for l in LAMS:
            per_well[(mode, dmax, l)] = np.array([run_dp(p, mode, dmax, lam=l)[0] for p in P])
    flat_pw = np.array([run_dp(P[0], 'unbounded', None, lam=LAMS[0])[1]] * 0)  # placeholder
    flat_pw = np.array([p_['flat'] for p_ in [dict(flat=np.sqrt(np.mean((pp['anchor'] - pp['tru']) ** 2)))
                                              for pp in P]])
    n = len(P)
    idx = np.arange(n)
    folds = [(idx[: n // 2], idx[n // 2:]), (idx[n // 2:], idx[: n // 2])]
    held, held_flat, picks = [], [], []
    for sel, rep in folds:
        best = min(per_well, key=lambda k: np.sqrt(np.mean(per_well[k][sel] ** 2)))
        picks.append((best, float(np.sqrt(np.mean(per_well[best][sel] ** 2)))))
        held.append(per_well[best][rep])
        held_flat.append(flat_pw[rep])
        nm = best[0] if best[1] is None else f'{best[0]} {best[1]:g}deg'
        print('  select on %2d wells -> %-16s lam=%-5g  |  held-out %2d wells: DP %7.3f  flat %7.3f'
              % (len(sel), nm, best[2], len(rep),
                 np.sqrt(np.mean(per_well[best][rep] ** 2)), np.sqrt(np.mean(flat_pw[rep] ** 2))))
    hd = np.sqrt(np.mean(np.concatenate(held) ** 2))
    hf = np.sqrt(np.mean(np.concatenate(held_flat) ** 2))
    print('  POOLED HELD-OUT: DP %.3f   flat-anchor %.3f   %s'
          % (hd, hf, 'beats flat' if hd < hf else 'does NOT beat flat'))
    print('  (the selected-on-all-wells minimum above is optimistic by construction)')
    # per-well spread of the held-out result
    allh = np.concatenate(held); allf = np.concatenate(held_flat)
    print('  per-well: DP beats flat on %.1f%% of held-out wells (n=%d)'
          % (100 * np.mean(allh < allf), len(allh)))
    print('\nG3.2 reference at lam=60: DP 12.527, flat-anchor 13.103. Deployed honest line ~8.86.')
    best = min(rows, key=lambda r: r[1])
    print(f'best arm: {best[0]} = {best[1]:.3f}')
    return rows


if __name__ == '__main__':
    main()
