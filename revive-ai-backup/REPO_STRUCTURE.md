# Repository Structure (After Cleanup)

This document shows the final repository structure after cleanup, optimized for public GitHub submission.

---

## 📁 Final Directory Tree

```
revive-ai/
│
├── 📄 README.md                          # Main repository overview (⚠️ needs update)
├── 📄 LICENSE                            # License file (TODO: add)
├── 📄 SYSTEM_DOCUMENTATION.md            # Complete production documentation (✅ current)
├── 📄 CLEANUP_PLAN.md                    # This cleanup plan
├── 📄 CLEANUP_SUMMARY.md                 # Quick cleanup summary
├── 📄 REPO_STRUCTURE.md                  # This file
├── 🔧 cleanup.sh                         # Automated cleanup script
├── 📄 .gitignore                         # Git ignore rules (✅ good)
│
├── 📁 frontend/                          # Production Web Application
│   ├── index.html                        # React SPA with Babel/Material-UI
│   └── README.md                         # Frontend documentation (TODO: create)
│
├── 📁 lambda/                            # AWS Lambda Functions
│   │
│   ├── 📁 api_handler/                   # Main API Lambda (Production)
│   │   ├── lambda_function.py            # Upload, Process, Results endpoints
│   │   │                                 # Async processing with self-invocation
│   │   │                                 # Sequential customer processing
│   │   └── requirements.txt              # Python dependencies
│   │
│   ├── 📁 bedrock_agent_executor/        # Bedrock Agent Action Group Executor
│   │   ├── lambda_function.py            # 5 tool handlers (calculateCLV, etc.)
│   │   └── requirements.txt              # Python dependencies
│   │
│   ├── 📁 shared/                        # Shared Lambda Layer
│   │   ├── __init__.py
│   │   ├── agents.py                     # CampaignGenerationAgent
│   │   ├── bedrock_client.py             # Bedrock API wrapper
│   │   ├── s3_helper.py                  # S3 operations helper
│   │   └── schemas.py                    # Data schemas
│   │
│   └── README.md                         # Lambda documentation (TODO: create)
│
├── 📁 bedrock-agent/                     # Bedrock Agent Configuration
│   │
│   ├── 📄 churn-analyzer-schema.json     # OpenAPI 3.0 schema for ChurnAnalyzer
│   │                                     # Defines 5 tools (Production)
│   │
│   ├── 🐍 test_agent.py                  # Agent testing script
│   ├── 🐍 test_minimal_input.py          # Minimal test script
│   ├── 🐍 test_multi_agent.py            # Multi-agent test (legacy)
│   ├── 🐍 demo_all_tools.py              # Demo all 5 tools
│   │
│   ├── 📄 README.md                      # Agent documentation
│   ├── 📄 TEST_SCENARIOS.md              # 5 validation scenarios
│   ├── 📄 DEMO_SHOWCASE.md               # Demo guide and examples
│   ├── 📄 EXTERNAL_TOOLS_COMPLETE.md     # External tool integration docs
│   │
│   ├── 📄 action-group-schema.json       # Action group definition (legacy)
│   ├── 📄 agent-permissions-policy.json  # IAM policy for agent
│   └── 📄 agent-trust-policy.json        # IAM trust policy for agent
│
├── 📁 iam/                               # IAM Policies and Roles
│   ├── lambda-role-policy.json           # Lambda execution role policy
│   ├── lambda-trust-policy.json          # Lambda trust relationship
│   ├── agent-permissions-policy.json     # Bedrock agent permissions
│   └── agent-trust-policy.json           # Bedrock agent trust policy
│
├── 📁 scripts/                           # Deployment & Setup Scripts
│   ├── deploy.sh                         # Main deployment script
│   ├── create-api-gateway.sh             # API Gateway setup
│   └── api-gateway-url.txt               # API Gateway endpoint URL
│
├── 📁 demo_data/                         # Demo & Example Data
│   ├── demo_results.json                 # Example processing results
│   ├── test_intelligence_summary.html    # Intelligence summary demo
│   ├── SHOWCASE_EXAMPLES.md              # Demo scenarios and outputs
│   └── README.md                         # Demo data documentation
│
└── 📁 archive/                           # Archived Documentation (Reference Only)
    ├── AGENT_ARCHITECTURE.md             # Old multi-agent architecture
    ├── ARCHITECTURE.md                   # Old system architecture
    ├── DEPLOYMENT_GUIDE.md               # Old deployment guide
    ├── QUICKSTART.md                     # Old quickstart guide
    ├── QUICK_REFERENCE.md                # Old reference guide
    ├── MULTI_AGENT_DEPLOYMENT.md         # Old multi-agent deployment
    ├── SETUP_INSTRUCTIONS.md             # Old setup instructions
    ├── MODEL_ACCESS_FIX.md               # Old troubleshooting
    ├── TROUBLESHOOTING.md                # Old troubleshooting
    └── DEPLOYMENT_COMPLETE.md            # Old deployment log
```

---

## 🗑️ Removed (Not Shown Above)

### Deleted Directories
- ❌ `lambda/worker_handler/` - Old SQS worker (40 files)
- ❌ `lambda/customer_worker/` - Unused worker (4 files)
- ❌ `lambda/build/` - Build directory (temporary)
- ❌ `lambda/layer/` - Layer build directory (temporary)
- ❌ `step_functions/` - Step Functions definitions (3 files)
- ❌ `bedrock-agent/venv/` - Python virtual environment (40 MB!)

