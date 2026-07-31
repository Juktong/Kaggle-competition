"""G3.3 — multi-hypothesis (MTP) trajectory smoke (local, no Kaggle, no submission).

Parameterisation follows the measured residual structure (2026-07-21): a well's toe residual relative to
a flat anchor is dominated by a constant offset plus a drift, with drift std 13.28 ft vs level-offset std
4.72 ft. So each hypothesis is a pair (offset, slope) describing the toe TVT trajectory relative to the
flat-anchor line; K hypotheses + K probabilities are emitted, trained with a best-of-K (MTP) loss.

The decisive question is NOT whether best-of-K beats K=1 -- an oracle always can. Under RMSE the optimal
single output is the conditional mean, which K=1 already produces. Multi-hypothesis can only pay if a
hypothesis can be SELECTED at inference. So the smoke reports three numbers side by side:
    K=1 regression | ORACLE best-of-K (upper bound) | argmax-probability selection (achievable)
plus the flat-anchor baseline and the deployed honest pipeline reference.

Inputs are test-available only: known-prefix statistics, typewell GR summary, trajectory geometry.
Env: MAXW, K, EPOCHS.
"""
import os, glob, numpy as np, pandas as pd

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
MAXW = int(os.environ.get('MAXW', '400'))
KH = int(os.environ.get('K', '5'))
EPOCHS = int(os.environ.get('EPOCHS', '60'))

rows = []
wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
rng = np.random.RandomState(13); rng.shuffle(wids)
for wid in wids[:MAXW]:
    try:
        hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['MD','Z','GR','TVT','TVT_input'])
        tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT','GR'])
    except Exception: continue
    kn = hw['TVT_input'].notna().values
    if kn.sum() < 150 or (~kn).sum() < 200: continue
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tvt = hw['TVT'].values.astype(float); md = hw['MD'].values.astype(float); z = hw['Z'].values.astype(float)
    ki = np.where(kn)[0]; ti = np.where(~kn)[0]
    anchor = float(hw['TVT_input'].values[ki][-1])
    # --- test-available features ---
    kp = hw['TVT_input'].values[ki].astype(float)
    tail = kp[-100:] if len(kp) >= 100 else kp
    pre_slope = float(np.polyfit(np.arange(len(tail)), tail, 1)[0]) if len(tail) > 5 else 0.0
    x = np.array([
        len(ki), len(ti), float(np.mean(gr[ki])), float(np.std(gr[ki])),
        float(np.mean(gr[ti])), float(np.std(gr[ti])),
        float(np.mean(gr[ti]) - np.mean(gr[ki])),                 # GR level shift heel->toe
        anchor, float(np.std(kp)), pre_slope * 100.0,
        float(md[ti].max() - md[ki].max()), float(z[ti].mean() - z[ki].mean()),
        float(np.nanmax(tw['TVT'].values) - np.nanmin(tw['TVT'].values)),
        float(np.nanmean(tw['GR'].values)), float(np.nanstd(tw['GR'].values)),
    ], float)
    # --- target: toe residual vs flat anchor, as (offset, slope-over-toe) ---
    res = tvt[ti] - anchor
    u = np.linspace(0, 1, len(res))
    b, a = np.polyfit(u, res, 1)          # res ~ a + b*u
    rows.append((wid, x, np.array([a, b]), res, anchor, tvt[ti]))
print(f"wells={len(rows)}  feat_dim={rows[0][1].shape[0]}  K={KH}", flush=True)

X = np.array([r[1] for r in rows], np.float32)
Yp = np.array([r[2] for r in rows], np.float32)          # (offset, slope)
mu, sd = X.mean(0), X.std(0) + 1e-6; Xn = ((X - mu) / sd).astype(np.float32)
ym, ys = Yp.mean(0), Yp.std(0) + 1e-6; Yn = ((Yp - ym) / ys).astype(np.float32)
perm = np.random.RandomState(0).permutation(len(rows))
ntr = int(0.75 * len(rows)); tr, va = perm[:ntr], perm[ntr:]

import torch, torch.nn as nn
torch.manual_seed(0); torch.set_num_threads(2)

