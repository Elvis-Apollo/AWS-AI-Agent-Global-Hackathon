"""
Customer Worker Lambda
Processes a single customer through both AI agents and stores results.
"""
import json
import os
import sys
from datetime import datetime
import traceback
import time

# Add shared module to path
sys.path.insert(0, '/opt/python')

from shared.bedrock_client import BedrockClient
from shared.agents import ChurnAnalysisAgent, CampaignGenerationAgent
from shared.s3_helper import S3Helper
from shared.schemas import validate_customer


# Environment variables
DATA_BUCKET = os.environ.get('DATA_BUCKET', 'revive-ai-data')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-sonnet-4-5-20250929-v1:0')


def lambda_handler(event, context):
    """
    Process a single customer through analysis and campaign generation.

    Event payload from Step Functions Map state:
    {
        "upload_id": "20251008_143022",
        "customer": {
            "customer_id": "c001",
            "email": "cto@acme.com",
            "company_name": "Acme Corp",
            "subscription_tier": "growth",
            "mrr": "799",
            "churn_date": "2025-09-15",
            "cancellation_reason": "Too expensive"
        }
    }

    Returns:
    {
        "customer_id": "c001",
        "status": "success",
        "analysis": {...},
        "campaign": {...}
    }
    """
    print(f"Processing customer worker with event: {json.dumps(event)}")

    upload_id = event.get('upload_id')
    customer = event.get('customer')

    if not upload_id or not customer:
        raise ValueError("Missing upload_id or customer in event")

    customer_id = customer.get('customer_id')

    try:
        # Validate customer data
        is_valid, error = validate_customer(customer)
        if not is_valid:
            raise ValueError(f"Invalid customer data: {error}")

        # Initialize clients
        bedrock = BedrockClient(model_id=BEDROCK_MODEL_ID)
        s3 = S3Helper(bucket_name=DATA_BUCKET)

        # Initialize agents
        analysis_agent = ChurnAnalysisAgent(bedrock)
        campaign_agent = CampaignGenerationAgent(bedrock)

        print(f"Running analysis for customer {customer_id}...")
        # Step 1: Analyze churn
        analysis = analysis_agent.analyze(customer)
        print(f"Analysis complete: category={analysis['category']}, confidence={analysis['confidence']}")

        # Add small delay between API calls to avoid throttling
        print("Waiting 1 second before generating campaign...")
        time.sleep(1)

        print(f"Generating campaign for customer {customer_id}...")
        # Step 2: Generate campaign
        campaign = campaign_agent.generate(customer, analysis)
        print(f"Campaign complete: {len(campaign['emails'])} emails generated")

        # Step 3: Build result payload
        result = {
            "customer_id": customer_id,
            "status": "success",
            "company_name": customer['company_name'],
            "email": customer['email'],
            "subscription_tier": customer['subscription_tier'],
            "mrr": customer['mrr'],
            "churn_date": customer['churn_date'],
            "cancellation_reason": customer.get('cancellation_reason', ''),
            "analysis": analysis,
            "campaign": campaign,
            "processed_at": datetime.utcnow().isoformat() + 'Z'
        }

        # Step 4: Save customer result to S3
        customer_key = f"results/{upload_id}/customers/{customer_id}.json"
        s3.put_json(customer_key, result)
        print(f"Saved customer result to {customer_key}")

        # Step 5: Update status.json (increment completed counter)
        try:
            status = s3.get_json(f"results/{upload_id}/status.json")
            if status:
                status['completed'] = status.get('completed', 0) + 1
                status['updated_at'] = datetime.utcnow().isoformat() + 'Z'

                # Calculate estimated remaining time
                total = status.get('total', 0)
                completed = status['completed']
                if completed > 0 and total > completed:
                    started_at = datetime.fromisoformat(status['started_at'].replace('Z', ''))
                    elapsed = (datetime.utcnow() - started_at).total_seconds()
                    avg_time_per_customer = elapsed / completed
                    remaining = total - completed
                    status['estimated_remaining_seconds'] = int(avg_time_per_customer * remaining)
                else:
                    status['estimated_remaining_seconds'] = 0

                s3.put_json(f"results/{upload_id}/status.json", status)
                print(f"Updated status: {completed}/{total} completed")
        except Exception as status_error:
            print(f"Warning: Failed to update status: {status_error}")
            # Don't fail the whole function if status update fails

        return result

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error processing customer {customer_id}: {error_msg}")
        print(f"Traceback: {error_trace}")

        # Update status with error
        try:
            s3 = S3Helper(bucket_name=DATA_BUCKET)
            status = s3.get_json(f"results/{upload_id}/status.json")
            if status:
                status['failed'] = status.get('failed', 0) + 1
                status['errors'] = status.get('errors', [])
                status['errors'].append({
                    "customer_id": customer_id,
                    "message": error_msg,
                    "timestamp": datetime.utcnow().isoformat() + 'Z'
                })
                status['updated_at'] = datetime.utcnow().isoformat() + 'Z'
                s3.put_json(f"results/{upload_id}/status.json", status)
        except Exception as status_error:
            print(f"Failed to update error in status: {status_error}")

        # Re-raise so Step Functions can catch and retry
        raise
