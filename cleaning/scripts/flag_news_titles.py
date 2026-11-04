"""
movies/cleaning/scripts/flag_news_titles.py

Flags rows whose titles contain known news broadcast keywords.
Updates raw.csv then writes a fresh review.csv.

Usage:  python cleaning/scripts/flag_news_titles.py
"""

import csv
import os

IN_FILE     = os.path.join('cleaning', 'raw.csv')
TMP_FILE    = os.path.join('cleaning', 'raw_tmp.csv')
REVIEW_FILE = os.path.join('cleaning', 'review.csv')

NEWS_KEYWORDS = [
    'bbcnews', 'cspan', 'c-span', 'wrc', 'telesur', 'belarustv', 'aljaz',
    'aljazam', 'wbal', 'wusa', 'cnn', 'cnnw', 'foxnews', 'foxnewsw',
    'msnbc', 'msnbcw', 'bloomberg', 'eyewitness news', 'wjla', 'wmar',
    'wttg', 'wjz', 'wcau', 'espreso', 'skaitv', 'deutsche wochenschau',
    'newsroom', 'wochenschau', 'srp', 'trsb', 'trhs', 'trojanvision',
    'plainville', 'bos news', 'hrv', 'nbc news', 'abc news', 'cbs news',
]

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

flagged = 0
for row in rows:
    if row.get('exclude') == 'true':
        continue
    title = row.get('title', '').lower()
    for kw in NEWS_KEYWORDS:
        if kw in title:
            row['exclude']        = 'true'
            row['exclude_reason'] = f'news keyword: {kw}'
            flagged += 1
            break

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, IN_FILE)

surviving = [r for r in rows if r.get('exclude') != 'true']

with open(REVIEW_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(surviving)

print(f'Flagged:   {flagged:,}')
print(f'Surviving: {len(surviving):,}')
print(f'Written to {REVIEW_FILE}')
