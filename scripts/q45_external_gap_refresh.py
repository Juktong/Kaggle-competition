"""Q45 — external leaderboard / public-kernel gap refresh.

Q19 (2026-07-29, early) enumerated 798 distinct public kernels for this competition, found the published
pool clustering at 7.06-8.86, and found EXACTLY TWO advertising better than our 6.563:

    leonidzaporozhets/new-strategy-score-6-213          6.213
    my0705/rogii-stacked-ensemble-highscoring-6-520      6.520

and resolved both: the first is our own base plus the single token `*1.3` on the GR sigma (measured here on
760 wells by Q36 -> fails the 3-well gate), the second is a hand-fitted +0.522 ft shift on one public well.

This script refreshes that snapshot cheaply and mechanically:

  1. leaderboard: leader, our score/rank, and the 200th-place score (the API caps a page at 200 rows);
  2. every public kernel for the competition, enumerated by RECENCY, with its last-run timestamp;
  3. advertised scores parsed out of titles/slugs, so anything claiming <= 6.5 is surfaced whether or not
     Q19 saw it;
  4. an explicit NEW-SINCE-Q19 set, by comparing against the two refs Q19 resolved and by timestamp.

Nothing here submits or runs a kernel. Output is a JSON blob plus a printed summary; the code-lineage diff
for any genuinely new candidate is done in a second pass (q45_lineage_diff.py) so that pulling sources is
only paid for the kernels that clear this filter.

Env: PAGES (max pages of 100), SINCE (ISO date for the "new" set).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

from kaggle.api.kaggle_api_extended import KaggleApi

COMP = "rogii-wellbore-geology-prediction"
PAGES = int(os.environ.get('PAGES', '40'))
SINCE = os.environ.get('SINCE', '2026-07-26')
OUT = os.environ.get('OUT', 'reports/logs/q45_kernel_snapshot_2026-07-30.json')

# what Q19 already resolved; anything else advertising <= 6.5 is genuinely new
Q19_RESOLVED = {
    'leonidzaporozhets/new-strategy-score-6-213': 'our base + GR-sigma *1.3 (Q36: fails 3-well gate)',
    'my0705/rogii-stacked-ensemble-highscoring-6-520': 'hand-fitted +0.522 ft shift on one public well',
}
OUR_BEST = 6.563

SCORE_RE = re.compile(r'(?<![0-9])([4-9])[-_. ]?(\d{3})(?![0-9])')


def advertised(text):
    """Parse an advertised LB score out of a title/slug: 6-213, 6.213, 6_213, 'score 6 213'."""
    out = []
    for m in SCORE_RE.finditer(text):
        v = float('%s.%s' % (m.group(1), m.group(2)))
        if 4.0 <= v <= 9.999:
            out.append(v)
    return min(out) if out else None


def main():
    api = KaggleApi()
    api.authenticate()

    # ---------- 1. leaderboard ----------
    print('=== 1. LEADERBOARD REFRESH (%s UTC) ===' % datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'),
          flush=True)
    lb = api.competition_leaderboard_view(COMP, page_size=200) or []
    rows = []
    for i, e in enumerate(lb):
        rows.append({'rank': i + 1,
                     'team': getattr(e, 'team_name', None),
                     'score': float(getattr(e, 'score', 'nan')),
                     'date': str(getattr(e, 'submission_date', ''))[:19]})
    print('fetched %d leaderboard rows (API caps a page at 200)' % len(rows))
    for r in rows[:10]:
        print('  %3d  %-40s %8.3f  %s' % (r['rank'], (r['team'] or '')[:40], r['score'], r['date']))
    if rows:
        print('  ...')
        print('  %3d  %-40s %8.3f   <- last fetched row' % (rows[-1]['rank'], (rows[-1]['team'] or '')[:40],
                                                            rows[-1]['score']))
        worse = [r for r in rows if r['score'] > OUR_BEST]
        print('\n  leader %.3f | rows worse than our %.3f: %d of %d'
              % (rows[0]['score'], OUR_BEST, len(worse), len(rows)))
        if worse:
            print('  first row worse than us: rank %d at %.3f' % (worse[0]['rank'], worse[0]['score']))

    # ---------- 2. kernels by recency ----------
    print('\n=== 2. PUBLIC KERNELS, ENUMERATED BY RECENCY ===', flush=True)
    seen, kern = set(), []
    for sort_by in ('dateRun', 'dateCreated'):
        for page in range(1, PAGES + 1):
            try:
                batch = api.kernels_list(competition=COMP, page=page, page_size=100, sort_by=sort_by) or []
            except Exception as exc:                      # noqa: BLE001 - record, do not abort the round
                print('  page %d (%s) failed: %s' % (page, sort_by, exc))
                break
            if not batch:
                break
            for k in batch:
                ref = getattr(k, 'ref', None)
                if not ref or ref in seen:
                    continue
                seen.add(ref)
                title = getattr(k, 'title', '') or ''
                kern.append({
                    'ref': ref,
                    'title': title,
                    'last_run': str(getattr(k, 'last_run_time', ''))[:19],
                    'votes': int(getattr(k, 'total_votes', 0) or 0),
                    # parse the SLUG ONLY, never the username: `sans6262q/...` would otherwise read as 6.262
                    'adv': advertised(ref.split('/', 1)[-1] + ' ' + title),
                })
        print('  after sort_by=%-12s distinct kernels = %d' % (sort_by, len(kern)), flush=True)

    kern.sort(key=lambda r: r['last_run'], reverse=True)
    print('\n  most recent 15 by last_run:')
    for r in kern[:15]:
        print('    %-19s %-6s %-58s %s' % (r['last_run'], ('%.3f' % r['adv']) if r['adv'] else '-',
                                           r['ref'][:58], 'votes %d' % r['votes']))

    # ---------- 3. advertised <= 6.5, and the distribution ----------
    print('\n=== 3. ADVERTISED SCORES ===', flush=True)
    adv = sorted([r for r in kern if r['adv'] is not None], key=lambda r: r['adv'])
    print('  kernels with a parseable advertised score: %d of %d' % (len(adv), len(kern)))
    print('  best 20 advertised:')
    for r in adv[:20]:
        tag = ''
        if r['ref'] in Q19_RESOLVED:
            tag = '  <- Q19 resolved: ' + Q19_RESOLVED[r['ref']]
        elif r['adv'] < OUR_BEST:
            tag = '  <- BETTER THAN OUR %.3f, NOT SEEN BY Q19' % OUR_BEST
        print('    %6.3f  %-58s %s%s' % (r['adv'], r['ref'][:58], r['last_run'], tag))

    cand = [r for r in adv if r['adv'] <= 6.5 and r['ref'] not in Q19_RESOLVED]
    print('\n  advertising <= 6.5 and NOT already resolved by Q19: %d' % len(cand))
    for r in cand:
        print('    %6.3f  %s  (%s)' % (r['adv'], r['ref'], r['last_run']))

    # ---------- 4. new since SINCE ----------
    print('\n=== 4. KERNELS RUN SINCE %s ===' % SINCE, flush=True)
    recent = [r for r in kern if r['last_run'] >= SINCE]
    print('  %d kernels last-run on/after %s' % (len(recent), SINCE))
    for r in recent[:40]:
        print('    %-19s %-6s %s' % (r['last_run'], ('%.3f' % r['adv']) if r['adv'] else '-', r['ref'][:70]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as fh:
        json.dump({'fetched_utc': datetime.now(timezone.utc).isoformat(),
                   'leaderboard': rows, 'kernels': kern}, fh, indent=1)
    print('\nwrote %s (%d kernels, %d lb rows)' % (OUT, len(kern), len(rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
