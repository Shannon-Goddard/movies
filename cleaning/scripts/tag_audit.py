"""
movies/cleaning/scripts/tag_audit.py

Audits genre, type, and collection distribution across surviving rows in raw.csv.
Only counts rows where exclude != 'true'.

Usage:
  python cleaning/scripts/tag_audit.py
Output: cleaning/tag_audit.txt
"""

import csv
import os
from collections import Counter

IN_FILE  = os.path.join('cleaning', 'raw.csv')
OUT_FILE = os.path.join('cleaning', 'tag_audit.txt')

genre_counts      = Counter()
type_counts       = Counter()
collection_counts = Counter()
genre_by_type     = {}  # type -> Counter of genres
total = 0

with open(IN_FILE, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row.get('exclude') == 'true':
            continue
        total += 1

        genre      = row.get('genre', '') or 'null'
        type_val   = row.get('type', '') or 'null'
        collection = row.get('collection', '') or 'null'

        genre_counts[genre] += 1
        type_counts[type_val] += 1
        collection_counts[collection] += 1

        if type_val not in genre_by_type:
            genre_by_type[type_val] = Counter()
        genre_by_type[type_val][genre] += 1

lines = []
lines.append(f'Tag Audit — surviving rows only (exclude != true)')
lines.append(f'Total surviving: {total:,}')
lines.append('')

lines.append('=' * 50)
lines.append('GENRE')
lines.append('=' * 50)
for genre, count in genre_counts.most_common():
    lines.append(f'  {genre:<20} {count:>7,}  ({count/total*100:.1f}%)')

lines.append('')
lines.append('=' * 50)
lines.append('TYPE')
lines.append('=' * 50)
for type_val, count in type_counts.most_common():
    lines.append(f'  {type_val:<20} {count:>7,}  ({count/total*100:.1f}%)')

lines.append('')
lines.append('=' * 50)
lines.append('COLLECTION')
lines.append('=' * 50)
for col, count in collection_counts.most_common():
    lines.append(f'  {col:<30} {count:>7,}  ({count/total*100:.1f}%)')

lines.append('')
lines.append('=' * 50)
lines.append('GENRE BREAKDOWN BY TYPE')
lines.append('=' * 50)
for type_val, genres in sorted(genre_by_type.items()):
    lines.append(f'\n  [{type_val}]')
    for genre, count in genres.most_common():
        lines.append(f'    {genre:<20} {count:>7,}')

output = '\n'.join(lines)
print(output)

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write(output)

print(f'\nWritten to {OUT_FILE}')
