"""
SQS Worker Lambda for processing individual customers with controlled concurrency.
Processes one customer per invocation from SQS messages.
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
import uuid
import boto3

# Add shared module to path
sys.path.insert(0, '/opt/python')

from shared.s3_helper import S3Helper
from shared.agents import CampaignGenerationAgent
from shared.bedrock_client import BedrockClient

# Environment variables
DATA_BUCKET = os.environ.get('DATA_BUCKET', 'revive-ai-data')
CHURN_ANALYZER_AGENT_ID = os.environ.get('CHURN_ANALYZER_AGENT_ID', 'HAKDC7PY1Z')
CHURN_ANALYZER_ALIAS_ID = os.environ.get('CHURN_ANALYZER_ALIAS_ID', 'TSTALIASID')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
s3 = S3Helper(DATA_BUCKET)


def lambda_handler(event, context):
    """
    Process a single customer from SQS message.

    Expected SQS message body:
    {
        "customer": {...},
        "upload_id": "...",
        "company_info": {...}
    }
    """
    print(f"Worker received {len(event.get('Records', []))} SQS messages")

    # Process each SQS message (should be 1 per invocation with batch size 1)
    for record in event.get('Records', []):
        try:
            # Parse message
            message_body = json.loads(record['body'])
            customer = message_body['customer']
            upload_id = message_body['upload_id']
            company_info = message_body.get('company_info', {})

            customer_id = customer['customer_id']

            # IDEMPOTENCY CHECK: Skip if already successfully processed
            try:
                existing_result = s3.get_json(f"results/{upload_id}/customers/{customer_id}.json")
                if existing_result and existing_result.get('customer_id') == customer_id:
                    print(f"[Worker] ⏭️  Skipping {customer_id} - already processed")
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'message': 'Already processed', 'customer_id': customer_id})
                    }
            except:
                pass  # File doesn't exist, proceed with processing

            print(f"[Worker] Processing customer {customer_id}")

            # Step 1: ChurnAnalyzer Agent
            print(f"[Worker] Step 1: ChurnAnalyzer for {customer_id}")
            churn_result = invoke_churn_analyzer_enhanced(customer)

            # Step 2: CampaignGenerationAgent
            print(f"[Worker] Step 2: CampaignGenerator for {customer_id}")
            bedrock = BedrockClient(model_id='us.anthropic.claude-3-5-haiku-20241022-v1:0')
            campaign_agent = CampaignGenerationAgent(bedrock)

            # Prepare data for campaign generation
            customer_for_campaign = customer.copy()
            analysis_for_campaign = {
                'full_text': churn_result.get('analysis_text', ''),
                'category': churn_result.get('category', 'unclear'),
                'confidence': churn_result.get('confidence', 0),
                'insights': churn_result.get('insights', []),
                'recommendation': churn_result.get('recommendation', '')
            }

            campaign_result = campaign_agent.generate(
                customer_for_campaign,
                analysis_for_campaign,
                company_info
            )

            # Step 3: Create intelligence summary
            print(f"[Worker] Step 3: Intelligence summary for {customer_id}")
            intelligence_summary = create_intelligence_summary(
                churn_result.get('analysis_text', ''),
                churn_result.get('tools_used', []),
                campaign_result.get('emails', []),
                customer
            )

            # Format result
            formatted_result = {
                'customer_id': customer_id,
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
                    'full_text': churn_result.get('analysis_text'),
                    'tools_used': churn_result.get('tools_used', [])
                },
                'campaign': campaign_result,
                'intelligence_summary': intelligence_summary,
                'processed_at': datetime.utcnow().isoformat() + 'Z'
            }

            # Save result to S3
            s3.put_json(f"results/{upload_id}/customers/{customer_id}.json", formatted_result)
            print(f"[Worker] ✓ Successfully processed {customer_id}")

            # Update status
            update_status_increment(upload_id, success=True)

        except Exception as e:
            print(f"[Worker] ✗ Failed to process customer: {str(e)}")
            import traceback
            traceback.print_exc()

            # Update status
            customer_id = message_body.get('customer', {}).get('customer_id', 'unknown')
            upload_id = message_body.get('upload_id', 'unknown')
            update_status_increment(upload_id, success=False, error=str(e), customer_id=customer_id)

            # Re-raise to trigger SQS retry (up to maxReceiveCount)
            raise

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Worker completed'})
    }


def invoke_churn_analyzer_enhanced(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke ChurnAnalyzer with enhanced prompt for optional tool usage.
    Includes exponential backoff retry for throttling.
    """
    session_id = str(uuid.uuid4())

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
                                inv_inputs = orch_trace['invocationInput']

                                if not isinstance(inv_inputs, list):
                                    inv_inputs = [inv_inputs]

                                for inv_input in inv_inputs:
                                    if 'actionGroupInvocationInput' in inv_input:
                                        tool_info = inv_input['actionGroupInvocationInput']
                                        tool_name = tool_info.get('function', 'unknown')
                                        if tool_name and tool_name not in [t['tool'] for t in tools_used]:
                                            tools_used.append({'tool': tool_name})

            return {
                'analysis_text': full_response,
                'tools_used': tools_used,
                'category': 'unclear',  # Extracted from analysis_text if needed
                'confidence': 0,
                'insights': [],
                'recommendation': ''
            }

        except Exception as e:
            error_message = str(e)

            if 'throttlingException' in error_message or 'ThrottlingException' in error_message:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"[Worker Retry] Throttled on InvokeAgent, waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[Worker Retry] Max retries reached on InvokeAgent")
                    raise
            else:
                raise

    raise Exception("Unexpected retry loop exit in invoke_churn_analyzer_enhanced")


