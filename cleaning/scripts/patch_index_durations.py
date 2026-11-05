"""
cleaning/scripts/patch_index_durations.py

Patches duration_sec in data/index.json using values from cleaning/updated-raw.csv.
Matches by film_id. Overwrites whatever is in index.json with the DynamoDB value.

Usage: python cleaning/scripts/patch_index_durations.py
"""

import csv, json, os

RAW_FILE   = os.path.join('cleaning', 'updated-raw.csv')
INDEX_FILE = os.path.join('data', 'index.json')

# Build duration lookup from updated-raw.csv
durations = {}
with open(RAW_FILE, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        d = r.get('duration_sec', '').strip()
        if d:
            try:
                durations[r['film_id']] = int(float(d))
            except: pass

print(f'Duration lookup built: {len(durations):,} entries')

# Patch index.json
with open(INDEX_FILE, encoding='utf-8') as f:
    catalog = json.load(f)

patched = 0
cleared = 0
for item in catalog:
    fid = item.get('film_id')
    if fid in durations:
        item['duration_sec'] = durations[fid]
        patched += 1
    elif 'duration_sec' in item:
        del item['duration_sec']
        cleared += 1

with open(INDEX_FILE, 'w', encoding='utf-8') as f:
    json.dump(catalog, f, separators=(',', ':'), ensure_ascii=False)

size_kb = os.path.getsize(INDEX_FILE) / 1024
print(f'Patched:   {patched:,}')
print(f'Cleared:   {cleared:,} (no duration in DynamoDB)')
print(f'File size: {size_kb:,.0f} KB ({size_kb/1024:.1f} MB)')
print(f'Written:   {INDEX_FILE}')
