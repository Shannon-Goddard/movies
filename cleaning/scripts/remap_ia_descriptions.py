"""
cleaning/scripts/remap_ia_descriptions.py

Pass 6b — remap surviving other-genre rows using IA description + subject data.
Reads other_ia_meta.csv, matches keywords against subjects + description,
updates genre in raw.csv. Exports still-unknown rows to cleaning/still_other.csv.

Usage: python cleaning/scripts/remap_ia_descriptions.py
"""

import csv, os, re

RAW_FILE  = os.path.join('cleaning', 'raw.csv')
META_FILE = os.path.join('cleaning', 'other_ia_meta.csv')
TMP_FILE  = os.path.join('cleaning', 'raw_tmp.csv')
OUT_FILE  = os.path.join('cleaning', 'still_other.csv')

# Ordered by specificity — first match wins
GENRE_KEYWORDS = [
    ('horror',      ['horror', 'terror', 'scary', 'ghost', 'haunted', 'vampire', 'zombie',
                     'slasher', 'supernatural', 'occult', 'demon', 'witch', 'werewolf',
                     'creature', 'monster', 'suspense', 'thriller']),
    ('sci-fi',      ['sci-fi', 'science fiction', 'scifi', 'space', 'alien', 'robot',
                     'futuristic', 'dystopia', 'time travel', 'extraterrestrial']),
    ('western',     ['western', 'cowboy', 'outlaw', 'frontier', 'gunfighter', 'saloon',
                     'sheriff', 'wild west', 'b western']),
    ('crime',       ['film noir', 'noir', 'crime', 'murder', 'detective', 'mystery',
                     'espionage', 'gangster', 'heist', 'spy', 'cryptography', 'suspense']),
    ('animation',   ['animation', 'animated', 'cartoon', 'anime']),
    ('documentary', ['documentary', 'newsreel', 'history', 'historical', 'wwii', 'war',
                     'propaganda', 'archive', 'nuclear', 'army', 'military']),
    ('musical',     ['musical', 'music', 'concert', 'opera', 'jazz', 'blues', 'folk',
                     'variety show', 'singing', 'dance']),
    ('comedy',      ['comedy', 'humor', 'funny', 'slapstick', 'parody', 'spoof',
                     'satire', 'farce', 'comic']),
    ('romance',     ['romance', 'romantic', 'love story', 'love']),
    ('drama',       ['drama', 'melodrama', 'family', 'silent film', 'silent drama']),
    ('action',      ['action', 'adventure', 'serial', 'cliffhanger', 'swashbuckler']),
    ('educational', ['educational', 'education', 'lecture', 'government', 'instructional']),
]

def _match(text):
    t = (text or '').lower()
    for genre, keywords in GENRE_KEYWORDS:
        if any(kw in t for kw in keywords):
            return genre
    return None

# Load meta lookup
with open(META_FILE, newline='', encoding='utf-8') as f:
    meta = {r['film_id']: r for r in csv.DictReader(f)}

# Load raw
with open(RAW_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

remapped = 0
still_other = []

for row in rows:
    if row.get('exclude') == 'true' or row.get('genre') != 'other':
        continue
    m = meta.get(row['film_id'])
    if not m:
        still_other.append(row)
        continue

    combined = f"{m.get('subjects','')} {m.get('description','')}"
    genre = _match(combined)
    if genre:
        row['genre'] = genre
        remapped += 1
    else:
        still_other.append(row)

# Write raw.csv
with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, RAW_FILE)

# Export still-unknown
with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['film_id','title','type','year','collection'], extrasaction='ignore')
    writer.writeheader()
    writer.writerows(still_other)

print(f'Remapped via IA meta:  {remapped:,}')
print(f'Still other:           {len(still_other):,}')
print(f'Updated:               {RAW_FILE}')
print(f'Unknown exported to:   {OUT_FILE}')
