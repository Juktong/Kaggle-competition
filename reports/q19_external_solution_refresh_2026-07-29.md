# Q19 — external solution refresh: two better-scoring public kernels resolved to one token and one hand-fit

Date: 2026-07-29
Task: `q19_external_solution_refresh` (`requires_gpu=false`, `can_submit=true`, `max_submit_cost=1`)
Scripts: `scripts/q19_gr_sigma_multiplier_smoke.py`, patch to `scripts/pf_honest_forward.py`
Logs: `reports/logs/q19_gr_sigma_2026-07-29.log`, `reports/logs/q19_gr_sigma_ext_2026-07-29.log`
Outcome: **one find converted into an executable smoke and measured; it FAILS the 3-well gate. No
submission, no Kaggle run. Quota untouched at 0/5.**

## 1. Public standing — the most material finding of this round

| | |
|---|---|
| public LB leader | **4.679** |
| 200th place | **6.389** |
| our best | **6.563** (`54922806`) |

The API caps a leaderboard page at 200 rows; **every one of the 200 fetched teams is ahead of our 6.563**.
So we are outside the top 200, and the leader is ~1.88 better.

This is recorded plainly because it is decision-relevant, but two qualifications matter and are not
rhetorical: (a) the public score is a **3-well** quantity, and Q18 measured that pooled gaps ≥1.00 still
reverse on ~28% of random 3-well draws, so the deficit's size on novel wells is not pinned down by this;
(b) the project targets the **private** ranking, which is not visible.

## 2. The published-method pool tops out at our own level

279 → 798 distinct public kernels enumerated for the competition. Parsing advertised scores from
titles/slugs, the published notebooks cluster at **7.06–8.86** (LB 7.061, 7.129, 7.159, 7.166, 7.168,
7.191, 7.201, 7.776, 7.872, 8.781, 8.860) — all *worse* than our 6.563. **Exactly two** advertise better:

| kernel | advertised | run |
|---|---|---|
| `leonidzaporozhets/new-strategy-score-6-213` | 6.213 | 2026-07-22 |
| `my0705/rogii-stacked-ensemble-highscoring-6-520` | 6.520 | 2026-07-28 |

**So the ~200 teams at 4.7–6.4 have not published their methods.** The external pool cannot close the gap
by adoption; there is nothing published at the 5.x level. Both better-than-us kernels use the *same*
7-dataset stack that our frontier already mounts (a subset of the Kaiwalya 9), i.e. same family.

Also checked: `origin/main`'s `a589fa8` "reproducible public 6.626 kernel" is
`kaiwalyaatulraut/rogii-public-tvt-solution` — the identical family our `54968060`/`54922806` derive from,
with the same 9 datasets. **Redundant, not a new method.** Dated 2026-07-23; it surfaced now only because
`origin/main` moved.

## 3. Find A — the 6.213 kernel is our own base plus ONE token

Normalised (comments and whitespace stripped) cell-by-cell comparison against our pristine base
`kaggle_kernel_kaiwalya_public_tvt_6626_repro`:

```
code cells ours=45  pub6.213=45
positionally identical after normalisation: 44 / 45
cell 29 differs:  insert  pub[2090:2094] = '*1.3'
```

The entire functional difference is:

```python
gs = float(np.clip(np.nanstd(kn.GR.fillna(0).values - tw_at_k), 10., 60.))          # ours
gs = float(np.clip(np.nanstd(kn.GR.fillna(0).values - tw_at_k), 10., 60.)) * 1.3    # theirs
```

`gs` is the GR noise sigma in the PF likelihood (`d = (gr − expected) / gs`). Multiplying it widens the
assumed measurement noise and flattens the likelihood — a **shrinkage/regularisation** change, which is
the class Rule #1 records as transferring. That is why it earned a measurement rather than dismissal.

Note this corrects an intermediate hypothesis of mine: an earlier constant-diff appeared to show a
`SUBMISSION_PROFILE = contact_gated_anchor` difference. That diff had concatenated **markdown** with code.
In code all three notebooks run `'vp_balanced_modelpkg_005'`, and the upstream comment block explicitly
records that `contact_gated_anchor*` are *"diagnostic ablations … [that] have underperformed"*. No kernel
was built on that false lead.

### Measured honestly, on our own PF

Our honest PF (`scripts/pf_honest_forward.py:22`) contains the identical sigma line, so the knob was
measured on train wells with truth rather than trusted from an advertised 3-well number. A backwards-
compatible `_GS_MULT` knob was added (default **1.0**, reproducing prior behaviour exactly). Protocol:
splits **by well**, 60 wells, multiplier chosen **nested** (selected on one half, scored on the disjoint
half, both ways).

```
multiplier  pooled RMSE    vs mult=1.0
1               14.2655         0.0000
1.5             11.9142        +2.3513
2               12.1177        +2.1478
2.5             15.3070        -1.0414
3               17.5072        -3.2417
```

The first grid stopped at 1.5 and both folds picked the edge, so the grid was extended — **1.5 is a
genuine interior optimum**, not an edge artifact.

