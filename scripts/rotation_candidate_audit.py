"""Rotation pipeline — unified candidate audit (sanity + diff + score table).

One command to audit any candidate submission produced by the rotation pipeline:
  - HARD sanity: 14151 rows, columns [id,tvt], id set+order == sample/reference, finite, no dups
  - distribution: min/mean/max/std, per-well stats
  - trajectory sanity: per-well slope / jump statistics (catches physically implausible paths)
  - diff table vs every reference output available locally (54922806-family, 54968060, 54844628, ...)
  - sha256 of the submission
  - homogeneity flag: refuses to recommend submitting a near-duplicate of an existing submission

Usage:
  python3 scripts/rotation_candidate_audit.py --candidate <path/to/submission.csv> [--label NAME]
  python3 scripts/rotation_candidate_audit.py --list-refs

Reference outputs are discovered under the shared job dir; each is a real, previously-submitted or
previously-run output so the diff table is against things whose public score we know.
"""
import os, sys, glob, json, hashlib, argparse
import numpy as np
import pandas as pd

SH = '/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp'
TRAIN = '/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii/train'
EXPECT_ROWS = 14151

# label -> (path, known public score or None)
REFERENCES = {
    '54844628_honest':      (f'{SH}/dep_out/submission.csv',        7.891),
    '54968060_overlapOFF':  (f'{SH}/a2full_out/submission.csv',     6.643),
    '6626pkg_fastsmoke':    (f'{SH}/smoke6626_out/submission.csv',  None),   # FAST fidelity, not a submission
}
# near-duplicate threshold: rmse-diff below this vs an existing SUBMITTED output => homogeneous
HOMOGENEITY_RMSE = 0.50


def _sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


def _truth_map():
    """train-copy TVT for the 3 visible test wells (a PROXY; leaderboard truth differs at fine scale)."""
    t = {}
    for w in ['000d7d20', '00bbac68', '00e12e8b']:
        p = f'{TRAIN}/{w}__horizontal_well.csv'
        if not os.path.exists(p):
            continue
        h = pd.read_csv(p)
        toe = h['TVT_input'].isna().values
        for i in np.where(toe)[0]:
            t[f'{w}_{i}'] = h['TVT'].values[i]
    return t


def audit(path, label=None, refs=None):
    label = label or os.path.basename(os.path.dirname(path)) or path
    refs = refs if refs is not None else REFERENCES
    out = {'label': label, 'path': path, 'checks': {}, 'diffs': {}}
    if not os.path.exists(path):
        out['checks']['exists'] = False
        return out
    s = pd.read_csv(path)
    out['sha256_16'] = _sha(path)

    # ---- HARD sanity ----
    c = out['checks']
    c['exists'] = True
    c['columns_ok'] = list(s.columns) == ['id', 'tvt']
    c['rows_ok'] = len(s) == EXPECT_ROWS
    c['no_dup_ids'] = not s['id'].duplicated().any()
    c['finite'] = bool(np.isfinite(s['tvt']).all())

    ref_key = next((k for k in refs if os.path.exists(refs[k][0])), None)
    if ref_key:
        r = pd.read_csv(refs[ref_key][0])
        c['id_set_ok'] = set(s['id']) == set(r['id'])
        c['id_order_ok'] = bool(len(s) == len(r) and (s['id'].values == r['id'].values).all())
    c['HARD_PASS'] = all(c.get(k, False) for k in
                         ['columns_ok', 'rows_ok', 'no_dup_ids', 'finite', 'id_set_ok', 'id_order_ok'])

    # ---- distribution ----
    out['dist'] = dict(min=float(s['tvt'].min()), mean=float(s['tvt'].mean()),
                       max=float(s['tvt'].max()), std=float(s['tvt'].std()))

    # ---- trajectory sanity (per well, along row index) ----
    s['well'] = s['id'].str.rsplit('_', n=1).str[0]
    traj = {}
    for w, g in s.groupby('well'):
        v = g['tvt'].values
        d = np.diff(v)
        traj[w] = dict(n=len(v), span=float(v.max() - v.min()),
                       max_abs_step=float(np.max(np.abs(d))) if len(d) else 0.0,
                       p99_abs_step=float(np.percentile(np.abs(d), 99)) if len(d) else 0.0)
    out['trajectory'] = traj

    # ---- diffs vs references ----
    smap = dict(zip(s['id'], s['tvt']))
    for name, (rp, score) in refs.items():
        if not os.path.exists(rp) or os.path.abspath(rp) == os.path.abspath(path):
            continue
        rr = pd.read_csv(rp)
        rmap = dict(zip(rr['id'], rr['tvt']))
        ids = [k for k in smap if k in rmap]
        if not ids:
            continue
        a = np.array([smap[k] for k in ids]); b = np.array([rmap[k] for k in ids])
        d = a - b
        out['diffs'][name] = dict(
            public_score=score,
            rmse=float(np.sqrt(np.mean(d ** 2))), mean_abs=float(np.mean(np.abs(d))),
            max_abs=float(np.max(np.abs(d))), p95_abs=float(np.percentile(np.abs(d), 95)),
            corr=float(np.corrcoef(a, b)[0, 1]), pct_gt1=float(100 * np.mean(np.abs(d) > 1)))

    # ---- local proxy RMSE vs train-copy TVT (relative comparison only) ----
    t = _truth_map()
    ids = [k for k in smap if k in t]
    if ids:
        e = np.array([smap[k] - t[k] for k in ids])
        out['proxy_rmse_traincopy'] = float(np.sqrt(np.mean(e ** 2)))

    # ---- homogeneity flag vs SUBMITTED references (those with a known score) ----
    hom = [n for n, dd in out['diffs'].items()
           if refs.get(n, (None, None))[1] is not None and dd['rmse'] < HOMOGENEITY_RMSE]
    out['homogeneous_with'] = hom
    out['submit_allowed_by_homogeneity'] = len(hom) == 0
    return out


