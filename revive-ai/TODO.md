# Bedrock Agent Implementation - Execution Plan

**Goal:** Transform current pipeline into Multi-Agent Orchestra using Amazon Bedrock AgentCore

**Timeline:** 12-16 hours (aggressive but achievable)
**Status:** ✅ Current pipeline working as BACKUP | 🚧 Agent system in progress

---

## 📊 Priority Matrix

### P0 - CRITICAL (Must have for demo)
- Core agent functionality
- At least 1 working primitive
- Basic reasoning demonstration

### P1 - HIGH (Should have for good demo)
- Multiple agents working together
- 3-5 primitives/tools
- Visible reasoning logs

### P2 - NICE TO HAVE (If time permits)
- Advanced features
- Polish and optimization
- Additional tools

---

## 🎯 Phase 1: Foundation (4-5 hours) - DO FIRST

### Task 1.1: Set up Bedrock Agent Infrastructure
**Priority:** P0 - CRITICAL
**Time:** 2 hours
**Parallel:** ❌ Must be done sequentially
**Owner:** Single developer

**Subtasks:**
- [x] Read Bedrock Agents documentation
- [ ] Create IAM role for Bedrock Agents (with Lambda invoke permissions)
- [ ] Create S3 bucket for agent schemas (or use existing `revive-ai-data`)
- [ ] Test basic agent creation in AWS Console
- [ ] Verify agent can be invoked via bedrock-agent-runtime

**Deliverable:** One working Bedrock Agent that can be invoked

**Blockers:** None - can start immediately

**Commands:**
```bash
# Create agent IAM role
aws iam create-role --role-name BedrockAgentRole --assume-role-policy-document file://agent-trust-policy.json

# Attach policies
aws iam attach-role-policy --role-name BedrockAgentRole --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
aws iam attach-role-policy --role-name BedrockAgentRole --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
```

---

### Task 1.2: Create Action Group Executor Lambda (Foundation)
**Priority:** P0 - CRITICAL  
**Time:** 1.5 hours
**Parallel:** ✅ Can work on this while agent is being created
**Owner:** Could be parallel developer

**Subtasks:**
- [ ] Create new Lambda function `bedrock-agent-executor`
- [ ] Implement action group handler pattern
- [ ] Add routing logic for different tools
- [ ] Test with mock agent invocation
- [ ] Deploy and get ARN

**Deliverable:** Lambda that can handle Bedrock Agent action group callbacks

**Code Structure:**
```python
# bedrock-agent-executor/lambda_function.py
def lambda_handler(event, context):
    # Parse Bedrock Agent request
    action_group = event['actionGroup']
    api_path = event['apiPath']
    parameters = event.get('parameters', [])
    
    # Route to appropriate handler
    if action_group == 'churn-analysis':
        if api_path == '/analyzeChurn':
            return handle_analyze_churn(parameters)
    
    # Return in Bedrock Agent format
    return {
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpStatusCode': 200,
            'responseBody': {...}
        }
    }
```

**Blockers:** None

---

### Task 1.3: Create OpenAPI Schema for First Agent
**Priority:** P0 - CRITICAL
**Time:** 1 hour  
**Parallel:** ✅ Can be done in parallel with Task 1.2
**Owner:** Could be parallel developer or same

**Subtasks:**
- [ ] Define schema for "Churn Analyzer" agent
- [ ] Create 2-3 core tools (analyzeChurn, calculateValue, searchWeb)
- [ ] Upload schema to S3
- [ ] Validate schema format

**Deliverable:** `churn-analyzer-schema.json` in S3

**File:** Already started in `/bedrock-agent/action-group-schema.json`

**Blockers:** None

---

### Task 1.4: Create First Bedrock Agent (Churn Analyzer)
**Priority:** P0 - CRITICAL
**Time:** 30 min
**Parallel:** ❌ Requires Tasks 1.1, 1.2, 1.3 complete
**Owner:** Single developer

**Subtasks:**
- [ ] Create agent in AWS Console (or via CLI)
- [ ] Configure foundation model (Claude 3.5 Haiku)
- [ ] Link action group to Lambda executor
- [ ] Link OpenAPI schema from S3
- [ ] Create agent alias
- [ ] Test invocation with sample input

**Deliverable:** Working Bedrock Agent that can be invoked

**AWS Console Steps:**
1. Bedrock Console → Agents → Create Agent
2. Name: `revive-ai-churn-analyzer`
3. Model: `us.anthropic.claude-3-5-haiku-20241022-v1:0`
4. Instructions: "Analyze customer churn and determine category, confidence, and insights"
5. Add Action Group → Link Lambda + Schema
6. Create alias: `PROD`

