"""
Bedrock Agent Action Group Executor
Handles tool invocations from Bedrock Agents
"""
import json
import boto3
import os
import sys
from datetime import datetime

# Add shared module to path
sys.path.insert(0, '/opt/python')

from shared.bedrock_client import BedrockClient
from shared.agents import ChurnAnalysisAgent, CampaignGenerationAgent
from shared.s3_helper import S3Helper

# Environment
DATA_BUCKET = os.environ.get('DATA_BUCKET', 'revive-ai-data')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'us.anthropic.claude-3-5-haiku-20241022-v1:0')

def lambda_handler(event, context):
    """
    Handle Bedrock Agent action group invocations.

    Event structure from Bedrock Agent:
    {
        "messageVersion": "1.0",
        "agent": {...},
        "sessionId": "...",
        "actionGroup": "churn-analysis-tools",
        "apiPath": "/analyzeChurn",
        "httpMethod": "POST",
        "parameters": [
            {"name": "customer_id", "type": "string", "value": "c001"},
            ...
        ],
        "requestBody": {...}
    }
    """
    print(f"Event: {json.dumps(event)}")

    try:
        # Extract request details
        action_group = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        parameters = event.get('parameters', [])
        request_body = event.get('requestBody', {})

        # Convert parameters list to dict for easier access
        params_dict = {}
        for param in parameters:
            params_dict[param['name']] = param['value']

        # ALSO check requestBody.content for parameters (Bedrock agents sometimes put them here)
        if request_body.get('content', {}).get('application/json', {}).get('properties'):
            for prop in request_body['content']['application/json']['properties']:
                if prop.get('name') and prop.get('value') is not None:
                    params_dict[prop['name']] = prop['value']

        # Route to appropriate handler
        result = route_action(action_group, api_path, params_dict, request_body)

        # Return in Bedrock Agent format
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': event.get('httpMethod', 'POST'),
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', ''),
                'apiPath': event.get('apiPath', ''),
                'httpMethod': event.get('httpMethod', 'POST'),
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }


def route_action(action_group, api_path, params, request_body):
    """Route to appropriate tool handler."""

    # Churn Analysis Tools
    if action_group == 'churn-analysis-tools':
        if api_path == '/analyzeChurn':
            return handle_analyze_churn(params, request_body)
        elif api_path == '/calculateCLV':
            return handle_calculate_clv(params)
        elif api_path == '/checkProductRoadmap':
            return handle_check_product_roadmap(params, request_body)
        elif api_path == '/getCRMHistory':
            return handle_get_crm_history(params, request_body)
        elif api_path == '/searchCompanyInfo':
            return handle_search_company_info(params, request_body)

    # Campaign Tools (original)
    elif action_group == 'campaign-tools':
        if api_path == '/generateCampaign':
            return handle_generate_campaign(params, request_body)

    # Campaign Generator Agent Tools (new)
    elif action_group == 'campaign-generator-tools':
        if api_path == '/generateEmailSequence':
            return handle_generate_email_sequence(params, request_body)
        elif api_path == '/personalizeContent':
            return handle_personalize_content(params, request_body)

    # Data Tools
    elif action_group == 'data-tools':
        if api_path == '/saveResults':
            return handle_save_results(params, request_body)
        elif api_path == '/retrieveCustomerData':
            return handle_retrieve_customer(params)

    # Coordinator Tools
    elif action_group == 'coordinator-tools':
        if api_path == '/escalateToHuman':
            return handle_escalate(params, request_body)
        elif api_path == '/invokeChurnAnalyzer':
            return handle_invoke_churn_analyzer(params, request_body)
        elif api_path == '/invokeCampaignGenerator':
            return handle_invoke_campaign_generator(params, request_body)
        elif api_path == '/makeDecision':
            return handle_make_decision(params, request_body)
        elif api_path == '/saveWorkflowResults':
            return handle_save_workflow_results(params, request_body)

    raise ValueError(f"Unknown action: {action_group}/{api_path}")


