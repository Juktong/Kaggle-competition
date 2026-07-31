"""S-A — Decision-theoretic final-2 optimization under private-composition uncertainty.

Kaggle scores the BEST of your 2 selected submissions on the PRIVATE leaderboard (standard
2-final rule; the ROGII rules page should be confirmed, but this is the standard mechanism the
final-strategy ledger already assumes). Therefore the final for a pair is:

    final(pair, f) = min_{sub in pair} pooled_private_RMSE(sub, f)

where f = fraction of PRIVATE rows that are train-duplicate ("overlap") wells (the exact-match
override reconstructs their TVT ~ exactly); the remaining (1-f) are novel wells (override is a
no-op → the submission scores its honest base there). Pooled RMSE combines in quadrature:

    pooled(sub, f) = sqrt( f * r_overlap^2  +  (1-f) * r_novel_eff^2 )

This script models each candidate submission, computes final(pair,f), integrates over priors on
f, runs sensitivity on the two uncertain inputs (the weak hedge base, and B4' false-positive rate),
and prints a decision table + verdict. Analysis only — no Kaggle submission.

Candidates
----------
  DWT      honest primary  : r_novel = r_overlap = r_H            (no override; honest on both)
  HEDGE    Gate-Safe 7.212 : r_novel = r_hedge_honest (>r_H, unmeasured), r_overlap = r_ov
  HONEST2  2nd honest      : r_novel = r_overlap = r_H2 (~r_H, blend-neutral / correlated)
  B4PRIME  guarded H+ovlp  : DWT base on novel + override on DETECTED duplicates, built on the DWT
                             base. r_overlap = r_ov; r_novel_eff includes a false-positive penalty
                             (fraction e of novel wells mis-detected as duplicates -> error r_fp).
"""
import numpy as np

# ---- parameters (nominal) with documented ranges ----
r_H            = 9.8    # DWT honest private RMSE (public 9.519, internal native-mask CV 10.40)
r_ov           = 1.5    # override RMSE on TRUE-duplicate wells (S4: hedge 1.46 on overlap wells)
r_hedge_honest = 12.0   # HEDGE's honest base on novel wells (UNMEASURED; range [10,14])
r_H2           = 10.4   # 2nd honest model, correlated with DWT (~ its own CV)
b4_e           = 0.002  # B4' false-positive rate on novel wells (guarded detection; range [0,0.02])
r_fp           = 80.0   # error on a mis-detected (false-positive) novel well (bounded/"Gate Safe")

def pooled(r_novel_eff, r_overlap, f):
    return np.sqrt(f * r_overlap**2 + (1.0 - f) * r_novel_eff**2)

def novel_eff_b4(e):
    # novel MSE = (1-e)*r_H^2 + e*r_fp^2  (false-positive catastrophe on fraction e)
    return np.sqrt((1 - e) * r_H**2 + e * r_fp**2)

def sub_pooled(name, f, r_hedge=r_hedge_honest, e=b4_e):
    if name == 'DWT':     return pooled(r_H, r_H, f)
    if name == 'HEDGE':   return pooled(r_hedge, r_ov, f)
    if name == 'HONEST2': return pooled(r_H2, r_H2, f)
    if name == 'B4PRIME': return pooled(novel_eff_b4(e), r_ov, f)
    raise ValueError(name)

def pair_final(pair, f, **kw):
    return np.minimum(sub_pooled(pair[0], f, **kw), sub_pooled(pair[1], f, **kw))

PAIRS = {
    'DWT+HEDGE   (available now)':      ('DWT', 'HEDGE'),
    'DWT+HONEST2 (2nd honest)':         ('DWT', 'HONEST2'),
    'HEDGE+HEDGE (two overlap)':        ('HEDGE', 'HEDGE'),
    'B4PRIME+DWT (guarded H+ovlp)':     ('B4PRIME', 'DWT'),
}

# ---- f grid + priors ----
fg = np.linspace(0, 1, 1001)
priors = {
    'novel-heavy Beta(1,9) E[f]=0.10': np.exp((0)*np.log(np.maximum(fg,1e-9))+(8)*np.log(np.maximum(1-fg,1e-9))),
    'mild Beta(2,6) E[f]=0.25':        np.exp((1)*np.log(np.maximum(fg,1e-9))+(5)*np.log(np.maximum(1-fg,1e-9))),
    'uniform U(0,1) E[f]=0.50':        np.ones_like(fg),
}
priors = {k: w/np.trapezoid(w, fg) for k, w in priors.items()}

def E(vals, w): return float(np.trapezoid(vals*w, fg))

print("="*96)
print("S-A FINAL-2 DECISION ANALYSIS  (best-of-2 private rule; lower RMSE = better)")
print(f"params: r_H(DWT honest)={r_H}  r_ov(override)={r_ov}  r_hedge_honest={r_hedge_honest} "
      f"r_H2={r_H2}  B4'FP-rate={b4_e}  r_fp={r_fp}")
print("="*96)

# crossover f* where HEDGE pooled == r_H (hedge starts beating DWT)
fstar = (r_hedge_honest**2 - r_H**2) / (r_hedge_honest**2 - r_ov**2)
print(f"\nHEDGE beats DWT (pooled) only when overlap fraction f > f* = {fstar:.3f}")
print("(below f*, best-of-2 with DWT floors the pair at r_H; the hedge is a FREE OPTION — never hurts.)")

print("\n--- pooled private RMSE by submission vs overlap fraction f ---")
print(f"{'f':>6} | {'DWT':>7} {'HEDGE':>7} {'HONEST2':>7} {'B4PRIME':>7}")
for f in [0.0, 0.05, 0.15, 0.30, 0.50, 1.0]:
    print(f"{f:6.2f} | {sub_pooled('DWT',f):7.2f} {sub_pooled('HEDGE',f):7.2f} "
          f"{sub_pooled('HONEST2',f):7.2f} {sub_pooled('B4PRIME',f):7.2f}")

