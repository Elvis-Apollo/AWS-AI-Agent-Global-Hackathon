# 🧪 Comprehensive Agent Test Scenarios

Test these 5 scenarios to demonstrate intelligent, autonomous tool usage.

---

## Test 1: High-Value Customer with Technical Pain Point ✅ (Already Tested)

**Input:**
```
Analyze customer c025 from DataTech Solutions who churned on 2025-10-01.
They said: "Needed better API rate limits and response times"
MRR: $2,499, Tier: Enterprise
```

**Expected Tools Called:**
- ✅ calculateCLV (assess value)
- ✅ checkProductRoadmap (find API improvements)
- ✅ getCRMHistory (verify technical issues in support tickets)
- ✅ searchCompanyInfo (check if they can afford to return)
- ✅ analyzeChurn (categorize the churn)

**What to Look For:**
- Agent finds API v2.0 in roadmap (perfect timing)
- CRM shows 3 support tickets about rate limits
- Company just raised $15M funding
- Comprehensive multi-source analysis

---

## Test 2: Minimal Information - Force Discovery

**Input:**
```
Customer c025 churned. Find out why and create a win-back strategy.
```

**Expected Tools Called:**
- ✅ getCRMHistory (MUST call - no customer data provided)
- ✅ calculateCLV (need to calculate value)
- ✅ searchCompanyInfo (discover company status)
- ✅ checkProductRoadmap (find relevant features)
- ✅ analyzeChurn (categorize from CRM data)

**What to Look For:**
- Agent recognizes it lacks basic information
- Proactively gathers all intelligence
- Builds complete picture from scratch
- Shows true autonomous data gathering

---

## Test 3: Price-Sensitive Customer (Tests Different Churn Category)

**Input:**
```
Analyze customer c007 from MarketPro Analytics.
Churned: 2025-09-25
Reason: "Not enough ROI for the subscription cost"
MRR: $199, Tier: Starter
```

**Expected Tools Called:**
- ✅ calculateCLV (likely LOW priority)
- ✅ getCRMHistory (discover low engagement - 15% API usage!)
- ⚠️ searchCompanyInfo (might skip - low value customer)
- ⚠️ checkProductRoadmap (pricing tier changes?)
- ✅ analyzeChurn (categorize as pricing/value)

**What to Look For:**
- Agent discovers real issue: LOW ENGAGEMENT, not price
- CRM shows only 15% API usage, no integrations setup
- Agent recommends onboarding/training, not discounts
- Intelligence reveals stated reason ≠ actual reason

---

## Test 4: Compliance-Driven Churn

**Input:**
```
Customer c017 - SecureData Corp churned on 2025-09-07.
Their stated reason: "Security certifications not meeting our standards"
MRR: $1,799, Enterprise tier
```

**Expected Tools Called:**
- ✅ calculateCLV (high-value customer)
- ✅ getCRMHistory (find security audit tickets)
- ✅ checkProductRoadmap (find SOC 2 certification launch: Mar 1!)
- ✅ searchCompanyInfo (understand their industry/compliance needs)
- ✅ analyzeChurn (categorize as compliance)

**What to Look For:**
- Roadmap shows SOC 2 Type II launching March 1, 2025
- CRM shows 3 security tickets during audit period
- Agent identifies: "Customer churned right before certification"
- Perfect timing for win-back campaign

---

## Test 5: Research Company Status First

**Input:**
```
Is DataTech Solutions still in business? Should we pursue them for win-back?
Customer ID: c025
```

**Expected Tools Called:**
- ✅ searchCompanyInfo (FIRST - directly asked)
- ✅ getCRMHistory (understand engagement)
- ✅ calculateCLV (assess value)
- ⚠️ checkProductRoadmap (optional)
- ⚠️ analyzeChurn (optional)

**What to Look For:**
- Agent prioritizes searchCompanyInfo (directly requested)
- Finds $15M Series A funding news
- Company is growing 200% YoY
- Agent concludes: "YES - high priority target"
- Demonstrates intelligent tool ordering based on query

---

## How to Test Each Scenario

### Option 1: AWS Console (Visual)
1. Go to: **AWS Console → Bedrock → Agents → ChurnAnalyzer**
2. Click **"Test in console"**
3. Paste each test input
4. Compare response to expected tools

### Option 2: Check Logs (Technical Verification)
```bash
# Clear your mind of previous tests
# Run ONE test scenario in console
# Then immediately check:

aws logs tail /aws/lambda/bedrock-agent-executor --since 2m --region us-east-1 | grep "Executing:"
```

You should see the tools listed above being called.

---

## Success Criteria

**The agent demonstrates intelligence if:**

1. ✅ **Context-aware tool selection** - Uses different tools for different scenarios
2. ✅ **Prioritizes based on query** - Calls most relevant tools first
3. ✅ **Discovers missing information** - Proactively fills data gaps
4. ✅ **Cross-references sources** - Identifies when stated reason ≠ actual behavior
5. ✅ **Efficient execution** - Doesn't call unnecessary tools for low-value customers

---

## Expected Results Summary

| Scenario | calculateCLV | getCRMHistory | searchCompanyInfo | checkProductRoadmap | analyzeChurn |
|----------|-------------|---------------|-------------------|---------------------|--------------|
| Test 1: Technical Pain | ✅ | ✅ | ✅ | ✅ | ✅ |
| Test 2: Minimal Info | ✅ | ✅ (critical) | ✅ | ✅ | ✅ |
| Test 3: Price-Sensitive | ✅ | ✅ (reveals truth) | ⚠️ maybe | ⚠️ maybe | ✅ |
| Test 4: Compliance | ✅ | ✅ | ✅ | ✅ (key!) | ✅ |
| Test 5: Company Research | ✅ | ✅ | ✅ (first!) | ⚠️ optional | ⚠️ optional |

**Legend:**
- ✅ Expected to call
- ⚠️ May or may not call (shows intelligent decision-making)

---

## What Makes a Good Demo

**Highlight these points:**

1. **Test 2 shows data discovery** - "Look, we gave it almost no info, and it gathered everything!"
2. **Test 3 shows intelligence** - "The customer said 'too expensive', but the agent discovered they barely used the product - it's an engagement problem, not a price problem!"
3. **Test 4 shows perfect timing** - "Customer left due to missing SOC 2, and we're launching it in 2 months!"
4. **Tool usage varies by scenario** - "See how it uses different tools based on what's actually needed?"

This demonstrates **true AI autonomy**, not just forced tool execution.
