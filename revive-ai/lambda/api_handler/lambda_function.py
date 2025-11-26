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
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add shared module to path
sys.path.insert(0, '/opt/python')

from shared.s3_helper import S3Helper
from shared.schemas import create_status_stub, validate_customer
from shared.rate_limiter import TokenBucketRateLimiter

import boto3

# Environment variables
DATA_BUCKET = os.environ.get('DATA_BUCKET', 'revive-ai-data')
FRONTEND_BUCKET = os.environ.get('FRONTEND_BUCKET', 'revive-ai-frontend')
COORDINATOR_AGENT_ID = os.environ.get('COORDINATOR_AGENT_ID', 'UPWE8NQKWH')
COORDINATOR_ALIAS_ID = os.environ.get('COORDINATOR_ALIAS_ID', 'ZDNG15XWYW')
CHURN_ANALYZER_AGENT_ID = os.environ.get('CHURN_ANALYZER_AGENT_ID', 'HAKDC7PY1Z')
CHURN_ANALYZER_ALIAS_ID = os.environ.get('CHURN_ANALYZER_ALIAS_ID', 'TSTALIASID')  # DRAFT version with better tool usage
CAMPAIGN_GENERATOR_AGENT_ID = os.environ.get('CAMPAIGN_GENERATOR_AGENT_ID', 'HXMON0RCRP')

# Concurrency settings
# With 125 RPM CrossRegionRequests limit:
# - Target: 100 RPM (80% of limit, 25 RPM safety buffer for retries)
# - Each customer makes ~8 API calls
# - 100 RPM = ~12 customers/minute throughput
# - MAX_WORKERS=10: High concurrency with rate limiting to prevent bursts
MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '10'))  # High concurrency for 1-500 customers
API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', '100'))  # Target 100 RPM (80% of 125 limit)

CAMPAIGN_GENERATOR_ALIAS_ID = os.environ.get('CAMPAIGN_GENERATOR_ALIAS_ID', 'TSTALIASID')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Global rate limiter instance (shared across threads)
rate_limiter = TokenBucketRateLimiter(rate_per_minute=API_RATE_LIMIT)

# Initialize Bedrock agent runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)


def lambda_handler(event, context):
    """
    Main handler for API Gateway and async processing.

    Routes:
    - POST /upload - Upload CSV
    - POST /process - Start agent-based processing (NEW)
    - POST /analyze-customer - Analyze single customer with agent (NEW)
    - GET /results - Get results
    - POST /demo - Load demo data
    - async_process - Background processing (async invocation)
    """
    print(f"Event: {json.dumps(event)}")

    # Check if this is an async processing invocation
    if event.get('async_process'):
        return handle_async_processing(event, context)

    # API Gateway request
    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
    path = event.get('path', event.get('rawPath', ''))

    try:
        if path == '/upload' and http_method == 'POST':
            return handle_upload(event)
        elif path == '/process' and http_method == 'POST':
            return handle_process_with_agent(event, context)  # Pass context for function name
        elif path == '/analyze-customer' and http_method == 'POST':
            return handle_analyze_customer(event)  # Single customer analysis
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


def parse_analysis_text(text: str) -> Dict[str, Any]:
    """
    Parse agent analysis text to extract structured data for UI.
    Extracts: category, confidence, summary, recommendation.
    """
    import re

    result = {
        'category': 'unclear',
        'confidence': 75,  # Default confidence
        'summary': '',
        'recommendation': ''
    }

    # Extract churn category
    category_patterns = {
        'pricing': r'(?i)(pricing|cost|expensive|budget|price|ROI|affordability)',
        'features': r'(?i)(feature|functionality|capability|missing|lack|API|integration|limitation)',
        'onboarding': r'(?i)(onboarding|learning curve|difficult|training|setup|user interface|UX)',
        'competition': r'(?i)(competitor|alternative|switched|better pricing)',
        'business_closure': r'(?i)(closure|downsizing|shutdown|economic|budget cut|grant funding)'
    }

    for category, pattern in category_patterns.items():
        if re.search(pattern, text):
            result['category'] = category
            break

    # Extract confidence percentage
    confidence_match = re.search(r'(?i)confidence[:\s]+(\d+)%', text)
    if confidence_match:
        result['confidence'] = int(confidence_match.group(1))

    # Extract summary (first meaningful paragraph)
    lines = [line.strip() for line in text.split('\n') if line.strip() and not line.strip().startswith('#')]
    if lines:
        # Get first substantial paragraph (skip headers and bullets)
        for line in lines[:5]:
            if len(line) > 50 and not line.startswith('-') and not line.startswith('*'):
                result['summary'] = line[:200]
                break
        if not result['summary'] and lines:
            result['summary'] = lines[0][:200]

    # Extract recommendation
    rec_match = re.search(r'(?i)(?:recommendation|next steps?|action)s?[\s:]+(.+?)(?:\n\n|\Z)', text, re.DOTALL)
    if rec_match:
        result['recommendation'] = rec_match.group(1).strip()[:300]

    return result


