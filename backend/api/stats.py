"""
movies/backend/api/stats.py

Lambda handler for GET /stats
Returns total film count and breakdown by type, era, color.
Memory-cached per Lambda instance (cold start refreshes).
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'movies')
REGION     = os.environ.get('AWS_REGION', 'us-east-1')

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)

CORS = {
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,OPTIONS',
}

def _serial(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(f'Not serializable: {type(obj)}')

_cache = None

def handler(event, context):
    global _cache
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS, 'body': ''}

    if not _cache:
        by_type  = {}
        by_era   = {}
        by_color = {}
        total    = 0

        kwargs = {'Select': 'SPECIFIC_ATTRIBUTES', 'ProjectionExpression': '#t, era, color',
                  'ExpressionAttributeNames': {'#t': 'type'}}
        while True:
            resp  = table.scan(**kwargs)
            for item in resp.get('Items', []):
                total += 1
                t = item.get('type');  by_type[t]  = by_type.get(t, 0)  + 1 if t else None
                e = item.get('era');   by_era[e]   = by_era.get(e, 0)   + 1 if e else None
                c = item.get('color'); by_color[c] = by_color.get(c, 0) + 1 if c else None
            if 'LastEvaluatedKey' not in resp:
                break
            kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

        _cache = {
            'total_films': total,
            'by_type':  {k: v for k, v in by_type.items()  if k},
            'by_era':   {k: v for k, v in by_era.items()   if k},
            'by_color': {k: v for k, v in by_color.items() if k},
        }

    return {
        'statusCode': 200,
        'headers': {**CORS, 'Content-Type': 'application/json'},
        'body': json.dumps(_cache, default=_serial),
    }
