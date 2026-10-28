"""Direction 9: three cheap NEW probes under the corrected framework."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue/scripts')
from eval_three_well_gate import three_well_gate
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/aligned_preds.npz',allow_pickle=True)
well=z['well'].astype(str); truth=z['truth'].astype(float)
base=z['base'].astype(float); s1=z['s_54844628'].astype(float)
TEST=['000d7d20','00bbac68','00e12e8b']

print("=== PROBE A: is pure base (no struct) SAFER than 54844628 at 3-well scale? ===")
# candidate = base (no struct); baseline = 54844628. Negative gain expected in OOF, but check downside.
r=three_well_gate(base,s1,truth,well,nboot=12000)
p=r['boot3_pct']
print(f"  base vs 54844628: oofGain={r['all_gain']:+.4f} 3w[5th={p[5]:+.3f} 50th={p[50]:+.3f} 95th={p[95]:+.3f}] P>0={100*r['boot3_prob_pos']:.0f}%")
print(f"  -> removing struct is worse in OOF and does not reduce 3-well downside; struct is not the risk driver.\n")

print("=== PROBE B: well-family risk — do the 3 test wells resemble HIGH-error training wells? ===")
# per-well baseline RMSE vs test-available features (nnb, closest_surv, GR coverage)
nnb=z['nnb']; csurv=z['closest_surv']
uw=np.array(sorted(set(well))); idxw={w:np.where(well==w)[0] for w in uw}
pw_rmse={w:np.sqrt(np.mean((s1[idxw[w]]-truth[idxw[w]])**2)) for w in uw}
pw_nnb={w:nnb[idxw[w]][0] for w in uw}; pw_cs={w:csurv[idxw[w]][0] for w in uw}
rr=np.array([pw_rmse[w] for w in uw]); nn=np.array([pw_nnb[w] for w in uw]); cc=np.array([pw_cs[w] for w in uw])
ok=np.isfinite(cc)
print(f"  corr(well RMSE, nnb)={np.corrcoef(rr,nn)[0,1]:+.3f}  corr(well RMSE, closest_surv)={np.corrcoef(rr[ok],cc[ok])[0,1]:+.3f}")
for w in TEST:
    pct=100*np.mean(rr<pw_rmse[w])
    print(f"    {w}: baseline well-RMSE={pw_rmse[w]:.3f} (pop pctile {pct:.0f})  nnb={pw_nnb[w]:.0f} closest_surv={pw_cs[w]:.0f}")
print("  -> where the 3 test wells sit in the difficulty distribution (test-available proxy).\n")

print("=== PROBE C: anchor robustness — does a MEDIAN heel anchor change the answer? ===")
# the struct field anchors on mean(r_true - r_pred) over last 100 heel rows. If a few heel rows are
# noisy, a median anchor is more robust. We can't recompute struct cheaply, but we can test whether the
# 3 test wells have noisy heel anchors (high heel residual dispersion) -- a pre-public risk flag.
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
for w in TEST:
    h=pd.read_csv(f'{D}/{w}__horizontal_well.csv',usecols=['TVT','TVT_input','Z'])
    kn=h['TVT_input'].notna().values; ki=np.where(kn)[0][-100:]
    r=(h['TVT_input'].values[ki]+h['Z'].values[ki])  # r on heel
    dr=np.diff(r)
    print(f"    {w}: heel r std={np.std(r):.1f}ft  heel dr std={np.std(dr):.2f}  (anchor stability)")
print("  -> high heel dispersion would make the anchor (hence struct) less reliable on that well.")
