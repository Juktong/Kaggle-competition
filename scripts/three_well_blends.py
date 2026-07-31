"""Direction 4: conservative blends optimised for 3-well DOWNSIDE, not 760-well OOF."""
import sys, numpy as np
sys.path.insert(0,'/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue/scripts')
from eval_three_well_gate import three_well_gate
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/aligned_preds.npz',allow_pickle=True)
base=z['s_54844628'].astype(float); truth=z['truth'].astype(float); well=z['well'].astype(str)
rmse=lambda p:float(np.sqrt(np.mean((np.asarray(p,float)-truth)**2)))
def gate(p): return three_well_gate(p,base,truth,well,nboot=12000)
print(f"baseline s_54844628 OOF={rmse(base):.4f}\n")
print(f"{'blend':32s} {'OOF':>8} {'oofGain':>8} | {'3w_5th':>8} {'3w_25th':>8} {'3w_50th':>8} {'P>0':>5} | {'gate':>5}")
def row(name,p):
    r=gate(p); v='PASS' if r['gate_pass'] else ('COND' if r['gate_conditional'] else 'FAIL')
    pc=r['boot3_pct']
    print(f"{name:32s} {rmse(p):>8.4f} {r['all_gain']:>+8.4f} | {pc[5]:>+8.3f} {pc[25]:>+8.3f} {pc[50]:>+8.3f} {100*r['boot3_prob_pos']:>4.0f}% | {v:>5}")
    return r
print("--- alpha-shrinkage toward baseline ---")
for tgt in ['s_54878409','topk96_l75','s_k96_aniso']:
    for a in [0.05,0.10,0.20,0.30,0.50]:
        row(f"{tgt} a={a:.2f}", base+a*(z[tgt].astype(float)-base))
print("\n--- robust combiners across model family ---")
dwt=z['dwt'].astype(float); pf=z['pf'].astype(float); s50=z['s_54878409'].astype(float); s1=z['s_54844628'].astype(float)
row("median(dwt,pf,s1)", np.median(np.column_stack([dwt,pf,s1]),1))
row("median(s1,s54878409,topk)", np.median(np.column_stack([s1,s50,z['topk96_l75'].astype(float)]),1))
row("trimmed 0.5*(s1+s54878409)", 0.5*s1+0.5*s50)
row("min-move: base + clip(cand-base,+-2)", base+np.clip(z['s_54878409'].astype(float)-base,-2,2))
print("\n=> looking for ANY blend with 3-well 5th>0 OR a strictly positive 25th with small downside.")
