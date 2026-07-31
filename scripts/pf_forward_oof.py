"""Honest PF-forward OOF for the Sunny PF90 physical/beam model.

The submitted Sunny PF90 (54710185, public 8.864) physical component (`SUNNY_CODE` in cell 108 of
`henry_v10_sunny80_blend`) predicts a well's toe two ways: `tvt_pf` = an honest 128-seed particle-filter
forward model (GR↔typewell matching from the known heel — test-available), and `tvt_phys` =
`tvt_from_contacts`, which LEAKS (uses `hw_tr['TVT']` toe truth + `hw_tr['EGFDU']` train-only surface) and
runs ONLY on wells present in train. The submitted model uses `tvt_phys` for overlap wells (~0.007 ft) and
`tvt_pf` for novel wells. So its 8.864 public is inflated by overlap leakage; the honest novel-well
performance is the PF forward alone. This script measures that: run the PF forward on TRAIN wells (heel +
typewell only, NO tvt_from_contacts), score vs toe truth = the honest novel-well OOF, comparable to DWT 10.40.

Usage: NS=32 MAXW=773 python3 scripts/pf_forward_oof.py   (pure CPU; ~60 min for 773 wells at n_seeds=32, 2 cores)
Requires: the henry notebook + local data/rogii. Reproducible extraction of SUNNY_CODE from cell 108.
"""
import os, time, glob, json, re, numpy as np, pandas as pd
from joblib import Parallel, delayed

NB = "kaggle_kernel_henry_v10_sunny80_blend/rogii-henry-v10-sunny80-blend.ipynb"
DATA = os.environ.get("ROGII_DATA", "data/rogii")

def load_sunny_funcs():
    nb = json.load(open(NB))
    cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    s = "".join(cells[108]["source"])
    m = re.search(r"SUNNY_CODE\s*=\s*'(.*?)'\n", s, re.S)
    code = m.group(1).encode().decode("unicode_escape")
    cut = code.find("sample = pd.read_csv(os.path.join(INPUT_DIR, 'sample_submission.csv')")
    funcs = code[:cut].replace("INPUT_DIR = find_input_dir()", f"INPUT_DIR = os.path.abspath({DATA!r})")
    ns = {}
    exec(funcs, ns)
    return ns

def main():
    ns = load_sunny_funcs()
    run_pf, load_well, TRAIN_DIR = ns["run_pf_lik_ensemble"], ns["load_well"], ns["TRAIN_DIR"]
    wids = sorted(os.path.basename(f).split("__")[0] for f in glob.glob(os.path.join(TRAIN_DIR, "*__horizontal_well.csv")))
    NS = int(os.environ.get("NS", "32")); MAXW = int(os.environ.get("MAXW", str(len(wids))))
    wids = wids[:MAXW]

    def one(wid):
        try:
            hw, tw = load_well(wid, "train")
            toe = hw["TVT_input"].isna().values
            if toe.sum() < 10 or hw["TVT_input"].notna().sum() < 10:
                return None
            pred = run_pf(hw, tw, n_particles=500, n_seeds=NS, scale=5.0)  # honest: heel + typewell only
            truth = hw["TVT"].values
            return (wid, pred[toe].astype(np.float32), truth[toe].astype(np.float32))
        except Exception as e:
            return ("ERR", str(e), wid)

    t0 = time.time()
    res = Parallel(n_jobs=-1, verbose=5)(delayed(one)(w) for w in wids)
    ok = [r for r in res if r and r[0] != "ERR"]
    print(f"done {len(wids)} wells in {(time.time()-t0)/60:.1f} min (n_seeds={NS}); ok={len(ok)}")
    pred = np.concatenate([r[1] for r in ok]); truth = np.concatenate([r[2] for r in ok])
    cv = float(np.sqrt(np.mean((pred - truth) ** 2)))
    print(f"HONEST PF-forward OOF CV (toe TVT RMSE) = {cv:.4f}  rows={len(pred)} wells={len(ok)}  vs DWT 10.3987")
    np.savez(os.environ.get("PF_OUT", "pf_oof.npz"),
             well=np.concatenate([np.full(len(r[1]), r[0]) for r in ok]).astype(str),
             pred=pred, truth=truth)

if __name__ == "__main__":
    main()
