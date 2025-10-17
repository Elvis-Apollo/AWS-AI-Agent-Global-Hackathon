# Repository Cleanup Plan for Public Submission

**Goal:** Organize the repository to reflect the current production system, remove obsolete code, and make it ready for public GitHub submission.

---

## 📊 Current State Analysis

**Repository Size Issues:**
- 40MB Python venv (should not be in repo)
- 20+ .zip deployment artifacts (ignored by .gitignore but committed)
- Multiple obsolete Lambda functions
- Outdated documentation from earlier architecture iterations

**Architecture Changes:**
- ✅ Removed SQS queues → Sequential processing
- ✅ Removed Step Functions → Lambda self-invocation
- ✅ Removed multi-agent coordinator → Single ChurnAnalyzer agent
- ✅ Removed DynamoDB table (kept for atomic increments only)
- ✅ Added CloudWatch dashboard

---

## 🗑️ Phase 1: Delete Obsolete Code

### 1.1 Remove Unused Lambda Functions
```bash
# Delete obsolete worker Lambda
rm -rf lambda/worker_handler/
rm -rf lambda/customer_worker/

# Delete old Lambda versions
rm lambda/api_handler/lambda_function_backup.py
rm lambda/api_handler/lambda_function_enhanced.py
```

### 1.2 Remove Step Functions (Deleted from AWS)
```bash
rm -rf step_functions/
rm iam/stepfunctions-trust-policy.json
rm iam/stepfunctions-role-policy.json
```

### 1.3 Remove Build Artifacts (Already in .gitignore but committed)
```bash
# Remove all .zip files (deployment artifacts)
find . -name "*.zip" -type f -delete

# Remove Python venv (40MB)
rm -rf bedrock-agent/venv/

# Remove build directories
rm -rf lambda/build/
rm -rf lambda/layer/
```

### 1.4 Remove Obsolete Bedrock Agent Schemas
```bash
# Keep: churn-analyzer-schema.json (production)
# Remove: coordinator and campaign-generator (not used as Bedrock agents)
rm bedrock-agent/coordinator-schema.json
rm bedrock-agent/campaign-generator-schema.json
```

### 1.5 Remove Obsolete Flow Definitions
```bash
rm bedrock-agent/simple-flow.json
rm bedrock-agent/advanced-flow.json
rm bedrock-agent/flow-definition.json
rm bedrock-agent/flow-trust-policy.json
rm bedrock-agent/flow-execution-role-policy.json
```

---

## 📝 Phase 2: Consolidate Documentation

### 2.1 Archive Outdated Documentation
```bash
mkdir -p archive/

# Move outdated architecture docs
mv AGENT_ARCHITECTURE.md archive/
mv ARCHITECTURE.md archive/
mv DEPLOYMENT_GUIDE.md archive/
mv QUICKSTART.md archive/

# Move obsolete bedrock-agent docs
mv bedrock-agent/MULTI_AGENT_DEPLOYMENT.md archive/
mv bedrock-agent/SETUP_INSTRUCTIONS.md archive/
mv bedrock-agent/MODEL_ACCESS_FIX.md archive/
mv bedrock-agent/TROUBLESHOOTING.md archive/
```

### 2.2 Keep Essential Documentation
**Keep:**
- ✅ `README.md` (update to reflect production)
- ✅ `SYSTEM_DOCUMENTATION.md` (current production docs)
- ✅ `bedrock-agent/README.md` (update)
- ✅ `bedrock-agent/TEST_SCENARIOS.md` (validation scenarios)
- ✅ `bedrock-agent/DEMO_SHOWCASE.md` (demo guide)
- ✅ `bedrock-agent/EXTERNAL_TOOLS_COMPLETE.md` (tool documentation)

### 2.3 Delete or Update
```bash
# Delete outdated TODO
rm TODO.md

# Keep QUICK_REFERENCE.md if useful, otherwise archive
# Review and decide: mv QUICK_REFERENCE.md archive/
```

---

## 📁 Phase 3: Reorganize Structure

### 3.1 Create Clear Production Structure
```
revive-ai/
├── README.md                          # Updated: Production overview
├── SYSTEM_DOCUMENTATION.md            # Complete system docs
├── LICENSE                            # Add license file
├── .gitignore                         # Already good
│
├── frontend/
│   ├── index.html                     # Production React SPA
│   └── README.md                      # Frontend docs (create)
│
├── lambda/
│   ├── api_handler/
│   │   ├── lambda_function.py         # Main production Lambda
│   │   └── requirements.txt
│   │
│   ├── bedrock_agent_executor/
│   │   ├── lambda_function.py         # Agent action group executor
│   │   └── requirements.txt
│   │
│   └── shared/                        # Lambda layer
│       ├── __init__.py
│       ├── agents.py
│       ├── bedrock_client.py
│       ├── s3_helper.py
│       └── schemas.py
│
├── bedrock-agent/
│   ├── churn-analyzer-schema.json     # Production agent schema
│   ├── test_agent.py                  # Test script
│   ├── README.md                      # Agent documentation
│   ├── TEST_SCENARIOS.md              # Validation scenarios
│   ├── DEMO_SHOWCASE.md               # Demo guide
│   └── EXTERNAL_TOOLS_COMPLETE.md     # Tool documentation
│
├── iam/
│   ├── lambda-role-policy.json        # Lambda IAM policy
│   ├── lambda-trust-policy.json       # Lambda trust policy
│   ├── agent-permissions-policy.json  # Bedrock agent policy
│   └── agent-trust-policy.json        # Bedrock agent trust policy
│
├── scripts/
│   ├── deploy.sh                      # Deployment script
│   └── create-api-gateway.sh          # API Gateway setup
│
├── demo_data/
│   ├── demo_results.json              # Example results
│   ├── SHOWCASE_EXAMPLES.md           # Demo examples
│   └── README.md                      # Demo data docs
│
└── archive/                           # Outdated docs (for reference)
    └── [old documentation files]
```

