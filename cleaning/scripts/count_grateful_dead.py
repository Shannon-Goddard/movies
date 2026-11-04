import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='us-east-1').Table('movies')

items = []
kwargs = {
    'IndexName': 'type-index',
    'KeyConditionExpression': Key('type').eq('concert'),
    'FilterExpression': Attr('director').contains('Grateful Dead'),
}
while True:
    resp = table.query(**kwargs)
    items.extend(resp.get('Items', []))
    if 'LastEvaluatedKey' not in resp:
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

print(f'Grateful Dead concerts: {len(items)}')
