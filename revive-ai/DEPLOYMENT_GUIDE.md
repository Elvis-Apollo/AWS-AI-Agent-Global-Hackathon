# Revive AI - Complete Deployment Guide

This guide walks you through deploying Revive AI to your AWS account from scratch.

## Prerequisites

- AWS Account with admin access or sufficient permissions
- AWS CLI installed and configured
- Python 3.11 installed locally (for testing)
- Git (for cloning the repository)

## Estimated Deployment Time

- **Quick Setup:** 30-45 minutes (manual AWS Console)
- **Scripted Setup:** 15-20 minutes (with automation)

## Step-by-Step Deployment

### Phase 1: Enable Bedrock Model Access (5 minutes)

This must be done first as it may require approval.

1. Log into AWS Console
2. Navigate to **Amazon Bedrock**
3. Click **Model access** in left sidebar
4. Click **Manage model access**
5. Find **Anthropic** section
6. Check the box for **Claude Sonnet 4.5**
7. Click **Request model access**
8. Wait for approval (usually instant, max 2 hours)

**Verify:** Status shows "Access granted"

---

### Phase 2: Create S3 Buckets (5 minutes)

#### Option A: AWS Console

**Data Bucket:**
1. Go to **S3** console
2. Click **Create bucket**
3. Name: `revive-ai-data`
4. Region: `us-east-1`
5. Block all public access: ✅ Enabled
6. Versioning: ✅ Enable
7. Click **Create bucket**

8. Create folders inside bucket:
   - uploads/
   - results/
   - demo/

**Frontend Bucket:**
1. Create another bucket
2. Name: `revive-ai-frontend`
3. Region: `us-east-1`
4. Block all public access: ❌ Disabled (for website hosting)
5. Click **Create bucket**

6. Enable static website hosting:
   - Go to bucket **Properties**
   - Scroll to **Static website hosting**
   - Click **Edit**
   - Enable: **Static website hosting**
   - Index document: `index.html`
   - Save changes

