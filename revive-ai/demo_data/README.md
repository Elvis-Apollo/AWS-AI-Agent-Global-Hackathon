# 📊 Demo Data - Comprehensive Test Customers

This directory contains demo CSV files for testing the ReviveAI multi-agent churn analysis system.

## 📁 Files

### `comprehensive_test_customers.csv`
**20 diverse customer scenarios** designed to showcase different agent behaviors and tool usage patterns.

## 🎯 Customer Scenarios Breakdown

### High-Value Customers (CLV > $50k) - Triggers All Intelligence Tools
| ID | Company | MRR | Tier | Churn Reason | Expected Tools |
|----|---------|-----|------|--------------|----------------|
| c001 | DataTech Solutions | $2,499 | Enterprise | API rate limits too restrictive | ✅ CLV, ✅ Roadmap (API v2.0), ✅ CRM, ✅ Company Info, ✅ Analyze |
| c003 | SecureData Corp | $1,799 | Enterprise | Need SOC 2 certification | ✅ CLV, ✅ Roadmap (SOC 2), ✅ CRM, ✅ Company Info, ✅ Analyze |
| c005 | InnovateLabs | $3,499 | Enterprise | Company downsizing | ✅ CLV, ✅ Company Info (verify status), ✅ CRM, ✅ Analyze |
| c012 | GlobalCorp | $4,999 | Enterprise | Need multi-region support | ✅ CLV, ✅ Roadmap, ✅ CRM, ✅ Company Info, ✅ Analyze |
| c015 | AI Tech Innovations | $2,899 | Enterprise | Missing AI/ML capabilities | ✅ CLV, ✅ Roadmap, ✅ CRM, ✅ Analyze |
| c020 | Enterprise Solutions Co | $5,999 | Enterprise | Need custom features | ✅ CLV, ✅ Roadmap, ✅ CRM, ✅ Company Info, ✅ Analyze |

### Mid-Value Customers (CLV $20k-$50k) - Selective Intelligence
| ID | Company | MRR | Tier | Churn Reason | Expected Tools |
|----|---------|-----|------|--------------|----------------|
| c004 | TechCorp Industries | $799 | Growth | Missing reporting features | ✅ CLV, ✅ Roadmap, ✅ Analyze |
| c006 | CloudServ Systems | $749 | Growth | Competitor pricing | ✅ CLV, ✅ Company Info, ✅ Analyze |
| c008 | EduTech Labs | $649 | Growth | Need LMS integrations | ✅ CLV, ✅ Roadmap, ✅ Analyze |
| c011 | FastGrowth Startup | $899 | Growth | Outgrew tier | ✅ CLV, ✅ CRM (verify usage), ✅ Analyze |
| c013 | API Company Inc | $1,299 | Growth | Poor documentation | ✅ CLV, ✅ CRM, ✅ Analyze |
| c017 | ScaleUp Ventures | $1,599 | Growth | Performance issues | ✅ CLV, ✅ Roadmap, ✅ CRM, ✅ Analyze |
| c019 | Tech Startup Labs | $699 | Growth | Switched to open source | ✅ CLV, ✅ Company Info, ✅ Analyze |

### Low-Value Customers (CLV < $20k) - Basic Analysis
| ID | Company | MRR | Tier | Churn Reason | Expected Tools |
|----|---------|-----|------|--------------|----------------|
| c002 | MarketPro Analytics | $199 | Starter | Not enough ROI | ✅ CLV, ✅ CRM (discover low engagement), ✅ Analyze |
| c007 | SmallBiz Solutions | $299 | Starter | Budget constraints | ✅ CLV, ✅ Analyze |
| c009 | Creative Design Studio | $249 | Starter | UI too difficult | ✅ CLV, ✅ CRM, ✅ Analyze |
| c014 | SaaSTools Provider | $399 | Starter | Not using features | ✅ CLV, ✅ CRM (verify adoption), ✅ Analyze |
| c016 | BudgetCo Services | $199 | Starter | Economic downturn | ✅ CLV, ✅ Analyze |
| c018 | Nonprofit Foundation | $99 | Starter | Lost funding | ✅ CLV, ✅ Analyze (likely skip) |

### Special Cases - Business Closure
| ID | Company | MRR | Tier | Churn Reason | Expected Tools |
|----|---------|-----|------|--------------|----------------|
| c010 | Retail Chain Plus | $1,899 | Enterprise | Business closure | ✅ CLV, ✅ Company Info (verify closure), ✅ Analyze |

