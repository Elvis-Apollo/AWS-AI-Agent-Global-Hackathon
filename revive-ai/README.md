# 🤖 ReviveAI - Intelligent Customer Win-Back System

> **AWS AI Agent Global Hackathon 2025**
> Multi-agent AI system for intelligent customer churn analysis and win-back campaigns

[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock_Agents-FF9900?logo=amazon-aws)](https://aws.amazon.com/bedrock/)
[![Claude 3.5](https://img.shields.io/badge/Model-Claude_3.5_Haiku-8B5CF6)](https://www.anthropic.com/claude)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Hackathon_Ready-success)](.)

---

## 🎯 What It Does

ReviveAI analyzes **why customers churn** and generates **intelligent win-back strategies** by:

- 🔍 **Gathering intelligence** from CRM, product roadmap, and web search
- 🧠 **Discovering truth** - stated reason vs. actual behavior
- ⏰ **Perfect timing** - identifies when to reach out based on product launches
- 💰 **Value prioritization** - focuses on high-CLV customers
- 📊 **Evidence-based** - every recommendation backed by data

---

## ⚡ Quick Demo

**Input:**
```
Customer c007 says: "Too expensive"
MRR: $199, Tier: Starter
```

**Agent Analysis:**
```
✅ CLV Calculation: $4,776 (LOW priority)
✅ CRM Check: 15% feature adoption, no integrations
✅ Insight: Engagement problem, NOT price
✅ Recommendation: Training & onboarding (not discounts)
```

**Result:** Agent discovered the real issue by cross-referencing data sources!

---

## 🏗️ Architecture

```
User Query
    ↓
Coordinator Agent (orchestrates)
    ↓
ChurnAnalyzer Agent (5 tools)
    ├─ calculateCLV → Customer value
    ├─ getCRMHistory → Usage patterns & support tickets
    ├─ searchCompanyInfo → Funding, growth, news
    ├─ checkProductRoadmap → Upcoming features
    └─ analyzeChurn → NLP categorization
    ↓
CampaignGenerator Agent (2 tools)
    ├─ generateEmailSequence
    └─ personalizeContent
    ↓
Intelligent Win-Back Strategy
```

**Technology:**
- 3 Amazon Bedrock Agents
- 11 Lambda-backed tools
- Claude 3.5 Haiku
- S3 knowledge base

---

## 📊 Test Results

| Test | Scenario | Agent Intelligence | Result |
|------|----------|-------------------|--------|
| ✅ 1 | Technical pain point | Found roadmap solution (API v2.0) | HIGH priority |
| ✅ 2 | Minimal information | Gathered all data autonomously | Complete discovery |
| ✅ 3 | "Too expensive" | Discovered 15% adoption issue | Correct diagnosis |
| ✅ 4 | Compliance churn | Found SOC 2 in 6 months | Perfect timing |
| ✅ 5 | Company research | $15M funding, 200% growth | Clear recommendation |

**Success Rate:** 5/5 scenarios validated

---

## 🏆 Hackathon Requirements Met

✅ Amazon Bedrock AgentCore (3 agents)
✅ Action Groups/Primitives (11 tools)
✅ External Integrations (S3, Web Search, CRM)
✅ Multi-source Intelligence (5 sources)
✅ Autonomous Decision Making

---

## 📂 Documentation

- **[SYSTEM_DOCUMENTATION.md](./SYSTEM_DOCUMENTATION.md)** - Complete technical documentation
- **[TEST_SCENARIOS.md](./bedrock-agent/TEST_SCENARIOS.md)** - 5 validation scenarios
- **[DEMO_SHOWCASE.md](./bedrock-agent/DEMO_SHOWCASE.md)** - Demo guide and examples

---

**🚀 Ready for AWS AI Agent Global Hackathon Evaluation!**
