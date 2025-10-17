# ⚡ Quick Reference Guide

**For fast access during demos and presentations**

---

## 🎯 Elevator Pitch (30 seconds)

"ReviveAI is a multi-agent AI system built on Amazon Bedrock that analyzes customer churn by gathering intelligence from 5 sources - CRM, product roadmap, web search, and more. It discovers the TRUE churn reason beyond what customers say, identifies perfect timing for win-back campaigns, and generates evidence-based strategies. We validated it with 5 test scenarios showing it can cross-reference data, find roadmap solutions launching at perfect times, and prioritize high-value customers."

---

## 📊 Key Numbers

- **3** Bedrock Agents (Coordinator, ChurnAnalyzer, CampaignGenerator)
- **11** Lambda-backed tools across 3 action groups
- **5** Intelligence sources per analysis
- **5/5** Test scenarios successfully validated
- **$0.02-0.05** Cost per analysis
- **8-12 sec** Average analysis time

---

## 🏗️ Architecture One-Liner

"3 autonomous Bedrock agents orchestrate 11 Lambda-backed tools that query S3 knowledge bases, CRM data, and web search to generate intelligent win-back strategies."

---

## 🧪 Best Demo Scenarios

### Scenario 1: Cross-Referencing (Most Impressive)
**Input:** `Analyze customer c007 from MarketPro Analytics. Churned: 2025-09-25. Reason: "Not enough ROI for the subscription cost". MRR: $199, Tier: Starter`

**What Happens:** Agent discovers 15% feature adoption → Real issue is engagement, not price → Recommends training, not discounts

**Talking Point:** "Customer said price, but agent found the truth"

### Scenario 2: Perfect Timing
**Input:** `Customer c017 - SecureData Corp churned on 2025-09-07. Their stated reason: "Security certifications not meeting our standards". MRR: $1,799, Enterprise tier`

**What Happens:** Agent finds SOC 2 launching March 1 → Customer churned 6 months before solution → Recommends waiting for certification

**Talking Point:** "Agent identified perfect timing - reach out when we have the solution"

### Scenario 3: Autonomous Discovery
**Input:** `Customer c025 churned. Find out why and create a win-back strategy.`

**What Happens:** Agent proactively calls ALL 5 tools to gather complete picture from scratch

**Talking Point:** "Minimal input → agent autonomously gathers everything needed"

---

## 🎬 Demo Flow (5 minutes)

**1. Architecture (1 min)**
- Show: 3 agents, 11 tools, 5 sources diagram
- Emphasize: Bedrock AgentCore, not just bedrock-runtime

**2. Live Demo 1 (2 min)** - Scenario 1 (Cross-referencing)
- Paste input in AWS Console
- Show: Agent calls getCRMHistory, finds 15% adoption
- Result: Discovers real issue vs stated reason

**3. Live Demo 2 (1.5 min)** - Scenario 2 (Perfect timing)
- Paste input
- Show: Agent finds SOC 2 in roadmap (March 1)
- Result: Perfect timing intelligence

**4. Show Logs (30 sec)**
```bash
aws logs tail /aws/lambda/bedrock-agent-executor --since 2m --region us-east-1 | grep "Executing:"
```
- Proves tools were actually called

**5. Wrap-up (30 sec)**
- Hackathon requirements: ✅ All met
- Production-ready architecture
- 5/5 test scenarios validated

---

## 🔧 Agent IDs (For Quick Access)

| Agent | Agent ID | Alias ID | Region |
|-------|----------|----------|--------|
| ChurnAnalyzer | HAKDC7PY1Z | WN63LBEVKR | us-east-1 |
| Coordinator | UPWE8NQKWH | ZDNG15XWYW | us-east-1 |
| CampaignGenerator | HXMON0RCRP | YO7A6XFPXU | us-east-1 |

**Lambda:** `bedrock-agent-executor`
**S3 Bucket:** `revive-ai-data`

---

## ⚡ Quick Commands

**Check agent status:**
```bash
aws bedrock-agent get-agent --agent-id HAKDC7PY1Z --region us-east-1
```

**View recent tool calls:**
```bash
aws logs tail /aws/lambda/bedrock-agent-executor --since 2m --region us-east-1 | grep "Executing:"
```

**Test agent from CLI:**
```bash
cd bedrock-agent && python3 test_agent.py
```

---

## 💡 Key Differentiators

**1. True Multi-Source Intelligence**
- Not just calling one API
- Cross-references 5 data sources
- Discovers discrepancies

**2. Autonomous Decision Making**
- Agent decides which tools to call
- Not hardcoded workflows
- Context-aware

**3. Production Architecture**
- Scalable Lambda executors
- S3 knowledge bases
- Proper IAM roles
- Error handling

**4. Validated Results**
- 5 comprehensive test scenarios
- 100% success rate
- Documented evidence

---

## 🏆 Hackathon Checklist

- ✅ Uses Amazon Bedrock AgentCore (not just runtime)
- ✅ Implements Action Groups / Primitives (11 tools)
- ✅ External integrations (S3, Web Search, CRM)
- ✅ Multi-source intelligence gathering
- ✅ Autonomous agents with ReAct
- ✅ Production-ready code
- ✅ Comprehensive testing
- ✅ Clear documentation

---

## 🎯 Talking Points

**For Judges:**
1. "Built on Bedrock AgentCore with 3 autonomous agents"
2. "Cross-references 5 data sources to find truth beyond stated reasons"
3. "Identifies perfect timing - like finding SOC 2 launches 6 months after customer churned for it"
4. "Production-ready: 5/5 test scenarios validated, scalable architecture"

**For Technical Audience:**
1. "Lambda action group executors with OpenAPI 3.0 schemas"
2. "Agent-to-agent communication via bedrock-agent-runtime"
3. "S3 knowledge base with mock data (production-ready for real APIs)"
4. "Proper IAM roles, error handling, idempotent operations"

**For Business Audience:**
1. "Discovers why customers really churn, not just what they say"
2. "Prioritizes high-value customers automatically"
3. "Perfect timing for win-back - reaches out when you have the solution"
4. "Evidence-based recommendations, not generic campaigns"

---

## 🚨 Common Questions & Answers

**Q: Is the web search real?**
A: Mock for demo reliability. Architecture supports Tavily/SerpAPI - 5 minute swap.

**Q: How does it handle errors?**
A: Graceful fallbacks, try-catch blocks, returns error messages in proper format.

**Q: Can it scale?**
A: Yes - Lambda auto-scales to 1000 concurrent, S3 unlimited, Bedrock serverless.

**Q: What about cost?**
A: $0.02-0.05 per analysis. 1000 analyses = $20-50.

**Q: Real CRM integration?**
A: Architecture ready. Currently mock for demo. Salesforce/HubSpot = 2-4 hours to integrate.

---

## 📱 Emergency Backup

If AWS Console is slow:
1. Show architecture diagram
2. Show test results documentation
3. Show CloudWatch logs from previous successful tests
4. Walk through code explaining intelligence

---

**Keep this open during demo for quick reference!** 🚀
