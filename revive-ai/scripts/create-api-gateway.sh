#!/bin/bash
# Script to create API Gateway with proper Lambda Proxy integration

set -e

echo "========================================="
echo "Creating API Gateway for Revive AI"
echo "========================================="

REGION="us-east-1"
API_NAME="revive-ai-api"
LAMBDA_FUNCTION="revive-ai-api-handler"

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Get Lambda ARN
LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_FUNCTION}"
echo "Lambda ARN: $LAMBDA_ARN"

# Step 1: Create REST API
echo ""
echo "Step 1: Creating REST API..."
API_ID=$(aws apigateway create-rest-api \
  --name "$API_NAME" \
  --endpoint-configuration types=REGIONAL \
  --region $REGION \
  --query 'id' \
  --output text)

echo "✓ API created with ID: $API_ID"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --region $REGION \
  --query 'items[0].id' \
  --output text)

echo "✓ Root resource ID: $ROOT_ID"

# Step 2: Create resources
echo ""
echo "Step 2: Creating resources..."

# Create /demo resource
DEMO_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part demo \
  --region $REGION \
  --query 'id' \
  --output text)
echo "✓ Created /demo resource: $DEMO_ID"

# Create /upload resource
UPLOAD_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part upload \
  --region $REGION \
  --query 'id' \
  --output text)
echo "✓ Created /upload resource: $UPLOAD_ID"

# Create /process resource
PROCESS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part process \
  --region $REGION \
  --query 'id' \
  --output text)
echo "✓ Created /process resource: $PROCESS_ID"

# Create /results resource
RESULTS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part results \
  --region $REGION \
  --query 'id' \
  --output text)
echo "✓ Created /results resource: $RESULTS_ID"

# Step 3: Create methods with Lambda Proxy integration
echo ""
echo "Step 3: Creating methods with Lambda Proxy integration..."

# Function to create method
create_method() {
  local RESOURCE_ID=$1
  local HTTP_METHOD=$2
  local RESOURCE_NAME=$3

  # Put method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method $HTTP_METHOD \
    --authorization-type NONE \
    --region $REGION \
    --no-api-key-required > /dev/null

  # Put integration (Lambda Proxy)
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method $HTTP_METHOD \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region $REGION > /dev/null

  echo "✓ Created $HTTP_METHOD /$RESOURCE_NAME with Lambda Proxy"
}

# Create POST /demo
create_method $DEMO_ID POST demo

# Create POST /upload
create_method $UPLOAD_ID POST upload

# Create POST /process
create_method $PROCESS_ID POST process

# Create GET /results
create_method $RESULTS_ID GET results

# Step 4: Add Lambda permissions
echo ""
echo "Step 4: Adding Lambda permissions..."

# Permission for API Gateway to invoke Lambda
aws lambda add-permission \
  --function-name $LAMBDA_FUNCTION \
  --statement-id apigateway-invoke-$(date +%s) \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*" \
  --region $REGION > /dev/null 2>&1 || echo "  (Permission may already exist)"

echo "✓ Lambda permissions configured"

# Step 5: Enable CORS for all methods
echo ""
echo "Step 5: Enabling CORS..."

enable_cors() {
  local RESOURCE_ID=$1
  local RESOURCE_NAME=$2

  # Create OPTIONS method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $REGION > /dev/null

  # Mock integration for OPTIONS
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    --region $REGION > /dev/null

  # Method response for OPTIONS
  aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters \
      "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false" \
    --region $REGION > /dev/null

  # Integration response for OPTIONS
  aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
      "method.response.header.Access-Control-Allow-Headers": "'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''",
      "method.response.header.Access-Control-Allow-Methods": "'\''GET,POST,OPTIONS'\''",
      "method.response.header.Access-Control-Allow-Origin": "'\''*'\''"
    }' \
    --region $REGION > /dev/null

  echo "✓ CORS enabled for /$RESOURCE_NAME"
}

enable_cors $DEMO_ID demo
enable_cors $UPLOAD_ID upload
enable_cors $PROCESS_ID process
enable_cors $RESULTS_ID results

# Step 6: Deploy API
echo ""
echo "Step 6: Deploying API to prod stage..."

aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --stage-description "Production" \
  --description "Initial deployment with Lambda Proxy integration" \
  --region $REGION > /dev/null

echo "✓ API deployed to prod stage"

# Step 7: Get Invoke URL
INVOKE_URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"

echo ""
echo "========================================="
echo "API Gateway created successfully!"
echo "========================================="
echo ""
echo "API ID: $API_ID"
echo "Invoke URL: $INVOKE_URL"
echo ""
echo "Next steps:"
echo "1. Update frontend/index.html with this URL:"
echo "   const API_BASE_URL = '$INVOKE_URL';"
echo ""
echo "2. Upload frontend to S3:"
echo "   aws s3 cp frontend/index.html s3://revive-ai-frontend/web/index.html"
echo ""
echo "3. Test the demo:"
echo "   curl -X POST $INVOKE_URL/demo"
echo ""
echo "========================================="

# Save URL to file for reference
echo $INVOKE_URL > api-gateway-url.txt
echo "API URL saved to: api-gateway-url.txt"
