import csv, os

IN_FILE  = os.path.join('cleaning', 'raw.csv')
OUT_FILE = os.path.join('cleaning', 'other.csv')

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader if r.get('exclude') != 'true' and r.get('genre') == 'other']

with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['film_id','title','type','year','collection','source_url'], extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

print(f'other rows: {len(rows):,}')
print(f'Written to {OUT_FILE}')
