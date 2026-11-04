"""
cleaning/scripts/pass5_other_cleanup.py

Three passes on raw.csv:
  1. Flag numeric-only titles (exclude = true, reason = numeric title)
  2. Deduplicate near-title matches — keep longest duration, flag the rest
  3. Backfill year from title for surviving rows missing year

Usage: python cleaning/scripts/pass5_other_cleanup.py
"""

import csv, os, re
from collections import defaultdict

IN_FILE  = os.path.join('cleaning', 'raw.csv')
TMP_FILE = os.path.join('cleaning', 'raw_tmp.csv')

YEAR_RE    = re.compile(r'\b(1[0-9]\d{2})\b')
NUMERIC_RE = re.compile(r'^\s*[\d\s\-_.,]+\s*$')

def _norm(title):
    t = re.sub(r'\(.*?\)|\[.*?\]', '', title or '').lower()
    return re.sub(r'\s+', ' ', t).strip()

def _duration(row):
    try:
        return float(row.get('duration_sec') or 0)
    except (ValueError, TypeError):
        return 0.0

def _extract_year(title):
    m = YEAR_RE.search(title or '')
    if m:
        y = int(m.group(1))
        return y if y < 1990 else None
    return None

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

# ── Undo any previous near-duplicate flags before re-running ────────────────
for row in rows:
    if row.get('exclude_reason') == 'near-duplicate title':
        row['exclude']        = ''
        row['exclude_reason'] = ''

# ── Pass 1: flag numeric-only titles ─────────────────────────────────────────
p1 = 0
for row in rows:
    if row.get('exclude') == 'true':
        continue
    if NUMERIC_RE.match(row.get('title', '')):
        row['exclude']        = 'true'
        row['exclude_reason'] = 'numeric title'
        p1 += 1

# ── Pass 2: near-duplicate dedup (surviving rows only) ───────────────────────
# Strategy: bucket by exact norm title — true duplicates share the same
# normalised title after stripping parens/brackets/year suffixes.
from collections import defaultdict

surviving = [r for r in rows if r.get('exclude') != 'true']

ARTICLES = {'the', 'a', 'an'}

def _first3(title):
    words = _norm(title).split()
    # skip leading article so 'the x y z' buckets on 'x y z' not 'the x y'
    if words and words[0] in ARTICLES:
        words = words[1:]
    return ' '.join(words[:3]) if len(words) >= 3 else None

# Bucket by first 3 words (article-skipped), then within each bucket
# only flag as dupe if one norm title is a prefix substring of the other.
buckets = defaultdict(list)
for r in surviving:
    key = _first3(r.get('title', ''))
    if key:
        buckets[key].append(r)

p2 = 0
for key, group in buckets.items():
    if len(group) < 2:
        continue
    # within bucket, find pairs where one norm title starts with the other
    norms = [(_norm(r.get('title', '')), r) for r in group]
    flagged_in_group = set()
    for i in range(len(norms)):
        ni, ri = norms[i]
        if ri['film_id'] in flagged_in_group:
            continue
        dupes = [ri]
        for j in range(len(norms)):
            if i == j:
                continue
            nj, rj = norms[j]
            if rj['film_id'] in flagged_in_group:
                continue
            # one must be a prefix of the other (with word boundary)
            shorter, longer = (ni, nj) if len(ni) <= len(nj) else (nj, ni)
            if longer.startswith(shorter) and (len(longer) == len(shorter) or longer[len(shorter)] in (' ', '-', '(', ',', ':')):
                dupes.append(rj)
        if len(dupes) > 1:
            dupes.sort(key=_duration, reverse=True)
            for dup in dupes[1:]:
                dup['exclude']        = 'true'
                dup['exclude_reason'] = 'near-duplicate title'
                flagged_in_group.add(dup['film_id'])
                p2 += 1

# ── Pass 3: backfill year from title ─────────────────────────────────────────
p3 = 0
for row in rows:
    if row.get('exclude') == 'true':
        continue
    if not row.get('year'):
        y = _extract_year(row.get('title', ''))
        if y:
            row['year'] = str(y)
            p3 += 1

# ── Write ─────────────────────────────────────────────────────────────────────
with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, IN_FILE)

surviving_final = sum(1 for r in rows if r.get('exclude') != 'true')
print(f'Pass 1 — numeric titles flagged:    {p1:,}')
print(f'Pass 2 — near-duplicates flagged:   {p2:,}')
print(f'Pass 3 — years backfilled:          {p3:,}')
print(f'Surviving:                          {surviving_final:,}')
print(f'Updated: {IN_FILE}')