```
NESTED (picks [1.5, 1.5])
  nested selected 11.9142   vs mult=1.0 14.2655   gain +2.3513
  3-WELL bootstrap: 5th -4.1145  50th +0.1954  95th +7.9324  P(gain>0) 0.5325
```

### Verdict on Find A — fails the gate

| gate condition | required | observed | verdict |
|---|---|---|---|
| nested gain positive | > 0 | **+2.3513** | PASS |
| 3-well bootstrap 5th pct | > 0 | **−4.1145** | **FAIL** |

And the win is **tail-driven**: at 1.5 it helps only **41.7%** of wells while the mean per-well gain is
+1.0052 — a large pooled number carried by a minority of wells. That is the exact signature the ledger
records before the `54878409` public regression (*"the pooled gain is an asymmetric tail, not a broad
shift"*). **No frontier run, no submission.**

The effect is nonetheless real and large at the pooled level, and it is the transferable *class*. What it
is not, on this evidence, is safe at the scale the competition scores.

## 4. Find B — the 6.520 kernel is a per-well constant fitted to the public wells

Its own embedded constants give it away:

```
_GS_PUBLIC_SCORE        = 6.568        <- its base, i.e. our 6.563 family
_EX_EXPECTED_WELL       = '00e12e8b'
_EX_EXTRA_SHIFT         = 0.522
_EX_EXPECTED_TOTAL_SHIFT= 2.522        <- the standard 2.00 hedge cap + 0.522
```

So 6.520 = base 6.568 plus a **hand-tuned +0.522 ft shift applied to one specific well**. This is a fitted
per-well constant tuned against the 3 public wells — the hard-selection pattern the ledger has closed
repeatedly. **Not adopted, and not queued.**

### It does yield a pre-registered reading for `55064411`

`00e12e8b` is precisely the well Q14 analysed: the bimodal hedge applies +2.0 ft there, and our local
measurement found that well's residual was *already* unbiased (−0.19 ft), so the hedge manufactures
+1.81 ft of bias. An independent public author has now found that pushing that same well **further up**
(+0.522) *improves the public score*.

Both facts are consistent under one explanation: **the hedge is tuned to the 3 public wells, not to a
general error.** Pre-registering the reading before `55064411` (hedge-OFF, still PENDING) lands:

- if `55064411` scores **materially worse than 6.563** — that is the *expected* outcome under this
  explanation, and it is evidence the hedge is a public-well-specific fit rather than a general
  correction. It would **strengthen**, not weaken, the case for hedge-OFF on the novel-well objective;
- if it scores **at or below 6.563**, the hedge was not load-bearing on public either, and Q14's local
  reasoning transfers directly.

Recorded now so the interpretation is not chosen after seeing the number.

## 5. Queued follow-ups (Q19 allows 1–3)

1. **`q36_gr_sigma_in_blend_oof`** — the standalone conservative PF is only a 0.5-weight component of the
   honest line. Rule #1 says averaging stabilises; the tail-driven failure above may be damped inside the
   DWT+PF blend. Test `_GS_MULT` ∈ {1.0, 1.3, 1.5} inside the **blend** OOF over the full 760 wells,
   nested, with the 3-well gate. Evidence: +2.35 nested pooled on the standalone PF, interior optimum at
   1.5. This is a **slot-2 (fully-owned) improvement path**, which is where our only OOF-validated
   candidate lives.
2. **`q37_frontier_gr_sigma_public_repro`** — only if (1) passes its 3-well gate: one-token `*1.3`
   frontier kernel reproducing the public 6.213 operating point exactly, smoke first. Held behind (1)
   deliberately: on current evidence it would be spending a slot on a tail-driven change.

Not queued: the 6.520 hand-fit (closed above); `contact_gated_anchor` (upstream records it as
underperforming, and it is not what the 6.213 kernel runs).

## 6. Rules basis

Only public Kaggle notebooks were read, via the Kaggle API, and **no third-party code was executed and no
external dataset was added**. The measured change is one arithmetic token re-implemented in our own
`pf_honest_forward.py` behind a default-1.0 flag. This is the same class of action already accepted for
the public Kaiwalya notebook our `54896975`/`54968060` family derives from, and consistent with the N6
constraint (methods only).

## 7. Negative results and limits

- The 6.213 and 6.520 figures are **advertised by their authors** in kernel titles; neither was
  independently verified, and neither can be — they are other accounts' submissions.
- The local measurement is on the **standalone conservative PF** (500 particles, single seed), whose
  baseline here is 14.27 on 60 wells — far from the deployed 8.86, because it excludes the DWT blend and
  the structural field. The multiplier's effect inside the full pipeline is **not** established by this,
  which is exactly why follow-up (1) is queued rather than a kernel being built.
- Single seed per well: PF run-to-run variance is not separated from the multiplier effect here.
- 60 wells, not 760. The nested split is 30/30.

## 8. Live-refresh notes

`55064411` still PENDING (~6 h). No private-score visibility. Quota 0/5 used, 5 remaining. No Kaggle
kernel launched by this task; no local GPU. `origin/main` at `a589fa8` (audited in §2).

## 9. Next

`q20_usage_aware_queue_builder`, then the two follow-ups queued in §5.
`q15_frontier_dependency_replacement` remains blocked on `55064411`'s in-flight kernel re-run.
