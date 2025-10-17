# Multi-Agent Orchestra Architecture

## 🎯 Dual System Strategy

### System A: Current Pipeline (BACKUP)
- **Status:** Production-ready, tested, working
- **Use case:** Fallback if agent system has issues
- **Demo:** "This is our MVP pipeline that works reliably"

### System B: Multi-Agent Orchestra (PRIMARY DEMO)
- **Status:** Advanced implementation showing true agentic AI
- **Use case:** Show innovation, meet hackathon requirements
- **Demo:** "This is our next-gen intelligent agent system"

---

## 🤖 Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER UPLOADS CSV                         │
└─────────────────────────────────────────┬───────────────────┘
                                          │
                                          ▼
                          ┌───────────────────────────┐
                          │   API Gateway + Lambda    │
                          │   (Agent Orchestrator)    │
                          └───────────────┬───────────┘
                                          │
                                          ▼
                          ┌───────────────────────────┐
                          │   MASTER COORDINATOR      │
                          │   Bedrock Agent           │
                          │   (Claude 3.5 Sonnet)     │
                          └───────────────┬───────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
        ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
        │ CHURN DETECTIVE │   │ VALUE CALCULATOR│   │ CAMPAIGN        │
        │ Agent           │   │ Agent           │   │ STRATEGIST Agent│
        │ (Claude Haiku)  │   │ (Claude Haiku)  │   │ (Claude Sonnet) │
        └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
                 │                     │                     │
        ┌────────┴────────┐   ┌────────┴────────┐   ┌────────┴────────┐
        │ TOOLS:          │   │ TOOLS:          │   │ TOOLS:          │
        │ • Web Search    │   │ • CLV Calculator│   │ • Email Gen     │
        │ • CRM Lookup    │   │ • ROI Model     │   │ • Personalize   │
        │ • Sentiment     │   │ • Priority Score│   │ • A/B Test      │
        │ • Root Cause    │   │ • Win-back Prob │   │ • Template      │
        └─────────────────┘   └─────────────────┘   └─────────────────┘
                 │                     │                     │
                 └─────────────────────┴─────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │ RESULTS AGGREGATOR      │
                          │ Lambda                  │
                          └───────────┬─────────────┘
                                      │
                                      ▼
                          ┌─────────────────────────┐
                          │ S3 Storage              │
                          │ • Analysis              │
                          │ • Campaigns             │
                          │ • Agent Reasoning Logs  │
                          └─────────────────────────┘
```

---

## 🎭 Agent Roles & Responsibilities

### 1️⃣ MASTER COORDINATOR (Bedrock Agent)
**Model:** Claude 3.5 Sonnet (needs reasoning capability)
**Purpose:** Orchestrate specialist agents and make strategic decisions

**Responsibilities:**
- Receive customer data
- Decide which specialist agents to invoke
- Coordinate multi-step workflows
- Handle exceptions and escalations
- Aggregate results from specialists

**Decision Logic:**
```python
if customer.mrr > 1000:
    invoke(ValueCalculator)
    if value_calculator.clv > 50000:
        decision = "ESCALATE_TO_HUMAN"
        return create_sales_ticket()

invoke(ChurnDetective)
churn_analysis = wait_for_result()

if churn_analysis.confidence < 70:
    # Uncertain, need more investigation
    invoke(WebSearch, query=f"{customer.company_name} recent news")

if churn_analysis.category in ["pricing", "features"]:
    invoke(CampaignStrategist, strategy="winback")
else:
    decision = "NO_ACTION_WORTHWHILE"
```

**Tools:**
- InvokeSpecialistAgent
- EscalateToHuman
- CreateTicket
- AggregateResults

---

### 2️⃣ CHURN DETECTIVE Agent
**Model:** Claude 3.5 Haiku (fast, cost-effective)
**Purpose:** Deep investigation into WHY customer churned

**Capabilities:**
- Analyze cancellation reason with NLP
- Search web for company news (still in business?)
- Check CRM for interaction history
- Sentiment analysis on support tickets
- Root cause analysis using reasoning

**Tools (Action Groups):**
1. `analyzeChurnReason` - NLP analysis of cancellation text
2. `searchCompanyNews` - Web search for company status
3. `checkCRMHistory` - Query CRM database
4. `analyzeSentiment` - Sentiment of past interactions
5. `identifyRootCause` - Multi-factor root cause analysis

**Example Reasoning:**
```
Customer said: "Too expensive"
But CRM shows: They only used 20% of features
Web search: Company just raised Series B funding
Sentiment: Positive interactions until last month

