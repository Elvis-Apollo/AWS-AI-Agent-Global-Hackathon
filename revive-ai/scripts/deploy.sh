#!/bin/bash
# Deployment script for Revive AI
# This script helps deploy the Lambda functions, Step Functions, and S3 resources

set -e

echo "========================================="
echo "Revive AI - Deployment Script"
echo "========================================="

# Configuration
REGION=${AWS_REGION:-us-east-1}
DATA_BUCKET="revive-ai-data"
FRONTEND_BUCKET="revive-ai-frontend"
BEDROCK_MODEL_ID="anthropic.claude-sonnet-4-5-20250929"

echo ""
echo "Configuration:"
echo "  Region: $REGION"
echo "  Data Bucket: $DATA_BUCKET"
echo "  Frontend Bucket: $FRONTEND_BUCKET"
echo "  Bedrock Model: $BEDROCK_MODEL_ID"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not installed. Please install it first."
    echo "Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

echo "Step 1: Creating S3 Buckets..."
echo "-------------------------------"

# Create data bucket
if aws s3 ls "s3://$DATA_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb "s3://$DATA_BUCKET" --region $REGION
    aws s3api put-bucket-versioning --bucket $DATA_BUCKET --versioning-configuration Status=Enabled
    echo "✓ Created data bucket: $DATA_BUCKET"
else
    echo "✓ Data bucket already exists: $DATA_BUCKET"
fi

# Create frontend bucket
if aws s3 ls "s3://$FRONTEND_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb "s3://$FRONTEND_BUCKET" --region $REGION
    aws s3 website "s3://$FRONTEND_BUCKET" --index-document index.html
    echo "✓ Created frontend bucket: $FRONTEND_BUCKET"
else
    echo "✓ Frontend bucket already exists: $FRONTEND_BUCKET"
fi

# Create folder structure in data bucket
echo "Creating folder structure in data bucket..."
aws s3api put-object --bucket $DATA_BUCKET --key uploads/ --region $REGION
aws s3api put-object --bucket $DATA_BUCKET --key results/ --region $REGION
aws s3api put-object --bucket $DATA_BUCKET --key demo/ --region $REGION
echo "✓ Folder structure created"

echo ""
echo "Step 2: Uploading demo data..."
echo "-------------------------------"
aws s3 cp ../demo_data/demo_50_customers.csv "s3://$DATA_BUCKET/demo/" --region $REGION
echo "✓ Demo CSV uploaded"

echo ""
echo "Step 3: Packaging Lambda functions..."
echo "--------------------------------------"

# Create deployment package directory
mkdir -p ../build
cd ../build

# Package shared layer
echo "Packaging shared layer..."
mkdir -p python/shared
cp -r ../lambda/shared/* python/shared/
zip -r shared-layer.zip python
echo "✓ Shared layer packaged"

# Package API handler
echo "Packaging API handler..."
rm -rf api-handler
mkdir -p api-handler
cp ../lambda/api_handler/lambda_function.py api-handler/
cd api-handler
zip -r ../api-handler.zip .
cd ..
echo "✓ API handler packaged"

# Package customer worker
echo "Packaging customer worker..."
rm -rf customer-worker
mkdir -p customer-worker
cp ../lambda/customer_worker/lambda_function.py customer-worker/
cd customer-worker
zip -r ../customer-worker.zip .
cd ..
echo "✓ Customer worker packaged"

cd ../scripts

echo ""
echo "========================================="
echo "Manual Steps Required:"
echo "========================================="
echo ""
echo "1. Create Lambda Layer:"
echo "   - Name: revive-ai-shared"
echo "   - Upload: build/shared-layer.zip"
echo "   - Runtime: Python 3.11"
echo ""
echo "2. Create Lambda Function: revive-ai-api-handler"
echo "   - Runtime: Python 3.11"
echo "   - Memory: 512 MB"
echo "   - Timeout: 30 seconds"
echo "   - Upload: build/api-handler.zip"
echo "   - Add Layer: revive-ai-shared"
echo "   - Environment Variables:"
echo "     DATA_BUCKET=$DATA_BUCKET"
echo "     FRONTEND_BUCKET=$FRONTEND_BUCKET"
echo "     STATE_MACHINE_ARN=<will be set after Step Functions creation>"
echo ""
echo "3. Create Lambda Function: revive-ai-customer-worker"
echo "   - Runtime: Python 3.11"
echo "   - Memory: 1024 MB"
echo "   - Timeout: 60 seconds"
echo "   - Upload: build/customer-worker.zip"
echo "   - Add Layer: revive-ai-shared"
echo "   - Environment Variables:"
echo "     DATA_BUCKET=$DATA_BUCKET"
echo "     BEDROCK_MODEL_ID=$BEDROCK_MODEL_ID"
echo ""
echo "4. Create IAM Role: revive-ai-lambda-role"
echo "   - Attach: AWSLambdaBasicExecutionRole"
echo "   - Add inline policy for S3 and Bedrock access"
echo ""
echo "5. Create Step Functions State Machine:"
echo "   - Name: revive-ai-orchestration"
echo "   - Type: Standard"
echo "   - Definition: Use step_functions/state_machine.json"
echo "   - Replace \${ApiHandlerLambdaArn} and \${CustomerWorkerLambdaArn}"
echo ""
echo "6. Create API Gateway:"
echo "   - Type: REST API"
echo "   - Resources: /upload, /process, /results, /demo"
echo "   - Enable CORS"
echo "   - Deploy to stage: prod"
echo ""
echo "7. Update Frontend:"
echo "   - Edit frontend/index.html"
echo "   - Set API_BASE_URL to your API Gateway URL"
echo "   - Upload to S3: aws s3 cp frontend/index.html s3://$FRONTEND_BUCKET/web/"
echo ""
echo "8. Enable Bedrock Model Access:"
echo "   - Go to AWS Bedrock Console"
echo "   - Enable Claude Sonnet 4.5 model"
echo ""
echo "========================================="
echo "Deployment packages ready in build/"
echo "========================================="
