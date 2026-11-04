"""
movies/cleaning/scripts/remap_genres.py

Pass 4 — Genre, type, and language remap on surviving rows in raw.csv.

Rules:
  Collection-based genre remaps (guaranteed correct):
    westerns              → genre: western
    film_noir             → genre: crime
    horror_and_suspense   → genre: horror
    animationandcartoons  → genre: animation
    concert type          → genre: musical

  Language detection (title-based):
    Non-Latin characters or known foreign keywords → language: foreign
    Everything else                                → language: en

Updates raw.csv in place. Does NOT touch excluded rows.

Usage:  python cleaning/scripts/remap_genres.py
"""

import csv
import os
import re

IN_FILE  = os.path.join('cleaning', 'raw.csv')
TMP_FILE = os.path.join('cleaning', 'raw_tmp.csv')

# ── Collection-based genre remaps ─────────────────────────
COLLECTION_GENRE_MAP = {
    'westerns':             'western',
    'film_noir':            'crime',
    'horror_and_suspense':  'horror',
    'animationandcartoons': 'animation',
}

# ── Foreign language detection ────────────────────────────
# Non-ASCII Latin extended characters common in Turkish, German, French, Spanish, etc.
FOREIGN_CHAR_RE = re.compile(
    r'[àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ'
    r'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß'
    r'şğıŞĞİçöüÇÖÜ'   # Turkish
    r'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'  # Polish
    r'а-яА-ЯёЁ]'  # Cyrillic
)

FOREIGN_KEYWORDS = [
    'turkish movie', 'türk filmi', 'yerli film', 'deutsche', 'wochenschau',
    'vose', 'subtitulado', 'subtitled', 'hindi movie', 'bollywood',
    'french film', 'italian film', 'japanese film',
]

def _is_foreign(title):
    t = title or ''
    if FOREIGN_CHAR_RE.search(t):
        return True
    tl = t.lower()
    return any(kw in tl for kw in FOREIGN_KEYWORDS)

# ── Main ──────────────────────────────────────────────────
with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

if 'language' not in fieldnames:
    fieldnames = fieldnames + ['language']

genre_remapped    = 0
language_foreign  = 0
language_en       = 0

for row in rows:
    if row.get('exclude') == 'true':
        continue

    collection = row.get('collection', '')
    type_val   = row.get('type', '')
    title      = row.get('title', '')

    # Collection-based genre remap
    if collection in COLLECTION_GENRE_MAP:
        row['genre'] = COLLECTION_GENRE_MAP[collection]
        genre_remapped += 1
    elif type_val == 'concert' and row.get('genre') in ('other', '', None):
        row['genre'] = 'musical'
        genre_remapped += 1
    elif type_val == 'newsreel' and row.get('genre') in ('other', '', None):
        row['genre'] = 'documentary'
        genre_remapped += 1
    elif type_val == 'educational' and row.get('genre') in ('other', '', None):
        row['genre'] = 'educational'
        genre_remapped += 1
    elif type_val == 'serial' and row.get('genre') in ('other', '', None):
        row['genre'] = 'action'
        genre_remapped += 1

    # Language detection
    if _is_foreign(title):
        row['language'] = 'foreign'
        language_foreign += 1
    else:
        row['language'] = 'en'
        language_en += 1

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, IN_FILE)

print(f'Genre remapped:    {genre_remapped:,}')
print(f'Language foreign:  {language_foreign:,}')
print(f'Language en:       {language_en:,}')
print(f'Updated:           {IN_FILE}')
