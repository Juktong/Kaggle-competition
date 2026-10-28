"""Q45 second pass — pull the candidate kernels and resolve each to its code lineage.

Only kernels that cleared the Q45 filter (advertised <= 6.5 and not already resolved by Q19, or a
materially-different architecture in the recency window) are pulled, so source-pull cost is paid only where
it can change a decision.

Method is the same as Q39's, which is what makes the results comparable: every kernel is normalised
(comments stripped, whitespace collapsed) and diffed CELL BY CELL against the pristine public base
`kaggle_kernel_kaiwalya_public_tvt_6626_repro/rogii-public-tvt-solution.ipynb` (45 code cells) — the family
our 54922806 / 54968060 / 55064411 all derive from. A kernel that positionally matches the base except for a
handful of tokens is the same method; one that does not match at all is a genuinely different architecture
and is characterised by its imports/model calls instead.

Env: REFS (comma-separated kernel refs), DEST (pull directory).
"""
import difflib
import json
import os
import re
import sys

from kaggle.api.kaggle_api_extended import KaggleApi

BASE = 'kaggle_kernel_kaiwalya_public_tvt_6626_repro/rogii-public-tvt-solution.ipynb'
DEST = os.environ.get('DEST', 'reports/logs/q45_pulled')
REFS = [r for r in os.environ.get('REFS', '').split(',') if r.strip()]

ARCH_TOKENS = ['CatBoost', 'LGBMRegressor', 'lightgbm', 'xgboost', 'XGB', 'torch', 'keras',
               'HistGradientBoosting', 'RandomForest', 'run_particle_filter', 'hmmlearn', 'viterbi',
               'MultiheadAttention', 'Transformer', 'dtw', 'wavelet', 'pywt', 'Ridge', 'KNeighbors']


def code_cells(path):
    nb = json.load(open(path))
    return [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']


def norm(src):
    """Strip comments and collapse whitespace so formatting differences do not register as changes."""
    out = []
    for line in src.split('\n'):
        line = re.sub(r'(?<!["\'])#.*$', '', line)
        line = re.sub(r'\s+', '', line)
        if line:
            out.append(line)
    return ''.join(out)


def token_diff(a, b, ctx=45):
    """Report the minimal edits between two normalised cells as concrete inserted/deleted text."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        ops.append('%-7s base[%d:%d]=%r  ->  new[%d:%d]=%r'
                   % (tag, i1, i2, a[i1:i2][:ctx], j1, j2, b[j1:j2][:ctx]))
    return ops


def main():
    api = KaggleApi()
    api.authenticate()
    base = [norm(c) for c in code_cells(BASE)]
    print('pristine base: %s  (%d code cells)\n' % (BASE, len(base)), flush=True)

    for ref in REFS:
        slug = ref.replace('/', '__')
        d = os.path.join(DEST, slug)
        os.makedirs(d, exist_ok=True)
        print('=' * 100)
        print('KERNEL %s' % ref, flush=True)
        try:
            api.kernels_pull(ref, path=d, metadata=True)
        except Exception as exc:                          # noqa: BLE001 - inaccessible is a finding, not a stop
            print('  PULL FAILED: %s' % exc)
            continue
        nbs = [f for f in os.listdir(d) if f.endswith('.ipynb')]
        pys = [f for f in os.listdir(d) if f.endswith('.py')]
        meta = os.path.join(d, 'kernel-metadata.json')
        if os.path.exists(meta):
            m = json.load(open(meta))
            print('  title %r | language %s | type %s' % (m.get('title'), m.get('language'), m.get('kernel_type')))
            print('  dataset_sources (%d): %s' % (len(m.get('dataset_sources') or []),
                                                  ', '.join(m.get('dataset_sources') or []) or '-'))
            print('  kernel_sources  (%d): %s' % (len(m.get('kernel_sources') or []),
                                                 ', '.join(m.get('kernel_sources') or []) or '-'))
        if not nbs:
            if pys:
                src = open(os.path.join(d, pys[0])).read()
                cells = [src]
                print('  (script kernel, %d chars)' % len(src))
            else:
                print('  NO SOURCE FILE PULLED -- treat as inaccessible')
                continue
        else:
            cells = code_cells(os.path.join(d, nbs[0]))
        new = [norm(c) for c in cells]
        joined = ''.join(cells)
        print('  code cells: base=%d  this=%d' % (len(base), len(new)))
        hits = [t for t in ARCH_TOKENS if t.lower() in joined.lower()]
        print('  architecture tokens present: %s' % (', '.join(hits) or '(none of the probe set)'))

        if len(new) == len(base):
            diff_cells = [i for i in range(len(base)) if base[i] != new[i]]
            print('  positionally identical after normalisation: %d / %d' % (len(base) - len(diff_cells), len(base)))
            print('  differing cells: %s' % (diff_cells or 'NONE -- pristine'))
            for i in diff_cells:
                print('  --- cell %d ---' % i)
                for op in token_diff(base[i], new[i])[:8]:
                    print('      %s' % op)
        else:
            # not the same cell count: measure how much of the base survives at all
            bset = set(base)
            shared = sum(1 for c in new if c in bset)
            print('  cell count differs -> lineage measured by SHARED NORMALISED CELLS: %d of this kernel\'s '
                  '%d cells appear verbatim in the base (%.0f%%)' % (shared, len(new), 100 * shared / max(len(new), 1)))
            if shared / max(len(new), 1) < 0.5:
                print('  => NOT the Kaiwalya family. Characterising by content instead:')
                for t in hits:
                    n = len(re.findall(re.escape(t), joined, flags=re.I))
                    print('      %-24s x%d' % (t, n))
                print('      total source chars %d' % len(joined))
    return 0


if __name__ == '__main__':
    sys.exit(main())
