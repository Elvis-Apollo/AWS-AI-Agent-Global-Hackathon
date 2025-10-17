# Revive AI - Quick Start Guide

Get Revive AI running in 30 minutes!

## What You'll Build

A complete serverless AI system that:
- Analyzes 50 churned customers
- Generates personalized win-back campaigns
- Completes in under 60 seconds

## Prerequisites

✅ AWS Account with admin access
✅ AWS CLI installed and configured
✅ 30 minutes of time

## Fast Track Deployment

### Step 1: Enable Bedrock (2 min)

```bash
# Open AWS Console
# Bedrock → Model Access → Enable "Claude Sonnet 4.5"
```

### Step 2: Create S3 Buckets (2 min)

```bash
# Data bucket
aws s3 mb s3://revive-ai-data --region us-east-1
aws s3api put-bucket-versioning --bucket revive-ai-data \
  --versioning-configuration Status=Enabled

# Frontend bucket
aws s3 mb s3://revive-ai-frontend --region us-east-1
aws s3 website s3://revive-ai-frontend --index-document index.html

# Public read policy
cat > /tmp/policy.json << 'EOF'
{"Version":"2012-10-17","Statement":[{"Sid":"PublicRead","Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::revive-ai-frontend/*"}]}
EOF
aws s3api put-bucket-policy --bucket revive-ai-frontend --policy file:///tmp/policy.json

# Upload demo data
aws s3 cp demo_data/demo_50_customers.csv s3://revive-ai-data/demo/
```

### Step 3: Create IAM Roles (3 min)

```bash
cd iam

# Lambda role
aws iam create-role --role-name revive-ai-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json

aws iam attach-role-policy --role-name revive-ai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy --role-name revive-ai-lambda-role \
  --policy-name ReviveAIPolicy --policy-document file://lambda-role-policy.json

# Step Functions role
aws iam create-role --role-name revive-ai-stepfunctions-role \
  --assume-role-policy-document file://stepfunctions-trust-policy.json

aws iam put-role-policy --role-name revive-ai-stepfunctions-role \
  --policy-name ReviveAIPolicy --policy-document file://stepfunctions-role-policy.json

cd ..
```

### Step 4: Deploy Lambda Functions (8 min)

```bash
cd lambda

# Package layer
mkdir -p build/python && cp -r shared build/python/
cd build && zip -r shared-layer.zip python && cd ..

# Publish layer
LAYER_ARN=$(aws lambda publish-layer-version \
  --layer-name revive-ai-shared \
  --zip-file fileb://build/shared-layer.zip \
  --compatible-runtimes python3.11 \
  --query LayerVersionArn --output text)

echo "Layer: $LAYER_ARN"

# Package functions
cd api_handler && zip -r ../build/api-handler.zip lambda_function.py && cd ..
cd customer_worker && zip -r ../build/customer-worker.zip lambda_function.py && cd ..

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Deploy API Handler
aws lambda create-function \
  --function-name revive-ai-api-handler \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/revive-ai-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://build/api-handler.zip \
  --timeout 30 --memory-size 512 \
  --environment Variables="{DATA_BUCKET=revive-ai-data,FRONTEND_BUCKET=revive-ai-frontend}"

aws lambda update-function-configuration \
  --function-name revive-ai-api-handler --layers $LAYER_ARN

# Deploy Customer Worker
aws lambda create-function \
  --function-name revive-ai-customer-worker \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/revive-ai-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://build/customer-worker.zip \
  --timeout 60 --memory-size 1024 \
  --environment Variables="{DATA_BUCKET=revive-ai-data,BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-20250929}"

aws lambda update-function-configuration \
  --function-name revive-ai-customer-worker --layers $LAYER_ARN

cd ..
```

### Step 5: Deploy Step Functions (3 min)

```bash
cd step_functions

# Get Lambda ARNs
API_ARN=$(aws lambda get-function --function-name revive-ai-api-handler \
  --query 'Configuration.FunctionArn' --output text)
WORKER_ARN=$(aws lambda get-function --function-name revive-ai-customer-worker \
  --query 'Configuration.FunctionArn' --output text)

# Update state machine definition
sed "s|\${ApiHandlerLambdaArn}|$API_ARN|g" state_machine.json > temp.json
sed "s|\${CustomerWorkerLambdaArn}|$WORKER_ARN|g" temp.json > state_machine_final.json

# Create state machine
STATE_MACHINE_ARN=$(aws stepfunctions create-state-machine \
  --name revive-ai-orchestration \
  --definition file://state_machine_final.json \
  --role-arn arn:aws:iam::${ACCOUNT_ID}:role/revive-ai-stepfunctions-role \
  --query stateMachineArn --output text)

echo "State Machine: $STATE_MACHINE_ARN"

# Update API Handler with State Machine ARN
aws lambda update-function-configuration \
  --function-name revive-ai-api-handler \
  --environment Variables="{DATA_BUCKET=revive-ai-data,FRONTEND_BUCKET=revive-ai-frontend,STATE_MACHINE_ARN=$STATE_MACHINE_ARN}"

cd ..
```

