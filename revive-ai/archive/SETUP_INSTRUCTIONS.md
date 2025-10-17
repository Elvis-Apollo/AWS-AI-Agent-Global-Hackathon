# Bedrock Agent Setup Instructions

## 🎯 Quick Start - Create Your First Agent

### Prerequisites
✅ IAM Role created: `ReviveAI-BedrockAgentRole`
✅ Lambda deployed: `bedrock-agent-executor`
✅ Schema uploaded: `s3://revive-ai-data/agents/churn-analyzer-schema.json`

---

## Step 1: Create Churn Analyzer Agent (AWS Console)

### Navigate to Bedrock Console
1. Go to AWS Console → Amazon Bedrock
2. Click **Agents** in left sidebar
3. Click **Create Agent**

### Agent Details
- **Agent name:** `revive-ai-churn-analyzer`
- **Description:** `Analyzes customer churn reasons and calculates customer value for win-back prioritization`
- **Agent resource role:** Select `ReviveAI-BedrockAgentRole`

Click **Create**

---

### Configure Agent

#### 1. Model Selection
- **Select model:** `Anthropic Claude 3.5 Haiku`
- **Model ID:** `us.anthropic.claude-3-5-haiku-20241022-v1:0`

#### 2. Instructions for the Agent
Paste this instruction:

```
You are a customer churn analysis specialist. Your role is to:

1. Analyze customer data to understand why they churned
2. Calculate their Customer Lifetime Value (CLV) to prioritize win-back efforts
3. Provide strategic recommendations for recovering the customer

When given customer information:
- First, use calculateCLV to determine their value and priority
- Then, use analyzeChurn to deeply understand their churn reason
- Provide clear, actionable insights

Be analytical, thorough, and strategic in your assessments.
```

Click **Save and exit**

---

### Add Action Group

#### Click "Add Action Group"

**Action group details:**
- **Action group name:** `churn-analysis-tools`
- **Description:** `Tools for analyzing churn and calculating customer value`
- **Action group type:** Select **Define with API schemas**

**Action group schema:**
- **Select:** S3
- **S3 URI:** `s3://revive-ai-data/agents/churn-analyzer-schema.json`

**Action group invocation:**
- **Select Lambda function:** `bedrock-agent-executor`

Click **Create**

---

### Create Alias

1. In the agent page, click **Create Alias**
2. **Alias name:** `PROD`
3. **Description:** `Production alias for churn analyzer`
4. Click **Create alias**

---

## Step 2: Get Agent IDs

After creation, note down:

```bash
# Get from AWS Console or run:
aws bedrock-agent list-agents --region us-east-1

# Note the agentId and agentAliasId
AGENT_ID=XXXXXXXXXX
ALIAS_ID=YYYYYYYYYY
```

---

## Step 3: Test the Agent

### Test via AWS Console

1. Go to agent page → **Test** tab
2. Enter test prompt:

```
Analyze this customer:
- Customer ID: c001
- Company: TechStart Inc
- MRR: $799
- Subscription: growth
- Churn Date: 2025-09-15
- Reason: Switched to competitor with better API documentation
```

3. Click **Run**
4. Watch the agent:
   - Call `calculateCLV` tool
   - Call `analyzeChurn` tool
   - Provide analysis and recommendations

### Expected Response:
```
Based on my analysis:

**Customer Value Assessment:**
- CLV: $19,176 (799 × 24 months)
- Priority: MEDIUM
- Win-back probability: 45%

**Churn Analysis:**
- Category: competition
- Confidence: 90%
- Key Insight: Customer switched due to better API documentation from competitor
- Recommendation: Re-engage with improved documentation and developer resources

**Strategic Recommendation:**
Standard automated campaign focusing on recent API documentation improvements
and developer experience enhancements.
```

---

## Step 4: Test via Python (bedrock-agent-runtime)

Create test script:

```python
import boto3
import json
import uuid

bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Replace with your agent IDs
AGENT_ID = 'YOUR_AGENT_ID'
ALIAS_ID = 'YOUR_ALIAS_ID'

def test_agent():
    session_id = str(uuid.uuid4())

    input_text = """
    Analyze this customer:
    - Customer ID: c017
    - Company: SecureData Corp
    - MRR: $1799
    - Subscription: enterprise
    - Churn Date: 2025-09-07
    - Reason: Security certifications not meeting our standards
    """

    response = bedrock_agent.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=ALIAS_ID,
        sessionId=session_id,
        inputText=input_text
    )

    # Parse streaming response
    event_stream = response['completion']
    for event in event_stream:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                text = chunk['bytes'].decode('utf-8')
                print(text, end='')

if __name__ == '__main__':
    test_agent()
```

