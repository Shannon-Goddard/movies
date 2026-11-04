import csv, os, sys

sys.stdout.reconfigure(encoding='utf-8')

IN_FILE = os.path.join('cleaning', 'other_ia_meta.csv')

with open(IN_FILE, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

has_desc = sum(1 for r in rows if r.get('description','').strip())
has_subj = sum(1 for r in rows if r.get('subjects','').strip())
empty    = sum(1 for r in rows if not r.get('description','').strip() and not r.get('subjects','').strip())

print(f'Total:           {len(rows):,}')
print(f'Has description: {has_desc:,}')
print(f'Has subjects:    {has_subj:,}')
print(f'Empty:           {empty:,}')
print()
print('Sample subjects (first 20 non-empty):')
shown = 0
for r in rows:
    if r.get('subjects','').strip():
        print(f"  [{r['type']}] {r['subjects'][:100]}")
        shown += 1
        if shown >= 20:
            break