def handle_analyze_churn(params, request_body):
    """Analyze customer churn reason."""
    print("Executing: analyzeChurn")

    # Extract customer data from request
    content = request_body.get('content', {})
    customer = {
        'customer_id': params.get('customer_id') or content.get('customer_id'),
        'company_name': params.get('company_name') or content.get('company_name'),
        'subscription_tier': params.get('subscription_tier') or content.get('subscription_tier', 'growth'),
        'mrr': float(params.get('mrr', 0)) if params.get('mrr') else float(content.get('mrr', 0)),
        'churn_date': params.get('churn_date') or content.get('churn_date'),
        'cancellation_reason': params.get('cancellation_reason') or content.get('cancellation_reason', '')
    }

    print(f"Analyzing customer: {customer['customer_id']}")

    # Use existing analysis agent
    bedrock = BedrockClient(model_id=BEDROCK_MODEL_ID)
    analysis_agent = ChurnAnalysisAgent(bedrock)
    result = analysis_agent.analyze(customer)

    print(f"Analysis result: {result}")
    return result


def handle_calculate_clv(params):
    """Calculate Customer Lifetime Value."""
    print("Executing: calculateCLV")

    mrr = float(params.get('mrr', 0))
    subscription_tier = params.get('subscription_tier', 'growth')

    # Simple CLV calculation: MRR × average tenure
    # Tier-based tenure assumptions
    tenure_months = {
        'starter': 12,
        'growth': 24,
        'enterprise': 36
    }

    avg_tenure = tenure_months.get(subscription_tier, 24)
    clv = mrr * avg_tenure

    # Prioritization
    if clv > 50000:
        priority = "CRITICAL"
        recommendation = "Escalate to VP Sales - high-value customer"
    elif clv > 20000:
        priority = "HIGH"
        recommendation = "Premium automated campaign + sales notification"
    elif clv > 5000:
        priority = "MEDIUM"
        recommendation = "Standard automated campaign"
    else:
        priority = "LOW"
        recommendation = "Basic campaign or no action"

    result = {
        'clv': clv,
        'avg_tenure_months': avg_tenure,
        'priority': priority,
        'recommendation': recommendation,
        'winback_probability': 0.65 if priority in ['HIGH', 'CRITICAL'] else 0.45
    }

    print(f"CLV result: {result}")
    return result


def handle_generate_campaign(params, request_body):
    """Generate win-back email campaign."""
    print("Executing: generateCampaign")

    content = request_body.get('content', {})

    # Extract customer and analysis data
    customer = {
        'customer_id': params.get('customer_id') or content.get('customer_id'),
        'company_name': params.get('company_name') or content.get('company_name'),
        'email': params.get('email') or content.get('email', 'customer@example.com'),
        'subscription_tier': params.get('subscription_tier') or content.get('subscription_tier', 'growth'),
        'mrr': float(params.get('mrr', 0)) if params.get('mrr') else float(content.get('mrr', 0)),
        'churn_date': params.get('churn_date') or content.get('churn_date'),
        'cancellation_reason': params.get('cancellation_reason') or content.get('cancellation_reason', '')
    }

    analysis = content.get('analysis', {
        'category': params.get('churn_category', 'unclear'),
        'confidence': 80,
        'insights': ['Customer churned'],
        'recommendation': 'Re-engage with value proposition'
    })

    print(f"Generating campaign for: {customer['customer_id']}, category: {analysis['category']}")

    # Use existing campaign agent
    bedrock = BedrockClient(model_id=BEDROCK_MODEL_ID)
    campaign_agent = CampaignGenerationAgent(bedrock)
    result = campaign_agent.generate(customer, analysis)

    print(f"Campaign generated: {len(result.get('emails', []))} emails")
    return result