**Blockers:** Tasks 1.1, 1.2, 1.3

---

## ✅ Phase 1 Checkpoint
**After Phase 1, you should have:**
- ✅ 1 working Bedrock Agent
- ✅ Agent can call at least 1 primitive/tool
- ✅ Can invoke agent via API and get response
- ✅ Meets minimum hackathon requirements

**Test:** Invoke agent with one customer, see it analyze churn

---

## 🎯 Phase 2: Core Multi-Agent (4-5 hours) - DO SECOND

### Task 2.1: Implement Core Action Group Tools
**Priority:** P0 - CRITICAL
**Time:** 2 hours
**Parallel:** ✅ Can split tools across developers
**Owner:** Can be 2 developers in parallel

**Subtasks:**
- [ ] Implement `analyzeChurn` - reuse existing analysis logic
- [ ] Implement `calculateCLV` - simple MRR × 24 months calculation
- [ ] Implement `generateCampaign` - reuse existing campaign logic
- [ ] Implement `saveResults` - S3 write operation
- [ ] Test each tool independently

**Deliverable:** 4 working primitives in executor Lambda

**Tools to build:**

**Tool 1: analyzeChurn** (30 min)
```python
def handle_analyze_churn(parameters):
    customer = extract_customer_from_params(parameters)
    # Call existing ChurnAnalysisAgent logic
    analysis_agent = ChurnAnalysisAgent(bedrock_client)
    result = analysis_agent.analyze(customer)
    return format_for_agent(result)
```

**Tool 2: calculateCLV** (20 min)
```python
def handle_calculate_clv(parameters):
    mrr = get_param(parameters, 'mrr')
    # Simple calculation
    clv = mrr * 24  # 2 year average
    priority = "HIGH" if clv > 20000 else "MEDIUM" if clv > 5000 else "LOW"
    return {'clv': clv, 'priority': priority}
```

**Tool 3: generateCampaign** (30 min)
```python
def handle_generate_campaign(parameters):
    customer = extract_customer_from_params(parameters)
    analysis = get_param(parameters, 'analysis')
    # Call existing CampaignGenerationAgent
    campaign_agent = CampaignGenerationAgent(bedrock_client)
    result = campaign_agent.generate(customer, analysis)
    return format_for_agent(result)
```

**Tool 4: saveResults** (20 min)
```python
def handle_save_results(parameters):
    upload_id = get_param(parameters, 'upload_id')
    customer_id = get_param(parameters, 'customer_id')
    data = get_param(parameters, 'data')
    # Save to S3
    s3.put_object(
        Bucket='revive-ai-data',
        Key=f'results/{upload_id}/customers/{customer_id}.json',
        Body=json.dumps(data)
    )
    return {'success': True}
```

**Blockers:** Phase 1 complete

---

### Task 2.2: Create Master Coordinator Agent
**Priority:** P1 - HIGH
**Time:** 1.5 hours
**Parallel:** ⚠️ Requires Task 2.1 partially complete
**Owner:** Single developer

**Subtasks:**
- [ ] Create OpenAPI schema for coordinator tools
- [ ] Implement coordinator action group (invoke other agents, escalate)
- [ ] Create coordinator agent in AWS Console
- [ ] Configure with stronger model (Claude Sonnet)
- [ ] Write coordinator instructions (orchestration logic)
- [ ] Test coordinator invoking churn analyzer

**Deliverable:** Coordinator agent that can orchestrate other agents

**Coordinator Instructions:**
```
You are a customer win-back coordinator. Your job is to:
1. Assess customer value using calculateCLV
2. If CLV > $50,000, escalate to human sales team
3. Otherwise, invoke churnAnalyzer to understand why they churned
4. Based on churn category, invoke campaignGenerator
5. Save all results using saveResults

Be strategic and autonomous in your decision-making.
```

**Blockers:** Task 2.1 (at least calculateCLV done)

---

### Task 2.3: Create Campaign Generator Agent  
**Priority:** P1 - HIGH
**Time:** 1 hour
**Parallel:** ✅ Can work in parallel with 2.2
**Owner:** Could be parallel developer

**Subtasks:**
- [ ] Create OpenAPI schema for campaign tools
- [ ] Implement campaign generation tool
- [ ] Create agent in AWS Console
- [ ] Configure with Sonnet (for better writing)
- [ ] Test campaign generation

**Deliverable:** Campaign generator agent

**Blockers:** Task 2.1 (generateCampaign tool)

---

### Task 2.4: Integrate Agent Invocation into API Handler
**Priority:** P0 - CRITICAL
**Time:** 1 hour
**Parallel:** ❌ Requires 2.1, 2.2 complete
**Owner:** Single developer