class MTP(nn.Module):
    def __init__(s, d, K):
        super().__init__(); s.K = K
        s.body = nn.Sequential(nn.Linear(d, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU())
        s.head = nn.Linear(64, K * 2); s.logit = nn.Linear(64, K)
    def forward(s, x):
        h = s.body(x)
        return s.head(h).view(-1, s.K, 2), s.logit(h)

def run(K, epochs=EPOCHS):
    m = MTP(X.shape[1], K); opt = torch.optim.Adam(m.parameters(), 3e-3)
    Xt = torch.tensor(Xn); Yt = torch.tensor(Yn)
    itr = torch.tensor(tr); iva = torch.tensor(va)
    for ep in range(epochs):
        m.train(); opt.zero_grad()
        hyp, lg = m(Xt[itr])                                  # (N,K,2), (N,K)
        err = ((hyp - Yt[itr][:, None, :]) ** 2).sum(-1)      # (N,K)
        best = err.argmin(1)
        loss = err.min(1).values.mean() + 0.1 * nn.functional.cross_entropy(lg, best)
        loss.backward(); opt.step()
        if ep % 20 == 0 or ep == epochs-1:
            print(f"   K={K} ep{ep:3d}: bestK-loss={float(err.min(1).values.mean()):.4f}", flush=True)
    m.eval()
    with torch.no_grad():
        hyp, lg = m(Xt[iva])
        hyp = hyp.numpy() * ys + ym                            # (Nv,K,2) denormalised
        prob = torch.softmax(lg, 1).numpy()
    return hyp, prob

def rmse_from_params(params, idxs):
    """params: (Nv,2) offset+slope -> reconstruct toe trajectory, pooled RMSE vs truth"""
    se = 0.0; n = 0
    for j, i in enumerate(idxs):
        _, _, _, res, anchor, tru = rows[i]
        u = np.linspace(0, 1, len(res))
        pred = anchor + params[j, 0] + params[j, 1] * u
        se += float(np.sum((pred - tru) ** 2)); n += len(tru)
    return float(np.sqrt(se / n))

print("\n=== training ===", flush=True)
h1, p1 = run(1)
hK, pK = run(KH)

# K=1 regression
r_k1 = rmse_from_params(h1[:, 0, :], va)
# oracle best-of-K: pick the hypothesis closest to truth (UPPER BOUND, not achievable)
best_idx = np.zeros(len(va), int)
for j, i in enumerate(va):
    _, _, ytrue, _, _, _ = rows[i]
    best_idx[j] = int(np.argmin(((hK[j] - ytrue) ** 2).sum(-1)))
r_or = rmse_from_params(hK[np.arange(len(va)), best_idx], va)
# achievable: argmax probability
am = pK.argmax(1)
r_am = rmse_from_params(hK[np.arange(len(va)), am], va)
# probability-weighted mean (the RMSE-optimal use of a mixture)
mix = (hK * pK[:, :, None]).sum(1)
r_mix = rmse_from_params(mix, va)
# flat anchor
r_flat = rmse_from_params(np.zeros((len(va), 2)), va)

div = float(np.mean(hK[:, :, 0].std(1)))
print(f"\n=== G3.3 results ({len(va)} held-out wells, K={KH}) ===")
print(f"  hypothesis diversity: mean std of offset across K = {div:.3f} ft  (nonzero => hypotheses differ)")
print(f"  flat-anchor baseline                  RMSE = {r_flat:.3f}")
print(f"  K=1 regression                        RMSE = {r_k1:.3f}")
print(f"  K={KH} argmax-probability (ACHIEVABLE) RMSE = {r_am:.3f}")
print(f"  K={KH} probability-weighted mean       RMSE = {r_mix:.3f}")
print(f"  K={KH} ORACLE best-of-K (upper bound)  RMSE = {r_or:.3f}")
print(f"  deployed honest pipeline OOF reference      ~8.86")
print(f"\n  ORACLE MARGIN over K=1 = {r_k1 - r_or:+.3f} ft   ACHIEVABLE MARGIN = {r_k1 - r_am:+.3f} ft")
print("\nGATE: multi-hypothesis pays only if the ACHIEVABLE margin is materially positive.")
print("      A large oracle margin with ~zero achievable margin repeats the top-K / selector finding.")
