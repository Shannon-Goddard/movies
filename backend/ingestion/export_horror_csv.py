"""
Export all horror items from DynamoDB to CSV.
Usage: python export_horror_csv.py
Output: horror_export.csv in project root
"""

import boto3
import csv
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'movies')
REGION     = os.environ.get('AWS_REGION', 'us-east-1')
OUT_FILE   = 'horror_export.csv'

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)

FIELDS = ['film_id', 'title', 'director', 'year', 'genre', 'type',
          'era', 'color', 'color_label', 'era_label', 'duration_sec',
          'collection', 'source_url', 'stream_url', 'poster_url', 'ingested_at']

def _val(v):
    if isinstance(v, Decimal):
        return int(v) if v % 1 == 0 else float(v)
    return v or ''

items = []
kwargs = {
    'IndexName': 'genre-index',
    'KeyConditionExpression': Key('genre').eq('horror'),
}
while True:
    resp = table.query(**kwargs)
    items.extend(resp.get('Items', []))
    if 'LastEvaluatedKey' not in resp:
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

print(f'Found {len(items)} horror items')

with open(OUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore')
    writer.writeheader()
    for item in sorted(items, key=lambda x: str(x.get('title', '')).lower()):
        writer.writerow({k: _val(item.get(k)) for k in FIELDS})

print(f'Written to {OUT_FILE}')
