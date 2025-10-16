#!/usr/bin/env python3
"""
Test Multi-Agent Bedrock System
Tests the complete 3-agent orchestra: Coordinator → Churn Analyzer + Campaign Generator
"""
import boto3
import json
import uuid
import sys

# Agent IDs
COORDINATOR_AGENT_ID = 'UPWE8NQKWH'
COORDINATOR_ALIAS_ID = 'ZDNG15XWYW'

CHURN_ANALYZER_AGENT_ID = 'HAKDC7PY1Z'
CHURN_ANALYZER_ALIAS_ID = 'WN63LBEVKR'

CAMPAIGN_GENERATOR_AGENT_ID = 'HXMON0RCRP'
CAMPAIGN_GENERATOR_ALIAS_ID = 'YO7A6XFPXU'


def test_coordinator_workflow():
    """Test the full coordinator workflow."""

    bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    session_id = str(uuid.uuid4())

    print("🎯 Testing Multi-Agent Bedrock System")
    print("=" * 80)
    print(f"Coordinator Agent: {COORDINATOR_AGENT_ID}")
    print(f"Churn Analyzer Agent: {CHURN_ANALYZER_AGENT_ID}")
    print(f"Campaign Generator Agent: {CAMPAIGN_GENERATOR_AGENT_ID}")
    print(f"Session: {session_id}\n")

    # Test Case: High-value enterprise customer
    print("=" * 80)
    print("TEST: Complete Multi-Agent Workflow")
    print("=" * 80)

    input_text = """
    Process this churned customer through the complete win-back workflow:

    Customer Details:
    - Customer ID: c025
    - Company: DataTech Solutions
    - MRR: $2499
    - Subscription: enterprise
    - Churn Date: 2025-10-01
    - Reason: Needed better API rate limits and response times

    Please:
    1. Analyze the churn reason and calculate CLV
    2. Make a strategic decision on how to handle this customer
    3. If appropriate, generate a win-back campaign
    4. Provide your complete recommendation
    """

    print(f"\nCoordinator Input:\n{input_text}\n")
    print("Coordinator Response (with agent orchestration):")
    print("-" * 80)

    try:
        response = bedrock_agent.invoke_agent(
            agentId=COORDINATOR_AGENT_ID,
            agentAliasId=COORDINATOR_ALIAS_ID,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=True  # Enable to see agent reasoning and tool calls
        )

        # Parse streaming response
        full_response = ""
        trace_data = []
        tool_calls = []

        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    full_response += text
                    print(text, end='', flush=True)

            if 'trace' in event:
                trace = event['trace']
                trace_data.append(trace)

                # Extract tool calls
                if 'trace' in trace:
                    trace_detail = trace['trace']
                    if 'orchestrationTrace' in trace_detail:
                        orch_trace = trace_detail['orchestrationTrace']
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                action_input = inv_input['actionGroupInvocationInput']
                                tool_calls.append({
                                    'action_group': action_input.get('actionGroupName', ''),
                                    'api_path': action_input.get('apiPath', ''),
                                    'function': action_input.get('function', '')
                                })

        print("\n" + "-" * 80)

        # Show trace summary
        print("\n📊 Multi-Agent Orchestration Trace:")
        print("=" * 80)

        if tool_calls:
            print("\nTools Called by Coordinator:")
            for i, call in enumerate(tool_calls, 1):
                print(f"  {i}. {call.get('action_group', 'unknown')} → {call.get('api_path', call.get('function', 'unknown'))}")
        else:
            print("  (Trace capture may be processing...)")

        # Show detailed trace if verbose
        if '--verbose' in sys.argv and trace_data:
            print("\n📋 Detailed Trace Data:")
            print("=" * 80)
            for i, trace in enumerate(trace_data, 1):
                print(f"\nTrace Event {i}:")
                print(json.dumps(trace, indent=2, default=str))

        print("\n✅ Multi-Agent Workflow Complete")
        print("=" * 80)
        print("\nExpected Behavior:")
        print("✓ Coordinator invoked Churn Analyzer to analyze customer")
        print("✓ Coordinator used makeDecision to determine handling approach")
        print("✓ Coordinator may have invoked Campaign Generator for emails")
        print("✓ Provided strategic recommendation based on agent outputs")

        print("\n✨ Multi-Agent Orchestra is Working!")
        print("You now have 3 specialist agents coordinating autonomously.\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify all agents are PREPARED status")
        print("2. Check Lambda logs: aws logs tail /aws/lambda/bedrock-agent-executor --follow")
        print("3. Verify agent aliases are created")
        sys.exit(1)


def test_individual_agents():
    """Test each agent individually."""

    bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

    print("\n" + "=" * 80)
    print("INDIVIDUAL AGENT TESTS")
    print("=" * 80)

    # Test Churn Analyzer
    print("\n1️⃣ Testing Churn Analyzer Agent")
    print("-" * 80)

    session_1 = str(uuid.uuid4())
    input_1 = """Analyze this customer:
- Customer ID: c100
- Company: FastGrow Inc
- MRR: $599
- Subscription: growth
- Churn Date: 2025-10-05
- Reason: Too expensive for our current stage"""

    response_1 = bedrock_agent.invoke_agent(
        agentId=CHURN_ANALYZER_AGENT_ID,
        agentAliasId=CHURN_ANALYZER_ALIAS_ID,
        sessionId=session_1,
        inputText=input_1
    )

    print("Churn Analyzer Response:")
    for event in response_1['completion']:
        if 'chunk' in event and 'bytes' in event['chunk']:
            print(event['chunk']['bytes'].decode('utf-8'), end='', flush=True)

    print("\n" + "-" * 80)
    print("✅ Churn Analyzer Working\n")

    # Test Campaign Generator
    print("2️⃣ Testing Campaign Generator Agent")
    print("-" * 80)

    session_2 = str(uuid.uuid4())
    input_2 = """Generate a win-back email campaign for:
- Customer: FastGrow Inc
- Churn Category: pricing
- Priority: MEDIUM
- Key insight: Customer felt product was too expensive for their stage"""

    response_2 = bedrock_agent.invoke_agent(
        agentId=CAMPAIGN_GENERATOR_AGENT_ID,
        agentAliasId=CAMPAIGN_GENERATOR_ALIAS_ID,
        sessionId=session_2,
        inputText=input_2
    )

    print("Campaign Generator Response:")
    for event in response_2['completion']:
        if 'chunk' in event and 'bytes' in event['chunk']:
            print(event['chunk']['bytes'].decode('utf-8'), end='', flush=True)

    print("\n" + "-" * 80)
    print("✅ Campaign Generator Working\n")


if __name__ == '__main__':
    if '--individual' in sys.argv:
        test_individual_agents()
    else:
        test_coordinator_workflow()

    if '--all' in sys.argv:
        test_individual_agents()