## 🧪 Testing Scenarios

### Scenario 1: Feature Gap → Roadmap Match
**Customer:** c001 (DataTech Solutions)
- Complains about API rate limits
- Agent should find API v2.0 in roadmap (Feb 15 launch)
- Perfect timing for win-back campaign

### Scenario 2: Price Complaint → Discover Low Engagement
**Customer:** c002 (MarketPro Analytics)
- Says "too expensive"
- Agent should check CRM and find only 15% feature adoption
- Real issue: poor onboarding, not price

### Scenario 3: Compliance → Find Certification Launch
**Customer:** c003 (SecureData Corp)
- Needs SOC 2 certification
- Agent finds SOC 2 Type II launching March 1
- Customer churned just before solution available

### Scenario 4: High CLV → Full Intelligence Gathering
**Customer:** c020 (Enterprise Solutions Co)
- $5,999 MRR = $215,964 CLV
- Agent should call ALL 5 tools for comprehensive analysis
- Escalate to VP Sales

### Scenario 5: Company Status Check
**Customer:** c005 (InnovateLabs)
- Says "downsizing"
- Agent should verify company status via searchCompanyInfo
- Determine if temporary or permanent closure

## 📈 Expected Agent Behavior

### Intelligent Tool Selection
The agent should demonstrate:
1. **Value-based prioritization** - More tools for high-CLV customers
2. **Context awareness** - Don't call redundant tools
3. **Cross-referencing** - Verify stated reasons with actual data
4. **Timing intelligence** - Find roadmap features launching soon
5. **Company research** - Check funding, growth, viability

### Tool Call Patterns by Customer Value

**Enterprise ($2k+ MRR):**
- Always: calculateCLV, analyzeChurn
- Usually: getCRMHistory, searchCompanyInfo, checkProductRoadmap
- Shows: Comprehensive multi-source intelligence

**Growth ($500-$2k MRR):**
- Always: calculateCLV, analyzeChurn
- Sometimes: getCRMHistory (if engagement mentioned), checkProductRoadmap (if features mentioned)
- Shows: Selective intelligence gathering

**Starter (<$500 MRR):**
- Always: calculateCLV, analyzeChurn
- Rarely: Other tools (unless specific signals warrant investigation)
- Shows: Efficient resource allocation

## 🚀 How to Use

### Test via API
```bash
# Upload the CSV
curl -X POST https://YOUR_API/upload \
  -H "Content-Type: text/csv" \
  --data-binary @comprehensive_test_customers.csv

# Process customers
curl -X POST https://YOUR_API/process \
  -H "Content-Type: application/json" \
  -d '{"upload_id": "YOUR_UPLOAD_ID"}'
```

### Test Individual Customer
```bash
curl -X POST https://YOUR_API/analyze-customer \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "c001",
    "company_name": "DataTech Solutions",
    "mrr": "2499",
    "subscription_tier": "enterprise",
    "churn_date": "2025-10-01",
    "cancellation_reason": "API rate limits are too restrictive"
  }'
```

### Test via AWS Bedrock Console
1. Go to: AWS Console → Bedrock → Agents → ChurnAnalyzer
2. Click "Test in console"
3. Paste customer details from any row above
4. Observe which tools the agent calls

## 📊 Expected Results

### High Success Rate Scenarios
- **c001, c003, c015**: Agent finds roadmap solutions
- **c002, c014**: Agent discovers engagement vs. price disconnect
- **c005, c010**: Agent verifies company status
- **c020, c012**: Agent escalates to sales (high CLV)

### Demonstrates Intelligence
- Cross-references stated reasons with CRM data
- Finds perfect timing for roadmap-based campaigns
- Prioritizes resources based on CLV
- Researches company viability before campaigns

## ✅ Validation Checklist

When testing this demo data, verify:
- [ ] CLV calculation varies correctly by tier (starter=12mo, growth=24mo, enterprise=36mo)
- [ ] High-value customers trigger more tool calls
- [ ] Agent finds roadmap matches (API v2.0, SOC 2, etc.)
- [ ] CRM data reveals engagement patterns
- [ ] Company search shows funding/growth status
- [ ] Agent categorizes churn correctly
- [ ] Recommendations are evidence-based

---

**Last Updated:** October 11, 2025
**Total Customers:** 20
**Coverage:** All churn categories, all tiers, all value ranges