def extract_key_findings_with_ai(analysis_text: str, customer: Dict[str, Any]) -> List[str]:
    """Use AI to extract 2-5 key findings from analysis."""
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
        bedrock = BedrockClient(model_id='us.anthropic.claude-3-5-haiku-20241022-v1:0')
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
        print(f"[Worker] Error extracting key findings: {e}")
        return []


def create_intelligence_summary(analysis_text: str, tools_used: List[Dict], campaign_emails: List[Dict], customer: Dict[str, Any]) -> Dict[str, Any]:
    """Create visual intelligence summary using AI for key findings extraction."""
    from datetime import datetime

    summary = {
        'total_tools_used': len(tools_used),
        'key_findings': [],
        'campaign_preview': {
            'total_emails': len(campaign_emails),
            'first_email_subject': '',
            'last_email_subject': ''
        },
        'generated_at': datetime.utcnow().isoformat() + 'Z'
    }

    # 1. Tools used
    summary['tools_list'] = [tool.get('tool', 'unknown') for tool in tools_used]

    # 2. Extract key findings using AI
    summary['key_findings'] = extract_key_findings_with_ai(analysis_text, customer)

    # 3. Campaign preview
    if campaign_emails:
        summary['campaign_preview']['first_email_subject'] = campaign_emails[0].get('subject', '')
        summary['campaign_preview']['last_email_subject'] = campaign_emails[-1].get('subject', '')

    return summary


def update_status_increment(upload_id: str, success: bool, error: str = None, customer_id: str = None):
    """
    Atomically increment completed/failed counters using DynamoDB.
    Thread-safe for concurrent Lambda invocations.
    """
    try:
        # Use DynamoDB for atomic increments
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        table_name = 'revive-ai-job-status'

        # Atomic increment using UpdateItem with ADD
        field_name = 'completed' if success else 'failed'
        update_expr = f'SET updated_at = :now ADD {field_name} :inc'

        expr_values = {
            ':inc': {'N': '1'},
            ':now': {'S': datetime.utcnow().isoformat() + 'Z'}
        }

        # Atomic update
        response = dynamodb.update_item(
            TableName=table_name,
            Key={'upload_id': {'S': upload_id}},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
            ReturnValues='ALL_NEW'
        )

        # Get updated values
        attrs = response['Attributes']
        completed = int(attrs.get('completed', {}).get('N', '0'))
        failed = int(attrs.get('failed', {}).get('N', '0'))
        total = int(attrs.get('total', {}).get('N', '0'))

        # Update S3 status file for API reads
        status = {
            'upload_id': upload_id,
            'status': 'completed' if completed + failed >= total else 'processing',
            'total': total,
            'completed': completed,
            'failed': failed,
            'updated_at': datetime.utcnow().isoformat() + 'Z'
        }

        if error and customer_id:
            existing_status = s3.get_json(f"results/{upload_id}/status.json") or {}
            status['errors'] = existing_status.get('errors', [])
            status['errors'].append({
                'customer_id': customer_id,
                'error': error,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        s3.put_json(f"results/{upload_id}/status.json", status)

    except Exception as e:
        print(f"[Worker] Warning: Failed to update status: {e}")
        import traceback
        traceback.print_exc()
