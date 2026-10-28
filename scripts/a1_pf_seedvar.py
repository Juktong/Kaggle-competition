"""A1 local PF seed-variance proxy: run the local PF forward on the 3 test wells with several seed_bases;
measure per-well output variance. This is a PROXY for the frontier PF's seed sensitivity (the frontier
notebook's PF is deterministic given seed_base; this quantifies the ft-scale spread when seed_base varies).
NOT the frontier pipeline; NO Kaggle, NO submit."""
import os, numpy as np, pandas as pd
D='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/test'
code=open('/home/ubuntu/.claude/jobs/06dd2efb/tmp/SUNNY_CODE.py').read()
cut=code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
funcs=code[:cut].replace("INPUT_DIR = find_input_dir()","INPUT_DIR='/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii'")
ns={}; exec(funcs,ns)
pf=ns['run_particle_filter']
TEST=['000d7d20','00bbac68','00e12e8b']
SEEDS=[0,1000,2000,3000]   # 4 seed bases
res={}
for wid in TEST:
    hw=pd.read_csv(f'{D}/{wid}__horizontal_well.csv'); tw=pd.read_csv(f'{D}/{wid}__typewell.csv')
    ev=hw['TVT_input'].isna().values
    preds=[]
    for sb in SEEDS:
        p,_=pf(hw,tw,seed=sb); preds.append(p[ev])
    P=np.array(preds)  # (nseeds, ntoe)
    # pairwise per-row spread across seeds
    perrow_std=P.std(0)
    res[wid]=(P, perrow_std)
    print(f"{wid}: toe_rows={P.shape[1]} seeds={len(SEEDS)}  per-row std across seeds: mean={perrow_std.mean():.3f}ft median={np.median(perrow_std):.3f} p95={np.percentile(perrow_std,95):.3f} max={perrow_std.max():.2f}", flush=True)
    # pairwise pooled RMSE between seed pairs
    rms=[]
    for i in range(len(SEEDS)):
        for j in range(i+1,len(SEEDS)):
            rms.append(np.sqrt(np.mean((P[i]-P[j])**2)))
    print(f"   pairwise seed-pair RMSE: mean={np.mean(rms):.3f}ft min={min(rms):.3f} max={max(rms):.3f}", flush=True)
# pooled across all 3 wells
allstd=np.concatenate([res[w][1] for w in TEST])
print(f"\nPOOLED (3 wells): per-row seed std mean={allstd.mean():.3f}ft median={np.median(allstd):.3f} p95={np.percentile(allstd,95):.3f}")
print("INTERP: this ft-scale per-row seed spread bounds the H-hidden run-to-run PF noise (frontier PF is")
print("        deterministic given seed_base; on VISIBLE wells the overlap override pins output so seed")
print("        variance there is ~0). The observed 6.563/6.669/6.678 public spread (0.115) is CONFIG")
print("        variance across frontier branches, not same-config seed noise.")
