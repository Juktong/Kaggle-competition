"""Infrastructure B: re-audit every candidate with the corrected 3-well gate."""
import sys, numpy as np
sys.path.insert(0,'/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue/scripts')
from eval_three_well_gate import three_well_gate
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/aligned_preds.npz',allow_pickle=True)
base=z['s_54844628']; truth=z['truth']; well=z['well']
rmse=lambda p:float(np.sqrt(np.mean((np.asarray(p,float)-truth.astype(float))**2)))
CANDS=['s_54878409','s_a20_w25','s_k96_aniso','base_k96','topk96_l75','dwt','pf','base']
print(f"baseline s_54844628 OOF={rmse(base):.4f}  (public 7.891)\n")
print(f"{'candidate':14s} {'OOF':>8} {'oofGain':>8} | {'ref760_5th':>10} | {'3w_5th':>8} {'3w_25th':>8} {'3w_50th':>8} {'P>0':>6} | {'gate':>10}")
rows=[]
for c in CANDS:
    r=three_well_gate(z[c],base,truth,well,nboot=20000)
    verdict='PASS' if r['gate_pass'] else ('COND' if r['gate_conditional'] else 'FAIL')
    p=r['boot3_pct']
    print(f"{c:14s} {rmse(z[c]):>8.4f} {r['all_gain']:>+8.4f} | {r['ref760_5th']:>+10.4f} | "
          f"{p[5]:>+8.3f} {p[25]:>+8.3f} {p[50]:>+8.3f} {100*r['boot3_prob_pos']:>5.0f}% | {verdict:>10}")
    rows.append((c,rmse(z[c]),r))
print("\nnote: dwt/pf/base are worse than baseline in OOF so they are trivial fails, shown for scale.")
print("residual-correction / router / L3-ungated were all OOF-negative vs baseline in prior rounds,")
print("so they fail the corrected gate a fortiori and are not re-run here.")
