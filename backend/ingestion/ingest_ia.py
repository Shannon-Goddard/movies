"""
movies/backend/ingestion/ingest_ia.py

Ingests video content from Internet Archive collections into DynamoDB.
Same pattern as music/backend/ingestion/ingest_ia.py — adapted for film metadata.

Usage:
  python ingest_ia.py --collection feature_films
  python ingest_ia.py --collection animationandcartoons
  python ingest_ia.py --collection short_films
  python ingest_ia.py --collection silent_films
  python ingest_ia.py --collection educational_films
  python ingest_ia.py --collection classic_tv
  python ingest_ia.py --collection live_concerts
  python ingest_ia.py --collection horror_and_suspense

Options:
  --collection   IA collection identifier (required)
  --limit        Max items to ingest (default: no limit)
  --resume       Resume from last saved cursor
"""

import argparse
import boto3
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from internetarchive import search_items, get_item

# ── Config ────────────────────────────────────────────────
TABLE_NAME   = os.environ.get('DYNAMODB_TABLE', 'movies')
REGION       = os.environ.get('AWS_REGION', 'us-east-1')
RESUME_FILE  = 'ia_resume_{collection}.json'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)

# ── Era detection ─────────────────────────────────────────
def _era(year):
    if not year: return None
    try:
        y = int(str(year)[:4])
        if y < 1930:  return 'silent'
        if y < 1960:  return 'classic'
        if y < 1980:  return 'vintage'
        return 'modern'
    except:
        return None

# ── Color detection (from IA subject/description tags) ────
def _color(meta):
    subjects = meta.get('subject', [])
    if isinstance(subjects, str):
        subjects = [subjects]
    subjects = [s if isinstance(s, str) else '' for s in subjects]
    desc     = (meta.get('description', '') or '')
    if isinstance(desc, list):
        desc = ' '.join(desc)
    combined = ' '.join(subjects).lower() + ' ' + desc.lower()
    if 'colorized' in combined:   return 'colorized'
    if 'color' in combined:       return 'color'
    if 'black and white' in combined or 'b&w' in combined or 'bw' in combined:
        return 'bw'
    return None

# ── Genre map — built from real IA subject tags (12k doc sample) ────────────
# Ordered: first match wins. More specific before broader.
_GENRE_MAP = [
    ('horror',      {'horror', 'terror', 'scary', 'creepy', 'paranormal', 'haunt',
                     'slasher', 'supernatural', 'ghost', 'zombie', 'zombies',
                     'survival horror', 'analog horror', 'horror film', 'horror movie',
                     'horror host', 'historias de terror', 'historia de misterio',
                     'miedo', 'misterio', 'fantasmas', 'monstruo', 'creepypasta',
                     'bloop', 'exploitation', 'b movie', 'one step beyond'}),
    ('sci-fi',      {'sci-fi', 'science fiction', 'fantasy', 'spirit'}),
    ('animation',   {'animation', 'cartoon', 'soviet cartoon', 'anime', 'lego',
                     'film & animation'}),
    ('documentary', {'documentary', 'documental', 'history', 'cold war', 'wwii', 'ww2',
                     'war', 'third reich cinema', 'german newsreel', 'deutsche wochenschau',
                     'newsreel', 'british', 'bbc', 'nbc', 'abc'}),
    ('educational', {'education', 'educational', 'lecture', 'public education',
                     'government', 'reflexion'}),
    ('musical',     {'musical', 'music', 'pop music', 'popular music', 'variety show'}),
    ('comedy',      {'comedy', 'silent comedy', 'classic comedy movies', 'humor',
                     'funny', 'parody', 'comedia', 'gracioso', 'chistoso', 'fun',
                     'sitcom', 'humour'}),
    ('crime',       {'crime', 'murder', 'film noir', 'police', 'mystery', 'thriller',
                     'suspense', 'detective'}),
    ('action',      {'action', 'adventure', 'western', 'cliffhanger', 'serial',
                     'fighting', 'cliffhanger'}),
    ('romance',     {'romance', 'love'}),
    ('drama',       {'drama', 'silent drama', 'family', 'anthology', 'story',
                     'indie', 'low budget'}),
]

_TAG_TO_GENRE = {tag: genre for genre, tags in _GENRE_MAP for tag in tags}

def _resolve_genre(subjects):
    if isinstance(subjects, str):
        subjects = [subjects]
    for s in subjects:
        if not isinstance(s, str):
            continue
        for tag in s.replace(',', ';').split(';'):
            mapped = _TAG_TO_GENRE.get(tag.strip().lower())
            if mapped:
                return mapped
    return 'other'

# ── Collection queries (some collections need subject: not collection:) ───────
COLLECTION_QUERIES = {
    'feature_films':        'collection:feature_films AND mediatype:movies',
    'animationandcartoons': 'collection:animationandcartoons AND mediatype:movies',
    'short_films':          'collection:short_films AND mediatype:movies',
    'silent_films':         'collection:silent_films AND mediatype:movies',
    'educational_films':    'mediatype:movies AND subject:educational',
    'classic_tv':           'collection:classic_tv AND mediatype:movies',
    'live_concerts':         'mediatype:movies AND (subject:"live concert" OR subject:concert OR subject:"live music")',
    'horror_and_suspense':  'mediatype:movies AND (subject:horror OR subject:suspense)',
    'film_noir':            'mediatype:movies AND (subject:"film noir" OR subject:noir)',
    'serials':              'mediatype:movies AND (subject:serial OR subject:cliffhanger)',
    'westerns':             'mediatype:movies AND (subject:western OR subject:cowboy)',
}