CONCLUSION: Not actually price-sensitive, likely:
- Wrong product fit (overprovisioned)
- Better to downsell than discount
- Recommend: Starter tier + feature training
```

---

### 3️⃣ VALUE CALCULATOR Agent
**Model:** Claude 3.5 Haiku (math/calculation tasks)
**Purpose:** Determine customer value and win-back priority

**Capabilities:**
- Calculate Customer Lifetime Value (CLV)
- Estimate win-back probability
- Compute ROI of win-back effort
- Prioritize customers for human intervention
- Risk assessment

**Tools (Action Groups):**
1. `calculateCLV` - LTV model using MRR, tenure, industry
2. `estimateWinbackProbability` - ML model prediction
3. `computeROI` - Cost of campaign vs potential recovery
4. `assessRisk` - Churn risk factors
5. `prioritizeCustomer` - Scoring algorithm

**Decision Matrix:**
```
CLV > $50k + High Winback Prob → Human sales team
CLV $10-50k + Medium Prob → Premium automated campaign
CLV < $10k + Low Prob → Basic campaign or ignore
```

**Output:**
```json
{
  "clv": 45600,
  "winback_probability": 0.65,
  "roi_estimate": 3.2,
  "priority": "HIGH",
  "recommendation": "Automated premium campaign with sales follow-up"
}
```

---

### 4️⃣ CAMPAIGN STRATEGIST Agent
**Model:** Claude 3.5 Sonnet (creative writing quality)
**Purpose:** Generate personalized, strategic email campaigns

**Capabilities:**
- Multi-email sequence generation
- Personalization based on churn analysis
- Strategy selection (aggressive discount vs value proposition)
- A/B test variant generation
- Email copywriting with brand voice

**Tools (Action Groups):**
1. `selectStrategy` - Choose campaign approach based on analysis
2. `generateEmailSequence` - Create 3-email series
3. `personalizeContent` - Deep personalization using all data
4. `createABVariants` - Generate test variants
5. `optimizeForGoal` - Optimize for open rate, click, or conversion

**Strategy Selection:**
```
Churn Reason: Pricing
Customer Value: High
Context: Competitor pricing lower

STRATEGY: Competitive Match + Added Value
Email 1: Acknowledge price sensitivity
Email 2: Match competitor price + highlight unique features
Email 3: Case study showing 2x ROI vs competitor
```

**Advanced Capabilities:**
- Uses Chain-of-Thought prompting for better creativity
- Considers customer industry, size, tech stack
- Adapts tone: Enterprise (formal) vs Startup (casual)
- Incorporates seasonal context (Q4 budgets, etc.)

---

## 🔧 Technical Implementation

### Agent Creation (AWS Console)

**Master Coordinator:**
```json
{
  "agentName": "revive-ai-coordinator",
  "foundationModel": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
  "instruction": "You are a customer win-back coordinator. Analyze churned customers and orchestrate specialist agents to create optimal win-back strategies. Make intelligent decisions about when to escalate to humans vs automate.",
  "actionGroups": [
    {
      "actionGroupName": "invoke-specialist-agent",
      "description": "Call specialist agents for deep analysis",
      "apiSchema": "s3://revive-ai-data/agents/coordinator-schema.json",
      "actionGroupExecutor": "arn:aws:lambda:us-east-1:xxx:function:coordinator-executor"
    },
    {
      "actionGroupName": "escalate-to-human",
      "description": "Create ticket for sales team",
      "apiSchema": "s3://revive-ai-data/agents/escalation-schema.json",
      "actionGroupExecutor": "arn:aws:lambda:us-east-1:xxx:function:escalation-executor"
    }
  ]
}
```

**Churn Detective:**
```json
{
  "agentName": "churn-detective",
  "foundationModel": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "instruction": "You are a churn investigation specialist. Use all available tools to deeply understand WHY a customer churned. Be thorough and analytical.",
  "actionGroups": [
    {
      "actionGroupName": "investigation-tools",
      "description": "Tools for investigating churn reasons",
      "apiSchema": "s3://revive-ai-data/agents/detective-schema.json",
      "actionGroupExecutor": "arn:aws:lambda:us-east-1:xxx:function:detective-executor"
    }
  ]
}
```

---

## 📊 Agent Orchestration Flow

### Example: Processing High-Value Customer

```python
# 1. Master Coordinator receives customer
customer = {
    "customer_id": "c017",
    "company_name": "SecureData Corp",
    "mrr": 1799,
    "churn_date": "2025-09-07",
    "cancellation_reason": "Security certifications not meeting our standards"
}

# 2. Master Coordinator reasoning
"""
This is high-value customer ($1799 MRR).
Let me first assess their value before deciding strategy.
"""
coordinator.invoke_tool("calculate_clv", customer_data)
# Result: CLV = $71,960 (40 months average tenure)

"""
CLV > $50k - this is CRITICAL customer.
Let me investigate the churn reason deeply.
"""
coordinator.invoke_agent("churn-detective", customer_data)

# 3. Churn Detective investigates
detective_reasoning = """
Customer mentioned "security certifications".
Let me search what certifications they might need.
"""
detective.invoke_tool("web_search", "SecureData Corp security requirements")
# Result: They're in healthcare - need HIPAA compliance

detective.invoke_tool("check_product_features", "HIPAA certification")
# Result: We DO have HIPAA compliance, but it's not well documented

