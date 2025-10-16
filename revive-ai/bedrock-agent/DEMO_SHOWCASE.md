# 🎯 Demo Showcase: All 5 ChurnAnalyzer Tools

## Quick Demo - Test All Tools

### Option 1: Via AWS Console (Visual Demo)

**Best for presentations!**

1. Go to: **AWS Console → Bedrock → Agents → ChurnAnalyzer**
2. Click **"Test in console"**
3. Test each tool with these prompts:

```
Tool 1 - CLV:
"Calculate the CLV for a customer with $2499 MRR on enterprise plan"

Tool 2 - CRM:
"Get the CRM history for customer c025"

Tool 3 - Web Search:
"Search for information about DataTech Solutions company"

Tool 4 - Roadmap:
"Check if we have any roadmap features that address API performance issues"

Tool 5 - Churn Analysis:
"Analyze why customer c025 from DataTech Solutions churned due to API rate limits"
```

### Option 2: Direct Lambda Test (Technical Demo)

**Best for proving tools work!**

Test CRM Tool:
```bash
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --cli-binary-format raw-in-base64-out \
  --payload '{
    "messageVersion": "1.0",
    "actionGroup": "churn-analysis-tools",
    "apiPath": "/getCRMHistory",
    "parameters": [{"name": "customer_id", "value": "c025"}],
    "requestBody": {"content": {"application/json": {"properties": [{"name": "customer_id", "value": "c025"}]}}}
  }' \
  --region us-east-1 \
  /tmp/crm-result.json

cat /tmp/crm-result.json | jq -r '.response.responseBody."application/json".body' | jq .
```

Test Roadmap Tool:
```bash
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --cli-binary-format raw-in-base64-out \
  --payload '{
    "messageVersion": "1.0",
    "actionGroup": "churn-analysis-tools",
    "apiPath": "/checkProductRoadmap",
    "parameters": [
      {"name": "churn_category", "value": "performance"},
      {"name": "churn_reason", "value": "API rate limits"}
    ],
    "requestBody": {"content": {"application/json": {"properties": []}}}
  }' \
  --region us-east-1 \
  /tmp/roadmap-result.json

cat /tmp/roadmap-result.json | jq -r '.response.responseBody."application/json".body' | jq .
```

Test Company Search Tool:
```bash
aws lambda invoke \
  --function-name bedrock-agent-executor \
  --cli-binary-format raw-in-base64-out \
  --payload '{
    "messageVersion": "1.0",
    "actionGroup": "churn-analysis-tools",
    "apiPath": "/searchCompanyInfo",
    "parameters": [{"name": "company_name", "value": "DataTech Solutions"}],
    "requestBody": {"content": {"application/json": {"properties": []}}}
  }' \
  --region us-east-1 \
  /tmp/company-result.json

cat /tmp/company-result.json | jq -r '.response.responseBody."application/json".body' | jq .
```

## What Each Tool Returns

### Tool 1: calculateCLV
```json
{
  "clv": 89976,
  "priority": "CRITICAL",
  "recommendation": "Escalate to VP Sales - high-value customer",
  "winback_probability": 0.65
}
```

### Tool 2: getCRMHistory
```json
{
  "customer_id": "c025",
  "usage_summary": {
    "months_active": 22,
    "usage_trend": "increasing",
    "recent_growth": "+35%"
  },
  "support_summary": {
    "total_tickets": 12,
    "recent_issues": [
      {"subject": "API rate limits hitting ceiling", "sentiment": "frustrated"}
    ]
  },
  "churn_risk_flags": [
    "Rate limit complaints (3 times in 2 months)",
    "Growth trajectory exceeding current tier"
  ]
}
```

### Tool 3: searchCompanyInfo
```json
{
  "company_name": "DataTech Solutions",
  "status": "Active",
  "recent_news": [
    {
      "title": "DataTech Solutions Secures $15M Series A Funding",
      "date": "2025-09-15",
      "sentiment": "positive"
    }
  ],
  "company_info": {
    "funding_stage": "Series A",
    "growth_trajectory": "rapid_growth"
  }
}
```

### Tool 4: checkProductRoadmap
```json
{
  "roadmap_version": "Q1 2025",
  "relevant_features_count": 2,
  "features": [
    {
      "feature_name": "API v2.0 with Enhanced Rate Limits",
      "release_date": "2025-02-15",
      "status": "in_development",
      "benefits": [
        "10,000 requests/minute (up from 1,000)",
        "Average response time < 100ms"
      ]
    }
  ]
}
```

### Tool 5: analyzeChurn
```json
{
  "churn_category": "performance",
  "confidence": 92,
  "insights": [
    "Customer experienced API rate limiting",
    "Growth trajectory exceeded current plan limits",
    "Technical pain point, not pricing"
  ],
  "recommendation": "Offer Enterprise upgrade with API v2 early access"
}
```

## Demo Talking Points

### External Integrations Showcase:

1. **✅ S3 Knowledge Base**
   - `s3://revive-ai-data/knowledge/product-roadmap.json`
   - `s3://revive-ai-data/knowledge/crm-history.json`

2. **✅ Web Search Integration**
   - Mock implementation (easily swapped with SerpAPI/Tavily)
   - Shows external API integration capability

3. **✅ CRM System Integration**
   - Mock CRM data showing usage patterns
   - Support ticket sentiment analysis
   - Health scores and risk flags

4. **✅ Multi-Agent Orchestration**
   - Coordinator → ChurnAnalyzer → CampaignGenerator
   - Agent-to-agent communication via bedrock-agent-runtime

5. **✅ Lambda Action Groups**
   - 11 total tools across 3 agents
   - OpenAPI 3.0 schemas defining all tools

## Architecture Summary

```
┌─────────────────────────────────────────────┐
│         Amazon Bedrock Agents (3)           │
├─────────────────────────────────────────────┤
│ 1. ChurnAnalyzer (5 tools)                  │
│    ├─ calculateCLV                          │
│    ├─ getCRMHistory ────────┐               │
│    ├─ searchCompanyInfo ────┼─ External     │
│    ├─ checkProductRoadmap ──┘   Tools       │
│    └─ analyzeChurn                          │
│                                              │
│ 2. Coordinator (4 tools)                    │
│    ├─ invokeChurnAnalyzer                   │
│    ├─ invokeCampaignGenerator               │
│    ├─ makeDecision                          │
│    └─ saveWorkflowResults                   │
│                                              │
│ 3. CampaignGenerator (2 tools)              │
│    ├─ generateEmailSequence                 │
│    └─ personalizeContent                    │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│      Lambda Action Group Executor           │
│      (bedrock-agent-executor)               │
└─────────────────────────────────────────────┘
              ↓
     ┌────────┴────────┐
     ↓                 ↓
┌──────────┐    ┌──────────────┐
│ S3 Data  │    │ External APIs │
│ (CRM,    │    │ (Web Search) │
│ Roadmap) │    └──────────────┘
└──────────┘
```

## Hackathon Requirements Met:

- ✅ **Amazon Bedrock AgentCore**: 3 agents deployed
- ✅ **Action Groups/Primitives**: 3 action groups, 11 tools total
- ✅ **External Integrations**: S3, CRM, Web Search
- ✅ **Multi-source Intelligence**: Parallel data gathering from 3+ sources
- ✅ **Autonomous Agents**: ReAct framework with tool selection
- ✅ **Production-Ready**: Scalable Lambda architecture

## Next Steps for Full Demo:

1. ✅ All tools working and testable
2. ⏳ API integration for programmatic access
3. ⏳ UI with agent reasoning visibility
4. ⏳ Demo video showing full workflow
