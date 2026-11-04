"""
movies/cleaning/scripts/junk_removal.py

Flags items below duration thresholds as exclude: true in raw.csv.
Also flags items with no duration (174 known) for manual review.
Also excludes entire collections: educational_films, newsandpublicaffairs.

Thresholds:
  short   < 180s  (3 min)
  cartoon < 300s  (5 min)
  all else < 600s (10 min)

Usage:
  python cleaning/scripts/junk_removal.py
Input:  cleaning/raw.csv
Output: cleaning/raw.csv (updated in place, adds/updates exclude + exclude_reason columns)
"""

import csv
import os

IN_FILE  = os.path.join('cleaning', 'raw.csv')
TMP_FILE = os.path.join('cleaning', 'raw_tmp.csv')

EXCLUDE_COLLECTIONS = {'educational_films', 'newsandpublicaffairs'}

THRESHOLDS = {
    'short':   180,
    'cartoon': 300,
}
DEFAULT_THRESHOLD = 600

def _threshold(type_val):
    return THRESHOLDS.get(str(type_val).lower(), DEFAULT_THRESHOLD)

def _should_exclude(row):
    if row.get('collection') in EXCLUDE_COLLECTIONS:
        return True, f'excluded collection: {row["collection"]}'

    duration = row.get('duration_sec', '')
    type_val  = row.get('type', '')

    if duration == '' or duration is None:
        return True, 'no duration'

    try:
        secs = int(float(duration))
    except (ValueError, TypeError):
        return True, 'invalid duration'

    limit = _threshold(type_val)
    if secs < limit:
        return True, f'duration {secs}s under {limit}s threshold for type={type_val or "unknown"}'

    return False, ''

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader    = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows      = list(reader)

if 'exclude' not in fieldnames:
    fieldnames = fieldnames + ['exclude', 'exclude_reason']

flagged = 0
for row in rows:
    if row.get('exclude') == 'true':
        continue  # already flagged, don't overwrite
    exclude, reason = _should_exclude(row)
    if exclude:
        row['exclude']        = 'true'
        row['exclude_reason'] = reason
        flagged += 1
    else:
        row.setdefault('exclude', '')
        row.setdefault('exclude_reason', '')

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

os.replace(TMP_FILE, IN_FILE)

total    = len(rows)
kept     = total - flagged
print(f'Total rows:  {total:,}')
print(f'Flagged:     {flagged:,}')
print(f'Kept:        {kept:,}')
print(f'Survival:    {kept/total*100:.1f}%')
print(f'Updated:     {IN_FILE}')
