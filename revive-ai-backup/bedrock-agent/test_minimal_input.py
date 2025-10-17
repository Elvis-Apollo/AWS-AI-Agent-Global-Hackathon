#!/usr/bin/env python3
"""
Test agent with MINIMAL input to force tool usage
"""
import boto3
import uuid

AGENT_ID = 'HAKDC7PY1Z'
ALIAS_ID = 'WN63LBEVKR'

bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# MINIMAL input - force agent to gather data via tools
input_text = """
Analyze customer c025 (DataTech Solutions).
They churned on 2025-10-01 saying: "Needed better API rate limits and response times"
"""

print("Testing with MINIMAL input to force tool usage...")
print(f"Input: {input_text}\n")
print("Expected: Agent should call ALL 5 tools to gather complete intelligence\n")
print("=" * 70)

response = bedrock_agent.invoke_agent(
    agentId=AGENT_ID,
    agentAliasId=ALIAS_ID,
    sessionId=str(uuid.uuid4()),
    inputText=input_text,
    enableTrace=True
)

for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']
        if 'bytes' in chunk:
            print(chunk['bytes'].decode('utf-8'), end='', flush=True)

print("\n" + "=" * 70)
print("\nNow check logs:")
print("aws logs tail /aws/lambda/bedrock-agent-executor --since 1m --region us-east-1 | grep 'Executing:'")
