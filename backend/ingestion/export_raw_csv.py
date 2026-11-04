"""
movies/backend/ingestion/export_raw_csv.py

Full DynamoDB table export to raw.csv — emergency backup of entire catalog.
Usage: python export_raw_csv.py
Output: raw.csv in current directory
"""

import boto3
import csv
import os
from decimal import Decimal

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'movies')
REGION     = os.environ.get('AWS_REGION', 'us-east-1')
OUT_FILE   = 'raw.csv'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)

FIELDS = [
    'film_id', 'title', 'director', 'year', 'genre', 'type',
    'era', 'era_label', 'color', 'color_label', 'duration_sec',
    'collection', 'source', 'source_url', 'stream_url', 'poster_url',
    'license_type', 'ingested_at'
]

def _val(v):
    if isinstance(v, Decimal):
        return int(v) if v % 1 == 0 else float(v)
    return v if v is not None else ''

print('Scanning DynamoDB...')
items = []
kwargs = {}
while True:
    resp = table.scan(**kwargs)
    items.extend(resp.get('Items', []))
    print(f'  {len(items)} items fetched...', end='\r')
    if 'LastEvaluatedKey' not in resp:
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

print(f'\nTotal items: {len(items)}')

with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
    writer.writeheader()
    for item in items:
        writer.writerow({k: _val(item.get(k)) for k in FIELDS})

print(f'Written to {OUT_FILE}')