def render(o):
    L = []
    L.append(f"=== candidate audit: {o['label']} ===")
    L.append(f"  path   : {o['path']}")
    if not o['checks'].get('exists'):
        L.append("  MISSING FILE"); return "\n".join(L)
    L.append(f"  sha256 : {o.get('sha256_16')}")
    c = o['checks']
    L.append(f"  HARD   : {'PASS' if c.get('HARD_PASS') else 'FAIL'}  " +
              " ".join(f"{k}={c.get(k)}" for k in
                       ['columns_ok', 'rows_ok', 'no_dup_ids', 'finite', 'id_set_ok', 'id_order_ok']))
    d = o['dist']
    L.append(f"  dist   : min={d['min']:.1f} mean={d['mean']:.1f} max={d['max']:.1f} std={d['std']:.1f}")
    for w, t in o.get('trajectory', {}).items():
        L.append(f"    traj {w}: n={t['n']} span={t['span']:.1f} max_step={t['max_abs_step']:.2f} p99_step={t['p99_abs_step']:.2f}")
    if 'proxy_rmse_traincopy' in o:
        L.append(f"  proxy  : RMSE vs train-copy TVT = {o['proxy_rmse_traincopy']:.3f} (relative only)")
    if o['diffs']:
        L.append(f"  {'vs reference':22s} {'public':>7} {'rmse':>8} {'max|d|':>8} {'corr':>8} {'%d>1':>6}")
        for n, dd in sorted(o['diffs'].items(), key=lambda kv: kv[1]['rmse']):
            ps = f"{dd['public_score']:.3f}" if dd['public_score'] is not None else "  n/a"
            L.append(f"  {n:22s} {ps:>7} {dd['rmse']:>8.3f} {dd['max_abs']:>8.2f} {dd['corr']:>8.5f} {dd['pct_gt1']:>5.1f}%")
    if o['homogeneous_with']:
        L.append(f"  HOMOGENEITY: near-duplicate of {o['homogeneous_with']} (rmse < {HOMOGENEITY_RMSE}) -> submit NOT recommended")
    else:
        L.append(f"  HOMOGENEITY: distinct from all scored references -> submit allowed on this axis")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate')
    ap.add_argument('--label')
    ap.add_argument('--json')
    ap.add_argument('--list-refs', action='store_true')
    a = ap.parse_args()
    if a.list_refs:
        for k, (p, s) in REFERENCES.items():
            print(f"  {k:22s} public={s}  exists={os.path.exists(p)}  {p}")
        return
    if not a.candidate:
        raise SystemExit("--candidate required (or --list-refs)")
    o = audit(a.candidate, a.label)
    print(render(o))
    if a.json:
        json.dump(o, open(a.json, 'w'), indent=1)
        print(f"  wrote {a.json}")


if __name__ == '__main__':
    main()
