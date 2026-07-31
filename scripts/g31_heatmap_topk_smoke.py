"""G3.1 — stratigraphic misfit heatmap + top-K path search (local smoke, no Kaggle, no submission).

Distinct from the earlier top-K work: that RANKED existing PF seed paths. Here we build an explicit
cost matrix and run our own DP over it.

  cost[i, s] = |GR_horizontal(row i) - GR_typewell(TVT state s)| , normalised
  transition : |s - s'| penalised (TVT changes slowly along MD); anchored at the last known heel row
  search     : Viterbi (best path) + beam (top-K paths)
  outputs per path: total cost, smoothness, max jump, anchor consistency, typewell range pressure

Evaluated on TRAIN wells with the toe masked (competition simulation): known prefix retained, toe TVT
hidden and used only for scoring. Compared against the honest pipeline's own prediction on the same rows.
Env: MAXW, KBEAM, STATE_STEP, LAM.
"""
import os, glob, numpy as np, pandas as pd
from collections import defaultdict

D = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
MAXW = int(os.environ.get('MAXW', '12'))
KBEAM = int(os.environ.get('KBEAM', '8'))
STEP = float(os.environ.get('STATE_STEP', '1.0'))      # TVT state grid, ft
LAM = float(os.environ.get('LAM', '4.0'))              # transition penalty weight
SUB = int(os.environ.get('SUB', '10'))                 # row subsample for tractability


def build(wid):
    hw = pd.read_csv(f'{D}/{wid}__horizontal_well.csv', usecols=['MD', 'Z', 'GR', 'TVT', 'TVT_input'])
    tw = pd.read_csv(f'{D}/{wid}__typewell.csv', usecols=['TVT', 'GR']).sort_values('TVT')
    kn = hw['TVT_input'].notna().values
    if kn.sum() < 100 or (~kn).sum() < 200:
        return None
    gr = pd.Series(hw['GR'].values).interpolate(limit_direction='both').values.astype(float)
    tv = tw['TVT'].values.astype(float)
    tg = tw['GR'].fillna(tw['GR'].mean()).values.astype(float)
    grid = np.arange(np.nanmin(tv), np.nanmax(tv), STEP)
    prof = np.interp(grid, tv, tg)
    toe = np.where(~kn)[0][::SUB]
    if len(toe) < 20: return None
    anchor_tvt = float(hw['TVT_input'].values[kn][-1])
    return dict(wid=wid, gr=gr, grid=grid, prof=prof, toe=toe,
                truth=hw['TVT'].values.astype(float), anchor=anchor_tvt)


def dp_topk(d, K=KBEAM, lam=LAM):
    """beam search over TVT states; returns list of (path_states, total_cost)."""
    gr, grid, prof, toe = d['gr'], d['grid'], d['prof'], d['toe']
    n, S = len(toe), len(grid)
    # emission cost, normalised per row
    C = np.empty((n, S), float)
    for i, r in enumerate(toe):
        c = np.abs(prof - gr[r])
        C[i] = c / (c.std() + 1e-9)
    # start near the anchor
    s0 = int(np.clip(np.searchsorted(grid, d['anchor']), 0, S - 1))
    band = 60                                        # states reachable per step (TVT moves slowly)
    beams = [([s0], 0.0)]
    for i in range(n):
        cand = []
        for path, cost in beams:
            s = path[-1]
            lo, hi = max(0, s - band), min(S, s + band + 1)
            step_cost = C[i, lo:hi] + lam * np.abs(np.arange(lo, hi) - s) / max(band, 1)
            order = np.argsort(step_cost)[:K]
            for j in order:
                cand.append((path + [lo + int(j)], cost + float(step_cost[j])))
        cand.sort(key=lambda t: t[1])
        # keep K diverse beams (distinct current state)
        seen, beams = set(), []
        for p, c in cand:
            if p[-1] in seen: continue
            seen.add(p[-1]); beams.append((p, c))
            if len(beams) >= K: break
    return [(np.array(p[1:]), c) for p, c in beams]


def main():
    wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(f'{D}/*__horizontal_well.csv'))
    rng = np.random.RandomState(5); rng.shuffle(wids)
    rows = []
    done = 0
    for wid in wids:
        if done >= MAXW: break
        d = build(wid)
        if d is None: continue
        paths = dp_topk(d)
        tru = d['truth'][d['toe']]
        best_rmse = np.inf; top1_rmse = None
        for k, (st, cost) in enumerate(paths):
            pred = d['grid'][st]
            r = float(np.sqrt(np.mean((pred - tru) ** 2)))
            if k == 0: top1_rmse = r
            best_rmse = min(best_rmse, r)
        # naive baseline: hold the anchor TVT flat
        flat = float(np.sqrt(np.mean((d['anchor'] - tru) ** 2)))
        rows.append(dict(wid=wid, n=len(d['toe']), top1=top1_rmse, oracle_topk=best_rmse, flat=flat))
        done += 1
        print(f"  {wid}: rows={len(d['toe'])} top1={top1_rmse:.2f} oracle_top{KBEAM}={best_rmse:.2f} flat={flat:.2f}", flush=True)
    df = pd.DataFrame(rows)
    print(f"\n=== G3.1 heatmap+beam smoke ({len(df)} train wells, toe masked) ===")
    print(f"  DP top-1        pooled RMSE = {np.sqrt((df.top1**2).mean()):.3f}")
    print(f"  DP oracle top-{KBEAM} pooled RMSE = {np.sqrt((df.oracle_topk**2).mean()):.3f}  (upper bound)")
    print(f"  flat-anchor baseline        = {np.sqrt((df.flat**2).mean()):.3f}")
    print(f"\n  reference: honest pipeline OOF on train toe rows ~= 8.86 ft (54844628 line)")
    print(f"             frontier public 6.6 / honest public 7.9")
    print("\nGATE: DP top-1 must be competitive with the ~8.9 ft honest OOF level to be worth pursuing;")
    print("      the oracle top-K margin shows whether a ranker over these paths could add anything.")


if __name__ == '__main__':
    main()