---

## 🔄 Phase 4: Update Key Files

### 4.1 Update README.md
**Current Issues:**
- References 3-agent architecture (outdated)
- No mention of production web interface
- Needs updated architecture diagram

**Update to include:**
- Production web application URL
- Current architecture (API Gateway → Lambda → Bedrock Agent)
- Quick start with CSV upload
- CloudWatch dashboard link
- Updated metrics (~40s per customer)

### 4.2 Create/Update Component READMEs
```bash
# Create frontend/README.md
# Update lambda/README.md (create if missing)
# Update bedrock-agent/README.md
```

### 4.3 Add Missing Files
```bash
# Add LICENSE (choose appropriate license)
# Add CONTRIBUTING.md (if open to contributions)
# Add .github/workflows/ (if adding CI/CD)
```

---

## 🧹 Phase 5: Clean Git History (Optional)

**If .zip files and venv are in git history:**
```bash
# Remove large files from git history using git-filter-repo or BFG
# This is optional but recommended for cleaner repo

# Install git-filter-repo
pip install git-filter-repo

# Remove venv from history
git filter-repo --path bedrock-agent/venv --invert-paths

# Remove all .zip files from history
git filter-repo --path-glob '*.zip' --invert-paths
```

**⚠️ Warning:** This rewrites git history. Only do this if:
- Repo is not yet public
- No other collaborators have cloned it
- You have a backup

---

## ✅ Phase 6: Final Verification

### 6.1 Repository Size Check
```bash
# Check repo size
du -sh .git/
du -sh .

# Should be < 5MB after cleanup (excluding node_modules if any)
```

### 6.2 Documentation Review Checklist
- [ ] README.md reflects current production system
- [ ] SYSTEM_DOCUMENTATION.md is up to date (✅ already done)
- [ ] All code files have clear comments
- [ ] IAM policies documented
- [ ] Deployment instructions clear
- [ ] Demo/testing instructions included

### 6.3 Code Review Checklist
- [ ] No hardcoded credentials or secrets
- [ ] All environment variables documented
- [ ] Requirements.txt files complete
- [ ] Lambda functions have clear docstrings
- [ ] No TODO comments in production code
- [ ] Error handling comprehensive

### 6.4 Public Submission Checklist
- [ ] LICENSE file added
- [ ] Clear README with badges
- [ ] Contact information / contribution guidelines
- [ ] Demo video link (if available)
- [ ] Architecture diagram (visual)
- [ ] No internal AWS account IDs (replace with placeholder)
- [ ] No internal URLs or domains

---

## 🚀 Phase 7: Execution Order

**Recommended execution order:**

1. **Backup everything**
   ```bash
   cp -r revive-ai revive-ai-backup
   ```

2. **Run Phase 1: Delete obsolete code** (30 min)
   - Delete unused Lambda functions
   - Delete Step Functions files
   - Delete build artifacts
   - Delete obsolete agent schemas

3. **Run Phase 2: Consolidate documentation** (20 min)
   - Create archive/ directory
   - Move outdated docs to archive/
   - Delete TODO.md

4. **Run Phase 3: Verify structure** (10 min)
   - Check all production files present
   - Verify Lambda functions work
   - Test imports

5. **Run Phase 4: Update key files** (1-2 hours)
   - Update README.md
   - Create component READMEs
   - Add LICENSE

6. **Run Phase 5: Clean git history** (optional, 30 min)
   - Only if needed for size reduction

7. **Run Phase 6: Final verification** (30 min)
   - Size check
   - Documentation review
   - Code review
   - Public submission checklist

8. **Push to GitHub** (10 min)
   ```bash
   git remote add origin https://github.com/your-username/revive-ai.git
   git push -u origin main
   ```

---

## 📈 Expected Results

**Before Cleanup:**
- Repository size: ~50-60 MB
- Files: ~200+
- Documentation: Fragmented across 15+ files
- Obsolete code: 3 unused Lambda functions

**After Cleanup:**
- Repository size: ~2-5 MB
- Files: ~50 essential files
- Documentation: Centralized in 5 key files
- Clean production structure

**Time Estimate:** 3-5 hours total

---

## 🎯 Success Criteria

✅ Repository size < 5 MB
✅ No .zip files or venv/ in git
✅ All documentation reflects production system
✅ Clear folder structure for public submission
✅ README.md is compelling and accurate
✅ No hardcoded secrets or internal URLs
✅ LICENSE file included
✅ Ready to share publicly on GitHub

---

**Created:** October 17, 2025
**Status:** Ready to execute