**Subtasks:**
- [ ] Update API handler Lambda to use bedrock-agent-runtime
- [ ] Add agent invocation logic
- [ ] Handle agent responses
- [ ] Add fallback to current pipeline if agent fails
- [ ] Test end-to-end flow

**Deliverable:** API can invoke agents instead of direct Lambdas

**Code:**
```python
import boto3

bedrock_agent = boto3.client('bedrock-agent-runtime')

def process_with_agent(customer):
    session_id = generate_session_id()
    
    response = bedrock_agent.invoke_agent(
        agentId='COORDINATOR_AGENT_ID',
        agentAliasId='PROD',
        sessionId=session_id,
        inputText=f"Process this customer: {json.dumps(customer)}"
    )
    
    # Parse streaming response
    result = parse_agent_response(response)
    return result
```

**Blockers:** Tasks 2.1, 2.2

---

## ✅ Phase 2 Checkpoint
**After Phase 2, you should have:**
- ✅ 3 Bedrock Agents (Coordinator, Churn Analyzer, Campaign Generator)
- ✅ 4-5 working primitives/tools
- ✅ Agents orchestrating each other
- ✅ End-to-end flow working
- ✅ All hackathon requirements met

**Test:** Upload 1 customer, watch it flow through multi-agent system

---

## 🎯 Phase 3: Enhanced Features (3-4 hours) - DO THIRD

### Task 3.1: Add Reasoning Visibility
**Priority:** P1 - HIGH
**Time:** 1.5 hours
**Parallel:** ✅ Can work independently
**Owner:** Single developer

**Subtasks:**
- [ ] Capture agent reasoning/trace from responses
- [ ] Store reasoning logs to S3
- [ ] Add reasoning display to frontend
- [ ] Create "Agent Thought Process" view

**Deliverable:** UI showing agent decision-making process

**Value:** Demonstrates explainable AI, judges love this

**Blockers:** Phase 2 complete

---

### Task 3.2: Add Value-Based Escalation
**Priority:** P1 - HIGH  
**Time:** 1 hour
**Parallel:** ✅ Can work in parallel with 3.1
**Owner:** Could be parallel developer

**Subtasks:**
- [ ] Implement escalation tool in executor
- [ ] Add logic to coordinator for high-value customers
- [ ] Create mock "sales ticket" output
- [ ] Show escalation in UI

**Deliverable:** High-value customers get escalated to humans

**Value:** Shows human-in-the-loop, practical AI

**Blockers:** Phase 2 complete

---

### Task 3.3: Add Web Search Tool (Optional)
**Priority:** P2 - NICE TO HAVE
**Time:** 1.5 hours
**Parallel:** ✅ Independent
**Owner:** Single developer

**Subtasks:**
- [ ] Integrate with web search API (SerpAPI or similar)
- [ ] Add searchWeb tool to action group
- [ ] Test churn analyzer using web search
- [ ] Show in demo

**Deliverable:** Agent can search web for company info

**Value:** Shows external tool integration

**Blockers:** Phase 2 complete

---

### Task 3.4: Add Pattern Detection
**Priority:** P2 - NICE TO HAVE
**Time:** 1 hour
**Parallel:** ✅ Independent
**Owner:** Single developer

**Subtasks:**
- [ ] Add logic to detect patterns across customers
- [ ] Alert when 5+ customers churn for same reason
- [ ] Display insights in UI
- [ ] Show in demo

**Deliverable:** System-level intelligence

**Value:** Shows learning/adaptation

**Blockers:** Phase 2 complete

---

## ✅ Phase 3 Checkpoint
**After Phase 3, you should have:**
- ✅ Reasoning transparency
- ✅ Smart escalation
- ✅ (Optional) External tool integration
- ✅ (Optional) Pattern detection
- ✅ Demo-ready system

---

## 🎯 Phase 4: Testing & Polish (2-3 hours) - DO LAST

### Task 4.1: End-to-End Testing
**Priority:** P0 - CRITICAL
**Time:** 1 hour
**Parallel:** ❌ Sequential testing
**Owner:** Full team

**Subtasks:**
- [ ] Test with 1 customer (happy path)
- [ ] Test with 5 customers (batch)
- [ ] Test with high-value customer (escalation path)
- [ ] Test error scenarios
- [ ] Verify all agents working
- [ ] Check reasoning logs

**Deliverable:** Confidence in demo reliability

**Blockers:** Phase 3 complete

---

### Task 4.2: Demo Preparation
**Priority:** P0 - CRITICAL
**Time:** 1 hour
**Parallel:** ✅ Can split tasks
**Owner:** Full team

