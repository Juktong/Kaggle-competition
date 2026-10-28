"""Honest PF-forward (Sunny physical novel-well component) vs DWT: CV + row-level nested blend.
Aligns pf_oof.npz (well, pred=TVT, truth=TVT) with DWT combo_state (well, oof, yt, base) by (well, position),
truth-verified. Reports PF CV vs DWT, error correlation, and deployable nested blend DWT + a*(PF-DWT)."""
import sys, numpy as np
from collections import defaultdict
DWT="/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz"
def main(pf_path):
    p=np.load(pf_path,allow_pickle=True); pw=p['well'].astype(str); pp=p['pred'].astype(np.float64); pt=p['truth'].astype(np.float64)
    pf_cv=float(np.sqrt(np.mean((pp-pt)**2)))
    print(f"Honest PF-forward OOF: rows={len(pp)} wells={len(np.unique(pw))}  CV (toe TVT RMSE)={pf_cv:.4f}  vs DWT 10.3987")
    cs=np.load(DWT); toe=cs['is_toe']; dw=cs['well'][toe].astype(str); do=cs['oof'][toe].astype(np.float64); dy=cs['yt'][toe].astype(np.float64)
    def idx(w):
        d=defaultdict(list); [d[x].append(i) for i,x in enumerate(w)]; return d
    pi,di=idx(pw),idx(dw); common=sorted(set(pi)&set(di))
    P=[];D=[];T=[];W=[]; mm=0
    for w in common:
        a=np.array(pi[w]); b=np.array(di[w])
        if len(a)!=len(b): mm+=1; continue
        if np.sqrt(np.mean((pt[a]-dy[b])**2))>2.0: mm+=1; continue
        P.append(pp[a]);D.append(do[b]);T.append(dy[b]);W.append(np.full(len(a),w))
    P=np.concatenate(P);D=np.concatenate(D);T=np.concatenate(T);W=np.concatenate(W)
    print(f"aligned wells={len(common)-mm} (skip={mm}) rows={len(T)}")
    print(f"pooled(aligned): DWT RMSE={np.sqrt(np.mean((D-T)**2)):.4f}  PF RMSE={np.sqrt(np.mean((P-T)**2)):.4f}  corr(errD,errPF)={np.corrcoef(D-T,P-T)[0,1]:.3f}")
    uw=np.array(sorted(set(W))); rng=np.random.RandomState(0); rng.shuffle(uw); g0=set(uw[:len(uw)//2]); m0=np.array([x in g0 for x in W]); m1=~m0
    def fit(m): d=P[m]-D[m]; r=T[m]-D[m]; v=np.dot(d,d); return float(np.dot(d,r)/v) if v>1e-9 else 0.0
    def rmse(m,a): return np.sqrt(np.mean((T[m]-(D[m]+a*(P[m]-D[m])))**2))
    a0,a1=fit(m0),fit(m1)
    g=((rmse(m1,0)-rmse(m1,a0))*m1.sum()+(rmse(m0,0)-rmse(m0,a1))*m0.sum())/len(T)
    print(f"nested blend a: fold0={a0:.3f} fold1={a1:.3f}  OOS pooled RMSE gain={g:+.4f}")
    # per-well win-rate + difficulty-split (well-family) -> is a selector viable?
    wl=np.array(sorted(set(W)))
    dR=np.array([np.sqrt(np.mean((D[W==w]-T[W==w])**2)) for w in wl])
    pR=np.array([np.sqrt(np.mean((P[W==w]-T[W==w])**2)) for w in wl])
    print(f"per-well: PF<DWT in {int((pR<dR).sum())}/{len(wl)} wells ({100*np.mean(pR<dR):.0f}%)  mean(DWT)={dR.mean():.3f} mean(PF)={pR.mean():.3f}")
    q=np.quantile(dR,[1/3,2/3])
    for name,sel in [("easy(DWT low)",dR<=q[0]),("mid",(dR>q[0])&(dR<=q[1])),("hard(DWT high)",dR>q[1])]:
        if sel.sum(): print(f"  {name:16s} n={sel.sum():3d}  DWT={dR[sel].mean():.3f} PF={pR[sel].mean():.3f}  PF<DWT={100*np.mean(pR[sel]<dR[sel]):.0f}%")
    # oracle selector (upper bound) vs deployable: route each well to min-RMSE model (oracle) vs fixed
    orc=np.sqrt((np.minimum(dR,pR)**2 * np.array([np.sum(W==w) for w in wl])).sum()/len(T))
    print(f"oracle per-well selector RMSE={orc:.4f} (upper bound; not deployable — needs truth to route)")
    # well-level bootstrap: is the fixed 0.5/0.5 blend gain robustly positive (not driven by a few tail wells)?
    idxw={w:np.where(W==w)[0] for w in wl}
    def pooled_gain_5050(sample_wells):
        rows=np.concatenate([idxw[w] for w in sample_wells])
        d,pp,t=D[rows],P[rows],T[rows]; bl=0.5*d+0.5*pp
        return np.sqrt(np.mean((d-t)**2))-np.sqrt(np.mean((bl-t)**2))
    br=np.random.RandomState(1); gains=np.array([pooled_gain_5050(wl[br.randint(0,len(wl),len(wl))]) for _ in range(300)])
    print(f"bootstrap 0.5/0.5 blend gain: mean={gains.mean():+.4f}  5th pct={np.percentile(gains,5):+.4f}  frac>0={100*np.mean(gains>0):.0f}%")
    print(f"full-sample 0.5/0.5 blend RMSE={np.sqrt(np.mean((0.5*D+0.5*P-T)**2)):.4f} vs DWT-aligned {np.sqrt(np.mean((D-T)**2)):.4f}")
    print(f"VERDICT: {'PF stronger than DWT on novel' if np.sqrt(np.mean((P-T)**2))<10.3987 else 'PF WEAKER/COMPARABLE vs DWT on novel (Sunny public 8.864 is overlap-leakage-inflated)'}")
if __name__=="__main__": main(sys.argv[1] if len(sys.argv)>1 else "pf_oof.npz")
