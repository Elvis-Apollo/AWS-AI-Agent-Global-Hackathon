#!/bin/bash
# Diagnostic script for Bedrock Agent issues

echo "========================================"
echo "Bedrock Agent Diagnostic Tool"
echo "========================================"
echo ""

echo "1. Checking Agent Status..."
echo "----------------------------"
echo "Churn Analyzer:"
aws bedrock-agent get-agent --agent-id HAKDC7PY1Z --region us-east-1 --query '{Status:agent.agentStatus,Model:agent.foundationModel,Role:agent.agentResourceRoleArn}' --output table

echo ""
echo "Coordinator:"
aws bedrock-agent get-agent --agent-id UPWE8NQKWH --region us-east-1 --query '{Status:agent.agentStatus,Model:agent.foundationModel,Role:agent.agentResourceRoleArn}' --output table

echo ""
echo "Campaign Generator:"
aws bedrock-agent get-agent --agent-id HXMON0RCRP --region us-east-1 --query '{Status:agent.agentStatus,Model:agent.foundationModel,Role:agent.agentResourceRoleArn}' --output table

echo ""
echo "2. Checking Alias Status..."
echo "----------------------------"
aws bedrock-agent get-agent-alias --agent-id UPWE8NQKWH --agent-alias-id ZDNG15XWYW --region us-east-1 --query 'agentAlias.{Status:agentAliasStatus,InvocationState:aliasInvocationState}' --output table

echo ""
echo "3. Checking IAM Role Trust Policy..."
echo "----------------------------"
aws iam get-role --role-name ReviveAI-BedrockAgentRole --query 'Role.AssumeRolePolicyDocument' --output json | jq .

echo ""
echo "4. Checking IAM Role Permissions..."
echo "----------------------------"
aws iam get-role-policy --role-name ReviveAI-BedrockAgentRole --policy-name BedrockAgentPermissions --query 'PolicyDocument.Statement[].{Action:Action,Resource:Resource}' --output json | jq .

echo ""
echo "5. Checking Model Access..."
echo "----------------------------"
echo "Haiku model (us.anthropic.claude-3-5-haiku-20241022-v1:0):"
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[?modelId==`us.anthropic.claude-3-5-haiku-20241022-v1:0`].{ModelId:modelId,Status:modelLifecycle.status}' --output table

echo ""
echo "6. Checking Lambda Permissions..."
echo "----------------------------"
echo "Lambda resource policy (allows agents to invoke):"
aws lambda get-policy --function-name bedrock-agent-executor --region us-east-1 2>&1 | jq -r '.Policy' | jq '.Statement[] | select(.Principal.Service == "bedrock.amazonaws.com")' 2>/dev/null || echo "No bedrock policy found"

echo ""
echo "7. Checking Action Groups..."
echo "----------------------------"
aws bedrock-agent list-agent-action-groups --agent-id UPWE8NQKWH --agent-version DRAFT --region us-east-1 --query 'actionGroupSummaries[].{Name:actionGroupName,State:actionGroupState}' --output table

echo ""
echo "8. Current AWS Identity..."
echo "----------------------------"
aws sts get-caller-identity --output table

echo ""
echo "========================================"
echo "Diagnostic Complete"
echo "========================================"
echo ""
echo "If all checks show:"
echo "  - Agent Status: PREPARED"
echo "  - Alias Status: PREPARED"
echo "  - Model Status: ACTIVE"
echo "  - Action Groups: ENABLED"
echo ""
echo "Then try testing in AWS Console first:"
echo "1. Go to Amazon Bedrock console"
echo "2. Click 'Agents' in left sidebar"
echo "3. Select 'revive-ai-coordinator'"
echo "4. Click 'Test' tab"
echo "5. Enter: 'Make a decision for customer with CLV 10000 and priority HIGH'"
echo ""