def handle_save_results(params, request_body):
    """Save campaign results to S3."""
    print("Executing: saveResults")

    content = request_body.get('content', {})

    upload_id = params.get('upload_id') or content.get('upload_id')
    customer_id = params.get('customer_id') or content.get('customer_id')
    data = content.get('data', {})

    # Save to S3
    s3 = S3Helper(DATA_BUCKET)
    key = f"results/{upload_id}/customers/{customer_id}.json"

    s3_client = boto3.client('s3')
    s3_client.put_object(
        Bucket=DATA_BUCKET,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType='application/json'
    )

    print(f"Saved to S3: {key}")

    return {
        'success': True,
        's3_key': key,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def handle_retrieve_customer(params):
    """Retrieve customer data from S3."""
    print("Executing: retrieveCustomerData")

    upload_id = params.get('upload_id')
    customer_id = params.get('customer_id')

    s3 = S3Helper(DATA_BUCKET)

    # Try to get from uploaded CSV data
    customers_data = s3.get_json(f"uploads/{upload_id}/customers.json")

    if customers_data:
        for customer in customers_data:
            if customer.get('customer_id') == customer_id:
                return customer

    return {'error': 'Customer not found'}


def handle_escalate(params, request_body):
    """Escalate high-value customer to sales team."""
    print("Executing: escalateToHuman")

    content = request_body.get('content', {})

    customer_id = params.get('customer_id') or content.get('customer_id')
    priority = params.get('priority') or content.get('priority', 'HIGH')
    clv = params.get('clv') or content.get('clv', 0)
    insight = params.get('insight') or content.get('insight', '')

    # Create escalation ticket (mock for demo)
    ticket_id = f"TICKET-{customer_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    escalation = {
        'ticket_id': ticket_id,
        'customer_id': customer_id,
        'priority': priority,
        'clv': clv,
        'insight': insight,
        'assigned_to': 'VP_Sales' if priority == 'CRITICAL' else 'Sales_Team',
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'status': 'OPEN',
        'action': 'Personal outreach required - high-value customer recovery'
    }

    print(f"Escalation created: {escalation}")

    # In production, this would:
    # - Create Salesforce ticket
    # - Send email to sales team
    # - Update CRM

    return escalation


def handle_invoke_churn_analyzer(params, request_body):
    """Invoke Churn Analyzer agent (for coordinator)."""
    print("Executing: invokeChurnAnalyzer (via Coordinator)")

    content = request_body.get('content', {})

    # Extract customer data
    customer = {
        'customer_id': params.get('customer_id') or content.get('customer_id'),
        'company_name': params.get('company_name') or content.get('company_name'),
        'subscription_tier': params.get('subscription_tier') or content.get('subscription_tier', 'growth'),
        'mrr': float(params.get('mrr', 0)) if params.get('mrr') else float(content.get('mrr', 0)),
        'churn_date': params.get('churn_date') or content.get('churn_date'),
        'cancellation_reason': params.get('cancellation_reason') or content.get('cancellation_reason', '')
    }

    print(f"Coordinator invoking Churn Analyzer for: {customer['customer_id']}")

    # Use bedrock-agent-runtime to invoke the churn analyzer agent
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

    # Format input for churn analyzer agent
    input_text = f"""Analyze this customer:
- Customer ID: {customer['customer_id']}
- Company: {customer['company_name']}
- MRR: ${customer['mrr']}
- Subscription: {customer['subscription_tier']}
- Churn Date: {customer.get('churn_date', 'N/A')}
- Reason: {customer['cancellation_reason']}"""

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId='HAKDC7PY1Z',
            agentAliasId='TSTALIASID',  # Use DRAFT alias with all 5 intelligence tools
            sessionId=str(customer['customer_id']) + '-session',
            inputText=input_text,
            enableTrace=True  # Enable traces to capture tool usage
        )

        # Collect response
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')

        print(f"Churn Analyzer response: {full_response[:200]}...")

        # Return the agent's intelligent analysis as plain text
        # The Coordinator will interpret this natural language response
        return {
            'analysis': full_response,
            'source': 'Churn Analyzer Agent with Multi-Tool Intelligence',
            'tools_used': 'calculateCLV, getCRMHistory, checkProductRoadmap, searchCompanyInfo, analyzeChurn'
        }

    except Exception as e:
        print(f"Error invoking Churn Analyzer agent: {e}")
        # Fallback to direct analysis
        bedrock = BedrockClient(model_id=BEDROCK_MODEL_ID)
        analysis_agent = ChurnAnalysisAgent(bedrock)
        return analysis_agent.analyze(customer)


