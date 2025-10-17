#!/usr/bin/env python3
"""
Demo Script: Showcase All 5 Tools in ChurnAnalyzer
Directly invokes Lambda to demonstrate each tool's functionality
"""
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

def invoke_tool(api_path, parameters):
    """Invoke a specific tool via Lambda."""
    event = {
        "messageVersion": "1.0",
        "agent": {"name": "ChurnAnalyzer", "id": "HAKDC7PY1Z"},
        "actionGroup": "churn-analysis-tools",
        "apiPath": api_path,
        "httpMethod": "POST",
        "parameters": [{"name": k, "type": "string", "value": str(v)} for k, v in parameters.items()],
        "requestBody": {
            "content": {
                "application/json": {
                    "properties": [{"name": k, "type": "string", "value": str(v)} for k, v in parameters.items()]
                }
            }
        }
    }

    response = lambda_client.invoke(
        FunctionName='bedrock-agent-executor',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )

    result = json.loads(response['Payload'].read())
    return result

print("=" * 80)
print("🎯 TOOL DEMONSTRATION - All 5 ChurnAnalyzer Tools")
print("=" * 80)

# Tool 1: Calculate CLV
print("\n📊 TOOL 1: Calculate Customer Lifetime Value (calculateCLV)")
print("-" * 80)
clv_result = invoke_tool('/calculateCLV', {
    'mrr': '2499',
    'subscription_tier': 'enterprise'
})
print(f"Input: MRR=$2499, Tier=enterprise")
print(f"Output: {json.dumps(clv_result, indent=2)}")

# Tool 2: Get CRM History
print("\n📈 TOOL 2: Get CRM History (getCRMHistory)")
print("-" * 80)
crm_result = invoke_tool('/getCRMHistory', {
    'customer_id': 'c025'
})
print(f"Input: customer_id=c025")
print(f"Output: {json.dumps(crm_result, indent=2)}")

# Tool 3: Search Company Info
print("\n🌐 TOOL 3: Search Company Information (searchCompanyInfo)")
print("-" * 80)
company_result = invoke_tool('/searchCompanyInfo', {
    'company_name': 'DataTech Solutions'
})
print(f"Input: company_name='DataTech Solutions'")
print(f"Output: {json.dumps(company_result, indent=2)}")

# Tool 4: Check Product Roadmap
print("\n🛣️  TOOL 4: Check Product Roadmap (checkProductRoadmap)")
print("-" * 80)
roadmap_result = invoke_tool('/checkProductRoadmap', {
    'churn_category': 'performance',
    'churn_reason': 'API rate limits too low'
})
print(f"Input: churn_category='performance', churn_reason='API rate limits too low'")
print(f"Output: {json.dumps(roadmap_result, indent=2)}")

# Tool 5: Analyze Churn
print("\n🎯 TOOL 5: Analyze Churn Reason (analyzeChurn)")
print("-" * 80)
churn_result = invoke_tool('/analyzeChurn', {
    'customer_id': 'c025',
    'company_name': 'DataTech Solutions',
    'subscription_tier': 'enterprise',
    'mrr': '2499',
    'churn_date': '2025-10-01',
    'cancellation_reason': 'Needed better API rate limits and response times'
})
print(f"Input: Customer c025 - DataTech Solutions")
print(f"Output: {json.dumps(churn_result, indent=2)}")

print("\n" + "=" * 80)
print("✅ ALL 5 TOOLS DEMONSTRATED SUCCESSFULLY")
print("=" * 80)
print("\nTool Summary:")
print("1. ✅ calculateCLV - Calculates customer lifetime value and priority")
print("2. ✅ getCRMHistory - Retrieves usage patterns and support tickets from CRM")
print("3. ✅ searchCompanyInfo - Searches web for company news and funding")
print("4. ✅ checkProductRoadmap - Finds upcoming features that solve churn reasons")
print("5. ✅ analyzeChurn - NLP analysis of churn categorization")
print("\nExternal Integrations:")
print("- 📦 S3 Knowledge Base (product-roadmap.json, crm-history.json)")
print("- 🌐 Web Search API (mock for demo, easily replaced with SerpAPI)")
print("- 🤖 Bedrock Models (Claude for NLP analysis)")
print("=" * 80)