### Step 6: Create API Gateway (5 min)

**Via AWS Console:**

1. API Gateway → Create REST API
2. Name: `revive-ai-api`
3. Create resources: `/upload`, `/process`, `/results`, `/demo`
4. Add POST/GET methods → integrate with `revive-ai-api-handler`
5. Enable CORS on all
6. Deploy to stage `prod`
7. **Copy Invoke URL**

**Save the URL:**
```bash
API_URL="https://3eb95lgb5c.execute-api.us-east-1.amazonaws.com/prod"
echo $API_URL
```

### Step 7: Deploy Frontend (2 min)

```bash
cd frontend

# Edit index.html - update line 10
# Change: const API_BASE_URL = 'YOUR_API_URL_HERE';

# Upload
aws s3 cp index.html s3://revive-ai-frontend/web/index.html

# Get URL
echo "Frontend: http://revive-ai-frontend.s3-website-us-east-1.amazonaws.com/web/index.html"
```

### Step 8: Test! (5 min)

1. **Open frontend URL**
2. **Click "Load Demo Data"**
3. **Watch magic happen** ✨
4. **Browse 50 generated campaigns**

## Verify Everything Works

### Test 1: Demo Mode
```bash
# Open frontend → Load Demo Data
# Should return results instantly
```

### Test 2: Real Processing
Create `test.csv`:
```csv
customer_id,email,company_name,subscription_tier,mrr,churn_date,cancellation_reason
test1,user@test.com,Test Co,growth,599,2025-09-15,Too expensive
```

Upload via frontend → Watch Step Functions → See results

### Test 3: Check Logs
```bash
# CloudWatch → Log Groups
# /aws/lambda/revive-ai-api-handler
# /aws/lambda/revive-ai-customer-worker
```

## Common Issues & Fixes

### ❌ Bedrock Access Denied
**Fix:** Console → Bedrock → Model Access → Enable Claude Sonnet 4.5

### ❌ Lambda Timeout
**Fix:** Increase timeout to 60s for worker, 30s for API handler

### ❌ S3 Access Denied
**Fix:** Check IAM role has S3 permissions in `lambda-role-policy.json`

### ❌ CORS Error
**Fix:** API Gateway → Enable CORS on all methods → Redeploy

### ❌ Frontend Blank
**Fix:** Check API_BASE_URL in index.html matches your API Gateway URL

## What's Next?

✅ System is running!
✅ Try uploading your own CSV
✅ Monitor Step Functions executions
✅ Check costs in AWS Billing
✅ Read ARCHITECTURE.md for deep dive

## Cost Estimate

**For 1000 customers/month:**
- Bedrock: ~$0.15
- Lambda: ~$0.02
- Step Functions: ~$0.05
- S3 + API Gateway: ~$0.03

**Total: ~$0.25/month**

## Architecture Summary

```
Frontend (S3)
   ↓
API Gateway
   ↓
Lambda API Handler
   ↓
Step Functions (orchestrates 8 parallel workers)
   ↓
Lambda Customer Worker × 8
   ├─ Bedrock Agent 1 (Churn Analysis)
   └─ Bedrock Agent 2 (Campaign Generation)
   ↓
S3 Results Storage
```

## Project Structure

```
revive-ai/
├── lambda/
│   ├── shared/              # AI agents, Bedrock client, utilities
│   ├── api_handler/         # API Gateway handler
│   └── customer_worker/     # Per-customer processor
├── step_functions/          # State machine definition
├── frontend/                # React SPA (single HTML)
├── iam/                     # IAM policies
├── demo_data/               # 50 sample customers
└── scripts/                 # Deployment helpers
```

## Support Resources

- **README.md** - Full project overview
- **ARCHITECTURE.md** - Technical deep dive
- **DEPLOYMENT_GUIDE.md** - Detailed step-by-step
- **CloudWatch Logs** - Real-time debugging

## Clean Up (Optional)

To delete everything:

```bash
# Delete Lambda functions
aws lambda delete-function --function-name revive-ai-api-handler
aws lambda delete-function --function-name revive-ai-customer-worker
aws lambda delete-layer-version --layer-name revive-ai-shared --version-number 1

# Delete Step Functions
aws stepfunctions delete-state-machine --state-machine-arn $STATE_MACHINE_ARN

# Delete S3 buckets (careful!)
aws s3 rb s3://revive-ai-data --force
aws s3 rb s3://revive-ai-frontend --force

# Delete IAM roles
aws iam delete-role-policy --role-name revive-ai-lambda-role --policy-name ReviveAIPolicy
aws iam detach-role-policy --role-name revive-ai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name revive-ai-lambda-role

aws iam delete-role-policy --role-name revive-ai-stepfunctions-role --policy-name ReviveAIPolicy
aws iam delete-role --role-name revive-ai-stepfunctions-role

# Delete API Gateway (via Console)
```

---

**🎉 You're done! Your AI agent system is live.**

Questions? Check the full docs or CloudWatch logs for troubleshooting.

**Built for AWS AI Agent Global Hackathon 2025**