Run:
```bash
python test_agent.py
```

---

## Step 5: Integration with API Handler

Update your API handler to use the agent:

```python
import boto3
import json
import uuid

bedrock_agent = boto3.client('bedrock-agent-runtime')

# Agent IDs (from Step 2)
CHURN_ANALYZER_AGENT_ID = 'YOUR_AGENT_ID'
CHURN_ANALYZER_ALIAS_ID = 'YOUR_ALIAS_ID'

def process_customer_with_agent(customer):
    """Process customer using Bedrock Agent instead of direct Lambda calls."""

    session_id = str(uuid.uuid4())

    # Format customer data for agent
    input_text = f"""
    Analyze this customer:
    - Customer ID: {customer['customer_id']}
    - Company: {customer['company_name']}
    - MRR: ${customer['mrr']}
    - Subscription: {customer['subscription_tier']}
    - Churn Date: {customer['churn_date']}
    - Reason: {customer.get('cancellation_reason', 'Not provided')}
    """

    # Invoke agent
    response = bedrock_agent.invoke_agent(
        agentId=CHURN_ANALYZER_AGENT_ID,
        agentAliasId=CHURN_ANALYZER_ALIAS_ID,
        sessionId=session_id,
        inputText=input_text,
        enableTrace=True  # Capture reasoning
    )

    # Collect response
    result_text = ""
    reasoning_trace = []

    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                result_text += chunk['bytes'].decode('utf-8')

        if 'trace' in event:
            # Capture agent reasoning for transparency
            reasoning_trace.append(event['trace'])

    return {
        'analysis': result_text,
        'reasoning_trace': reasoning_trace,
        'session_id': session_id
    }
```

---

## 🎯 Success Criteria

After completing setup, you should have:

✅ **Agent created and active** in Bedrock Console
✅ **2 working primitives:** calculateCLV, analyzeChurn
✅ **Agent callable** via bedrock-agent-runtime API
✅ **Reasoning visible** via enableTrace parameter
✅ **Meets hackathon requirements:**
   - Uses Bedrock AgentCore ✓
   - Has primitives/action groups ✓
   - Uses reasoning LLM ✓
   - Shows autonomous decision-making ✓
   - Integrates external tools (Lambda) ✓

---

## 🐛 Troubleshooting

### Agent returns errors
- Check Lambda logs: `aws logs tail /aws/lambda/bedrock-agent-executor --follow`
- Verify IAM role has Lambda invoke permissions
- Check schema is valid JSON in S3

### Tools not being called
- Review agent instructions - be explicit about when to use tools
- Check action group schema matches Lambda implementation
- Verify Lambda has necessary permissions (S3, Bedrock)

### Empty responses
- Agent may need clearer instructions
- Try more specific input prompts
- Check enableTrace to see agent reasoning

---

## 📊 Next Steps

1. **Test thoroughly** - Try different customer scenarios
2. **Create more agents** - Campaign Generator, Coordinator
3. **Add more tools** - Web search, escalation, save results
4. **Build UI** - Show agent reasoning in frontend
5. **Demo prep** - Create compelling demo scenarios

---

## 🚀 Quick Command Reference

```bash
# List agents
aws bedrock-agent list-agents --region us-east-1

# Get agent details
aws bedrock-agent get-agent --agent-id AGENT_ID --region us-east-1

# Update agent
aws bedrock-agent update-agent --agent-id AGENT_ID --agent-name "..." --region us-east-1

# List aliases
aws bedrock-agent list-agent-aliases --agent-id AGENT_ID --region us-east-1

# Test via CLI (use Python for better experience)
aws bedrock-agent-runtime invoke-agent \
  --agent-id AGENT_ID \
  --agent-alias-id ALIAS_ID \
  --session-id $(uuidgen) \
  --input-text "Analyze customer c001" \
  --region us-east-1
```

---

**Created:** 2025-10-10
**Status:** Ready for implementation
**Time to complete:** ~30 minutes for first agent