def handle_invoke_campaign_generator(params, request_body):
    """Invoke Campaign Generator agent (for coordinator)."""
    print("Executing: invokeCampaignGenerator (via Coordinator)")

    content = request_body.get('content', {})

    customer_id = params.get('customer_id') or content.get('customer_id')
    company_name = params.get('company_name') or content.get('company_name')

    # Parse churn_analysis from params (it comes as a string)
    churn_analysis_str = params.get('churn_analysis', '{}')
    if isinstance(churn_analysis_str, str):
        churn_analysis = json.loads(churn_analysis_str)
    else:
        churn_analysis = churn_analysis_str

    print(f"Coordinator invoking Campaign Generator for: {customer_id}")

    # Invoke the CampaignGenerator Bedrock agent
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

    # Format input for campaign generator agent
    churn_analysis_summary = f"""Customer: {company_name}
Category: {churn_analysis.get('churn_category', 'unclear')}
Confidence: {churn_analysis.get('confidence', 80)}%
Insights: {', '.join(churn_analysis.get('insights', []))}
Recommendation: {churn_analysis.get('recommendation', '')}"""

    input_text = f"""Create a win-back email campaign for customer {customer_id} at {company_name}.

Churn Analysis:
{churn_analysis_summary}

Generate a 3-email sequence to win back this customer."""

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId='HXMON0RCRP',
            agentAliasId='TSTALIASID',  # Use DRAFT alias
            sessionId=str(customer_id) + '-campaign-session',
            inputText=input_text,
            enableTrace=True
        )

        # Collect response
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')

        print(f"Campaign Generator response: {full_response[:200]}...")

        # Return campaign text - Coordinator will interpret it
        return {
            'campaign': full_response,
            'source': 'Campaign Generator Agent',
            'customer_id': customer_id
        }

    except Exception as e:
        print(f"Error invoking Campaign Generator agent: {e}")
        # Fallback to direct generation
        customer = {
            'customer_id': customer_id,
            'company_name': company_name,
            'email': params.get('email') or content.get('email', 'customer@example.com'),
            'subscription_tier': churn_analysis.get('subscription_tier', 'growth'),
            'mrr': churn_analysis.get('mrr', '500'),
            'cancellation_reason': churn_analysis.get('churn_category', 'unclear')
        }

        analysis_fixed = {
            'category': churn_analysis.get('churn_category', churn_analysis.get('category', 'unclear')),
            'confidence': churn_analysis.get('confidence', 80),
            'insights': churn_analysis.get('insights', ['Customer churned']),
            'recommendation': churn_analysis.get('recommendation', 'Re-engage with targeted campaign')
        }

        bedrock = BedrockClient(model_id=BEDROCK_MODEL_ID)
        campaign_agent = CampaignGenerationAgent(bedrock)
        result = campaign_agent.generate(customer, analysis_fixed)
        return result


