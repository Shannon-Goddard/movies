"""
movies/backend/ingestion/backfill_duration.py

Backfills duration_sec for all DynamoDB items missing it.
Pass 1: IA metadata API (fast)
Pass 2: ffprobe on stream_url (slow, fallback for anything still missing)

Usage:
  python backfill_duration.py              # both passes
  python backfill_duration.py --pass1-only # metadata API only
  python backfill_duration.py --pass2-only # ffprobe only (items still missing after pass 1)

Progress is checkpointed to backfill_duration_progress.json so it's resumable.
"""

import argparse
import boto3
import json
import os
import subprocess
import time
import urllib.request
from decimal import Decimal

TABLE_NAME      = os.environ.get('DYNAMODB_TABLE', 'movies')
REGION          = os.environ.get('AWS_REGION', 'us-east-1')
PROGRESS_FILE   = 'backfill_duration_progress.json'
CHECKPOINT_EVERY = 100

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)

# ── Helpers ───────────────────────────────────────────────

def _load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'done': [], 'failed': []}

def _save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def _parse_hms(s):
    """Parse HH:MM:SS or MM:SS or raw seconds string → int seconds."""
    s = str(s).strip()
    if ':' in s:
        parts = [int(p) for p in s.split(':')]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
    return int(float(s))

def _duration_from_ia(identifier):
    """Try IA metadata API. Returns int seconds or None."""
    try:
        url = f'https://archive.org/metadata/{identifier}/files'
        req = urllib.request.Request(url, headers={'User-Agent': 'movies-backfill/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        for f in data.get('result', []):
            fmt = f.get('format', '')
            if fmt in ('h.264', 'MPEG4', '512Kb MPEG4', 'Ogg Video') and 'length' in f:
                return _parse_hms(f['length'])
    except Exception:
        pass
    return None

def _duration_from_ffprobe(stream_url):
    """Run ffprobe on stream_url. Returns int seconds or None."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_format', stream_url],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        secs = float(data['format']['duration'])
        return int(secs)
    except Exception:
        pass
    return None

def _identifier_from_url(source_url):
    """Extract IA identifier from source_url like https://archive.org/details/IDENTIFIER"""
    return source_url.rstrip('/').split('/')[-1] if source_url else None

def _update_duration(film_id, seconds):
    table.update_item(
        Key={'film_id': film_id},
        UpdateExpression='SET duration_sec = :d',
        ExpressionAttributeValues={':d': seconds}
    )

# ── Fetch all items missing duration ─────────────────────

def _fetch_missing():
    print('Scanning DynamoDB for items missing duration_sec...')
    items = []
    kwargs = {
        'ProjectionExpression': 'film_id, source_url, stream_url',
        'FilterExpression': 'attribute_not_exists(duration_sec)',
    }
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get('Items', []))
        print(f'  {len(items)} found so far...', end='\r')
        if 'LastEvaluatedKey' not in resp:
            break
        kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']
    print(f'\nTotal missing duration: {len(items)}')
    return items

# ── Passes ────────────────────────────────────────────────

def run_pass1(items, progress):
    done_set = set(progress['done'])
    pending  = [i for i in items if i['film_id'] not in done_set]
    print(f'\nPass 1 (IA metadata API): {len(pending)} items')

    updated = 0
    for idx, item in enumerate(pending):
        film_id    = item['film_id']
        source_url = item.get('source_url', '')
        identifier = _identifier_from_url(source_url)

        if identifier:
            secs = _duration_from_ia(identifier)
            if secs is not None:
                _update_duration(film_id, secs)
                progress['done'].append(film_id)
                updated += 1
            else:
                progress['failed'].append(film_id)
        else:
            progress['failed'].append(film_id)

        if (idx + 1) % CHECKPOINT_EVERY == 0:
            _save_progress(progress)
            print(f'  {idx+1}/{len(pending)} processed, {updated} updated')

        time.sleep(0.3)

    _save_progress(progress)
    print(f'Pass 1 done. {updated} durations filled.')
    return progress

def run_pass2(items, progress):
    done_set    = set(progress['done'])
    failed_set  = set(progress['failed'])
    # Only items that failed pass 1 and haven't been resolved yet
    pending = [i for i in items if i['film_id'] in failed_set and i['film_id'] not in done_set]
    print(f'\nPass 2 (ffprobe): {len(pending)} items')

    updated = 0
    for idx, item in enumerate(pending):
        film_id    = item['film_id']
        stream_url = item.get('stream_url', '')

        if stream_url:
            secs = _duration_from_ffprobe(stream_url)
            if secs is not None:
                _update_duration(film_id, secs)
                progress['done'].append(film_id)
                progress['failed'].remove(film_id)
                updated += 1

        if (idx + 1) % CHECKPOINT_EVERY == 0:
            _save_progress(progress)
            print(f'  {idx+1}/{len(pending)} processed, {updated} updated')

        time.sleep(0.5)

    _save_progress(progress)
    print(f'Pass 2 done. {updated} durations filled.')
    return progress

# ── Main ──────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pass1-only', action='store_true')
    parser.add_argument('--pass2-only', action='store_true')
    args = parser.parse_args()

    progress = _load_progress()
    items    = _fetch_missing()

    if not args.pass2_only:
        progress = run_pass1(items, progress)

    if not args.pass1_only:
        # Re-fetch after pass 1 to get updated missing list for pass 2
        if not args.pass2_only:
            items = _fetch_missing()
        progress = run_pass2(items, progress)

    remaining = len([i for i in items if i['film_id'] not in set(progress['done'])])
    print(f'\nFinal: {len(progress["done"])} filled, {remaining} still missing (no duration available anywhere)')
