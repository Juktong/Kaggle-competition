"""Direction 3 / infrastructure: public-vs-private ROW-SPLIT stability.

The whole test set is 3 wells; public and private are ROW SPLITS of those SAME 3 wells. So the question
that decides private is not 'does the gain hold on other wells' but 'does the gain on one row-subset of
these wells hold on the complementary row-subset'. Within-well residual autocorrelation is +0.9998 at
lag 1, so we test both a RANDOM row split and a CONTIGUOUS block split (Kaggle splits are usually random,
but wellbore MD-ordered data could be blocked).

For a candidate vs baseline s_54844628, on the 3 ACTUAL test wells (OOF proxy) and on random 3-well
draws: split rows 50/50 many times, compute pooled RMSE gain on each half, and report how well one half
predicts the other -- corr(gainA,gainB) and P(gainB<0 | gainA<0).
"""
import sys, numpy as np
SH='/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
z=np.load(f'{SH}/aligned_preds.npz',allow_pickle=True)
well=z['well'].astype(str); truth=z['truth'].astype(float); base=z['s_54844628'].astype(float)
TEST=['000d7d20','00bbac68','00e12e8b']
from collections import defaultdict
idxw=defaultdict(list)
for i,w in enumerate(well): idxw[w].append(i)
idxw={w:np.array(v) for w,v in idxw.items()}
uw=np.array(sorted(idxw))

def split_gain(cand, rows, rng, mode):
    eb=(base[rows]-truth[rows])**2; ec=(cand[rows]-truth[rows])**2
    n=len(rows)
    if mode=='random':
        perm=rng.permutation(n); h=n//2; A=perm[:h]; B=perm[h:]
    else:  # contiguous block per the concatenation (rows are grouped by well, in toe order)
        h=n//2; A=np.arange(h); B=np.arange(h,n)
    gA=np.sqrt(eb[A].mean())-np.sqrt(ec[A].mean())
    gB=np.sqrt(eb[B].mean())-np.sqrt(ec[B].mean())
    return gA,gB

def audit(candname, mode='random', ndraw=3, ntrial=4000):
    cand=z[candname].astype(float)
    rng=np.random.RandomState(3)
    GA,GB=[],[]
    for _ in range(ntrial):
        ws=uw[rng.randint(0,len(uw),ndraw)]
        rows=np.concatenate([idxw[w] for w in ws])
        a,b=split_gain(cand,rows,rng,mode)
        GA.append(a); GB.append(b)
    GA=np.array(GA); GB=np.array(GB)
    corr=np.corrcoef(GA,GB)[0,1]
    neg=GA<0
    pbb=float(np.mean(GB[neg]<0)) if neg.sum()>0 else float('nan')
    # actual 3 test wells
    rows=np.concatenate([idxw[w] for w in TEST if w in idxw])
    # many random splits of the FIXED 3 test wells
    ta,tb=[],[]
    for _ in range(4000):
        a,b=split_gain(cand,rows,rng,mode); ta.append(a); tb.append(b)
    ta=np.array(ta); tb=np.array(tb)
    return corr,pbb,GA,GB,ta,tb

print("mode=RANDOM row split (Kaggle-typical), candidate vs s_54844628 baseline")
print(f"{'candidate':13s} {'corr(A,B)':>9} {'P(B<0|A<0)':>11} | {'3-testwell split: mean':>22} {'P(gain<0)':>10} {'5th':>7} {'95th':>7}")
for c in ['s_54878409','s_a20_w25','s_k96_aniso','topk96_l75']:
    corr,pbb,GA,GB,ta,tb=audit(c,'random')
    allt=np.concatenate([ta,tb])
    print(f"{c:13s} {corr:>9.3f} {100*pbb:>10.1f}% | {allt.mean():>+22.4f} {100*np.mean(allt<0):>9.1f}% {np.percentile(allt,5):>+7.3f} {np.percentile(allt,95):>+7.3f}")
print("\nmode=CONTIGUOUS block split")
for c in ['s_54878409','topk96_l75']:
    corr,pbb,GA,GB,ta,tb=audit(c,'block')
    allt=np.concatenate([ta,tb])
    print(f"{c:13s} corr(A,B)={corr:.3f}  P(B<0|A<0)={100*pbb:.1f}%  3-testwell mean={allt.mean():+.4f} P(gain<0)={100*np.mean(allt<0):.1f}%")
print("\nINTERPRETATION: high corr(A,B) => public gain predicts private gain on the SAME wells.")
print("For the 3 actual test wells, 'mean' is the OOF-proxy gain and 'P(gain<0)' is how often a random")
print("public-row-half would show a loss -- i.e. how reliably public would have warned us.")
