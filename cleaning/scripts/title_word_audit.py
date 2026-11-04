"""
movies/cleaning/scripts/title_word_audit.py

Finds the most common words in titles of surviving rows.
Strips common stop words to surface meaningful terms.

Usage:  python cleaning/scripts/title_word_audit.py
Output: cleaning/title_word_audit.txt
"""

import csv
import os
import re
from collections import Counter

IN_FILE  = os.path.join('cleaning', 'raw.csv')
OUT_FILE = os.path.join('cleaning', 'title_word_audit.txt')
TOP_N    = 100

STOP_WORDS = {
    'the', 'a', 'an', 'of', 'in', 'and', 'to', 'is', 'it', 'at', 'on',
    'for', 'with', 'by', 'from', 'as', 'or', 'be', 'this', 'that', 'are',
    'was', 'his', 'her', 'he', 'she', 'they', 'we', 'you', 'i', 'my',
    'no', 'not', 'but', 'so', 'up', 'do', 'if', 'its', 'de', 'la', 'el',
    'les', 'le', 'un', 'une', 'et', 'en', 'du', 'des', 'los', 'las',
    'part', 'vol', 'episode', 'ep', 'chapter', 'ch', 'aka',
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
}

words = Counter()
total = 0

with open(IN_FILE, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row.get('exclude') == 'true':
            continue
        total += 1
        title = row.get('title', '') or ''
        for word in re.findall(r"[a-zA-Z']+", title.lower()):
            if word not in STOP_WORDS and len(word) > 2:
                words[word] += 1

lines = [
    f'Title Word Audit — surviving rows only',
    f'Total surviving: {total:,}',
    f'Top {TOP_N} words',
    '',
    f'  {"Word":<25} {"Count":>7}',
    f'  {"-"*25} {"-"*7}',
]
for word, count in words.most_common(TOP_N):
    lines.append(f'  {word:<25} {count:>7,}')

output = '\n'.join(lines)
print(output)

with open(OUT_FILE, 'w', encoding='utf-8') as f:
    f.write(output)

print(f'\nWritten to {OUT_FILE}')