7. Add bucket policy for public read:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::revive-ai-frontend/*"
       }
     ]
   }
   ```

#### Option B: AWS CLI

```bash
# Data bucket
aws s3 mb s3://revive-ai-data --region us-east-1
aws s3api put-bucket-versioning --bucket revive-ai-data \
  --versioning-configuration Status=Enabled

# Frontend bucket
aws s3 mb s3://revive-ai-frontend --region us-east-1
aws s3 website s3://revive-ai-frontend \
  --index-document index.html

# Bucket policy for frontend
cat > /tmp/frontend-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::revive-ai-frontend/*"
    }
  ]
}
EOF

aws s3api put-bucket-policy --bucket revive-ai-frontend \
  --policy file:///tmp/frontend-policy.json
```

**Upload Demo Data:**
```bash
aws s3 cp demo_data/demo_50_customers.csv s3://revive-ai-data/demo/
```

---

### Phase 3: Create IAM Roles (10 minutes)

#### Lambda Execution Role

**Console Method:**

1. Go to **IAM** → **Roles**
2. Click **Create role**
3. Select **AWS service** → **Lambda**
4. Click **Next**
5. Attach policy: `AWSLambdaBasicExecutionRole`
6. Click **Next**
7. Role name: `revive-ai-lambda-role`
8. Click **Create role**

9. Add inline policy:
   - Click the role
   - Click **Add permissions** → **Create inline policy**
   - Switch to **JSON** tab
   - Paste content from `iam/lambda-role-policy.json`
   - Name: `ReviveAILambdaPolicy`
   - Click **Create policy**

**CLI Method:**

```bash
cd iam

# Create role
aws iam create-role \
  --role-name revive-ai-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach managed policy
aws iam attach-role-policy \
  --role-name revive-ai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Add inline policy
aws iam put-role-policy \
  --role-name revive-ai-lambda-role \
  --policy-name ReviveAILambdaPolicy \
  --policy-document file://lambda-role-policy.json
```

#### Step Functions Execution Role

**Console Method:**

1. Go to **IAM** → **Roles**
2. Click **Create role**
3. Select **AWS service** → **Step Functions**
4. Click **Next**
5. Skip attaching policies (we'll add inline)
6. Role name: `revive-ai-stepfunctions-role`
7. Click **Create role**

8. Add inline policy from `iam/stepfunctions-role-policy.json`

**CLI Method:**

```bash
# Create role
aws iam create-role \
  --role-name revive-ai-stepfunctions-role \
  --assume-role-policy-document file://stepfunctions-trust-policy.json

# Add inline policy
aws iam put-role-policy \
  --role-name revive-ai-stepfunctions-role \
  --policy-name ReviveAIStepFunctionsPolicy \
  --policy-document file://stepfunctions-role-policy.json
```

---

### Phase 4: Package and Deploy Lambda Functions (15 minutes)

#### Step 1: Package Shared Layer

```bash
cd lambda

# Create build directory
mkdir -p build/python

# Copy shared modules
cp -r shared build/python/

# Create zip
cd build
zip -r shared-layer.zip python
cd ..
```

#### Step 2: Publish Lambda Layer

**Console:**
1. Go to **Lambda** → **Layers**
2. Click **Create layer**
3. Name: `revive-ai-shared`
4. Upload: `lambda/build/shared-layer.zip`
5. Compatible runtimes: Python 3.11
6. Click **Create**
7. **Copy the Layer ARN** (you'll need this)

**CLI:**
```bash
LAYER_ARN=$(aws lambda publish-layer-version \
  --layer-name revive-ai-shared \
  --zip-file fileb://build/shared-layer.zip \
  --compatible-runtimes python3.11 \
  --region us-east-1 \
  --query 'LayerVersionArn' \
  --output text)

echo "Layer ARN: $LAYER_ARN"
```

#### Step 3: Package Lambda Functions

```bash
# API Handler
cd api_handler
zip -r ../build/api-handler.zip lambda_function.py
cd ..

# Customer Worker
cd customer_worker
zip -r ../build/customer-worker.zip lambda_function.py
cd ..
```

#### Step 4: Deploy API Handler Lambda

**Console:**
1. Go to **Lambda** → **Functions**
2. Click **Create function**
3. Name: `revive-ai-api-handler`
4. Runtime: Python 3.11
5. Execution role: Use existing → `revive-ai-lambda-role`
6. Click **Create function**

7. Upload code:
   - Code source → **Upload from** → .zip file
   - Upload `lambda/build/api-handler.zip`
   - Click **Save**

8. Add layer:
   - Scroll to **Layers**
   - Click **Add a layer**
   - Custom layers → `revive-ai-shared`
   - Version: Latest
   - Click **Add**

9. Configure:
   - **Configuration** tab → **General configuration** → **Edit**
   - Memory: 512 MB
   - Timeout: 30 seconds
   - Click **Save**

10. Environment variables:
    - **Configuration** → **Environment variables** → **Edit**
    - Add:
      - `DATA_BUCKET` = `revive-ai-data`
      - `FRONTEND_BUCKET` = `revive-ai-frontend`
      - `STATE_MACHINE_ARN` = (leave empty for now, will update later)
    - Click **Save**

**CLI:**
```bash
# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create function
aws lambda create-function \
  --function-name revive-ai-api-handler \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/revive-ai-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://build/api-handler.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{DATA_BUCKET=revive-ai-data,FRONTEND_BUCKET=revive-ai-frontend}" \
  --region us-east-1

# Add layer
aws lambda update-function-configuration \
  --function-name revive-ai-api-handler \
  --layers $LAYER_ARN \
  --region us-east-1
```

#### Step 5: Deploy Customer Worker Lambda

**Console:** (Same steps as API Handler but with these values)
- Name: `revive-ai-customer-worker`
- Upload: `lambda/build/customer-worker.zip`
- Memory: 1024 MB
- Timeout: 60 seconds
- Environment variables:
  - `DATA_BUCKET` = `revive-ai-data`
  - `BEDROCK_MODEL_ID` = `anthropic.claude-sonnet-4-5-20250929`

**CLI:**
```bash
aws lambda create-function \
  --function-name revive-ai-customer-worker \
  --runtime python3.11 \
  --role arn:aws:iam::${ACCOUNT_ID}:role/revive-ai-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://build/customer-worker.zip \
  --timeout 60 \
  --memory-size 1024 \
  --environment Variables="{DATA_BUCKET=revive-ai-data,BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-20250929}" \
  --region us-east-1

aws lambda update-function-configuration \
  --function-name revive-ai-customer-worker \
  --layers $LAYER_ARN \
  --region us-east-1
```

---

### Phase 5: Create Step Functions State Machine (5 minutes)

1. Get Lambda ARNs:
```bash
API_HANDLER_ARN=$(aws lambda get-function --function-name revive-ai-api-handler --query 'Configuration.FunctionArn' --output text)
WORKER_ARN=$(aws lambda get-function --function-name revive-ai-customer-worker --query 'Configuration.FunctionArn' --output text)

echo "API Handler ARN: $API_HANDLER_ARN"
echo "Worker ARN: $WORKER_ARN"
```

2. Update state machine definition:
```bash
cd step_functions

# Replace placeholders in state_machine.json
sed "s|\${ApiHandlerLambdaArn}|$API_HANDLER_ARN|g" state_machine.json > state_machine_updated.json
sed -i "s|\${CustomerWorkerLambdaArn}|$WORKER_ARN|g" state_machine_updated.json
```

3. Create state machine via **Console:**
   - Go to **Step Functions**
   - Click **Create state machine**
   - Choose: **Write your workflow in code**
   - Type: Standard
   - Paste content from `state_machine_updated.json`
   - Name: `revive-ai-orchestration`
   - Permissions: Use existing role → `revive-ai-stepfunctions-role`
   - Click **Create state machine**
   - **Copy the State Machine ARN**

**OR via CLI:**
```bash
STATE_MACHINE_ARN=$(aws stepfunctions create-state-machine \
  --name revive-ai-orchestration \
  --definition file://state_machine_updated.json \
  --role-arn arn:aws:iam::${ACCOUNT_ID}:role/revive-ai-stepfunctions-role \
  --region us-east-1 \
  --query 'stateMachineArn' \
  --output text)

echo "State Machine ARN: $STATE_MACHINE_ARN"
```

4. Update API Handler with State Machine ARN:
```bash
aws lambda update-function-configuration \
  --function-name revive-ai-api-handler \
  --environment Variables="{DATA_BUCKET=revive-ai-data,FRONTEND_BUCKET=revive-ai-frontend,STATE_MACHINE_ARN=$STATE_MACHINE_ARN}" \
  --region us-east-1
```

---

### Phase 6: Create API Gateway (10 minutes)

**Console Method:**

1. Go to **API Gateway**
2. Click **Create API**
3. Choose **REST API** (not private)
4. Click **Build**
5. Name: `revive-ai-api`
6. Endpoint Type: Regional
7. Click **Create API**

8. Create `/upload` resource:
   - Actions → Create Resource
   - Resource Name: upload
   - Create Resource

9. Create POST method for `/upload`:
   - Select `/upload`
   - Actions → Create Method → POST
   - Integration type: Lambda Function
   - Lambda Function: `revive-ai-api-handler`
   - Save
   - Click OK on permission popup

10. Enable CORS:
    - Select `/upload`
    - Actions → Enable CORS
    - Use defaults
    - Click Enable

11. **Repeat steps 8-10 for:**
    - `/process` (POST)
    - `/results` (GET)
    - `/demo` (POST)

12. Deploy API:
    - Actions → Deploy API
    - Stage: **New Stage**
    - Stage name: `prod`
    - Deploy
    - **Copy the Invoke URL**

**Example Invoke URL:** `https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod`

---

### Phase 7: Deploy Frontend (5 minutes)

1. Edit `frontend/index.html`:
```javascript
// Line 10: Update API_BASE_URL
const API_BASE_URL = 'https://YOUR_API_GATEWAY_INVOKE_URL/prod';
```

2. Upload to S3:
```bash
aws s3 cp frontend/index.html s3://revive-ai-frontend/web/index.html
```

3. Get website URL:
```bash
echo "Frontend URL: http://revive-ai-frontend.s3-website-us-east-1.amazonaws.com/web/index.html"
```

---

### Phase 8: Testing (5-10 minutes)

#### Test 1: Demo Data

1. Open frontend URL in browser
2. Click **"Load Demo Data"**
3. Wait ~5 seconds
4. Verify campaigns display

#### Test 2: Real Processing

1. Create test CSV with 5 customers:
```csv
customer_id,email,company_name,subscription_tier,mrr,churn_date,cancellation_reason
t001,test@test1.com,Test Company 1,starter,199,2025-09-15,Too expensive
t002,test@test2.com,Test Company 2,growth,599,2025-09-16,Missing features
t003,test@test3.com,Test Company 3,growth,799,2025-09-17,Poor onboarding
t004,test@test4.com,Test Company 4,enterprise,1299,2025-09-18,Found competitor
t005,test@test5.com,Test Company 5,starter,149,2025-09-19,Business closing
```

2. Upload via frontend
3. Watch Step Functions execution in AWS Console
4. Verify processing completes in <30 seconds
5. Check results in frontend

#### Test 3: CloudWatch Logs

1. Go to **CloudWatch** → **Log groups**
2. Check logs:
   - `/aws/lambda/revive-ai-api-handler`
   - `/aws/lambda/revive-ai-customer-worker`
3. Verify no errors

---

## Troubleshooting

### Issue: Bedrock Access Denied

**Error:** `AccessDeniedException: Could not access model`

**Fix:**
1. Verify Bedrock model access is granted
2. Check IAM role has `bedrock:InvokeModel` permission
3. Ensure correct model ID: `anthropic.claude-sonnet-4-5-20250929`

### Issue: Lambda Timeout

**Error:** `Task timed out after 30.00 seconds`

**Fix:**
1. Increase Lambda timeout (API Handler: 30s, Worker: 60s)
2. Check Bedrock response times in CloudWatch
3. Reduce `max_tokens` in prompts if needed

### Issue: S3 Access Denied

**Error:** `AccessDenied: Access Denied`

**Fix:**
1. Verify IAM role has S3 permissions
2. Check bucket names in environment variables
3. Ensure buckets exist in correct region

### Issue: Frontend Not Loading

**Error:** Blank page or CORS errors

**Fix:**
1. Verify API Gateway URL in `index.html`
2. Check CORS is enabled on all API methods
3. Ensure S3 bucket has public read policy
4. Check browser console for errors

### Issue: Step Functions Failed

**Error:** State machine execution failed

**Fix:**
1. Check CloudWatch logs for Lambda errors
2. Verify Lambda ARNs in state machine definition
3. Check IAM role has `lambda:InvokeFunction` permission
4. Review execution history in Step Functions console

---

## Post-Deployment Checklist

- [ ] Bedrock model access granted
- [ ] Both S3 buckets created and configured
- [ ] IAM roles created with correct policies
- [ ] Lambda layer published
- [ ] Both Lambda functions deployed
- [ ] Lambda functions have correct environment variables
- [ ] Step Functions state machine created
- [ ] API Gateway deployed to prod stage
- [ ] Frontend uploaded to S3
- [ ] Demo data works
- [ ] Test CSV processes successfully
- [ ] No errors in CloudWatch logs

---

## Next Steps

1. **Generate Demo Results:**
   ```bash
   # Process demo CSV through system
   # Save output to demo/demo_results.json for instant demo mode
   ```

2. **Set up Monitoring:**
   - Create CloudWatch dashboard
   - Set up alarms for errors
   - Configure billing alerts

3. **Optimize Costs:**
   - Review Lambda memory settings
   - Set S3 lifecycle policies
   - Configure log retention

4. **Prepare Presentation:**
   - Practice demo flow
   - Prepare Q&A answers
   - Record backup video

---

## Deployment Costs

**One-time Setup:** $0

**Operational Costs (per month for 1000 customers/day):**
- Bedrock: ~$4.50
- Lambda: ~$0.60
- Step Functions: ~$1.50
- S3: ~$0.30
- API Gateway: ~$0.30

**Total:** ~$7/month for 30,000 customers

---

## Support

For issues:
1. Check CloudWatch Logs
2. Review AWS service quotas
3. Verify IAM permissions
4. Check this troubleshooting guide

---

**Last Updated:** 2025-10-08
**Deployment Version:** 1.0
