# Bedrock Agent Troubleshooting Guide

## ✅ Permissions Fixed

### Issue: Access Denied Error
**Error:** `accessDeniedException when calling the InvokeAgent operation`

### Root Cause:
Bedrock agents need specific IAM permissions that weren't included in initial setup:
1. Agent execution role needs `bedrock:InvokeAgent` (for agent-to-agent calls)
2. Lambda execution role needs `bedrock:InvokeAgent` (for Lambda to invoke agents)

### Fix Applied:

#### 1. Updated ReviveAI-BedrockAgentRole Policy:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeAgent"
  ],
  "Resource": [
    "arn:aws:bedrock:us-east-1:292101577831:agent/*",
    "arn:aws:bedrock:us-east-1:292101577831:agent-alias/*/*"
  ]
}
```

#### 2. Updated revive-ai-lambda-role Policy:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeAgent"
  ],
  "Resource": [
    "arn:aws:bedrock:us-east-1:292101577831:agent/*",
    "arn:aws:bedrock:us-east-1:292101577831:agent-alias/*/*"
  ]
}
```

#### 3. Re-prepared Agents:
After updating IAM permissions, agents must be re-prepared:
```bash
aws bedrock-agent prepare-agent --agent-id UPWE8NQKWH --region us-east-1
```

### Status: ✅ FIXED

---

## Testing After Fix

### Quick Test:
```bash
cd /Users/elvischen/Documents/PROJECTS/AWS\ AI\ Agent\ Global\ Hackathon/revive-ai/bedrock-agent

# If boto3 not installed:
python3 -m venv venv
source venv/bin/activate
pip install boto3

# Run test:
python test_multi_agent.py
```

### Expected Output:
- Coordinator agent processes customer
- Invokes Churn Analyzer via `invokeChurnAnalyzer` tool
- Makes decision via `makeDecision` tool
- Generates recommendations

---

## Common Issues

### 1. Agent Status Not PREPARED
**Check:**
```bash
aws bedrock-agent get-agent --agent-id UPWE8NQKWH --region us-east-1 --query 'agent.agentStatus'
```

**Fix:**
```bash
aws bedrock-agent prepare-agent --agent-id UPWE8NQKWH --region us-east-1
```

### 2. Alias Not Ready
**Check:**
```bash
aws bedrock-agent get-agent-alias --agent-id UPWE8NQKWH --agent-alias-id ZDNG15XWYW --region us-east-1 --query 'agentAlias.agentAliasStatus'
```

**Fix:** Wait 10-15 seconds for alias to become PREPARED

### 3. Lambda Permission Issues
**Check Lambda can invoke agent:**
```bash
aws iam get-role-policy --role-name revive-ai-lambda-role --policy-name bedrock-invoke
```

**Should include:** `bedrock:InvokeAgent` action

### 4. Model Access Issues
**Check model is available:**
```bash
aws bedrock list-foundation-models --region us-east-1 | grep "claude-3-5-sonnet-20241022"
```

### 5. CloudWatch Logs
**Watch Lambda executor logs:**
```bash
aws logs tail /aws/lambda/bedrock-agent-executor --follow --region us-east-1
```

**Look for:**
- Tool invocations
- Agent responses
- Error messages

---

## Verification Checklist

Before testing, verify:

- [ ] Agent status: PREPARED
- [ ] Alias status: PREPARED
- [ ] IAM role has `bedrock:InvokeAgent`
- [ ] Lambda role has `bedrock:InvokeAgent`
- [ ] Lambda has resource policy allowing agents to invoke it
- [ ] Model (Claude Sonnet/Haiku) is available in region

**Check all:**
```bash
# Agent status
aws bedrock-agent get-agent --agent-id UPWE8NQKWH --region us-east-1 --query 'agent.agentStatus'

# Alias status
aws bedrock-agent get-agent-alias --agent-id UPWE8NQKWH --agent-alias-id ZDNG15XWYW --region us-east-1 --query 'agentAlias.agentAliasStatus'

# Role permissions
aws iam get-role-policy --role-name ReviveAI-BedrockAgentRole --policy-name BedrockAgentPermissions | jq '.PolicyDocument.Statement[].Action'

# Lambda permissions
aws iam get-role-policy --role-name revive-ai-lambda-role --policy-name bedrock-invoke | jq '.PolicyDocument.Statement[].Action'
```

---

## Agent IDs Reference

```
Churn Analyzer:
  Agent ID:  HAKDC7PY1Z
  Alias ID:  WN63LBEVKR
  Model:     Claude 3.5 Haiku

Coordinator:
  Agent ID:  UPWE8NQKWH
  Alias ID:  ZDNG15XWYW
  Model:     Claude 3.5 Sonnet

Campaign Generator:
  Agent ID:  HXMON0RCRP
  Alias ID:  YO7A6XFPXU
  Model:     Claude 3.5 Sonnet
```

---

## If Still Getting Errors

1. **Check exact error message** in test output
2. **Check CloudWatch logs** for Lambda executor
3. **Verify agent was re-prepared** after permission changes
4. **Test individual agents first:**
   ```bash
   python test_multi_agent.py --individual
   ```
5. **Enable verbose trace:**
   ```bash
   python test_multi_agent.py --verbose
   ```

---

**Last Updated:** 2025-10-10
**Status:** Permissions fixed, agents re-prepared, ready for testing
