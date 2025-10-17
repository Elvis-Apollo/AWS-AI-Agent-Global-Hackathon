"""
API Handler Lambda
Handles all API Gateway routes and Step Functions orchestration tasks.
"""
import json
import os
import sys
import csv
import io
import base64
from datetime import datetime
from typing import Dict, Any

# Add shared module to path
sys.path.insert(0, '/opt/python')

from shared.s3_helper import S3Helper
from shared.schemas import create_status_stub, validate_customer

import boto3

# Environment variables
DATA_BUCKET = os.environ.get('DATA_BUCKET', 'revive-ai-data')
FRONTEND_BUCKET = os.environ.get('FRONTEND_BUCKET', 'revive-ai-frontend')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-sonnet-4-5-20250929-v1:0')


def lambda_handler(event, context):
    """
    Main handler for API Gateway and Step Functions tasks.

    Routes:
    - POST /upload - Upload CSV
    - POST /process - Start processing
    - GET /results - Get results
    - POST /demo - Load demo data
    - prepare_job - Step Functions PrepareJob task
    - finalize_job - Step Functions FinalizeJob task
    """
    print(f"Event: {json.dumps(event)}")

    # Check if this is a Step Functions task (direct invocation)
    if 'task' in event:
        task = event['task']
        if task == 'prepare_job':
            return prepare_job_handler(event)
        elif task == 'finalize_job':
            return finalize_job_handler(event)

    # API Gateway request
    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', ''))
    path = event.get('path', event.get('rawPath', ''))

    try:
        if path == '/upload' and http_method == 'POST':
            return handle_upload(event)
        elif path == '/process' and http_method == 'POST':
            return handle_process(event)
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
    # Parse multipart form data (simplified)
    # In production, use a proper multipart parser
    body = event.get('body', '')
    is_base64 = event.get('isBase64Encoded', False)

    if is_base64:
        body = base64.b64decode(body).decode('utf-8')

    # For now, assume CSV is in the body directly
    # In real deployment, handle proper multipart parsing
    csv_content = body

    # Generate upload_id
    upload_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    # Parse and validate CSV
    try:
        customers = []
        reader = csv.DictReader(io.StringIO(csv_content))

        for row in reader:
            # Validate each customer
            is_valid, error = validate_customer(row)
            if not is_valid:
                return response(400, {
                    'error': 'Invalid CSV format',
                    'details': error
                })
            customers.append(row)

        if len(customers) == 0:
            return response(400, {
                'error': 'CSV file is empty'
            })

        # Save to S3
        s3 = S3Helper(DATA_BUCKET)
        s3.put_text(f"uploads/{upload_id}.csv", csv_content)

        # Also save parsed customers as JSON for Step Functions
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


def handle_process(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start Step Functions execution for uploaded file.
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

    # Start Step Functions execution
    sfn_client = boto3.client('stepfunctions')

    execution_input = {
        'upload_id': upload_id,
        'customers': customers,
        'total': len(customers)
    }

    try:
        execution_response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=upload_id,
            input=json.dumps(execution_input)
        )

        execution_arn = execution_response['executionArn']

        return response(202, {
            'upload_id': upload_id,
            'status': 'processing',
            'execution_arn': execution_arn,
            'message': f'Step Function started for {len(customers)} customers'
        })

    except Exception as e:
        return response(500, {
            'error': f'Failed to start processing: {str(e)}'
        })


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
        # Status file doesn't exist yet - Step Functions hasn't started
        # Return a pending status instead of 404
        return response(200, {
            'status': 'processing',
            'completed': 0,
            'total': 0,
            'progress': 0,
            'failures': 0,
            'execution_arn': '',
            'estimated_remaining_seconds': 0
        })

    # If still processing, return progress
    if status['status'] == 'processing':
        return response(200, {
            'status': 'processing',
            'completed': status.get('completed', 0),
            'total': status.get('total', 0),
            'progress': int((status.get('completed', 0) / max(status.get('total', 1), 1)) * 100),
            'failures': status.get('failed', 0),
            'execution_arn': status.get('execution_arn', ''),
            'estimated_remaining_seconds': status.get('estimated_remaining_seconds', 0)
        })

    # If complete, return full results
    campaigns = []

    # Read aggregated results
    customers_data = s3.get_json(f"results/{upload_id}/customers.json")
    if customers_data:
        campaigns = customers_data
    else:
        # Fallback: read individual customer files
        customer_keys = s3.list_objects(f"results/{upload_id}/customers/")
        for key in customer_keys:
            if key.endswith('.json'):
                customer_result = s3.get_json(key)
                if customer_result:
                    campaigns.append(customer_result)

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


def prepare_job_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    PrepareJob Step Functions task.

    Initializes status.json for the processing job.
    """
    upload_id = event['upload_id']
    total = event['total']
    execution_arn = event.get('execution_arn', '')

    s3 = S3Helper(DATA_BUCKET)

    # Create status stub
    status = create_status_stub(upload_id, total, execution_arn)

    # Save to S3
    s3.put_json(f"results/{upload_id}/status.json", status)

    print(f"Prepared job for upload {upload_id}: {total} customers")

    return {
        'upload_id': upload_id,
        'status': 'prepared'
    }


def finalize_job_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    FinalizeJob Step Functions task.

    Aggregates all customer results and marks job as complete.
    """
    upload_id = event['upload_id']

    s3 = S3Helper(DATA_BUCKET)

    # List all customer result files
    customer_keys = s3.list_objects(f"results/{upload_id}/customers/")

    all_customers = []
    all_analyses = []
    all_campaigns = []

    for key in customer_keys:
        if key.endswith('.json'):
            customer_result = s3.get_json(key)
            if customer_result and customer_result.get('status') == 'success':
                all_customers.append(customer_result)

                # Extract analysis
                analysis = customer_result.get('analysis', {})
                if analysis:
                    all_analyses.append(analysis)

                # Extract campaign
                campaign = customer_result.get('campaign', {})
                if campaign:
                    all_campaigns.append(campaign)

    # Save aggregated results
    s3.put_json(f"results/{upload_id}/customers.json", all_customers)
    s3.put_json(f"results/{upload_id}/analyses.json", all_analyses)
    s3.put_json(f"results/{upload_id}/campaigns.json", all_campaigns)

    # Update status to complete
    status = s3.get_json(f"results/{upload_id}/status.json")
    if status:
        status['status'] = 'complete'
        status['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        status['estimated_remaining_seconds'] = 0
        s3.put_json(f"results/{upload_id}/status.json", status)

    print(f"Finalized job for upload {upload_id}: {len(all_customers)} successful")

    return {
        'upload_id': upload_id,
        'status': 'complete',
        'successful': len(all_customers)
    }
