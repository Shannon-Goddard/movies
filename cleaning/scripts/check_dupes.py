import csv, os

IN_FILE = os.path.join('cleaning', 'raw.csv')

with open(IN_FILE, newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

dupes = [r for r in rows if r.get('exclude_reason') == 'near-duplicate title']
print(f'Total near-duplicate flagged: {len(dupes):,}\n')

# Print 40 samples spread across the list so we see variety
step = max(1, len(dupes) // 40)
for r in dupes[::step][:40]:
    print(f"  [{r['type']}] {r['title'][:90]}  ({r['duration_sec']}s)")
