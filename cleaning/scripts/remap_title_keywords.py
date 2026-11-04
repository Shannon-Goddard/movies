"""
movies/cleaning/scripts/remap_title_keywords.py

Remaps remaining genre=other rows using title keyword scanning.
Only touches surviving rows where genre is still 'other'.

Usage:  python cleaning/scripts/remap_title_keywords.py
"""

import csv
import os
import re

IN_FILE  = os.path.join('cleaning', 'raw.csv')
TMP_FILE = os.path.join('cleaning', 'raw_tmp.csv')

# Order matters — first match wins. More specific before broader.
TITLE_GENRE_MAP = [
    ('horror',       ['horror', 'terror', 'scary', 'haunted', 'ghost', 'vampire',
                      'zombie', 'monster', 'creature', 'demon', 'devil', 'witch',
                      'werewolf', 'dracula', 'frankenstein', 'mummy', 'evil',
                      'curse', 'possessed', 'exorcist', 'slasher', 'killer',
                      'blood', 'dead', 'death', 'crypt', 'coffin', 'grave',
                      'nightmare', 'phantom', 'specter', 'macabre', 'sinister']),
    ('sci-fi',       ['sci-fi', 'science fiction', 'space', 'planet', 'galaxy',
                      'rocket', 'alien', 'robot', 'android', 'cyborg', 'laser',
                      'moon', 'mars', 'saturn', 'cosmos', 'atomic', 'nuclear',
                      'mutant', 'radiation', 'flying saucer', 'ufo', 'time machine',
                      'future', 'ray gun', 'interstellar', 'apollo']),
    ('western',      ['western', 'cowboy', 'outlaw', 'sheriff', 'gunfighter',
                      'frontier', 'saloon', 'ranch', 'desperado', 'bandit',
                      'marshal', 'stagecoach', 'gold rush', 'wild west']),
    ('crime',        ['murder', 'detective', 'mystery', 'noir', 'gangster',
                      'heist', 'robbery', 'thief', 'stolen', 'fugitive',
                      'prison', 'jail', 'cop', 'police', 'fbi', 'spy',
                      'assassin', 'hitman', 'blackmail', 'smuggler']),
    ('comedy',       ['comedy', 'comic', 'funny', 'laugh', 'humor', 'humour',
                      'farce', 'slapstick', 'jest', 'clown', 'buffoon']),
    ('musical',      ['musical', 'music', 'concert', 'opera', 'symphony',
                      'orchestra', 'jazz', 'blues', 'singing', 'dancer',
                      'broadway', 'vaudeville', 'band', 'song', 'melody']),
    ('documentary',  ['documentary', 'document', 'history', 'historical',
                      'biography', 'biopic', 'war', 'battle', 'wwii', 'ww2',
                      'world war', 'civil war', 'revolution', 'expedition',
                      'nature', 'wildlife', 'exploration', 'journey']),
    ('romance',      ['romance', 'romantic', 'love story', 'love affair',
                      'forbidden love', 'heartbreak']),
    ('drama',        ['drama', 'dramatic', 'tragedy', 'tragic', 'family',
                      'struggle', 'survival', 'redemption', 'sacrifice']),
    ('action',       ['adventure', 'action', 'hero', 'quest', 'battle',
                      'fight', 'warrior', 'sword', 'jungle', 'treasure',
                      'escape', 'rescue', 'mission', 'agent', 'commando']),
]

def _map_title(title):
    t = title.lower()
    for genre, keywords in TITLE_GENRE_MAP:
        for kw in keywords:
            if kw in t:
                return genre
    return None

with open(IN_FILE, newline='', encoding='utf-8') as f:
    reader     = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows       = list(reader)

remapped = 0
still_other = 0

for row in rows:
    if row.get('exclude') == 'true':
        continue
    if row.get('genre') != 'other':
        continue

    mapped = _map_title(row.get('title', ''))
    if mapped:
        row['genre'] = mapped
        remapped += 1
    else:
        still_other += 1

with open(TMP_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
os.replace(TMP_FILE, IN_FILE)

print(f'Remapped via title: {remapped:,}')
print(f'Still other:        {still_other:,}')
print(f'Updated:            {IN_FILE}')
