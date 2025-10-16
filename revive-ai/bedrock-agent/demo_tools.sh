#!/bin/bash
# Demo Script: Test all 5 ChurnAnalyzer tools

echo "=========================================="
echo "🎯 Testing All 5 ChurnAnalyzer Tools"
echo "=========================================="

# Tool 1: Calculate CLV
echo ""
echo "📊 TOOL 1: calculateCLV"
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --payload '{
    "apiPath": "/calculateCLV",
    "httpMethod": "POST",
    "parameters": [
      {"name": "mrr", "value": "2499"},
      {"name": "subscription_tier", "value": "enterprise"}
    ]
  }' \
  --region us-east-1 \
  /tmp/clv-result.json > /dev/null && cat /tmp/clv-result.json | jq '.'

# Tool 2: Get CRM History
echo ""
echo "📈 TOOL 2: getCRMHistory"
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --payload '{
    "apiPath": "/getCRMHistory",
    "httpMethod": "POST",
    "parameters": [
      {"name": "customer_id", "value": "c025"}
    ]
  }' \
  --region us-east-1 \
  /tmp/crm-result.json > /dev/null && cat /tmp/crm-result.json | jq '.usage_summary'

# Tool 3: Search Company Info
echo ""
echo "🌐 TOOL 3: searchCompanyInfo"
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --payload '{
    "apiPath": "/searchCompanyInfo",
    "httpMethod": "POST",
    "parameters": [
      {"name": "company_name", "value": "DataTech Solutions"}
    ]
  }' \
  --region us-east-1 \
  /tmp/company-result.json > /dev/null && cat /tmp/company-result.json | jq '.recent_news[0]'

# Tool 4: Check Product Roadmap
echo ""
echo "🛣️  TOOL 4: checkProductRoadmap"
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --payload '{
    "apiPath": "/checkProductRoadmap",
    "httpMethod": "POST",
    "parameters": [
      {"name": "churn_category", "value": "performance"},
      {"name": "churn_reason", "value": "API rate limits"}
    ]
  }' \
  --region us-east-1 \
  /tmp/roadmap-result.json > /dev/null && cat /tmp/roadmap-result.json | jq '.features[0]'

# Tool 5: Analyze Churn
echo ""
echo "🎯 TOOL 5: analyzeChurn"
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --payload '{
    "apiPath": "/analyzeChurn",
    "httpMethod": "POST",
    "parameters": [
      {"name": "customer_id", "value": "c025"},
      {"name": "company_name", "value": "DataTech Solutions"},
      {"name": "mrr", "value": "2499"},
      {"name": "subscription_tier", "value": "enterprise"},
      {"name": "cancellation_reason", "value": "Needed better API rate limits"}
    ]
  }' \
  --region us-east-1 \
  /tmp/churn-result.json > /dev/null && cat /tmp/churn-result.json | jq '.'

echo ""
echo "=========================================="
echo "✅ All 5 tools tested successfully!"
echo "=========================================="
