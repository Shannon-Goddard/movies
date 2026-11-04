"""
cleaning/scripts/fetch_ia_descriptions.py

Fetches IA metadata (description + subject tags) for all surviving rows
with genre == 'other'. Writes results to cleaning/other_ia_meta.csv.
Resumable — skips film_ids already in the output file.

Usage: python cleaning/scripts/fetch_ia_descriptions.py
"""

import csv, json, os, time, urllib.request

IN_FILE  = os.path.join('cleaning', 'raw.csv')
OUT_FILE = os.path.join('cleaning', 'other_ia_meta.csv')
DELAY    = 0.5  # seconds between requests

FIELDNAMES = ['film_id', 'title', 'type', 'year', 'collection', 'description', 'subjects']

def _identifier(source_url):
    return source_url.rstrip('/').split('/')[-1] if source_url else None

def _fetch(identifier):
    url = f'https://archive.org/metadata/{identifier}'
    req = urllib.request.Request(url, headers={'User-Agent': 'movies-cleaner/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        meta = data.get('metadata', {})
        desc = meta.get('description', '')
        # subject can be a string or list
        subj = meta.get('subject', '')
        if isinstance(subj, list):
            subj = ', '.join(subj)
        # strip html tags from description
        import re
        desc = re.sub(r'<[^>]+>', ' ', str(desc)).strip()
        desc = re.sub(r'\s+', ' ', desc)[:300]
        return desc, subj
    except Exception:
        return '', ''

# ── Load already-done film_ids ────────────────────────────
done = set()
if os.path.exists(OUT_FILE):
    with open(OUT_FILE, newline='', encoding='utf-8') as f:
        done = {r['film_id'] for r in csv.DictReader(f)}
    print(f'Resuming — {len(done):,} already fetched')

# ── Load other-genre surviving rows ──────────────────────
with open(IN_FILE, newline='', encoding='utf-8') as f:
    rows = [r for r in csv.DictReader(f)
            if r.get('exclude') != 'true' and r.get('genre') == 'other']

pending = [r for r in rows if r['film_id'] not in done]
print(f'Total other: {len(rows):,}  |  Pending: {len(pending):,}')

# ── Fetch ─────────────────────────────────────────────────
mode = 'a' if done else 'w'
with open(OUT_FILE, mode, newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction='ignore')
    if mode == 'w':
        writer.writeheader()

    for i, row in enumerate(pending):
        ident = _identifier(row.get('source_url', ''))
        desc, subj = _fetch(ident) if ident else ('', '')

        writer.writerow({
            'film_id':     row['film_id'],
            'title':       row['title'],
            'type':        row['type'],
            'year':        row['year'],
            'collection':  row['collection'],
            'description': desc,
            'subjects':    subj,
        })
        f.flush()

        if (i + 1) % 100 == 0:
            print(f'  {i+1:,}/{len(pending):,} fetched...')

        time.sleep(DELAY)

print(f'\nDone. Written to {OUT_FILE}')
