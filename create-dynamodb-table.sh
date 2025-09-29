#!/bin/bash

# DynamoDBテーブルを作成するスクリプト

TABLE_NAME="AlexaConversations"
REGION="us-west-2"  # Lambdaと同じリージョンを使用

echo "Creating DynamoDB table: $TABLE_NAME"

aws dynamodb create-table \
    --table-name $TABLE_NAME \
    --attribute-definitions \
        AttributeName=userId,AttributeType=S \
    --key-schema \
        AttributeName=userId,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION

echo "Waiting for table to be created..."
aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION

echo "Table created successfully!"

# TTLを有効化
echo "Enabling TTL..."
aws dynamodb update-time-to-live \
    --table-name $TABLE_NAME \
    --time-to-live-specification "Enabled=true,AttributeName=ttl" \
    --region $REGION

echo "TTL enabled!"

# テーブル情報を表示
echo "Table description:"
aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION | jq '.Table | {TableName, TableStatus, ItemCount}'