def parse_campaign_emails(text: str) -> List[Dict[str, Any]]:
    """
    Parse campaign text to extract structured email sequence.
    Returns array of email objects for UI display.
    """
    import re

    emails = []

    # Try to find structured emails in text
    email_patterns = [
        r'Email\s+(\d+)[\s:]+Subject[\s:]+(.+?)\n(.+?)(?=Email\s+\d+|$)',
        r'Subject[\s:]+(.+?)\n\n(.+?)(?=Subject[\s:]|$)',
    ]

    # Try pattern matching
    for pattern in email_patterns:
        matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 3:
                number, subject, body = match.groups()
                emails.append({
                    'number': int(number) if number.isdigit() else len(emails) + 1,
                    'subject': subject.strip()[:200],
                    'body': body.strip()[:800],
                    'cta': extract_cta(body)
                })
            elif len(match.groups()) == 2:
                subject, body = match.groups()
                emails.append({
                    'number': len(emails) + 1,
                    'subject': subject.strip()[:200],
                    'body': body.strip()[:800],
                    'cta': extract_cta(body)
                })

    # If no structured emails found, create a single email from the content
    if not emails and text:
        # Look for subject line
        subject_match = re.search(r'(?:Subject|Email)[\s:]+(.+?)(?:\n|$)', text, re.IGNORECASE)
        subject = subject_match.group(1).strip() if subject_match else "Your Personalized Win-Back Offer"

        # Use first 800 chars as body
        body = text[:800]

        emails.append({
            'number': 1,
            'subject': subject,
            'body': body,
            'cta': extract_cta(text)
        })

    return emails


def extract_cta(text: str) -> str:
    """Extract call-to-action from text."""
    import re

    # Common CTA patterns
    cta_patterns = [
        r'(?i)(schedule|book|claim|get|start|try|contact|reach out|click here).*?(?:\.|$)',
        r'(?i)call[\s-]to[\s-]action[\s:]+(.+?)(?:\n|$)',
    ]

    for pattern in cta_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()[:100]

    return "Schedule a Call"


def extract_key_findings_with_ai(analysis_text: str, customer: Dict[str, Any]) -> List[str]:
    """
    Use AI (Claude Haiku) to intelligently extract 2-5 key findings from analysis.
    """
    from shared.bedrock_client import BedrockClient

    system_prompt = """You are an expert at analyzing customer churn data and identifying the most critical, actionable insights.

Your task: Extract 2-5 KEY FINDINGS that are truly noteworthy.

ONLY include findings that are:
- Significant (high value, critical risk, strong opportunity)
- Actionable (directly informs win-back strategy)
- Specific to this customer (not generic observations)

Use emojis to highlight importance:
- 🚨 for high-value customers or critical situations
- ✅ for strong win-back opportunities
- ⚠️ for serious risks or concerns
- 📉 for poor engagement/usage metrics
- 🏃 for competitive threats
- 🗺️ for product roadmap matches
- 💰 for significant CLV
- 💵 for budget/pricing sensitivity

If there are fewer than 2 truly noteworthy findings, return empty array."""

    user_prompt = f"""Analyze this customer churn intelligence report and extract 2-5 KEY FINDINGS.

Customer Context:
- Company: {customer.get('company_name', 'Unknown')}
- MRR: ${customer.get('mrr', '0')}/month
- Tier: {customer.get('subscription_tier', 'Unknown')}
- Churn Reason: {customer.get('cancellation_reason', 'Not provided')}

Churn Intelligence Report:
{analysis_text[:2000]}

Return ONLY a JSON array of 2-5 strings (or empty array if no noteworthy findings).

Example format:
["🚨 High-value customer: $85,000 CLV at risk", "✅ Strong win-back potential (78%)", "📉 Barely using product (15% adoption)"]

Your response (JSON array only):"""

    try:
        bedrock = BedrockClient(model_id='us.anthropic.claude-haiku-4-5-20251001-v1:0')
        response = bedrock.invoke_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=512
        )

        findings = response.get('data', [])

        if isinstance(findings, list) and all(isinstance(f, str) for f in findings):
            return findings[:5]
        else:
            return []
    except Exception as e:
        print(f"Error extracting key findings with AI: {e}")
        return []


