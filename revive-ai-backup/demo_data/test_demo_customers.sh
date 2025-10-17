#!/bin/bash
# Test script for demo customers
# Tests 5 key scenarios from comprehensive_test_customers.csv

API_ENDPOINT="https://65rpczwxta.execute-api.us-east-1.amazonaws.com/prod/analyze-customer"
LAMBDA_FUNCTION="revive-ai-api-handler"

echo "🧪 Testing Demo Customers via ReviveAI"
echo "========================================"

# Test 1: High-value customer with API complaint (should trigger roadmap check)
echo -e "\n📊 TEST 1: DataTech Solutions (c001) - API Rate Limits"
echo "Expected: CLV, CRM, Roadmap (API v2.0), Company Info, Analyze"
aws lambda invoke --function-name $LAMBDA_FUNCTION --cli-binary-format raw-in-base64-out \
  --payload '{"httpMethod": "POST", "path": "/analyze-customer", "body": "{\"customer_id\": \"c001\", \"company_name\": \"DataTech Solutions\", \"mrr\": \"2499\", \"subscription_tier\": \"enterprise\", \"churn_date\": \"2025-10-01\", \"cancellation_reason\": \"API rate limits are too restrictive and response times are too slow\"}"}' \
  --region us-east-1 /tmp/test1.json > /dev/null
TOOLS1=$(cat /tmp/test1.json | jq -r '.body | fromjson | .tool_count // 0')
echo "✅ Result: $TOOLS1 tools called"

# Test 2: Low-value customer claiming price issue (should discover engagement problem)
echo -e "\n📊 TEST 2: MarketPro Analytics (c002) - ROI Complaint"
echo "Expected: CLV, CRM (discover low adoption), Analyze"
aws lambda invoke --function-name $LAMBDA_FUNCTION --cli-binary-format raw-in-base64-out \
  --payload '{"httpMethod": "POST", "path": "/analyze-customer", "body": "{\"customer_id\": \"c002\", \"company_name\": \"MarketPro Analytics\", \"mrr\": \"199\", \"subscription_tier\": \"starter\", \"churn_date\": \"2025-09-25\", \"cancellation_reason\": \"Not enough ROI - product seems too expensive\"}"}' \
  --region us-east-1 /tmp/test2.json > /dev/null
TOOLS2=$(cat /tmp/test2.json | jq -r '.body | fromjson | .tool_count // 0')
echo "✅ Result: $TOOLS2 tools called"

# Test 3: Compliance customer (should find SOC 2 in roadmap)
echo -e "\n📊 TEST 3: SecureData Corp (c003) - Security Certification"
echo "Expected: CLV, Roadmap (SOC 2), CRM, Company Info, Analyze"
aws lambda invoke --function-name $LAMBDA_FUNCTION --cli-binary-format raw-in-base64-out \
  --payload '{"httpMethod": "POST", "path": "/analyze-customer", "body": "{\"customer_id\": \"c003\", \"company_name\": \"SecureData Corp\", \"mrr\": \"1799\", \"subscription_tier\": \"enterprise\", \"churn_date\": \"2025-09-07\", \"cancellation_reason\": \"Security certifications do not meet our compliance standards - need SOC 2\"}"}' \
  --region us-east-1 /tmp/test3.json > /dev/null
TOOLS3=$(cat /tmp/test3.json | jq -r '.body | fromjson | .tool_count // 0')
echo "✅ Result: $TOOLS3 tools called"

# Test 4: Company downsizing (should verify company status)
echo -e "\n📊 TEST 4: InnovateLabs (c005) - Company Downsizing"
echo "Expected: CLV, Company Info (verify status), Analyze"
aws lambda invoke --function-name $LAMBDA_FUNCTION --cli-binary-format raw-in-base64-out \
  --payload '{"httpMethod": "POST", "path": "/analyze-customer", "body": "{\"customer_id\": \"c005\", \"company_name\": \"InnovateLabs\", \"mrr\": \"3499\", \"subscription_tier\": \"enterprise\", \"churn_date\": \"2025-09-20\", \"cancellation_reason\": \"Company downsizing due to economic conditions\"}"}' \
  --region us-east-1 /tmp/test4.json > /dev/null
TOOLS4=$(cat /tmp/test4.json | jq -r '.body | fromjson | .tool_count // 0')
echo "✅ Result: $TOOLS4 tools called"

# Test 5: Highest value customer (should use all intelligence sources)
echo -e "\n📊 TEST 5: Enterprise Solutions Co (c020) - Custom Features"
echo "Expected: ALL 5 TOOLS for comprehensive analysis"
aws lambda invoke --function-name $LAMBDA_FUNCTION --cli-binary-format raw-in-base64-out \
  --payload '{"httpMethod": "POST", "path": "/analyze-customer", "body": "{\"customer_id\": \"c020\", \"company_name\": \"Enterprise Solutions Co\", \"mrr\": \"5999\", \"subscription_tier\": \"enterprise\", \"churn_date\": \"2025-09-09\", \"cancellation_reason\": \"Need custom enterprise features and dedicated support\"}"}' \
  --region us-east-1 /tmp/test5.json > /dev/null
TOOLS5=$(cat /tmp/test5.json | jq -r '.body | fromjson | .tool_count // 0')
CLV5=$(cat /tmp/test5.json | jq -r '.body | fromjson | .analysis' | grep -o 'CLV: \$[0-9,]*' || echo "CLV not found")
echo "✅ Result: $TOOLS5 tools called, $CLV5"

echo -e "\n========================================"
echo "SUMMARY:"
echo "  c001 (DataTech): $TOOLS1 tools"
echo "  c002 (MarketPro): $TOOLS2 tools"
echo "  c003 (SecureData): $TOOLS3 tools"
echo "  c005 (InnovateLabs): $TOOLS4 tools"
echo "  c020 (Enterprise): $TOOLS5 tools"
echo ""
echo "💡 TIP: Higher-value customers should trigger more tools"
echo "📊 Check CloudWatch logs: aws logs tail /aws/lambda/bedrock-agent-executor --since 5m --region us-east-1 | grep 'Executing:'"