# ── Type mapping from collection ─────────────────────────
COLLECTION_TYPE_MAP = {
    'feature_films':         'feature',
    'animationandcartoons':  'cartoon',
    'short_films':           'short',
    'silent_films':          'feature',
    'educational_films':     'educational',
    'classic_tv':            'serial',
    'live_concerts':          'concert',
    'horror_and_suspense':   'feature',
    'film_noir':             'feature',
    'serials':               'serial',
    'westerns':              'feature',
}

# ── Main ingest ───────────────────────────────────────────
def ingest(collection, limit=None, resume=False, start_id=None):
    resume_file = RESUME_FILE.format(collection=collection)
    base_query  = COLLECTION_QUERIES.get(collection, f'collection:{collection} AND mediatype:movies')
    query       = base_query

    if start_id:
        print(f'Starting from: {start_id}')
        query = f'({base_query}) AND identifier:[{start_id} TO z]'
    elif resume and os.path.exists(resume_file):
        with open(resume_file) as f:
            last_id = json.load(f).get('last_id')
        if last_id:
            print(f'Resuming after: {last_id}')
            query = f'({base_query}) AND identifier:[{last_id} TO z]'

    params = {'fields': ['identifier','title','creator','date','subject','description','runtime'],
              'sorts': ['identifier asc']}

    print(f'Querying IA: {query[:80]}...')
    written   = 0
    deduped   = 0
    processed = 0
    last_id   = None

    for result in search_items(query, **params):
        if limit and written >= limit:
            break

        identifier = result.get('identifier')
        if not identifier:
            continue

        last_id    = identifier
        processed += 1
        if processed % 100 == 0:
            with open(resume_file, 'w') as f:
                json.dump({'last_id': last_id}, f)

        try:
            for attempt in range(3):
                try:
                    item = get_item(identifier)
                    break
                except Exception:
                    if attempt == 2: raise
                    time.sleep(5 * (attempt + 1))
            meta = item.metadata
            files = list(item.get_files(formats=['h.264', 'MPEG4', 'Ogg Video', '512Kb MPEG4']))

            # Pick best stream file
            stream_file = next((f for f in files if f.name.endswith('.mp4')), None) or \
                          next((f for f in files), None)
            if not stream_file:
                continue

            stream_url = f'https://archive.org/download/{identifier}/{stream_file.name}'
            poster_url = f'https://archive.org/services/img/{identifier}'

            year = None
            raw_date = meta.get('date', '')
            if raw_date:
                try: year = int(str(raw_date)[:4])
                except: pass

            film_id = hashlib.md5(stream_url.encode()).hexdigest()

            subjects = meta.get('subject', [])
            genre    = _resolve_genre(subjects)

            director = meta.get('creator', '') or ''
            if isinstance(director, list):
                director = director[0] if director else ''

            era   = _era(year)
            color = _color(meta)

            item_data = {
                'film_id':     film_id,
                'title':       meta.get('title', identifier),
                'director':    director,
                'year':        year,
                'genre':       genre,
                'type':        COLLECTION_TYPE_MAP.get(collection, 'feature'),
                'stream_url':  stream_url,
                'poster_url':  poster_url,
                'source':      'internet_archive',
                'source_url':  f'https://archive.org/details/{identifier}',
                'license_type': meta.get('licenseurl', 'https://creativecommons.org/publicdomain/mark/1.0/'),
                'collection':  collection,
                'ingested_at': datetime.now(timezone.utc).isoformat(),
            }

            # Only set GSI key fields if non-null — DynamoDB rejects null GSI keys
            if era:
                item_data['era']       = era
                item_data['era_label'] = {'silent': 'Silent Era', 'classic': '1930s\u201350s', 'vintage': '1960s\u201370s', 'modern': '1980s+'}.get(era, '')
            if color:
                item_data['color']       = color
                item_data['color_label'] = {'bw': 'B&W', 'color': 'Color', 'colorized': 'Colorized'}.get(color, '')

            # Duration from runtime field (format: HH:MM:SS or MM:SS)
            runtime = meta.get('runtime', '')
            if runtime:
                try:
                    parts = [int(p) for p in str(runtime).split(':')]
                    if len(parts) == 3:
                        item_data['duration_sec'] = parts[0]*3600 + parts[1]*60 + parts[2]
                    elif len(parts) == 2:
                        item_data['duration_sec'] = parts[0]*60 + parts[1]
                except:
                    pass

            # Write to DynamoDB (conditional — skip if exists)
            try:
                table.put_item(
                    Item=item_data,
                    ConditionExpression='attribute_not_exists(film_id)'
                )
                written += 1
                if written % 100 == 0:
                    print(f'  {written} written, {deduped} deduped...')
            except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                deduped += 1

        except Exception as e:
            print(f'  Error on {identifier}: {e}')
            continue

        time.sleep(0.1)  # be polite to IA

    print(f'\nDone. {written} written, {deduped} deduped.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', required=True)
    parser.add_argument('--limit',   type=int, default=None)
    parser.add_argument('--resume',   action='store_true')
    parser.add_argument('--start-id', default=None)
    args = parser.parse_args()
    ingest(args.collection, args.limit, args.resume, args.start_id)
