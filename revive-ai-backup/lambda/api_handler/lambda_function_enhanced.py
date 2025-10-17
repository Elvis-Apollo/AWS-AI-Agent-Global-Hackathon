"""
Enhanced API Handler Lambda with Bedrock Agent Integration
Handles API Gateway routes with Coordinator agent instead of Step Functions.
"""
import json
import os
import sys
import csv
import io
import base64
from datetime import datetime
from typing import Dict, Any, List
import uuid

# Add shared module to path
sys.path.insert(0, '/opt/python')

from shared.s3_helper import S3Helper
from shared.schemas import create_status_stub, validate_customer

import boto3

# Environment variables
DATA_BUCKET = os.environ.get('DATA_BUCKET', 'revive-ai-data')
FRONTEND_BUCKET = os.environ.get('FRONTEND_BUCKET', 'revive-ai-frontend')
COORDINATOR_AGENT_ID = os.environ.get('COORDINATOR_AGENT_ID', 'UPWE8NQKWH')
COORDINATOR_ALIAS_ID = os.environ.get('COORDINATOR_ALIAS_ID', 'ZDNG15XWYW')
CHURN_ANALYZER_AGENT_ID = os.environ.get('CHURN_ANALYZER_AGENT_ID', 'HAKDC7PY1Z')
CHURN_ANALYZER_ALIAS_ID = os.environ.get('CHURN_ANALYZER_ALIAS_ID', 'WN63LBEVKR')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize Bedrock agent runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)


def lambda_handler(event, context):
    """
    Main handler for API Gateway.

    Routes:
    - POST /upload - Upload CSV
    - POST /process - Start agent-based processing (NEW)
    - POST /analyze-customer - Analyze single customer with agent (NEW)
    - GET /results - Get results
    - POST /demo - Load demo data
    """
    print(f"Event: {json.dumps(event)}")

    # API Gateway request
    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
    path = event.get('path', event.get('rawPath', ''))

    try:
        if path == '/upload' and http_method == 'POST':
            return handle_upload(event)
        elif path == '/process' and http_method == 'POST':
            return handle_process_with_agent(event)  # NEW: Agent-based processing
        elif path == '/analyze-customer' and http_method == 'POST':
            return handle_analyze_customer(event)  # NEW: Single customer analysis
        elif path == '/results' and http_method == 'GET':
            return handle_results(event)
        elif path == '/demo' and http_method == 'POST':
            return handle_demo(event)
        else:
            return response(404, {'error': 'Not found'})
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }


def handle_upload(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle CSV upload.

    Expects multipart/form-data with file field.
    """
    body = event.get('body', '')
    is_base64 = event.get('isBase64Encoded', False)

    if is_base64:
        body = base64.b64decode(body).decode('utf-8')

    csv_content = body
    upload_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    try:
        customers = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            is_valid, error = validate_customer(row)
            if not is_valid:
                return response(400, {
                    'error': 'Invalid CSV format',
                    'details': error
                })
            customers.append(row)

        if len(customers) == 0:
            return response(400, {'error': 'CSV file is empty'})

        # Save to S3
        s3 = S3Helper(DATA_BUCKET)
        s3.put_text(f"uploads/{upload_id}.csv", csv_content)
        s3.put_json(f"uploads/{upload_id}.json", customers)

        return response(200, {
            'upload_id': upload_id,
            'status': 'uploaded',
            'customer_count': len(customers)
        })

    except Exception as e:
        return response(400, {
            'error': 'Failed to parse CSV',
            'details': str(e)
        })


def handle_process_with_agent(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process uploaded customers using Coordinator agent.
    Processes customers one by one and collects results.
    """
    body = json.loads(event.get('body', '{}'))
    upload_id = body.get('upload_id')

    if not upload_id:
        return response(400, {'error': 'Missing upload_id'})

    # Get customers from S3
    s3 = S3Helper(DATA_BUCKET)
    customers = s3.get_json(f"uploads/{upload_id}.json")

    if not customers:
        return response(404, {'error': 'Upload not found'})

    # Initialize status
    status = create_status_stub(upload_id, len(customers), 'agent-based')
    s3.put_json(f"results/{upload_id}/status.json", status)

    # Process each customer with Coordinator agent
    results = []
    completed = 0
    failed = 0

    for customer in customers:
        try:
            # Invoke Coordinator agent
            result = invoke_coordinator_agent(customer)
            result['status'] = 'success'
            results.append(result)
            completed += 1

            # Save individual result
            customer_id = customer.get('customer_id', f'customer_{completed}')
            s3.put_json(f"results/{upload_id}/customers/{customer_id}.json", result)

        except Exception as e:
            print(f"Failed to process customer: {e}")
            failed += 1
            results.append({
                'customer_id': customer.get('customer_id', f'customer_{completed + failed}'),
                'status': 'failed',
                'error': str(e)
            })

        # Update progress
        status['completed'] = completed
        status['failed'] = failed
        status['progress'] = int((completed / len(customers)) * 100)
        s3.put_json(f"results/{upload_id}/status.json", status)

    # Finalize
    status['status'] = 'complete'
    status['estimated_remaining_seconds'] = 0
    s3.put_json(f"results/{upload_id}/status.json", status)
    s3.put_json(f"results/{upload_id}/customers.json", results)

    return response(202, {
        'upload_id': upload_id,
        'status': 'complete',
        'completed': completed,
        'failed': failed,
        'total': len(customers)
    })


def handle_analyze_customer(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single customer using Bedrock agents.
    Returns detailed analysis with agent reasoning traces.

    Request body:
    {
        "customer_id": "c025",
        "company_name": "DataTech Solutions",
        "mrr": "2499",
        "subscription_tier": "enterprise",
        "churn_date": "2025-10-01",
        "cancellation_reason": "Needed better API rate limits"
    }
    """
    body = json.loads(event.get('body', '{}'))

    # Validate required fields
    required = ['customer_id', 'company_name', 'cancellation_reason']
    for field in required:
        if field not in body:
            return response(400, {'error': f'Missing required field: {field}'})

    try:
        # Invoke ChurnAnalyzer agent directly (with reasoning traces)
        result = invoke_churn_analyzer_with_traces(body)

        return response(200, {
            'status': 'success',
            'customer_id': body['customer_id'],
            'analysis': result['analysis'],
            'reasoning_traces': result['reasoning_traces'],
            'tools_used': result['tools_used'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

    except Exception as e:
        print(f"Error analyzing customer: {e}")
        import traceback
        traceback.print_exc()
        return response(500, {
            'status': 'error',
            'error': str(e)
        })


def invoke_coordinator_agent(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke Coordinator agent for a customer.
    Returns comprehensive win-back strategy.
    """
    session_id = str(uuid.uuid4())

    # Build input text for Coordinator
    input_text = f"""
Analyze this churned customer and create a comprehensive win-back strategy:

Customer Details:
- Customer ID: {customer.get('customer_id', 'unknown')}
- Company: {customer.get('company_name', 'unknown')}
- MRR: ${customer.get('mrr', '0')}
- Subscription Tier: {customer.get('subscription_tier', 'unknown')}
- Churn Date: {customer.get('churn_date', 'unknown')}
- Cancellation Reason: {customer.get('cancellation_reason', 'No reason provided')}

Please provide:
1. Comprehensive churn analysis
2. Customer lifetime value assessment
3. Win-back campaign recommendations
"""

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=COORDINATOR_AGENT_ID,
            agentAliasId=COORDINATOR_ALIAS_ID,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=True  # Enable reasoning traces
        )

        # Collect response and traces
        full_response = ""
        reasoning_traces = []

        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')

            if 'trace' in event:
                reasoning_traces.append(event['trace'])

        return {
            'customer': customer,
            'analysis': full_response,
            'reasoning_traces': reasoning_traces,
            'session_id': session_id
        }

    except Exception as e:
        print(f"Error invoking Coordinator agent: {e}")
        raise


def invoke_churn_analyzer_with_traces(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke ChurnAnalyzer agent with full reasoning traces.
    Returns analysis plus detailed tool usage information.
    """
    session_id = str(uuid.uuid4())

    # Build input text
    input_text = f"""
Analyze customer {customer.get('customer_id', 'unknown')} from {customer.get('company_name', 'unknown')}.

Customer Details:
- MRR: ${customer.get('mrr', 'unknown')}
- Subscription Tier: {customer.get('subscription_tier', 'unknown')}
- Churn Date: {customer.get('churn_date', 'unknown')}
- Reason: {customer.get('cancellation_reason', 'No reason provided')}

Provide comprehensive multi-source intelligence analysis.
"""

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=CHURN_ANALYZER_AGENT_ID,
            agentAliasId=CHURN_ANALYZER_ALIAS_ID,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=True  # Critical: enables reasoning visibility
        )

        # Collect response and traces
        full_response = ""
        reasoning_traces = []
        tools_used = []

        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')

            if 'trace' in event:
                trace = event['trace']
                reasoning_traces.append(trace)

                # Extract tool usage from traces
                if 'trace' in trace:
                    trace_details = trace['trace']
                    if 'orchestrationTrace' in trace_details:
                        orch_trace = trace_details['orchestrationTrace']

                        # Look for invocationInput (tool being called)
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                tool_info = inv_input['actionGroupInvocationInput']
                                tools_used.append({
                                    'tool': tool_info.get('apiPath', 'unknown'),
                                    'action_group': tool_info.get('actionGroupName', 'unknown')
                                })

                        # Look for observation (tool result)
                        if 'observation' in orch_trace:
                            observation = orch_trace['observation']
                            if 'actionGroupInvocationOutput' in observation:
                                # Tool completed successfully
                                pass

        return {
            'analysis': full_response,
            'reasoning_traces': reasoning_traces,
            'tools_used': tools_used,
            'tool_count': len(tools_used),
            'session_id': session_id
        }

    except Exception as e:
        print(f"Error invoking ChurnAnalyzer agent: {e}")
        raise


def handle_results(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get processing results for an upload.
    """
    params = event.get('queryStringParameters', {}) or {}
    upload_id = params.get('upload_id')

    if not upload_id:
        return response(400, {'error': 'Missing upload_id parameter'})

    s3 = S3Helper(DATA_BUCKET)

    # Special case for demo
    if upload_id == 'demo':
        demo_data = s3.get_json('demo/demo_results.json')
        if demo_data:
            return response(200, demo_data)
        else:
            return response(404, {'error': 'Demo data not found'})

    # Read status
    status = s3.get_json(f"results/{upload_id}/status.json")

    if not status:
        return response(200, {
            'status': 'processing',
            'completed': 0,
            'total': 0,
            'progress': 0,
            'failures': 0
        })

    # If still processing, return progress
    if status['status'] == 'processing':
        return response(200, {
            'status': 'processing',
            'completed': status.get('completed', 0),
            'total': status.get('total', 0),
            'progress': int((status.get('completed', 0) / max(status.get('total', 1), 1)) * 100),
            'failures': status.get('failed', 0)
        })

    # If complete, return full results
    campaigns = []
    customers_data = s3.get_json(f"results/{upload_id}/customers.json")
    if customers_data:
        campaigns = customers_data

    return response(200, {
        'status': status['status'],
        'upload_id': upload_id,
        'total': status.get('total', 0),
        'completed': status.get('completed', 0),
        'failed': status.get('failed', 0),
        'campaigns': campaigns
    })


def handle_demo(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return pre-generated demo data.
    """
    s3 = S3Helper(DATA_BUCKET)
    demo_data = s3.get_json('demo/demo_results.json')

    if not demo_data:
        return response(404, {'error': 'Demo data not found'})

    return response(200, demo_data)
