"""Honest PF-forward OOF harness (batched/checkpointed/resumable).
Reads SUNNY_CODE (henry_v10_sunny80_blend cell 108) honest functions run_pf_lik_ensemble/load_well,
strips the leaked main loop + tvt_from_contacts, runs the PF forward on each TRAIN well from its own
heel+typewell only (honest novel-well proxy), scores vs toe truth. Env: NS, MAXW, BATCH, CKPT, LOG.
Produced the 773-well OOF CV 10.9952; DWT+PF 0.5/0.5 blend OOF 9.2969 (see scripts/pf_dwt_blend.py)."""
import os, time, glob, numpy as np, pandas as pd
from joblib import Parallel, delayed

JOB=os.environ['CLAUDE_JOB_DIR']
code=open(os.path.join(JOB,'tmp/SUNNY_CODE.py')).read()
cut=code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
funcs=code[:cut].replace("INPUT_DIR = find_input_dir()","INPUT_DIR = os.path.abspath('data/rogii')")
ns={}; exec(funcs, ns)
run_pf=ns['run_pf_lik_ensemble']; load_well=ns['load_well']; TRAIN_DIR=ns['TRAIN_DIR']
train_wids=sorted(os.path.basename(f).split('__')[0] for f in glob.glob(os.path.join(TRAIN_DIR,'*__horizontal_well.csv')))

NS=int(os.environ.get('NS','24')); MAXW=int(os.environ.get('MAXW','773')); BATCH=int(os.environ.get('BATCH','16'))
CKPT=os.environ.get('CKPT', os.path.join(JOB,'tmp/pf_oof.npz')); LOG=os.environ.get('LOG', os.path.join(JOB,'tmp/pf_oof_progress.log'))

# deterministic shuffle -> a partial (early-killed) run is still representative of the population
rng=np.random.RandomState(42); order=list(train_wids); rng.shuffle(order); wids=order[:MAXW]

# resume from checkpoint (skip already-scored wells)
done={}
if os.path.exists(CKPT):
    d=np.load(CKPT,allow_pickle=True); dw=d['well'].astype(str)
    for w in np.unique(dw):
        m=dw==w; done[w]=(d['pred'][m], d['truth'][m])
todo=[w for w in wids if w not in done]

def logline(s):
    with open(LOG,'a') as f: f.write(s+'\n')
    print(s, flush=True)

def one(wid):
    try:
        hw,tw=load_well(wid,'train')
        toe=hw['TVT_input'].isna().values
        if toe.sum()<10 or hw['TVT_input'].notna().sum()<10: return None
        pred=run_pf(hw,tw,n_particles=500,n_seeds=NS,scale=5.0)
        truth=hw['TVT'].values
        return (wid, pred[toe].astype(np.float32), truth[toe].astype(np.float32))
    except Exception as e:
        return ('ERR',str(e),wid)

logline(f"=== PF-forward OOF (honest: heel+typewell only) NS={NS} MAXW={MAXW} BATCH={BATCH} todo={len(todo)} resumed={len(done)} ===")
t0=time.time(); cv=float('nan')
for i in range(0,len(todo),BATCH):
    batch=todo[i:i+BATCH]
    res=Parallel(n_jobs=2)(delayed(one)(w) for w in batch)
    for r in res:
        if r is None: continue
        if r[0]=='ERR': logline(f"  ERR {r[2]}: {str(r[1])[:80]}")
        else: done[r[0]]=(r[1],r[2])
    ws=sorted(done)
    allpred=np.concatenate([done[w][0] for w in ws]); alltruth=np.concatenate([done[w][1] for w in ws])
    np.savez(CKPT, well=np.concatenate([np.full(len(done[w][0]),w) for w in ws]).astype(str), pred=allpred, truth=alltruth)
    cv=float(np.sqrt(np.mean((allpred-alltruth)**2)))
    pw=np.array([np.sqrt(np.mean((done[w][0]-done[w][1])**2)) for w in ws])
    logline(f"[{(time.time()-t0)/60:5.1f}m] wells={len(ws):3d} rows={len(allpred):>8d} runCV={cv:.4f} medWell={np.median(pw):.3f} p90={np.percentile(pw,90):.2f}  (DWT 10.3987)")
logline(f"DONE wells={len(done)} final CV={cv:.4f}  saved pf_oof.npz")
