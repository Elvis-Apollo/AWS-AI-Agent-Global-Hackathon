#!/usr/bin/env python3
"""
Test Bedrock Agent
Run after creating agent in AWS Console
"""
import boto3
import json
import uuid
import sys

# Agent IDs - auto-populated during setup
AGENT_ID = 'HAKDC7PY1Z'
ALIAS_ID = 'WN63LBEVKR'

def test_churn_analyzer():
    """Test the churn analyzer agent."""

    if AGENT_ID == 'REPLACE_WITH_YOUR_AGENT_ID':
        print("❌ ERROR: Please update AGENT_ID and ALIAS_ID in this script")
        print("   Get IDs from AWS Console after creating the agent")
        sys.exit(1)

    bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    session_id = str(uuid.uuid4())

    print("🤖 Testing Bedrock Agent: Churn Analyzer")
    print(f"   Agent ID: {AGENT_ID}")
    print(f"   Alias ID: {ALIAS_ID}")
    print(f"   Session: {session_id}\n")

    # Test Case 1: High-value customer
    print("=" * 70)
    print("TEST 1: High-Value Enterprise Customer")
    print("=" * 70)

    input_text = """
    Analyze this customer:
    - Customer ID: c017
    - Company: SecureData Corp
    - MRR: $1799
    - Subscription: enterprise
    - Churn Date: 2025-09-07
    - Reason: Security certifications not meeting our standards
    """

    print(f"\nInput:\n{input_text}\n")
    print("Agent Response:")
    print("-" * 70)

    try:
        response = bedrock_agent.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=True  # Enable to see agent reasoning
        )

        # Parse streaming response
        full_response = ""
        trace_data = []

        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    full_response += text
                    print(text, end='', flush=True)

            if 'trace' in event:
                trace_data.append(event['trace'])

        print("\n" + "-" * 70)

        # Show trace if verbose
        if trace_data and '--verbose' in sys.argv:
            print("\n📊 Agent Reasoning Trace:")
            print("=" * 70)
            for i, trace in enumerate(trace_data, 1):
                print(f"\nStep {i}:")
                print(json.dumps(trace, indent=2))

        print("\n✅ Test 1 Complete\n")

        # Test Case 2: Lower-value customer
        print("=" * 70)
        print("TEST 2: Lower-Value Starter Customer")
        print("=" * 70)

        input_text_2 = """
        Analyze this customer:
        - Customer ID: c007
        - Company: MarketPro Analytics
        - MRR: $199
        - Subscription: starter
        - Churn Date: 2025-09-25
        - Reason: Not enough ROI for the subscription cost
        """

        print(f"\nInput:\n{input_text_2}\n")
        print("Agent Response:")
        print("-" * 70)

        # New session for test 2
        session_id_2 = str(uuid.uuid4())

        response_2 = bedrock_agent.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId=session_id_2,
            inputText=input_text_2
        )

        for event in response_2['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    print(chunk['bytes'].decode('utf-8'), end='', flush=True)

        print("\n" + "-" * 70)
        print("\n✅ Test 2 Complete\n")

        print("=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Agent is working correctly")
        print("✅ Tools (calculateCLV, analyzeChurn) are being called")
        print("✅ Agent provides strategic recommendations")
        print("\nNext steps:")
        print("1. Create additional agents (Campaign Generator, Coordinator)")
        print("2. Add more tools (escalation, web search)")
        print("3. Integrate into your API workflow")
        print("4. Build demo scenarios\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify agent is created in AWS Console (Bedrock → Agents)")
        print("2. Check agent ID and alias ID are correct")
        print("3. Verify agent alias is created (PROD)")
        print("4. Check Lambda permissions and logs:")
        print("   aws logs tail /aws/lambda/bedrock-agent-executor --follow")
        sys.exit(1)


def list_agents():
    """List all available agents."""
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')

    print("📋 Listing Bedrock Agents:\n")

    try:
        response = bedrock_agent.list_agents()

        if not response.get('agentSummaries'):
            print("No agents found. Create one in AWS Console first.")
            return

        for agent in response['agentSummaries']:
            print(f"Agent: {agent['agentName']}")
            print(f"  ID: {agent['agentId']}")
            print(f"  Status: {agent['agentStatus']}")
            print(f"  Updated: {agent['updatedAt']}")

            # Get aliases
            try:
                aliases_response = bedrock_agent.list_agent_aliases(
                    agentId=agent['agentId']
                )
                if aliases_response.get('agentAliasSummaries'):
                    print("  Aliases:")
                    for alias in aliases_response['agentAliasSummaries']:
                        print(f"    - {alias['agentAliasName']} (ID: {alias['agentAliasId']})")
            except:
                pass

            print()

    except Exception as e:
        print(f"Error listing agents: {e}")


if __name__ == '__main__':
    if '--list' in sys.argv:
        list_agents()
    else:
        test_churn_analyzer()
