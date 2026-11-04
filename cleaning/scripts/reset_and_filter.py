"""
movies/cleaning/scripts/reset_and_filter.py

Resets all exclude flags in raw.csv then flags year >= 1990.

Usage:  python cleaning/scripts/reset_and_filter.py
"""

import csv
import os
import re

IN_FILE  = os.path.join('cleaning', 'raw.csv')
TMP_FILE = os.path.join('cleaning', 'raw_tmp.csv')

YEAR_RE = re.compile(r'\b(1[89]\d{2}|200\d|201\d|202\d)\b')

def _get_year(row):
    year = row.get('year', '')
    try:
        return int(float(year)) if year else None
    except (ValueError, TypeError):
        return None

def _extract_year(title):
    match = YEAR_RE.search(title or '')
    return int(match.group(1)) if match else None

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

flagged = 0
for row in rows:
    # Reset
    row['exclude']        = ''
    row['exclude_reason'] = ''

    year = _get_year(row) or _extract_year(row.get('title', ''))

    if year and year >= 1990:
        row['exclude']        = 'true'
        row['exclude_reason'] = f'year {year} >= 1990'
        flagged += 1

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, IN_FILE)

surviving = len([r for r in rows if r.get('exclude') != 'true'])
print(f'Total rows:  {len(rows):,}')
print(f'Flagged:     {flagged:,}')
print(f'Surviving:   {surviving:,}')
