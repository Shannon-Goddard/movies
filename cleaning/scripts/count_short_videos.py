import csv, os, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

with open(os.path.join('cleaning', 'raw.csv'), newline='', encoding='utf-8') as f:
    rows = [r for r in csv.DictReader(f) if r.get('exclude') != 'true']

under5 = []
for r in rows:
    try:
        if float(r.get('duration_sec') or 0) < 300:
            under5.append(r)
    except: pass

print(f'Surviving total:     {len(rows):,}')
print(f'Under 5 min (<300s): {len(under5):,}')
print()
by_type = Counter(r['type'] for r in under5)
for t, c in by_type.most_common():
    print(f'  {t}: {c:,}')