**Subtasks:**
- [ ] Create 3 demo scenarios (normal, high-value, pattern)
- [ ] Prepare demo script
- [ ] Test demo flow timing (< 10 min)
- [ ] Create fallback plan if agent system fails
- [ ] Prepare architecture diagram for presentation

**Deliverable:** Polished demo ready to present

**Blockers:** Task 4.1

---

### Task 4.3: Documentation
**Priority:** P1 - HIGH
**Time:** 1 hour
**Parallel:** ✅ Can split docs
**Owner:** Full team

**Subtasks:**
- [ ] Update README with agent architecture
- [ ] Document agent setup instructions
- [ ] Add "How it works" explanation
- [ ] Update SECURITY_COMPLIANCE.md with agent details
- [ ] Create architecture diagram

**Deliverable:** Clear documentation for judges

**Blockers:** None (can be parallel)

---

## ✅ Phase 4 Checkpoint
**After Phase 4, you should have:**
- ✅ Tested, reliable system
- ✅ Polished demo
- ✅ Clear documentation
- ✅ Ready to present

---

## 📅 Suggested Timeline

### Day 1 (8 hours)
- **Hours 1-2:** Phase 1.1, 1.2, 1.3 (parallel)
- **Hours 3-4:** Phase 1.4 + testing
- **Hours 5-8:** Phase 2.1, 2.2, 2.3 (parallel)

**End of Day 1:** Have 3 agents with 4-5 tools working

---

### Day 2 (8 hours)
- **Hours 1-2:** Phase 2.4 (integration)
- **Hours 3-5:** Phase 3.1, 3.2 (parallel)
- **Hours 6-7:** Phase 4.1, 4.2 (testing + demo prep)
- **Hour 8:** Phase 4.3 (documentation) + buffer

**End of Day 2:** Ready to demo

---

## 🚨 Risk Mitigation

### Risk 1: Agent Creation Takes Longer Than Expected
**Mitigation:** Have current pipeline as fallback
**Contingency:** Demo current system + show agent architecture slides

### Risk 2: Agent Invocation Fails During Demo
**Mitigation:** Pre-record demo video as backup
**Contingency:** Switch to current pipeline, explain agent vision

### Risk 3: Tools Don't Work as Expected
**Mitigation:** Test each tool independently before integration
**Contingency:** Reduce to 1-2 agents with 2-3 tools (still meets requirements)

### Risk 4: Run Out of Time
**Mitigation:** Prioritize P0 tasks first
**Contingency:** Phase 1 + 2 = minimum viable agent demo

---

## ✅ Definition of Done

### Minimum Viable (P0 - Must Have)
- [ ] At least 1 Bedrock Agent created
- [ ] At least 1 action group with 2+ primitives
- [ ] Agent uses reasoning LLM (Claude)
- [ ] Agent makes autonomous decisions
- [ ] Agent integrates with external tools (S3, Lambda)
- [ ] Can demo end-to-end flow

### Good Demo (P1 - Should Have)
- [ ] 2-3 Bedrock Agents orchestrating
- [ ] 4-5 primitives/tools
- [ ] Visible reasoning logs
- [ ] Smart escalation logic
- [ ] Clean UI showing agent workflow

### Excellent Demo (P2 - Nice to Have)
- [ ] Multi-agent collaboration
- [ ] Web search integration
- [ ] Pattern detection
- [ ] Comprehensive documentation
- [ ] Polished presentation

---

## 📊 Progress Tracking

**Current Status:** Phase 0 - Planning Complete ✅

**Next Up:** Phase 1.1 - Set up Bedrock Agent Infrastructure

**Estimated Completion:** Day 2, Hour 8

---

## 🎯 Success Metrics

### Technical
- [ ] All agents invokable via API
- [ ] <5 second response time per customer
- [ ] >90% success rate
- [ ] Reasoning logs captured

### Demo
- [ ] <10 minute demo flow
- [ ] 3 scenarios prepared
- [ ] Fallback plan ready
- [ ] Architecture explained clearly

### Hackathon Requirements
- [x] Uses Bedrock AgentCore ✅
- [ ] Has primitives/action groups
- [x] Uses reasoning LLMs ✅
- [ ] Shows autonomous decision-making
- [ ] Integrates external tools
- [ ] Multi-agent if possible

---

## 💡 Pro Tips

1. **Test Early, Test Often** - Don't wait until end to test agents
2. **Keep Current System** - Always have fallback demo
3. **Document As You Go** - Easier than trying to remember later
4. **Parallel Work** - Split tasks when possible to save time
5. **Don't Over-Engineer** - P0 tasks first, P2 only if time

---

**Last Updated:** 2025-10-10
**Owner:** Revive AI Team
**Status:** Ready to Execute