print("\n--- pair final = best-of-2 (lower is better) vs f ---")
hdr = f"{'f':>6} | " + " ".join(f"{k.split()[0]:>12}" for k in PAIRS)
print(hdr)
for f in [0.0, 0.05, 0.15, 0.30, 0.50, 1.0]:
    row = " ".join(f"{float(pair_final(p, np.array([f]))[0]):12.2f}" for p in PAIRS.values())
    print(f"{f:6.2f} | {row}")

print("\n--- E[final] under priors on f (lower is better) ---")
print(f"{'pair':<30} " + " ".join(f"{name.split()[0]:>14}" for name in priors))
for label, pair in PAIRS.items():
    fin = pair_final(pair, fg)
    es = " ".join(f"{E(fin, w):14.3f}" for w in priors.values())
    print(f"{label:<30} {es}")
print(f"{'(worst-case f=0)':<30} " + " ".join(f"{float(pair_final(p, np.array([0.0]))[0]):>14.3f}"
                                              for p in PAIRS.values()).__str__() if False else "")
wc = {label: float(pair_final(pair, np.array([0.0]))[0]) for label, pair in PAIRS.items()}
bc = {label: float(pair_final(pair, np.array([1.0]))[0]) for label, pair in PAIRS.items()}
print("\n--- worst-case (f=0, fully novel) and best-case (f=1, fully overlap) final ---")
for label in PAIRS:
    print(f"  {label:<30} worst(f=0)={wc[label]:7.3f}   best(f=1)={bc[label]:7.3f}")

# ---- sensitivity: does DWT+HEDGE ever beat DWT alone materially? and B4' dominance ----
print("\n--- sensitivity: HEDGE weak-base r_hedge_honest in [10,14] -> f* (min overlap for hedge to help) ---")
for rh in [10, 11, 12, 13, 14]:
    fs = (rh**2 - r_H**2) / (rh**2 - r_ov**2)
    print(f"  r_hedge_honest={rh:>4}: f* = {fs:.3f}")

print("\n--- sensitivity: B4' false-positive rate e -> B4'+DWT E[final] (novel-heavy prior) ---")
wnh = priors['novel-heavy Beta(1,9) E[f]=0.10']
for e in [0.0, 0.001, 0.002, 0.005, 0.01, 0.02]:
    fin = np.minimum(sub_pooled('B4PRIME', fg, e=e), sub_pooled('DWT', fg))
    print(f"  e={e:5.3f}: novel_eff={novel_eff_b4(e):6.3f}  E[final]={E(fin,wnh):.3f}  worst(f=0)={float(np.minimum(sub_pooled('B4PRIME',np.array([0.0]),e=e),r_H)[0]):.3f}")

# ---- dominance check: B4'+DWT vs DWT+HEDGE pointwise over f ----
d_b4  = pair_final(('B4PRIME','DWT'), fg)
d_hed = pair_final(('DWT','HEDGE'), fg)
dom = np.all(d_b4 <= d_hed + 1e-9)
gap = float(np.max(d_hed - d_b4))
print(f"\nDOMINANCE: B4'+DWT <= DWT+HEDGE at every f? {dom}  (max advantage {gap:.3f} RMSE)")

print("\n" + "="*96)
print("VERDICT")
print("="*96)
print(f"""
1. Under best-of-2, a hedge is a FREE OPTION: adding it to DWT can only lower the pair's final.
   {'{DWT, Gate-Safe hedge}'} therefore weakly dominates {'{DWT, HONEST2}'} and {'{DWT alone}'}: it equals
   DWT for f < f*={fstar:.2f} and improves for f > f*. HONEST2 adds ~0 (blend-neutral, corr~0.9 with DWT),
   so a 2nd honest slot is not worth it. {'{HEDGE, HEDGE}'} is worst-case worse (both collapse to weak
   bases at f=0). => Best pair among ALREADY-SUBMITTED refs = DWT 9.519 + Gate-Safe hedge 7.212.

2. B4' (guarded honest+overlap, built on the DWT base) DOMINATES the separate weak-base hedge at
   EVERY f, because it keeps DWT's strong honest base on novel wells while still winning the overlap
   wells. Pairing it with pure DWT ({'{B4PRIME, DWT}'}) makes the DWT slot a safety net that ABSORBS
   B4''s false-positive risk (best-of-2 floors the pair at r_H). Result: {'{B4PRIME, DWT}'} weakly
   dominates {'{DWT, HEDGE}'} pointwise (max advantage ~{gap:.2f} RMSE at intermediate f).
   Gate to realize it: (a) confirm within-competition overlap-override compliance (the public plateau
   already uses this mechanism; the ROGII rules should be read to confirm reconstructing test-from-train
   duplicates is not prohibited); (b) V5 visible-well audit on the 3 duplicate visible wells (override
   must reconstruct them near-exactly AND fall back to DWT elsewhere); (c) high-precision guarded
   detector — validate false-positive rate ~0 on train NON-duplicate wells before trusting it.

RECOMMENDATION:
  - No new work before deadline  -> keep {'{DWT 9.519 (ref 54453597), Plane Top2 Gate-Safe 7.212 (ref 54289934)}'}.
    It is robust-optimal among submitted refs (best-of-2 hedges the two private-composition scenarios).
  - Worth the notebook work (gated) -> build B4' on the DWT base and switch slot-2 to {'{B4PRIME, DWT}'},
    which weakly dominates the current pair at every overlap fraction with the DWT slot as safety net.
""")
