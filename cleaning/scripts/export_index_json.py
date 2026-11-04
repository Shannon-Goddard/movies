"""
cleaning/scripts/export_index_json.py

Exports surviving rows from raw.csv to data/index.json.
Only includes fields the frontend needs — keeps the file lean.

Usage: python cleaning/scripts/export_index_json.py
Output: data/index.json
"""

import csv, json, os

IN_FILE  = os.path.join('cleaning', 'raw.csv')
OUT_FILE = os.path.join('data', 'index.json')

FIELDS = [
    'film_id', 'title', 'director', 'year', 'genre', 'type',
    'era', 'era_label', 'color', 'color_label', 'language',
    'duration_sec', 'poster_url', 'stream_url', 'source_url',
]

with open(IN_FILE, newline='', encoding='utf-8') as f:
    rows = [r for r in csv.DictReader(f) if r.get('exclude') != 'true']

out = []
for r in rows:
    item = {k: r[k] for k in FIELDS if r.get(k)}
    # coerce numeric fields
    if 'year' in item:
        try: item['year'] = int(float(item['year']))
        except: del item['year']
    if 'duration_sec' in item:
        try: item['duration_sec'] = int(float(item['duration_sec']))
        except: del item['duration_sec']
    out.append(item)

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(out, f, separators=(',', ':'), ensure_ascii=False)

size_kb = os.path.getsize(OUT_FILE) / 1024
print(f'Rows exported:  {len(out):,}')
print(f'File size:      {size_kb:,.0f} KB ({size_kb/1024:.1f} MB)')
print(f'Written to:     {OUT_FILE}')
