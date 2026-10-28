"""Honest PF-forward OOF WITH per-row uncertainty (seed spread) + likelihood dispersion.
Re-implements run_pf_lik_ensemble's loop to capture the weighted std across seeds (per-row PF uncertainty)
and the seed log-likelihood dispersion (well-level PF confidence) — the ASYMMETRIC signals a selector needs.
Batched/checkpointed/resumable. Env: NS, MAXW, BATCH, CKPT, LOG."""
import os, time, glob, numpy as np, pandas as pd
from joblib import Parallel, delayed

JOB = os.environ['CLAUDE_JOB_DIR']
code = open('/home/ubuntu/.claude/jobs/06dd2efb/tmp/SUNNY_CODE.py').read()
cut = code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
funcs = code[:cut].replace("INPUT_DIR = find_input_dir()", "INPUT_DIR = os.path.abspath('data/rogii')")
ns = {}; exec(funcs, ns)
run_pfilter = ns['run_particle_filter']; load_well = ns['load_well']; TRAIN_DIR = ns['TRAIN_DIR']
train_wids = sorted(os.path.basename(f).split('__')[0] for f in glob.glob(os.path.join(TRAIN_DIR, '*__horizontal_well.csv')))

NS = int(os.environ.get('NS', '24')); MAXW = int(os.environ.get('MAXW', '773')); BATCH = int(os.environ.get('BATCH', '16'))
CKPT = os.environ.get('CKPT', os.path.join(JOB, 'tmp/pf_unc.npz'))
LOG = os.environ.get('LOG', os.path.join(JOB, 'tmp/pf_unc.log'))
SCALE = 5.0

rng = np.random.RandomState(42); order = list(train_wids); rng.shuffle(order); wids = order[:MAXW]
done = {}
if os.path.exists(CKPT):
    d = np.load(CKPT, allow_pickle=True); dw = d['well'].astype(str)
    for w in np.unique(dw):
        m = dw == w
        done[w] = (d['pred'][m], d['truth'][m], d['unc'][m], float(d['likdisp'][m][0]))
todo = [w for w in wids if w not in done]

def log(s):
    with open(LOG, 'a') as f: f.write(s + '\n')
    print(s, flush=True)

def one(wid):
    try:
        hw, tw = load_well(wid, 'train')
        toe = hw['TVT_input'].isna().values
        if toe.sum() < 10 or hw['TVT_input'].notna().sum() < 10: return None
        preds = []; liks = []
        for s in range(NS):
            p, ll = run_pfilter(hw, tw, n_particles=500, seed=s)
            preds.append(np.asarray(p, dtype=np.float64)); liks.append(float(ll))
        L = np.array(liks); Ln = L - L.max(); w = np.exp(Ln / SCALE); w = w / w.sum()
        P = np.stack(preds, 0)                       # (NS, nrows)
        mean = (w[:, None] * P).sum(0)               # weighted mean = the standard PF pred
        var = (w[:, None] * (P - mean) ** 2).sum(0)  # weighted variance across seeds
        unc = np.sqrt(np.maximum(var, 0.0))          # per-row PF uncertainty
        likdisp = float(np.std(L))                   # seed log-lik dispersion (well-level PF confidence)
        truth = hw['TVT'].values
        return (wid, mean[toe].astype(np.float32), truth[toe].astype(np.float32),
                unc[toe].astype(np.float32), likdisp)
    except Exception as e:
        return ('ERR', str(e), wid)

log(f"=== PF-uncertainty OOF NS={NS} MAXW={MAXW} BATCH={BATCH} todo={len(todo)} resumed={len(done)} ===")
t0 = time.time(); cv = float('nan')
for i in range(0, len(todo), BATCH):
    batch = todo[i:i + BATCH]
    res = Parallel(n_jobs=2)(delayed(one)(w) for w in batch)
    for r in res:
        if r is None: continue
        if r[0] == 'ERR': log(f"  ERR {r[2]}: {str(r[1])[:70]}")
        else: done[r[0]] = (r[1], r[2], r[3], r[4])
    ws = sorted(done)
    ap = np.concatenate([done[w][0] for w in ws]); at = np.concatenate([done[w][1] for w in ws])
    au = np.concatenate([done[w][2] for w in ws])
    np.savez(CKPT,
             well=np.concatenate([np.full(len(done[w][0]), w) for w in ws]).astype(str),
             pred=ap, truth=at, unc=au,
             likdisp=np.concatenate([np.full(len(done[w][0]), done[w][3]) for w in ws]).astype(np.float32))
    cv = float(np.sqrt(np.mean((ap - at) ** 2)))
    log(f"[{(time.time()-t0)/60:5.1f}m] wells={len(ws):3d} rows={len(ap):>8d} CV={cv:.4f} meanUnc={au.mean():.2f}")
log(f"DONE wells={len(done)} CV={cv:.4f} saved {CKPT}")
