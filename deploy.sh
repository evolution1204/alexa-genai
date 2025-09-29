#!/bin/bash
# Alexa GenAI Assistant - Lambda Deployment Script
# 2025-09-22

echo "================================"
echo "Alexa GenAI Lambda Deployment"
echo "================================"

# 色付き出力用の関数
green() { echo -e "\033[0;32m$1\033[0m"; }
yellow() { echo -e "\033[0;33m$1\033[0m"; }
red() { echo -e "\033[0;31m$1\033[0m"; }

# Step 1: クリーンアップ
echo ""
yellow "Step 1: Cleaning up previous deployment..."
rm -rf deployment/package
mkdir -p deployment/package

# Step 2: 依存関係のインストール
echo ""
yellow "Step 2: Installing dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install --target ./deployment/package ask-sdk-core requests -q
    green "✓ Dependencies installed"
else
    red "✗ pip3 not found. Please install Python 3 and pip3"
    exit 1
fi

# Step 3: Lambda関数のコピー
echo ""
yellow "Step 3: Copying Lambda function..."
cp lambda/lambda_function.py deployment/package/
green "✓ Lambda function copied"

# Step 4: ZIPファイルの作成
echo ""
yellow "Step 4: Creating deployment package..."
cd deployment/package
zip -r ../lambda_function.zip . -q
cd ../..
green "✓ Deployment package created"

# Step 5: ファイルサイズの確認
echo ""
yellow "Step 5: Verifying package..."
FILESIZE=$(ls -lh deployment/lambda_function.zip | awk '{print $5}')
green "✓ Package size: $FILESIZE"

# Step 6: 完了メッセージ
echo ""
echo "================================"
green "Deployment package ready!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Upload deployment/lambda_function.zip to AWS Lambda"
echo "2. Set environment variable: openai_api_key"
echo "3. Update Alexa skill endpoint with Lambda ARN"
echo "4. Test in Alexa simulator"
echo ""
echo "Package location: deployment/lambda_function.zip"
echo ""

# オプション: AWS CLIでのアップロード
if command -v aws &> /dev/null; then
    echo "AWS CLI detected. To deploy directly, run:"
    echo "  aws lambda update-function-code --function-name [YOUR_FUNCTION_NAME] --zip-file fileb://deployment/lambda_function.zip"
fi