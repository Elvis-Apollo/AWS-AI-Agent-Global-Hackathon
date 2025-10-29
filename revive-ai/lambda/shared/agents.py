"""AI Agent implementations for churn analysis and campaign generation."""
from typing import Dict, Any
from .bedrock_client import BedrockClient
from .schemas import validate_analysis, validate_campaign


class ChurnAnalysisAgent:
    """Agent 1: Analyze why customer churned."""

    def __init__(self, bedrock_client: BedrockClient):
        self.bedrock = bedrock_client

    def analyze(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze customer churn and categorize reason.

        Args:
            customer: Customer data dict

        Returns:
            Analysis dict with category, confidence, insights, recommendation
        """
        system_prompt = "You are a SaaS customer success analyst expert at understanding churn patterns."

        cancellation_reason = customer.get('cancellation_reason', 'Not provided')

        user_prompt = f"""Analyze why this customer churned.

Customer: {customer.get('company_name', 'Unknown')}
Subscription: {customer.get('subscription_tier', 'Unknown')} (${customer.get('mrr', '0')}/month)
Churn Date: {customer.get('churn_date', 'Unknown')}
Reason Given: {cancellation_reason}

Categorize into ONE of: pricing, features, onboarding, competition, business_closure, unclear

Provide:
- Confidence score (0-100)
- 3-5 specific insights
- Tactical recommendation

Respond ONLY with valid JSON:
{{
  "category": "...",
  "confidence": 85,
  "insights": ["...", "...", "..."],
  "recommendation": "..."
}}"""

        response = self.bedrock.invoke_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1024
        )

        analysis = response['data']

        # Add customer_id to result
        analysis['customer_id'] = customer['customer_id']

        # Validate
        is_valid, error = validate_analysis(analysis)
        if not is_valid:
            raise ValueError(f"Invalid analysis output: {error}")

        return analysis


class CampaignGenerationAgent:
    """Agent 2: Generate personalized win-back email campaigns using AI intelligence."""

    def __init__(self, bedrock_client: BedrockClient):
        self.bedrock = bedrock_client

    def generate(self, customer: Dict[str, Any], analysis: Dict[str, Any], company_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate 3-email win-back campaign based on comprehensive churn intelligence.

        Args:
            customer: Customer data dict
            analysis: Churn analysis dict with full_text from ChurnAnalyzer
            company_info: Optional dict with SaaS company context (name, product_name, value_proposition)

        Returns:
            Campaign dict with emails array
        """
        # Default company info if not provided
        if company_info is None:
            company_info = {
                'name': 'our platform',
                'product_name': 'our product',
                'value_proposition': 'powerful analytics and insights'
            }
        system_prompt = """You are an expert SaaS win-back campaign strategist and email copywriter.

Your expertise includes:
- Understanding complex churn reasons and root causes
- Crafting highly personalized, empathetic messaging
- Choosing the right offers and solutions based on customer context
- Balancing professional tone with authentic warmth
- Creating compelling CTAs that drive action

You have access to comprehensive churn intelligence from multiple data sources. Use this intelligence to create the most effective win-back campaign possible."""

        # Get full analysis text (contains all intelligence from ChurnAnalyzer's 5 tools)
        full_analysis = analysis.get('full_text', '')

        # Fallback to structured fields if full_text not available
        if not full_analysis:
            insights_text = '\n'.join(f"- {insight}" for insight in analysis.get('insights', []))
            full_analysis = f"""Category: {analysis.get('category', 'unclear')}
Confidence: {analysis.get('confidence', 0)}%
Insights:
{insights_text}
Recommendation: {analysis.get('recommendation', '')}"""

        user_prompt = f"""Create a highly personalized 3-email win-back sequence for this churned customer.

YOUR COMPANY CONTEXT (write from this perspective):
- Company Name: {company_info.get('name', 'our platform')}
- Product: {company_info.get('product_name', 'our product')}
- Value Proposition: {company_info.get('value_proposition', 'powerful analytics and insights')}

CUSTOMER CONTEXT:
- Company: {customer.get('company_name', 'Unknown')}
- Previous Plan: {customer.get('subscription_tier', 'Unknown')} (${customer.get('mrr', '0')}/month)
- Churn Date: {customer.get('churn_date', 'Unknown')}
- Stated Reason: {customer.get('cancellation_reason', 'Not provided')}

COMPREHENSIVE CHURN INTELLIGENCE:
{full_analysis}

TASK:
Based on this intelligence, create the most effective 3-email win-back campaign. Use your expertise to:

1. Identify the ROOT CAUSE of churn (look beyond surface-level reasons)
2. Choose the right tone, messaging, and offers for THIS specific customer
3. Address their actual needs (e.g., if low adoption → offer training/onboarding, NOT discounts)
4. Personalize with company name and specific context
5. Create compelling, authentic emails that maximize win-back probability

EMAIL SEQUENCE STRATEGY:
- Email 1 (Day 7): Gentle re-engagement, acknowledge their decision, show understanding
- Email 2 (Day 14): Address the ROOT CAUSE with concrete solutions
- Email 3 (Day 30): Compelling final offer or call to action

QUALITY REQUIREMENTS:
- Subject: <50 characters, compelling, personalized to customer's company name
- Body: 150-300 words, professional but warm, specific to their situation
- CTA: Clear action, 3-7 words, relevant to their needs
- Write naturally from YOUR company's perspective using the company context provided above
- Reference your company name, product, and value proposition naturally when appropriate
- NEVER use placeholders like [Company Name], [Product], [Feature], etc. - use actual values provided
- Avoid: Generic templates, desperate tone, inappropriate offers, any placeholders or brackets

Respond ONLY with valid JSON:
{{
  "summary": "One sentence capturing the win-back strategy (e.g., 'Address HIPAA compliance gap with new certification + 25% discount')",
  "emails": [
    {{"number": 1, "subject": "...", "body": "...", "cta": "..."}},
    {{"number": 2, "subject": "...", "body": "...", "cta": "..."}},
    {{"number": 3, "subject": "...", "body": "...", "cta": "..."}}
  ]
}}"""

        response = self.bedrock.invoke_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=2048
        )

        campaign = response['data']

        # Add customer_id to result
        campaign['customer_id'] = customer['customer_id']

        # Validate
        is_valid, error = validate_campaign(campaign)
        if not is_valid:
            raise ValueError(f"Invalid campaign output: {error}")

        return campaign
