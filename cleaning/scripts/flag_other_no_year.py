"""
cleaning/scripts/flag_other_no_year.py

Flags surviving other-genre rows with no year as exclude = true.
Rows with a year stay — they participate in type/era/color filters.

Usage: python cleaning/scripts/flag_other_no_year.py
"""

import csv, os

RAW_FILE = os.path.join('cleaning', 'raw.csv')
TMP_FILE = os.path.join('cleaning', 'raw_tmp.csv')

with open(RAW_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

flagged = 0
for row in rows:
    if row.get('exclude') == 'true' or row.get('genre') != 'other':
        continue
    if not row.get('year', '').strip():
        row['exclude']        = 'true'
        row['exclude_reason'] = 'other genre, no year'
        flagged += 1

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, RAW_FILE)

surviving = sum(1 for r in rows if r.get('exclude') != 'true')
print(f'Flagged (other, no year): {flagged:,}')
print(f'Surviving:                {surviving:,}')
print(f'Updated:                  {RAW_FILE}')
