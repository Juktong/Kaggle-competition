"""Well-level Sunny-vs-DWT honesty + decorrelation + blend analysis.

Takes a Sunny OOF (sunny_oof.npz from the henry GroupKFold fork: well, oof_drift, y_drift) and the DWT
native-mask OOF (combo_state.npz: well, oof, yt, is_toe). Aligns at the WELL level (per-well mean drift
error) — robust to row-order/preprocessing differences between the two pipelines. Reports:
  - Sunny meta OOF CV vs DWT toe CV (10.40);
  - per-well error correlation corr(err_Sunny, err_DWT);
  - well-level nested blend weight w* for DWT + w*(Sunny-DWT) and the CV gain;
  - whether a DWT+Sunny blend is worth pursuing (positive stable weight + gain) or blend-neutral.

Usage: python3 scripts/sunny_dwt_blend_analysis.py <sunny_oof.npz>
"""
import sys, numpy as np

DWT = "/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz"

def main(sunny_path):
    s = np.load(sunny_path, allow_pickle=True)
    s_well = s["well"].astype(str); s_oof = s["oof_drift"].astype(np.float64); s_y = s["y_drift"].astype(np.float64)
    # Sunny per-well mean pred/truth (drift)
    su = {}
    for w in np.unique(s_well):
        m = s_well == w
        su[w] = (s_oof[m].mean(), s_y[m].mean(), np.sqrt(np.mean((s_oof[m]-s_y[m])**2)), int(m.sum()))
    sunny_cv = float(np.sqrt(np.mean((s_oof - s_y)**2)))
    print(f"Sunny GroupKFold OOF: rows={len(s_oof)} wells={len(su)}  meta OOF CV (drift RMSE)={sunny_cv:.4f}")

    d = np.load(DWT)
    d_well = d["well"].astype(str); toe = d["is_toe"]; d_oof = d["oof"].astype(np.float64); d_yt = d["yt"].astype(np.float64); d_base = d["base"].astype(np.float64)
    dwt_cv = float(np.sqrt(np.mean((d_oof[toe]-d_yt[toe])**2)))
    print(f"DWT native-mask OOF: toe CV (TVT RMSE)={dwt_cv:.4f}  (the 10.40 honest proxy)")
    # DWT per-well mean drift error (drift = pred - truth in TVT == same as drift-space since base cancels)
    dw = {}
    for w in np.unique(d_well[toe]):
        m = (d_well == w) & toe
        # DWT error in TVT space; per-well mean signed error + rmse
        err = d_oof[m] - d_yt[m]
        dw[w] = (err.mean(), np.sqrt(np.mean(err**2)), int(m.sum()))

    common = sorted(set(su) & set(dw))
    print(f"\ncommon wells (Sunny ∩ DWT): {len(common)} / Sunny {len(su)} / DWT {len(dw)}")
    if len(common) < 5:
        print("  INSUFFICIENT well overlap for a blend assessment (Sunny train_df wells differ from DWT).")
        return
    # per-well signed mean error
    es = np.array([su[w][0]-su[w][1] for w in common])   # Sunny per-well mean signed drift error
    ed = np.array([dw[w][0] for w in common])            # DWT per-well mean signed error
    r = np.corrcoef(es, ed)[0,1]
    print(f"per-well mean-error correlation corr(Sunny,DWT) = {r:+.3f}  (low => decorrelated => blend may help)")
    # well-level nested blend: predict DWT well-error using Sunny well-error, honest 2-split
    idx = np.arange(len(common)); rng = np.random.RandomState(0); rng.shuffle(idx)
    h = len(idx)//2; A, B = idx[:h], idx[h:]
    def wstar(sub):
        x = es[sub]; yv = ed[sub]; v = np.dot(x,x)
        return float(np.dot(x,yv)/v) if v>1e-9 else 0.0
    wA, wB = wstar(A), wstar(B)
    # apply cross: gain in per-well error variance
    def gain(sub,w):
        return float(np.mean(ed[sub]**2) - np.mean((ed[sub]-w*es[sub])**2))
    g = (gain(B,wA)*len(B)+gain(A,wB)*len(A))/len(common)
    print(f"well-level nested blend weight: wA={wA:+.3f} wB={wB:+.3f}  out-of-sample per-well-var gain={g:+.4f}")
    stable = (np.sign(wA)==np.sign(wB)) and abs(wA)>0.05 and abs(wB)>0.05
    print(f"VERDICT: {'positive-stable well-level blend signal — worth a row-level test' if (stable and g>0) else 'blend-neutral / unstable — DWT+Sunny blend not warranted (use best-of-2 selection)'}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv)>1 else "sunny_oof.npz")
