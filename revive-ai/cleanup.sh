#!/bin/bash
# Repository Cleanup Script for Public Submission
# Run this from the revive-ai root directory

set -e  # Exit on error

echo "🧹 ReviveAI Repository Cleanup Script"
echo "====================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check we're in the right directory
if [ ! -f "SYSTEM_DOCUMENTATION.md" ]; then
    echo -e "${RED}Error: Please run this script from the revive-ai root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  Warning: This will delete obsolete code and reorganize the repository${NC}"
echo "Recommended: Create a backup first (cp -r ../revive-ai ../revive-ai-backup)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo ""
echo "📊 Phase 1: Analyzing current state..."
echo "----------------------------------------"
du -sh . 2>/dev/null || echo "Current size: Unknown"
echo "Files: $(find . -type f | wc -l)"
echo ""

echo "🗑️  Phase 2: Deleting obsolete code..."
echo "----------------------------------------"

# 2.1 Remove unused Lambda functions
echo "Removing obsolete Lambda functions..."
rm -rf lambda/worker_handler/ 2>/dev/null && echo "✅ Removed lambda/worker_handler/" || echo "⏭️  Already removed: lambda/worker_handler/"
rm -rf lambda/customer_worker/ 2>/dev/null && echo "✅ Removed lambda/customer_worker/" || echo "⏭️  Already removed: lambda/customer_worker/"
rm -f lambda/api_handler/lambda_function_backup.py 2>/dev/null && echo "✅ Removed backup Lambda" || echo "⏭️  Already removed: backup Lambda"
rm -f lambda/api_handler/lambda_function_enhanced.py 2>/dev/null && echo "✅ Removed enhanced Lambda" || echo "⏭️  Already removed: enhanced Lambda"

# 2.2 Remove Step Functions
echo "Removing Step Functions files..."
rm -rf step_functions/ 2>/dev/null && echo "✅ Removed step_functions/" || echo "⏭️  Already removed: step_functions/"
rm -f iam/stepfunctions-trust-policy.json 2>/dev/null && echo "✅ Removed Step Functions IAM" || echo "⏭️  Already removed: Step Functions IAM"
rm -f iam/stepfunctions-role-policy.json 2>/dev/null || true

# 2.3 Remove build artifacts
echo "Removing build artifacts..."
find . -name "*.zip" -type f -delete && echo "✅ Removed all .zip files" || echo "⏭️  No .zip files found"
rm -rf bedrock-agent/venv/ 2>/dev/null && echo "✅ Removed venv/ (40MB saved)" || echo "⏭️  Already removed: venv/"
rm -rf lambda/build/ 2>/dev/null || true
rm -rf lambda/layer/ 2>/dev/null || true
echo "✅ Removed build directories"

# 2.4 Remove obsolete agent schemas
echo "Removing obsolete agent schemas..."
rm -f bedrock-agent/coordinator-schema.json 2>/dev/null && echo "✅ Removed coordinator schema" || echo "⏭️  Already removed: coordinator schema"
rm -f bedrock-agent/campaign-generator-schema.json 2>/dev/null && echo "✅ Removed campaign-generator schema" || echo "⏭️  Already removed: campaign-generator schema"

# 2.5 Remove obsolete flow definitions
echo "Removing flow definitions..."
rm -f bedrock-agent/simple-flow.json 2>/dev/null || true
rm -f bedrock-agent/advanced-flow.json 2>/dev/null || true
rm -f bedrock-agent/flow-definition.json 2>/dev/null || true
rm -f bedrock-agent/flow-trust-policy.json 2>/dev/null || true
rm -f bedrock-agent/flow-execution-role-policy.json 2>/dev/null || true
echo "✅ Removed flow definition files"

# 2.6 Remove deployment zip that's in root
rm -f api-handler-updated.zip 2>/dev/null || true

echo ""
echo "📝 Phase 3: Archiving outdated documentation..."
echo "-----------------------------------------------"

# Create archive directory
mkdir -p archive

# Move outdated docs
echo "Moving outdated documentation to archive/..."
mv AGENT_ARCHITECTURE.md archive/ 2>/dev/null && echo "✅ Archived AGENT_ARCHITECTURE.md" || echo "⏭️  Already archived"
mv ARCHITECTURE.md archive/ 2>/dev/null && echo "✅ Archived ARCHITECTURE.md" || echo "⏭️  Already archived"
mv DEPLOYMENT_GUIDE.md archive/ 2>/dev/null && echo "✅ Archived DEPLOYMENT_GUIDE.md" || echo "⏭️  Already archived"
mv QUICKSTART.md archive/ 2>/dev/null && echo "✅ Archived QUICKSTART.md" || echo "⏭️  Already archived"
mv QUICK_REFERENCE.md archive/ 2>/dev/null || true

# Move obsolete bedrock-agent docs
mv bedrock-agent/MULTI_AGENT_DEPLOYMENT.md archive/ 2>/dev/null || true
mv bedrock-agent/SETUP_INSTRUCTIONS.md archive/ 2>/dev/null || true
mv bedrock-agent/MODEL_ACCESS_FIX.md archive/ 2>/dev/null || true
mv bedrock-agent/TROUBLESHOOTING.md archive/ 2>/dev/null || true
mv bedrock-agent/DEPLOYMENT_COMPLETE.md archive/ 2>/dev/null || true

# Delete obsolete TODO
rm -f TODO.md 2>/dev/null && echo "✅ Removed TODO.md" || echo "⏭️  Already removed: TODO.md"

echo ""
echo "📊 Phase 4: Final state analysis..."
echo "-----------------------------------"
echo "Repository size after cleanup:"
du -sh . 2>/dev/null || echo "Size: Unknown"
echo "Files remaining: $(find . -type f | wc -l)"
echo ""

echo "📁 Essential files preserved:"
echo "  ✅ frontend/index.html (Production React SPA)"
echo "  ✅ lambda/api_handler/lambda_function.py (Main Lambda)"
echo "  ✅ lambda/shared/ (Lambda layer)"
echo "  ✅ lambda/bedrock_agent_executor/ (Agent executor)"
echo "  ✅ bedrock-agent/churn-analyzer-schema.json (Agent schema)"
echo "  ✅ SYSTEM_DOCUMENTATION.md (Production docs)"
echo "  ✅ README.md (Repository overview)"
echo ""

echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""
echo "📋 Next steps:"
echo "  1. Review README.md and update if needed"
echo "  2. Add LICENSE file (if not present)"
echo "  3. Check SYSTEM_DOCUMENTATION.md is up to date (✅ already done)"
echo "  4. Review archive/ directory and confirm you don't need those files"
echo "  5. Commit changes: git add . && git commit -m 'Clean up repository for public submission'"
echo "  6. Push to GitHub: git push origin main"
echo ""
echo "📚 See CLEANUP_PLAN.md for detailed documentation"