### Deleted Files
- ❌ `lambda/api_handler/lambda_function_backup.py` - Old version
- ❌ `lambda/api_handler/lambda_function_enhanced.py` - Old version
- ❌ `bedrock-agent/coordinator-schema.json` - Unused agent
- ❌ `bedrock-agent/campaign-generator-schema.json` - Unused agent
- ❌ `bedrock-agent/simple-flow.json` - Unused flow
- ❌ `bedrock-agent/advanced-flow.json` - Unused flow
- ❌ `bedrock-agent/flow-definition.json` - Unused flow
- ❌ `bedrock-agent/flow-trust-policy.json` - Unused policy
- ❌ `bedrock-agent/flow-execution-role-policy.json` - Unused policy
- ❌ `iam/stepfunctions-role-policy.json` - Unused policy
- ❌ `iam/stepfunctions-trust-policy.json` - Unused policy
- ❌ `TODO.md` - Outdated task list
- ❌ `api-handler-updated.zip` - Deployment artifact
- ❌ ~20 other `.zip` files - Deployment artifacts

---

## 📊 File Count Summary

| Category | Before | After | Change |
|----------|--------|-------|--------|
| **Lambda Functions** | 4 directories | 2 directories | -50% |
| **Documentation (root)** | 10 files | 6 files | -40% |
| **Documentation (bedrock-agent)** | 12 files | 6 files | -50% |
| **Build Artifacts (.zip)** | ~20 files | 0 files | -100% |
| **Python venv** | 1 (40 MB) | 0 | -100% |
| **Total Files** | ~200+ | ~50 | -75% |

---

## 🎯 Production Code (Essential)

### What's Actually Running in AWS

**Frontend:**
- `frontend/index.html` → Deployed to S3 static hosting
- URL: http://revive-ai-frontend.s3-website-us-east-1.amazonaws.com

**Lambda Functions:**
- `lambda/api_handler/lambda_function.py` → revive-ai-api-handler (1024MB, 900s)
- `lambda/bedrock_agent_executor/lambda_function.py` → bedrock-agent-executor

**Lambda Layer:**
- `lambda/shared/*` → Shared utilities (S3Helper, BedrockClient, Agents)

**Bedrock Agent:**
- `bedrock-agent/churn-analyzer-schema.json` → ChurnAnalyzer (ID: HAKDC7PY1Z)

**Infrastructure:**
- API Gateway: 65rpczwxta.execute-api.us-east-1.amazonaws.com
- S3: revive-ai-data (uploads, results)
- DynamoDB: revive-ai-job-status (atomic status tracking)
- CloudWatch: revive-ai-monitoring dashboard

---

## 📝 Documentation Hierarchy

### Primary Documentation (Current & Accurate)
1. **README.md** - Repository overview (⚠️ needs update)
2. **SYSTEM_DOCUMENTATION.md** - Complete production docs (✅ current)
3. **bedrock-agent/README.md** - Agent documentation
4. **bedrock-agent/TEST_SCENARIOS.md** - Validation scenarios
5. **bedrock-agent/DEMO_SHOWCASE.md** - Demo guide

### Supporting Documentation
- **CLEANUP_PLAN.md** - This cleanup plan (detailed)
- **CLEANUP_SUMMARY.md** - Quick cleanup guide
- **REPO_STRUCTURE.md** - This file (structure overview)
- **demo_data/SHOWCASE_EXAMPLES.md** - Example outputs

### Archived Documentation (Reference Only)
- **archive/** - Old documentation from earlier iterations

---

## 🚀 Next Steps for Public Submission

### Must Do (Before GitHub Push)
1. [ ] Run `./cleanup.sh` to execute cleanup
2. [ ] Update `README.md` to reflect production system
3. [ ] Add `LICENSE` file (MIT or Apache 2.0)
4. [ ] Remove any hardcoded AWS account IDs or secrets
5. [ ] Replace internal URLs with placeholders

### Should Do (Before GitHub Push)
6. [ ] Create `frontend/README.md`
7. [ ] Create `lambda/README.md`
8. [ ] Add architecture diagram (PNG/SVG)
9. [ ] Add screenshots of web interface

### Nice to Have (After GitHub Push)
10. [ ] Add demo video
11. [ ] Create `.github/` templates (issues, PRs)
12. [ ] Add `CONTRIBUTING.md`
13. [ ] Set up GitHub Actions CI/CD

---

## 💡 Tips for Reviewers

**Start Here:**
1. Read `README.md` for overview
2. Read `SYSTEM_DOCUMENTATION.md` for complete technical details
3. Check `bedrock-agent/TEST_SCENARIOS.md` for validation proof

**Understand the Code:**
1. `lambda/api_handler/lambda_function.py` - Main entry point (300 lines)
2. `lambda/shared/agents.py` - Campaign generation logic
3. `bedrock-agent/churn-analyzer-schema.json` - Agent tool definitions

**See It Working:**
1. Visit frontend URL: http://revive-ai-frontend.s3-website-us-east-1.amazonaws.com
2. Check CloudWatch dashboard: revive-ai-monitoring
3. Review demo results in `demo_data/`

---

**Created:** October 17, 2025
**Last Updated:** October 17, 2025
**Status:** Final structure after cleanup
