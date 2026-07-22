"""Direction 1: anti-harm guard. Apply the candidate only where a test-available guard predicts it is
SAFE (does not hurt vs baseline); keep baseline elsewhere. Guard trained LEAVE-WELL-OUT (nested), then
evaluated with the corrected 3-well gate. Goal: raise the 3-well 5th percentile by removing harmful rows.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/ubuntu/workstation/JoeProject/Kaggle-competition/.claude/worktrees/autonomous-queue/scripts')
from eval_three_well_gate import three_well_gate
from collections import defaultdict
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/aligned_preds.npz',allow_pickle=True)
well=z['well'].astype(str); ridx=z['ridx'].astype(int); truth=z['truth'].astype(float)
base=z['s_54844628'].astype(float); cand=z['s_54878409'].astype(float)
nnb=z['nnb'].astype(float); csurv=z['closest_surv'].astype(float); call=z['closest_all'].astype(float)
# extra test-available features
sv=np.load(f'{SH}/struct_aniso_surv.npz',allow_pickle=True)
gradmag=dict(zip(sv['meta_well'].astype(str),sv['meta_gradmag'].astype(float)))
gm=np.array([gradmag.get(w,0.0) for w in well])
rd=np.load(f'{SH}/struct_oof_rowdist.npz',allow_pickle=True)
rw=rd['well'].astype(str); rr=rd['ridx'].astype(int); rnn=rd['nn_dist'].astype(float)
nnmap=defaultdict(dict)
for w,r,v in zip(rw,rr,rnn): nnmap[w][int(r)]=v
nn=np.array([nnmap[w].get(int(r),np.nan) for w,r in zip(well,ridx)])
uz=np.load(f'{SH}/pf_unc.npz',allow_pickle=True)
uw2=uz['well'].astype(str); uu=uz['unc'].astype(float)
umap=defaultdict(list)
for w,v in zip(uw2,uu): umap[w].append(v)
# unc is per-row per well in order; align by position
uidx=defaultdict(list)
for i,w in enumerate(well): uidx[w].append(i)
unc=np.full(len(well),np.nan)
for w in set(well)&set(uw2):
    pos=uidx[w]; vals=umap[w]
    if len(pos)==len(vals):
        for k,i in enumerate(pos): unc[i]=vals[k]
delta=cand-base
absdelta=np.abs(delta)
FEAT=np.column_stack([absdelta, np.nan_to_num(csurv,nan=2000), nnb, np.nan_to_num(gm,nan=0),
                      np.nan_to_num(nn,nan=1000), np.nan_to_num(unc,nan=np.nanmedian(unc[np.isfinite(unc)]))])
FN=['absdelta','csurv','nnb','gradmag','nn_dist','pf_unc']
# per-row harm label: does candidate increase squared error?
harm=((cand-truth)**2 > (base-truth)**2).astype(int)   # 1 = hurt on this row
uw=np.array(sorted(set(well)))
rng=np.random.RandomState(0); fold={w:i%5 for i,w in enumerate(rng.permutation(uw))}
foldv=np.array([fold[w] for w in well])
from sklearn.ensemble import HistGradientBoostingClassifier
gated=(nnb>=4)&(csurv<1000)&np.isfinite(csurv)   # only rows where candidate differs from base
print(f"rows={len(well)} gated(cand!=base)={100*gated.mean():.1f}% harm-rate-on-gated={100*harm[gated].mean():.1f}%",flush=True)
safe=np.ones(len(well),bool)  # default: apply candidate (=safe)
proba=np.zeros(len(well))
for f in range(5):
    tr=(foldv!=f)&gated; te=(foldv==f)&gated
    if tr.sum()<500 or te.sum()==0: continue
    idx=np.where(tr)[0][::3]
    clf=HistGradientBoostingClassifier(max_iter=150,learning_rate=0.08,max_depth=6,min_samples_leaf=200).fit(FEAT[idx],harm[idx])
    proba[te]=clf.predict_proba(FEAT[te])[:,1]
# guard: apply candidate only where P(harm) < threshold
from eval_three_well_gate import three_well_gate
print(f"\nAUC of harm predictor (gated rows):",end=' ')
from sklearn.metrics import roc_auc_score
print(f"{roc_auc_score(harm[gated],proba[gated]):.4f}",flush=True)
print(f"\n{'guard threshold':22s} {'appliedFrac':>11} {'OOF':>8} {'oofGain':>8} | {'3w_5th':>8} {'3w_25th':>8} {'P>0':>5}")
rmse=lambda p:float(np.sqrt(np.mean((p-truth)**2)))
for thr in [1.01,0.60,0.55,0.50,0.45,0.40]:
    guarded=base.copy()
    apply=gated&(proba<thr)
    guarded[apply]=cand[apply]
    r=three_well_gate(guarded,base,truth,well,nboot=8000)
    pc=r['boot3_pct']
    tag='ungated(all)' if thr>1 else f'P(harm)<{thr:.2f}'
    print(f"{tag:22s} {100*apply.mean():>10.1f}% {rmse(guarded):>8.4f} {r['all_gain']:>+8.4f} | {pc[5]:>+8.3f} {pc[25]:>+8.3f} {100*r['boot3_prob_pos']:>4.0f}%",flush=True)
print("\n=> if no threshold makes 3w_5th>0, a per-row harm guard cannot rescue this candidate at 3-well scale.")
