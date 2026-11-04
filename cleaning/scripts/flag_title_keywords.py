"""
movies/cleaning/scripts/flag_title_keywords.py

Flags rows whose titles contain junk keywords.
Updates raw.csv in place.

Usage:  python cleaning/scripts/flag_title_keywords.py
"""

import csv
import os

IN_FILE  = os.path.join('cleaning', 'raw.csv')
TMP_FILE = os.path.join('cleaning', 'raw_tmp.csv')

JUNK_KEYWORDS = ['trailer']

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

flagged = 0
for row in rows:
    if row.get('exclude') == 'true':
        continue
    title = row.get('title', '').lower()
    for kw in JUNK_KEYWORDS:
        if kw in title:
            row['exclude']        = 'true'
            row['exclude_reason'] = f'title keyword: {kw}'
            flagged += 1
            break

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, IN_FILE)

surviving = len([r for r in rows if r.get('exclude') != 'true'])
print(f'Flagged:   {flagged:,}')
print(f'Surviving: {surviving:,}')
