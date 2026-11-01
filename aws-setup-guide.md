# AWS Setup Guide

This guide covers deploying the backend for the movies platform.
The frontend is static and deploys automatically via GitHub Pages — no AWS needed for that.

Built by [Amazon Q](https://aws.amazon.com/q/developer/) alongside Shannon Goddard.

---

## What You're Deploying

| Service | Purpose |
|---|---|
| Amazon DynamoDB | Film index with GSI-based filtering |
| AWS Lambda (x2) | Search and stats API handlers |
| Amazon API Gateway | REST API routing with CORS |

---

## Prerequisites

- AWS account
- AWS CLI installed and configured (`aws configure`)
- Python 3.12+

---

## 1. DynamoDB Table

Create the `movies` table with 4 GSIs for genre, type, era, and color filtering:

```json
{
  "TableName": "movies",
  "AttributeDefinitions": [
    {"AttributeName": "film_id", "AttributeType": "S"},
    {"AttributeName": "genre",   "AttributeType": "S"},
    {"AttributeName": "type",    "AttributeType": "S"},
    {"AttributeName": "era",     "AttributeType": "S"},
    {"AttributeName": "color",   "AttributeType": "S"}
  ],
  "KeySchema": [
    {"AttributeName": "film_id", "KeyType": "HASH"}
  ],
  "BillingMode": "PAY_PER_REQUEST",
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "genre-index",
      "KeySchema": [
        {"AttributeName": "genre",   "KeyType": "HASH"},
        {"AttributeName": "film_id", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    },
    {
      "IndexName": "type-index",
      "KeySchema": [
        {"AttributeName": "type",    "KeyType": "HASH"},
        {"AttributeName": "film_id", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    },
    {
      "IndexName": "era-index",
      "KeySchema": [
        {"AttributeName": "era",     "KeyType": "HASH"},
        {"AttributeName": "film_id", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    },
    {
      "IndexName": "color-index",
      "KeySchema": [
        {"AttributeName": "color",   "KeyType": "HASH"},
        {"AttributeName": "film_id", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    }
  ]
}
```

Save as `create-table.json` and run:

```bash
aws dynamodb create-table --cli-input-json file://create-table.json
```

> **Important:** DynamoDB GSI keys cannot be null. The ingestion script handles this automatically — `era` and `color` are only written to items where they can be detected.

---

## 2. IAM Role

Create a Lambda execution role with DynamoDB and CloudWatch Logs access.

**Trust policy** (`trust-policy.json`):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

**Inline policy** (`lambda-policy.json`) — replace `YOUR_ACCOUNT_ID` and `YOUR_REGION`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:YOUR_REGION:YOUR_ACCOUNT_ID:table/movies",
        "arn:aws:dynamodb:YOUR_REGION:YOUR_ACCOUNT_ID:table/movies/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:YOUR_REGION:YOUR_ACCOUNT_ID:log-group:/aws/lambda/movies-*:*"
    }
  ]
}
```

```bash
aws iam create-role \
  --role-name movies-lambda-role \
  --assume-role-policy-document file://trust-policy.json

aws iam put-role-policy \
  --role-name movies-lambda-role \
  --policy-name movies-lambda-policy \
  --policy-document file://lambda-policy.json
```

---

## 3. Lambda Functions

Zip and deploy each handler. Replace `YOUR_ACCOUNT_ID` and `YOUR_REGION`:

```bash
# Search
zip movies-search.zip backend/api/search.py
aws lambda create-function \
  --function-name movies-search \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/movies-lambda-role \
  --handler search.handler \
  --zip-file fileb://movies-search.zip \
  --environment "Variables={DYNAMODB_TABLE=movies}" \
  --timeout 15 \
  --memory-size 256

# Stats
zip movies-stats.zip backend/api/stats.py
aws lambda create-function \
  --function-name movies-stats \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/movies-lambda-role \
  --handler stats.handler \
  --zip-file fileb://movies-stats.zip \
  --environment "Variables={DYNAMODB_TABLE=movies}" \
  --timeout 15 \
  --memory-size 256
```

To redeploy after code changes:
```bash
aws lambda update-function-code \
  --function-name movies-search \
  --zip-file fileb://movies-search.zip
```

---

## 4. API Gateway

```bash
# Create API
API_ID=$(aws apigateway create-rest-api \
  --name movies-api \
  --query "id" --output text)

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query "items[0].id" --output text)

# Create /films and /films/search
FILMS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID --parent-id $ROOT_ID \
  --path-part films --query "id" --output text)

SEARCH_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID --parent-id $FILMS_ID \
  --path-part search --query "id" --output text)

# Create /stats
STATS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID --parent-id $ROOT_ID \
  --path-part stats --query "id" --output text)
```

Add GET and OPTIONS methods to both resources, wire GET to Lambda (AWS_PROXY), wire OPTIONS to MOCK, add CORS headers to OPTIONS responses, grant API Gateway invoke permission on both Lambdas, then deploy:

```bash
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name v1
```

Your invoke URL will be:
```
https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/v1
```

Paste that into `js/api.js` as `BASE_URL`.

---

## 5. Ingestion

Install the Internet Archive Python library:
```bash
pip install internetarchive boto3
```

Run collections smallest to largest. Each can be resumed with `--resume` if interrupted:

```bash
python backend/ingestion/ingest_ia.py --collection educational_films
python backend/ingestion/ingest_ia.py --collection horror_and_suspense
python backend/ingestion/ingest_ia.py --collection short_films
python backend/ingestion/ingest_ia.py --collection animationandcartoons
python backend/ingestion/ingest_ia.py --collection silent_films
python backend/ingestion/ingest_ia.py --collection newsandpublicaffairs
python backend/ingestion/ingest_ia.py --collection classic_tv
python backend/ingestion/ingest_ia.py --collection feature_films
```

> IA's scrape cursors expire after ~30-40 minutes on large collections. If you hit `ValueError: Bad cursor`, just rerun with `--resume` — progress is saved every 100 writes.

---

## 6. Google Cast (Optional)

1. Go to [cast.google.com/publish](https://cast.google.com/publish)
2. Add new application → Custom Receiver
3. Set the Receiver URL to your GitHub Pages URL
4. Copy the 8-character App ID into `js/player.js`

The App ID is not sensitive — it's designed to be public.

---

## Genre Mapping

The ingestion script uses a genre map built from a 12,000-item sample of real Internet Archive subject tags across all 8 collections. This approach yields significantly more genre matches than relying on schema headers alone. The map covers English and Spanish tags and is located in `backend/ingestion/ingest_ia.py`.

---

## Notes

- All film content is sourced from the Internet Archive and is either public domain or Creative Commons licensed
- The `era` and `color` fields are optional — items without a detectable year or color are written without those GSI fields rather than failing
- The `director` field on IA items is sometimes a list — the ingestion script normalizes it to a string
- DynamoDB numbers are returned as `Decimal` — both Lambda functions include a custom JSON serializer to handle this
