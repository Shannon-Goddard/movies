"""
movies/backend/api/search.py

Lambda handler for GET /films/search
Supports: q, genre, type, era, color, limit, offset

DynamoDB table: movies
  PK: film_id (string)
  GSI: genre-index       (genre + film_id)
  GSI: type-index        (type + film_id)
  GSI: era-index         (era + film_id)
  GSI: color-index       (color + film_id)

Same Lambda + API Gateway pattern as music project.
Deploy identically — zip + upload, same IAM policy.
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
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

def handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS, 'body': ''}

    params = event.get('queryStringParameters') or {}
    q      = params.get('q', '').strip()
    genre  = params.get('genre', '').strip().lower()
    ftype  = params.get('type', '').strip().lower()
    era    = params.get('era', '').strip().lower()
    color  = params.get('color', '').strip().lower()
    limit  = min(int(params.get('limit', 20)), 50)
    offset = int(params.get('offset', 0))

    try:
        if q:
            films = _full_scan_search(q, limit, offset)
        elif genre:
            films = _gsi_query('genre-index', 'genre', genre, limit, offset)
        elif ftype:
            films = _gsi_query('type-index', 'type', ftype, limit, offset)
        elif era:
            films = _gsi_query('era-index', 'era', era, limit, offset)
        elif color:
            films = _gsi_query('color-index', 'color', color, limit, offset)
        else:
            films = _scan_all(limit, offset)

        return {
            'statusCode': 200,
            'headers': {**CORS, 'Content-Type': 'application/json'},
            'body': json.dumps({'films': films, 'count': len(films), 'offset': offset}, default=_serial),
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS,
            'body': json.dumps({'error': str(e)}),
        }


def _gsi_query(index, key_name, value, limit, offset):
    resp = table.query(
        IndexName=index,
        KeyConditionExpression=Key(key_name).eq(value),
        Limit=limit + offset,
    )
    return resp.get('Items', [])[offset:offset + limit]


def _full_scan_search(q, limit, offset):
    q_lower = q.lower()
    resp = table.scan(
        FilterExpression=
            Attr('title').contains(q) |
            Attr('director').contains(q) |
            Attr('genre').contains(q_lower),
        Limit=500,
    )
    items = resp.get('Items', [])
    return items[offset:offset + limit]


def _scan_all(limit, offset):
    resp = table.scan(Limit=limit + offset)
    return resp.get('Items', [])[offset:offset + limit]