detective_conclusion = {
    "root_cause": "Documentation gap, not actual product gap",
    "confidence": 95,
    "insight": "We have what they need, they just didn't know",
    "recommendation": "Re-engage with security documentation + HIPAA audit report"
}

# 4. Master Coordinator decides
"""
This is recoverable! They left due to misunderstanding.
High value + High confidence = Worth human intervention + premium campaign
"""
coordinator.invoke_tool("escalate_to_human", {
    "priority": "URGENT",
    "clv": 71960,
    "insight": "Have HIPAA cert, customer unaware",
    "action": "VP Sales reach out with compliance documentation"
})

coordinator.invoke_agent("campaign-strategist", {
    "customer": customer_data,
    "strategy": "education-based",
    "special_note": "Emphasize HIPAA compliance, send security docs"
})

# 5. Campaign Strategist generates
strategist_reasoning = """
Customer is in healthcare, values security.
Tone should be: Professional, detail-oriented, compliance-focused
Strategy: Education, not sales-y
"""
campaign = generate_campaign({
    "email_1": {
        "subject": "SecureData - Our HIPAA BAA & Compliance Documentation",
        "tone": "Professional, informative",
        "key_point": "We have the certifications you need"
    },
    # ...
})

# 6. Results aggregated
final_output = {
    "customer_id": "c017",
    "clv": 71960,
    "priority": "CRITICAL",
    "escalated_to": "VP_Sales",
    "sales_ticket": "TICK-12345",
    "automated_campaign": campaign,
    "reasoning_log": [...],  # Full agent thought process
    "estimated_win_probability": 0.78
}
```

---

## 🎯 Key Differentiators (Why This Wins)

### 1. True Autonomy
- Agents make real decisions, not just execute pipeline
- Different paths for different customers
- Self-correcting and adaptive

### 2. Multi-Agent Collaboration
- Specialist agents with focused expertise
- Coordinator orchestrates based on context
- Demonstrates advanced AI architecture

### 3. Reasoning Transparency
- Can show agent "thought process"
- Explainable AI for business users
- Build trust through transparency

### 4. Business Intelligence
- Not just automation, adds strategic insights
- Identifies patterns (e.g., "7 pricing churns today")
- Adapts strategy based on learnings

### 5. Human-in-the-Loop
- Smart escalation to sales team
- Agents augment humans, not replace
- Practical for real business use

---

## 🚀 Demo Flow (10 minutes)

### Demo A: Pipeline System (Backup - 3 min)
"First, let me show you our production pipeline..."
- Upload CSV
- Show batch processing
- Display results
- "This works reliably for standard cases"

### Demo B: Agent Orchestra (Primary - 7 min)
"Now let me show you our intelligent agent system..."

**Scenario 1: High-Value Customer (2 min)**
- Upload one high-value customer
- Show Master Coordinator reasoning
- Watch it invoke Value Calculator
- See escalation to sales team
- Show detailed reasoning log

**Scenario 2: Feature Request (2 min)**
- Customer churned for missing feature
- Churn Detective searches product roadmap
- Finds feature coming in Q1
- Campaign Strategist creates roadmap-focused campaign
- Show personalized result

**Scenario 3: Pattern Detection (2 min)**
- Upload 5 customers (all pricing issues)
- Agent identifies pattern
- Shows strategic insight: "Pricing problem detected"
- Generates product team alert
- Demonstrates system-level intelligence

**Wrap up (1 min)**
- Show architecture diagram
- Explain: 4 agents, 15+ tools, autonomous decision-making
- Meets all hackathon requirements authentically

---

## 📋 Hackathon Requirements Met

✅ **Bedrock AgentCore:** 4 Bedrock Agents created
✅ **Primitives:** 15+ action groups across agents
✅ **Reasoning LLMs:** Claude Sonnet + Haiku for reasoning
✅ **Autonomous:** Agents make real decisions
✅ **External Tools:** Web search, CRM, APIs, S3
✅ **Multi-agent:** Coordinator + 3 specialists collaborating

**Bonus:**
✅ Explainable AI (reasoning logs)
✅ Human-in-the-loop (escalation)
✅ Real business value (not just tech demo)
✅ Production considerations (fallback system)

---

## 💰 Cost Estimate

**Development:**
- Master Coordinator: 4 hours
- Churn Detective: 3 hours  
- Value Calculator: 2 hours
- Campaign Strategist: 3 hours
- Action Group Lambdas: 2 hours
- Agent Setup in AWS: 1 hour
- Testing & Integration: 3 hours

**Total: ~18 hours** (aggressive timeline)

**Runtime Costs:**
- Bedrock Agent invocations: ~$0.01 per customer
- Lambda: Minimal (within free tier)
- S3: Negligible

**50 customers: ~$0.50 total**

---

## 🎓 What Judges Will Learn

1. **You understand agentic AI** - Not just prompting
2. **You make strategic decisions** - Dual system approach
3. **You think about production** - Fallback, costs, reliability
4. **You solve real problems** - Not just tech for tech's sake
5. **You're innovative** - Multi-agent is cutting edge

This is a **winning** hackathon submission. 🏆