def create_intelligence_summary(analysis_text: str, tools_used: List[Dict], campaign_emails: List[Dict], customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visual intelligence summary using AI for key findings extraction.
    Shows the AI's decision-making process for UI display.
    """
    import re

    summary = {
        'data_sources': [],
        'key_findings': [],
        'strategy': ''
    }

    # 1. Data sources from tools_used
    tool_names = {
        '/analyzeChurn': {'name': 'Churn Pattern Analysis', 'icon': '🔍'},
        '/calculateCLV': {'name': 'Customer Lifetime Value', 'icon': '💰'},
        '/getCRMHistory': {'name': 'CRM & Usage Data', 'icon': '📊'},
        '/searchCompanyInfo': {'name': 'Company Intelligence', 'icon': '🏢'},
        '/checkProductRoadmap': {'name': 'Product Roadmap', 'icon': '🗺️'}
    }

    for tool in tools_used:
        tool_path = tool.get('tool', '')
        if tool_path in tool_names:
            summary['data_sources'].append(tool_names[tool_path])

    # 2. Extract key findings using AI (intelligent, context-aware)
    summary['key_findings'] = extract_key_findings_with_ai(analysis_text, customer)

    # 3. Campaign strategy chosen (analyze email content)
    email_bodies = " ".join([e.get('body', '') for e in campaign_emails]).lower()

    strategies = []
    if 'training' in email_bodies or 'onboarding' in email_bodies or 'workshop' in email_bodies:
        strategies.append('Implementation support & training')
    if 'consultant' in email_bodies or 'dedicated' in email_bodies:
        strategies.append('Dedicated customer success')
    if 'discount' in email_bodies or '%' in email_bodies:
        strategies.append('Financial incentive')
    if 'roadmap' in email_bodies or 'upcoming' in email_bodies or 'new feature' in email_bodies:
        strategies.append('Product roadmap preview')

    summary['strategy'] = ' + '.join(strategies) if strategies else 'Personalized engagement approach'

    return summary


def process_single_customer(
    customer: Dict[str, Any],
    upload_id: str,
    company_info: Dict[str, Any],
    s3: S3Helper
) -> Dict[str, Any]:
    """
    Process a single customer through churn analysis and campaign generation.
    Thread-safe function for concurrent processing.

    Args:
        customer: Customer data dict
        upload_id: Upload ID for result storage
        company_info: Company context for campaign generation
        s3: S3 helper instance

    Returns:
        Formatted result dict with status='success' or 'failed'
    """
    customer_id = customer.get('customer_id', 'unknown')

    try:
        print(f"[Async] Processing customer {customer_id}...")

        # Step 1: ChurnAnalyzer Agent (rate limiting happens inside invoke function)
        churn_result = invoke_churn_analyzer_enhanced(customer)
        analysis_text = churn_result.get('analysis', '')

        # Step 2: CampaignGenerationAgent
        from shared.bedrock_client import BedrockClient
        from shared.agents import CampaignGenerationAgent

        bedrock = BedrockClient(model_id='us.anthropic.claude-haiku-4-5-20251001-v1:0')
        campaign_agent = CampaignGenerationAgent(bedrock)

        customer_for_campaign = customer.copy()
        analysis_for_campaign = {
            'full_text': analysis_text,
            'category': churn_result.get('category', 'unclear'),
            'confidence': churn_result.get('confidence', 0),
            'insights': churn_result.get('insights', []),
            'recommendation': churn_result.get('recommendation', '')
        }

        campaign_result = campaign_agent.generate(customer_for_campaign, analysis_for_campaign, company_info)

        # Step 3: Create intelligence summary
        intelligence_summary = create_intelligence_summary(
            analysis_text=analysis_text,
            tools_used=churn_result.get('tools_used', []),
            campaign_emails=campaign_result.get('emails', []),
            customer=customer
        )

        # Format result - flatten customer fields to top level for frontend
        formatted_result = {
            'customer_id': customer_id,
            'status': 'success',
            # Customer fields at top level
            'email': customer.get('email'),
            'company_name': customer.get('company_name'),
            'subscription_tier': customer.get('subscription_tier'),
            'mrr': customer.get('mrr'),
            'churn_date': customer.get('churn_date'),
            'cancellation_reason': customer.get('cancellation_reason'),
            # Also keep nested customer for backward compatibility
            'customer': {
                'email': customer.get('email'),
                'company_name': customer.get('company_name'),
                'subscription_tier': customer.get('subscription_tier'),
                'mrr': customer.get('mrr'),
                'churn_date': customer.get('churn_date'),
                'cancellation_reason': customer.get('cancellation_reason')
            },
            'analysis': {
                'category': churn_result.get('category'),
                'confidence': churn_result.get('confidence'),
                'full_text': analysis_text,
                'tools_used': churn_result.get('tools_used', [])
            },
            'campaign': campaign_result,
            'intelligence_summary': intelligence_summary,
            'processed_at': datetime.utcnow().isoformat() + 'Z'
        }

        # Save individual result
        s3.put_json(f"results/{upload_id}/customers/{customer_id}.json", formatted_result)
        print(f"[Async] ✓ Successfully processed {customer_id}")

        return formatted_result

    except Exception as e:
        print(f"[Async] ✗ Failed to process customer {customer_id}: {e}")
        import traceback
        traceback.print_exc()

        return {
            'customer_id': customer_id,
            'status': 'failed',
            'error': str(e)
        }


def handle_async_processing(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handle async processing triggered by Event invocation.
    Processes customers concurrently using ThreadPoolExecutor with rate limiting.
    """
    upload_id = event.get('upload_id')
    customers = event.get('customers', [])

    print(f"[Async] Starting concurrent processing for upload {upload_id} with {len(customers)} customers (MAX_WORKERS={MAX_WORKERS}, API_RATE_LIMIT={API_RATE_LIMIT} RPM)")

    s3 = S3Helper(DATA_BUCKET)

    # Prepare company info
    company_info = {
        'name': 'ReviveAI',
        'product_name': 'ReviveAI Platform',
        'value_proposition': 'AI-powered customer analytics and retention platform'
    }

    # Thread-safe counters
    completed_lock = threading.Lock()
    completed = 0
    failed = 0
    results = []

    # Adaptive progress update frequency based on batch size
    if len(customers) < 10:
        update_interval = 1  # Every customer for small batches
    elif len(customers) < 50:
        update_interval = 5  # Every 5 customers for medium batches
    else:
        update_interval = 10  # Every 10 customers for large batches

    print(f"[Async] Progress update interval: every {update_interval} customers")

    def update_progress():
        """Thread-safe progress update."""
        nonlocal completed, failed
        with completed_lock:
            status = s3.get_json(f"results/{upload_id}/status.json") or {}
            status['completed'] = completed
            status['failed'] = failed
            status['progress'] = int((completed / len(customers)) * 100) if len(customers) > 0 else 0
            status['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            s3.put_json(f"results/{upload_id}/status.json", status)

    # Process customers concurrently
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_customer = {
            executor.submit(process_single_customer, customer, upload_id, company_info, s3): customer
            for customer in customers
        }

        # Process completed tasks as they finish
        for future in as_completed(future_to_customer):
            result = future.result()
            results.append(result)

            # Update counters
            with completed_lock:
                if result['status'] == 'success':
                    completed += 1
                else:
                    failed += 1

            # Update progress adaptively
            if (completed + failed) % update_interval == 0 or (completed + failed) == len(customers):
                update_progress()

    # Finalize
    final_status = s3.get_json(f"results/{upload_id}/status.json") or {}
    final_status['status'] = 'complete'
    final_status['completed'] = completed
    final_status['failed'] = failed
    final_status['progress'] = 100
    final_status['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    s3.put_json(f"results/{upload_id}/status.json", final_status)
    s3.put_json(f"results/{upload_id}/customers.json", results)

    print(f"[Async] Completed concurrent processing: {completed} succeeded, {failed} failed")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'upload_id': upload_id,
            'status': 'complete',
            'completed': completed,
            'failed': failed,
            'total': len(customers)
        })
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


def handle_process_with_agent(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Process uploaded customers using async Lambda invocation.
    Returns immediately and processes in background.
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

    # IDEMPOTENCY: Check if already processing/processed
    existing_status = s3.get_json(f"results/{upload_id}/status.json")
    if existing_status and existing_status.get('status') in ['processing', 'complete']:
        print(f"[API] Upload {upload_id} already {existing_status.get('status')}")
        return response(202, {
            'upload_id': upload_id,
            'status': existing_status.get('status', 'processing'),
            'total': existing_status.get('total', len(customers)),
            'completed': existing_status.get('completed', 0),
            'message': f'Poll /results?upload_id={upload_id} for progress'
        })

    # Initialize status
    status = create_status_stub(upload_id, len(customers), 'agent-based')
    s3.put_json(f"results/{upload_id}/status.json", status)

    # Invoke async processing
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)

    async_payload = {
        'async_process': True,
        'upload_id': upload_id,
        'customers': customers
    }

    try:
        lambda_client.invoke(
            FunctionName=context.function_name,  # Invoke self
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(async_payload)
        )
        print(f"[API] Started async processing for {upload_id}")
    except Exception as e:
        print(f"[API] Failed to start async processing: {e}")
        return response(500, {'error': f'Failed to start processing: {str(e)}'})

    return response(202, {
        'upload_id': upload_id,
        'status': 'processing',
        'total': len(customers),
        'completed': 0,
        'message': f'Processing started. Poll /results?upload_id={upload_id} for progress'
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
            'tools_used': result['tools_used'],
            'tool_count': result['tool_count'],
            'session_id': result['session_id'],
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


def invoke_coordinator_with_traces(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke Coordinator agent with full reasoning traces and tool extraction.
    Returns comprehensive win-back strategy with autonomous decision-making traces.
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
1. Comprehensive churn analysis using multiple intelligence sources
2. Customer lifetime value assessment
3. Win-back campaign recommendations
"""

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=COORDINATOR_AGENT_ID,
            agentAliasId=COORDINATOR_ALIAS_ID,
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

                # Extract tool usage from traces (same as ChurnAnalyzer)
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

        return {
            'analysis': full_response,
            'reasoning_traces': reasoning_traces,
            'tools_used': tools_used,
            'tool_count': len(tools_used),
            'session_id': session_id
        }

    except Exception as e:
        print(f"Error invoking Coordinator agent: {e}")
        raise


def invoke_bedrock_agent_with_retry(agent_id: str, alias_id: str, session_id: str, input_text: str, max_retries: int = 5):
    """
    Invoke Bedrock agent with exponential backoff retry logic.
    Handles throttling exceptions gracefully.
    """
    import time
    import random

    for attempt in range(max_retries):
        try:
            response = bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=True
            )
            return response

        except Exception as e:
            error_message = str(e)

            # Check if it's a throttling error
            if 'throttlingException' in error_message or 'ThrottlingException' in error_message:
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt + random jitter
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"[Retry] Throttled, waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[Retry] Max retries reached, giving up")
                    raise
            else:
                # Not a throttling error, raise immediately
                raise

    # Should never reach here
    raise Exception("Unexpected retry loop exit")


def invoke_churn_analyzer_enhanced(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke ChurnAnalyzer with enhanced prompt to trigger multiple intelligence tools.
    Shows autonomous decision-making and multi-source analysis.
    Includes exponential backoff retry for throttling.
    """
    session_id = str(uuid.uuid4())

    # Smart prompt - agent decides which tools are actually needed
    input_text = f"""
Analyze churned customer {customer.get('customer_id', 'unknown')} from {customer.get('company_name', 'unknown')}.

Customer Details:
- Customer ID: {customer.get('customer_id', 'unknown')}
- Company: {customer.get('company_name', 'unknown')}
- Subscription Tier: {customer.get('subscription_tier', 'unknown')}
- MRR: ${customer.get('mrr', '0')}
- Churn Date: {customer.get('churn_date', 'unknown')}
- Cancellation Reason: {customer.get('cancellation_reason', 'No reason provided')}

You have access to these intelligence tools (use ONLY the ones that will provide valuable insights for THIS specific customer):
- calculateCLV: Calculate customer lifetime value and win-back ROI
- searchCompanyInfo: Research company funding, growth trajectory, and market position
- getCRMHistory: Review product usage patterns, adoption metrics, and support tickets
- checkProductRoadmap: Check if upcoming features address their concerns
- analyzeChurn: Deep analysis of churn patterns and root causes

IMPORTANT: Be efficient. Only call tools that will add meaningful value based on the churn reason:
- If reason is clear (e.g., "too expensive"), you may only need calculateCLV + analyzeChurn
- If reason is vague or complex, use more tools to investigate
- Prioritize tools that directly address the stated cancellation reason

Provide a strategic win-back analysis with actionable recommendations.
"""

    import time
    import random

    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Rate limit: Acquire 1 token before API call
            rate_limiter.acquire(tokens=1)

            response = bedrock_agent_runtime.invoke_agent(
                agentId=CHURN_ANALYZER_AGENT_ID,
                agentAliasId=CHURN_ANALYZER_ALIAS_ID,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=True
            )

            # Collect response and traces
            full_response = ""
            reasoning_traces = []
            tools_used = []

            # THIS is where throttling actually happens - during stream iteration
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

                        # DEBUG: Print orchestration trace keys
                        print(f"DEBUG orch_trace keys: {list(orch_trace.keys())}")
                        if 'invocationInput' in orch_trace:
                            print(f"DEBUG invocationInput type: {type(orch_trace['invocationInput'])}, length: {len(orch_trace['invocationInput']) if isinstance(orch_trace['invocationInput'], list) else 'N/A'}")

                        # Look for invocationInput (tool being called) - can be array for parallel calls
                        if 'invocationInput' in orch_trace:
                            inv_inputs = orch_trace['invocationInput']

                            # Handle both single invocation and parallel invocations
                            if not isinstance(inv_inputs, list):
                                inv_inputs = [inv_inputs]

                            for inv_input in inv_inputs:
                                if 'actionGroupInvocationInput' in inv_input:
                                    tool_info = inv_input['actionGroupInvocationInput']
                                    tools_used.append({
                                        'tool': tool_info.get('apiPath', 'unknown'),
                                        'action_group': tool_info.get('actionGroupName', 'unknown')
                                    })

            # Success! Return results
            return {
                'analysis': full_response,
                'reasoning_traces': reasoning_traces,
                'tools_used': tools_used,
                'tool_count': len(tools_used),
                'session_id': session_id
            }

        except Exception as e:
            error_message = str(e)

            # Check if it's a throttling error
            if 'throttlingException' in error_message.lower() or 'throttling' in error_message.lower():
                if attempt < max_retries - 1:
                    # Longer exponential backoff: (2^attempt * 3) + random jitter
                    # attempt 0: 3-4s, attempt 1: 6-7s, attempt 2: 12-13s, attempt 3: 24-25s, attempt 4: 48-49s
                    wait_time = (2 ** attempt * 3) + random.uniform(0, 1)
                    print(f"[Retry] Throttled, waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries} (customer: {customer.get('customer_id', 'unknown')})")
                    time.sleep(wait_time)
                    continue  # Retry
                else:
                    print(f"[Retry] Max retries reached after {max_retries} attempts (customer: {customer.get('customer_id', 'unknown')})")
                    raise
            else:
                # Not a throttling error, raise immediately
                print(f"Error invoking ChurnAnalyzer agent (customer: {customer.get('customer_id', 'unknown')}): {e}")
                raise

    # Should never reach here
    raise Exception("Unexpected retry loop exit")


def invoke_campaign_generator(customer: Dict[str, Any], analysis: str) -> Dict[str, Any]:
    """
    Invoke CampaignGenerator agent to create personalized win-back campaign.
    Takes customer data and churn analysis as input.
    """
    session_id = str(uuid.uuid4())

    # Build input for campaign generation
    input_text = f"""
Create a personalized win-back campaign for this churned customer:

Customer Information:
- Company: {customer.get('company_name', 'unknown')}
- Customer ID: {customer.get('customer_id', 'unknown')}
- Email: {customer.get('email', 'not provided')}
- Tier: {customer.get('subscription_tier', 'unknown')}
- MRR: ${customer.get('mrr', '0')}

Churn Analysis Summary:
{analysis[:1000]}

Generate a comprehensive win-back campaign including:
1. Personalized email subject line and body
2. Key value propositions to address their concerns
3. Special incentive or offer (if appropriate)
4. Optimal timing and channel recommendations
"""

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=CAMPAIGN_GENERATOR_AGENT_ID,
            agentAliasId=CAMPAIGN_GENERATOR_ALIAS_ID,
            sessionId=session_id,
            inputText=input_text,
            enableTrace=True
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

                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                tool_info = inv_input['actionGroupInvocationInput']
                                tools_used.append({
                                    'tool': tool_info.get('apiPath', 'unknown'),
                                    'action_group': tool_info.get('actionGroupName', 'unknown')
                                })

        return {
            'campaign': full_response,
            'reasoning_traces': reasoning_traces,
            'tools_used': tools_used,
            'tool_count': len(tools_used),
            'session_id': session_id
        }

    except Exception as e:
        print(f"Error invoking CampaignGenerator agent: {e}")
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

                        # DEBUG: Print orchestration trace keys
                        print(f"DEBUG orch_trace keys: {list(orch_trace.keys())}")
                        if 'invocationInput' in orch_trace:
                            print(f"DEBUG invocationInput type: {type(orch_trace['invocationInput'])}, length: {len(orch_trace['invocationInput']) if isinstance(orch_trace['invocationInput'], list) else 'N/A'}")

                        # Look for invocationInput (tool being called) - can be array for parallel calls
                        if 'invocationInput' in orch_trace:
                            inv_inputs = orch_trace['invocationInput']

                            # Handle both single invocation and parallel invocations
                            if not isinstance(inv_inputs, list):
                                inv_inputs = [inv_inputs]

                            for inv_input in inv_inputs:
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

    # Check if all workers are done (for fan-out pattern)
    completed = status.get('completed', 0)
    failed = status.get('failed', 0)
    total = status.get('total', 0)

    # If all workers are done, finalize status and aggregate results
    if status['status'] == 'processing' and (completed + failed) >= total and total > 0:
        print(f"[Results] All workers done: {completed} completed, {failed} failed out of {total}")

        # Aggregate individual customer results
        campaigns = []
        try:
            # List all customer result files
            import boto3
            s3_client = boto3.client('s3')
            prefix = f"results/{upload_id}/customers/"

            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=DATA_BUCKET, Prefix=prefix)

            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if key.endswith('.json'):
                            customer_result = s3.get_json(key)
                            if customer_result:
                                campaigns.append(customer_result)

            print(f"[Results] Aggregated {len(campaigns)} customer results")

            # Save aggregated results
            s3.put_json(f"results/{upload_id}/customers.json", campaigns)

            # Finalize status
            status['status'] = 'complete'
            status['estimated_remaining_seconds'] = 0
            s3.put_json(f"results/{upload_id}/status.json", status)

        except Exception as e:
            print(f"[Results] Error aggregating results: {e}")
            # Continue anyway

        return response(200, {
            'status': 'complete',
            'upload_id': upload_id,
            'total': total,
            'completed': completed,
            'failed': failed,
            'campaigns': campaigns
        })

    # If still processing, return progress
    if status['status'] == 'processing':
        return response(200, {
            'status': 'processing',
            'completed': completed,
            'total': total,
            'progress': int((completed / max(total, 1)) * 100),
            'failures': failed
        })

    # If complete (already finalized), return full results
    campaigns = []
    customers_data = s3.get_json(f"results/{upload_id}/customers.json")
    if customers_data:
        campaigns = customers_data

    return response(200, {
        'status': status['status'],
        'upload_id': upload_id,
        'total': total,
        'completed': completed,
        'failed': failed,
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
