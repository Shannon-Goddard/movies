"""
movies/cleaning/scripts/year_cleanup.py

Step 1: For rows missing year, attempt to extract a 4-digit year from the title.
Step 2: Flag any row where year >= 2009 as exclude: true.
Step 3: Export surviving rows to cleaning/review-2.csv.

Usage:  python cleaning/scripts/year_cleanup.py
"""

import csv
import os
import re

IN_FILE     = os.path.join('cleaning', 'raw.csv')
TMP_FILE    = os.path.join('cleaning', 'raw_tmp.csv')
REVIEW_FILE = os.path.join('cleaning', 'review-2.csv')

YEAR_RE = re.compile(r'\b(1[89]\d{2}|200[0-8])\b')  # 1800s-1900s and 2000-2008 only

def _extract_year(title):
    match = YEAR_RE.search(title or '')
    return int(match.group(1)) if match else None

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

extracted = 0
flagged   = 0

for row in rows:
    if row.get('exclude') == 'true':
        continue

    year = row.get('year', '')
    try:
        year = int(float(year)) if year else None
    except (ValueError, TypeError):
        year = None

    # Try extracting from title if missing
    if not year:
        year = _extract_year(row.get('title', ''))
        if year:
            row['year'] = year
            extracted += 1

    # Flag 2009+
    if year and year >= 2009:
        row['exclude']        = 'true'
        row['exclude_reason'] = f'year {year} >= 2009'
        flagged += 1

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, IN_FILE)

surviving = [r for r in rows if r.get('exclude') != 'true']

with open(REVIEW_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(surviving)

print(f'Years extracted from title: {extracted:,}')
print(f'Flagged (year >= 2009):     {flagged:,}')
print(f'Surviving:                  {len(surviving):,}')
print(f'Written to {REVIEW_FILE}')
