"""
movies/cleaning/scripts/export_review_csv.py

Exports only surviving rows (exclude != true) from raw.csv to review.csv.

Usage:  python cleaning/scripts/export_review_csv.py
Output: cleaning/review.csv
"""

import csv
import os

IN_FILE  = os.path.join('cleaning', 'raw.csv')
OUT_FILE = os.path.join('cleaning', 'review.csv')

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = [r for r in reader if r.get('exclude') != 'true']

with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

print(f'Surviving rows: {len(rows):,}')
print(f'Written to {OUT_FILE}')