def handle_make_decision(params, request_body):
    """Make strategic decision on customer handling."""
    print("Executing: makeDecision")

    content = request_body.get('content', {})

    customer_id = params.get('customer_id') or content.get('customer_id')
    clv = float(params.get('clv', 0)) if params.get('clv') else float(content.get('clv', 0))
    priority = params.get('priority') or content.get('priority', 'MEDIUM')
    churn_category = params.get('churn_category') or content.get('churn_category', 'unclear')
    winback_probability = float(params.get('winback_probability', 0.5)) if params.get('winback_probability') else float(content.get('winback_probability', 0.5))

    print(f"Making decision for {customer_id}: CLV=${clv}, Priority={priority}, Winback={winback_probability}")

    # Decision logic
    if clv > 50000 and priority == 'CRITICAL':
        decision = 'ESCALATE_TO_HUMAN'
        reasoning = f'High-value customer (CLV ${clv}) requires personal attention from senior sales team'
        assigned_to = 'VP_Sales'
        next_action = 'Schedule executive call within 24 hours'
    elif clv > 20000 and winback_probability > 0.6:
        decision = 'AUTOMATED_CAMPAIGN'
        reasoning = f'Valuable customer (CLV ${clv}) with good winback probability ({winback_probability:.0%})'
        assigned_to = 'Marketing_Automation'
        next_action = 'Launch premium automated campaign with sales notification'
    elif clv > 5000:
        decision = 'AUTOMATED_CAMPAIGN'
        reasoning = f'Medium-value customer (CLV ${clv}) suitable for standard automated approach'
        assigned_to = 'Marketing_Automation'
        next_action = 'Launch standard automated campaign'
    elif winback_probability < 0.3:
        decision = 'SKIP'
        reasoning = f'Low winback probability ({winback_probability:.0%}) and moderate CLV (${clv})'
        assigned_to = 'None'
        next_action = 'No action - customer unlikely to return'
    else:
        decision = 'AUTOMATED_CAMPAIGN'
        reasoning = f'Standard case - CLV ${clv}, winback probability {winback_probability:.0%}'
        assigned_to = 'Marketing_Automation'
        next_action = 'Launch basic automated campaign'

    result = {
        'decision': decision,
        'reasoning': reasoning,
        'assigned_to': assigned_to,
        'next_action': next_action,
        'customer_id': customer_id,
        'clv': clv,
        'priority': priority,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    print(f"Decision result: {result}")
    return result


def handle_save_workflow_results(params, request_body):
    """Save complete workflow results."""
    print("Executing: saveWorkflowResults")

    content = request_body.get('content', {})

    upload_id = params.get('upload_id') or content.get('upload_id')
    customer_id = params.get('customer_id') or content.get('customer_id')
    workflow_data = content.get('workflow_data', {})

    # Add metadata
    workflow_data['saved_at'] = datetime.utcnow().isoformat() + 'Z'
    workflow_data['workflow_version'] = '2.0-multi-agent'

    # Save to S3
    s3_client = boto3.client('s3')
    key = f"workflows/{upload_id}/customers/{customer_id}.json"

    s3_client.put_object(
        Bucket=DATA_BUCKET,
        Key=key,
        Body=json.dumps(workflow_data, indent=2),
        ContentType='application/json'
    )

    print(f"Workflow saved to S3: {key}")

    return {
        'success': True,
        's3_key': key,
        'customer_id': customer_id,
        'timestamp': workflow_data['saved_at']
    }


def handle_generate_email_sequence(params, request_body):
    """Generate email sequence (Campaign Generator Agent tool)."""
    print("Executing: generateEmailSequence")

    content = request_body.get('content', {})

    customer_id = params.get('customer_id') or content.get('customer_id')
    company_name = params.get('company_name') or content.get('company_name')
    churn_category = params.get('churn_category') or content.get('churn_category', 'unclear')
    priority = params.get('priority') or content.get('priority', 'MEDIUM')
    insights = content.get('insights', [])

    print(f"Generating email sequence for {customer_id}, category: {churn_category}")

    # Use existing campaign generation logic
    customer = {
        'customer_id': customer_id,
        'company_name': company_name,
        'email': 'customer@example.com',
        'subscription_tier': 'growth',
        'mrr': '0',  # Add mrr field to avoid KeyError
        'cancellation_reason': churn_category
    }

    analysis = {
        'category': churn_category,
        'confidence': 80,
        'insights': insights if insights else ['Customer churned'],
        'recommendation': 'Re-engage with targeted campaign'
    }

    bedrock = BedrockClient(model_id=BEDROCK_MODEL_ID)
    campaign_agent = CampaignGenerationAgent(bedrock)
    result = campaign_agent.generate(customer, analysis)

    return {
        'emails': result.get('emails', []),
        'campaign_strategy': result.get('strategy', 'Personalized win-back campaign based on churn analysis')
    }


def handle_personalize_content(params, request_body):
    """Personalize campaign content."""
    print("Executing: personalizeContent")

    content = request_body.get('content', {})

    customer_id = params.get('customer_id') or content.get('customer_id')
    template = params.get('template') or content.get('template', '')
    customer_data = content.get('customer_data', {})

    print(f"Personalizing content for {customer_id}")

    # Simple personalization - replace tokens
    personalized = template
    tokens_used = []

    if '{company_name}' in template and customer_data.get('company_name'):
        personalized = personalized.replace('{company_name}', customer_data['company_name'])
        tokens_used.append('company_name')

    if '{mrr}' in template and customer_data.get('mrr'):
        personalized = personalized.replace('{mrr}', str(customer_data['mrr']))
        tokens_used.append('mrr')

    if '{subscription_tier}' in template and customer_data.get('subscription_tier'):
        personalized = personalized.replace('{subscription_tier}', customer_data['subscription_tier'])
        tokens_used.append('subscription_tier')

    return {
        'personalized_content': personalized,
        'personalization_tokens': tokens_used,
        'customer_id': customer_id
    }


def handle_check_product_roadmap(params, request_body):
    """Check product roadmap for upcoming features that address churn reasons."""
    print("Executing: checkProductRoadmap")

    content = request_body.get('content', {})

    churn_category = params.get('churn_category') or content.get('churn_category', '')
    churn_reason = params.get('churn_reason') or content.get('churn_reason', '')

    print(f"Checking roadmap for churn category: {churn_category}")

    # Load roadmap from S3
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(
            Bucket=DATA_BUCKET,
            Key='knowledge/product-roadmap.json'
        )
        roadmap = json.loads(response['Body'].read().decode('utf-8'))

        # Find relevant features
        relevant_features = []
        keywords = churn_reason.lower().split() + [churn_category.lower()]

        for feature in roadmap['upcoming_features']:
            # Check if feature solves this churn reason
            solves = feature.get('solves_churn_reasons', [])
            matches = any(keyword in ' '.join(solves).lower() for keyword in keywords)

            if matches or churn_category.lower() in feature['category'].lower():
                relevant_features.append({
                    'feature': feature['feature'],
                    'release_date': feature['release_date'],
                    'status': feature['status'],
                    'description': feature['description'],
                    'benefits': feature['benefits']
                })

        result = {
            'roadmap_version': roadmap['roadmap_version'],
            'relevant_features_count': len(relevant_features),
            'features': relevant_features[:3],  # Top 3 most relevant
            'recent_improvements': roadmap.get('recent_improvements', [])
        }

        print(f"Found {len(relevant_features)} relevant features")
        return result

    except Exception as e:
        print(f"Error loading roadmap: {e}")
        return {
            'error': 'Could not load product roadmap',
            'roadmap_version': 'unavailable',
            'relevant_features_count': 0,
            'features': []
        }


def handle_get_crm_history(params, request_body):
    """Retrieve customer CRM history and usage patterns."""
    print("Executing: getCRMHistory")

    content = request_body.get('content', {})

    customer_id = params.get('customer_id') or content.get('customer_id')

    print(f"Retrieving CRM history for: {customer_id}")

    # Load CRM data from S3
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(
            Bucket=DATA_BUCKET,
            Key='knowledge/crm-history.json'
        )
        crm_data = json.loads(response['Body'].read().decode('utf-8'))

        # Get customer history
        customer_history = crm_data['customers'].get(customer_id)

        if not customer_history:
            return {
                'found': False,
                'customer_id': customer_id,
                'message': 'No CRM history found for this customer'
            }

        # Return summarized history
        result = {
            'found': True,
            'customer_id': customer_id,
            'usage_summary': {
                'months_active': customer_history['usage_history']['total_months'],
                'usage_trend': customer_history['usage_history']['usage_trend'],
                'feature_adoption': customer_history['usage_history']['feature_adoption'],
                'recent_growth': customer_history['usage_history'].get('last_3_months_growth', 'N/A')
            },
            'support_summary': {
                'total_tickets': customer_history['support_history']['total_tickets'],
                'satisfaction': customer_history['support_history']['satisfaction_score'],
                'recent_issues': [
                    {
                        'date': ticket['date'],
                        'subject': ticket['subject'],
                        'sentiment': ticket['sentiment']
                    }
                    for ticket in customer_history['support_history'].get('recent_tickets', [])[:3]
                ]
            },
            'health_metrics': {
                'engagement_score': customer_history['engagement_score'],
                'health_score': customer_history['health_score_before_churn'],
                'churn_risk_flags': customer_history.get('churn_risk_flags', [])
            },
            'insights': {
                'missed_opportunities': customer_history.get('upsell_opportunities_missed', [])
            }
        }

        print(f"CRM history retrieved: {customer_history['usage_history']['total_months']} months")
        return result

    except Exception as e:
        print(f"Error loading CRM history: {e}")
        return {
            'found': False,
            'customer_id': customer_id,
            'error': str(e)
        }


def handle_search_company_info(params, request_body):
    """Search for company information via web search (mock for demo)."""
    print("Executing: searchCompanyInfo")

    content = request_body.get('content', {})

    company_name = params.get('company_name') or content.get('company_name', '')
    search_query = params.get('query') or content.get('query', '')

    print(f"Searching for company: {company_name}, query: {search_query}")

    # Mock web search results (in production, would call SerpAPI, Tavily, etc.)
    # For demo, return realistic mock data

    mock_results = {
        'DataTech Solutions': {
            'company_status': 'Active',
            'recent_news': [
                {
                    'title': 'DataTech Solutions Secures $15M Series A Funding',
                    'date': '2025-09-15',
                    'source': 'TechCrunch',
                    'summary': 'DataTech Solutions announced $15M Series A to expand their data analytics platform',
                    'url': 'https://techcrunch.com/...',
                    'sentiment': 'positive'
                },
                {
                    'title': 'DataTech Solutions Growing Rapidly in Enterprise Market',
                    'date': '2025-08-20',
                    'source': 'VentureBeat',
                    'summary': 'Company reports 200% YoY growth, expanding team and infrastructure',
                    'url': 'https://venturebeat.com/...',
                    'sentiment': 'positive'
                }
            ],
            'company_info': {
                'industry': 'Data Analytics',
                'size': '50-100 employees',
                'founded': '2021',
                'headquarters': 'San Francisco, CA',
                'funding_stage': 'Series A',
                'growth_trajectory': 'rapid_growth'
            }
        },
        'MarketPro Analytics': {
            'company_status': 'Active',
            'recent_news': [
                {
                    'title': 'MarketPro Analytics Pivots to New Market Segment',
                    'date': '2025-09-01',
                    'source': 'Business Insider',
                    'summary': 'Startup shifts focus from B2B to B2C analytics',
                    'url': 'https://businessinsider.com/...',
                    'sentiment': 'neutral'
                }
            ],
            'company_info': {
                'industry': 'Market Research',
                'size': '10-20 employees',
                'founded': '2023',
                'headquarters': 'Austin, TX',
                'funding_stage': 'Bootstrapped',
                'growth_trajectory': 'early_stage'
            }
        },
        'SecureData Corp': {
            'company_status': 'Active',
            'recent_news': [
                {
                    'title': 'SecureData Corp Passes Annual SOC 2 Audit',
                    'date': '2025-09-10',
                    'source': 'SecurityWeek',
                    'summary': 'Company achieves SOC 2 Type II certification, strengthening security posture',
                    'url': 'https://securityweek.com/...',
                    'sentiment': 'positive'
                },
                {
                    'title': 'SecureData Corp Expands Compliance Team',
                    'date': '2025-08-25',
                    'source': 'InfoSecurity Magazine',
                    'summary': 'Hiring 5 new compliance officers to meet growing regulatory demands',
                    'url': 'https://infosecurity-magazine.com/...',
                    'sentiment': 'positive'
                }
            ],
            'company_info': {
                'industry': 'Cybersecurity',
                'size': '100-200 employees',
                'founded': '2019',
                'headquarters': 'Boston, MA',
                'funding_stage': 'Series B',
                'growth_trajectory': 'steady_growth'
            }
        }
    }

    # Return mock results for known companies, or generic result
    company_data = mock_results.get(company_name, {
        'company_status': 'Active',
        'recent_news': [],
        'company_info': {
            'industry': 'Unknown',
            'size': 'Unknown',
            'note': 'Limited public information available'
        }
    })

    result = {
        'company_name': company_name,
        'search_query': search_query or f'{company_name} recent news',
        'status': company_data['company_status'],
        'recent_news': company_data.get('recent_news', [])[:2],  # Top 2 news items
        'company_info': company_data.get('company_info', {}),
        'data_source': 'Web Search (Demo)',
        'search_timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    print(f"Search complete: Found {len(company_data.get('recent_news', []))} news items")
    return result
