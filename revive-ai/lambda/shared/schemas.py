"""Data schemas and validation for Revive AI."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

VALID_TIERS = ['starter', 'growth', 'enterprise']
VALID_CATEGORIES = ['pricing', 'features', 'onboarding', 'competition', 'business_closure', 'unclear']


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_customer(customer: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate customer data.

    Returns:
        (is_valid, error_message)
    """
    required_fields = ['customer_id', 'email', 'company_name', 'subscription_tier', 'mrr', 'churn_date']

    for field in required_fields:
        if field not in customer or not customer[field]:
            return False, f"Missing required field: {field}"

    # Email validation
    if not validate_email(customer['email']):
        return False, f"Invalid email format: {customer['email']}"

    # Tier validation
    if customer['subscription_tier'] not in VALID_TIERS:
        return False, f"Invalid subscription_tier: {customer['subscription_tier']}. Must be one of {VALID_TIERS}"

    # MRR validation
    try:
        mrr = float(customer['mrr'])
        if mrr <= 0:
            return False, f"MRR must be positive, got: {mrr}"
    except (ValueError, TypeError):
        return False, f"Invalid MRR value: {customer['mrr']}"

    # Date validation
    try:
        datetime.fromisoformat(customer['churn_date'])
    except (ValueError, TypeError):
        return False, f"Invalid churn_date format: {customer['churn_date']}. Must be ISO 8601 format"

    return True, None


def validate_analysis(analysis: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate churn analysis output.

    Returns:
        (is_valid, error_message)
    """
    required_fields = ['category', 'confidence', 'insights', 'recommendation']

    for field in required_fields:
        if field not in analysis:
            return False, f"Missing required field: {field}"

    # Category validation with auto-correction
    category = analysis['category'].lower()

    # Map common variations to valid categories
    category_mapping = {
        'security': 'features',
        'compliance': 'features',
        'integration': 'features',
        'support': 'onboarding',
        'budget': 'pricing',
        'cost': 'pricing'
    }

    if category in category_mapping:
        analysis['category'] = category_mapping[category]
    elif category not in VALID_CATEGORIES:
        # Default to 'unclear' if we can't map it
        analysis['category'] = 'unclear'

    # Confidence validation
    try:
        conf = int(analysis['confidence'])
        if not 0 <= conf <= 100:
            return False, f"Confidence must be 0-100, got: {conf}"
    except (ValueError, TypeError):
        return False, f"Invalid confidence value: {analysis['confidence']}"

    # Insights validation
    if not isinstance(analysis['insights'], list):
        return False, "Insights must be an array"

    if len(analysis['insights']) < 3 or len(analysis['insights']) > 5:
        return False, f"Insights must have 3-5 items, got: {len(analysis['insights'])}"

    return True, None


def validate_campaign(campaign: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate campaign output.

    Returns:
        (is_valid, error_message)
    """
    # Validate summary (optional but recommended)
    if 'summary' in campaign:
        summary = campaign['summary']
        if not isinstance(summary, str) or len(summary) < 10:
            return False, "Summary must be at least 10 characters"
        if len(summary) > 300:
            return False, f"Summary too long ({len(summary)} chars, max 300)"

    if 'emails' not in campaign:
        return False, "Missing 'emails' field"

    emails = campaign['emails']

    if not isinstance(emails, list):
        return False, "'emails' must be an array"

    if len(emails) != 3:
        return False, f"Must have exactly 3 emails, got: {len(emails)}"

    for i, email in enumerate(emails, 1):
        # Check required fields
        required = ['number', 'subject', 'body', 'cta']
        for field in required:
            if field not in email:
                return False, f"Email {i} missing field: {field}"

        # Validate number (should match position in array)
        if email['number'] != i:
            return False, f"Email {i} has incorrect number: {email['number']}"

        # Validate subject length (relaxed)
        if len(email['subject']) > 60:
            return False, f"Email {i} subject too long ({len(email['subject'])} chars, max 60)"

        # Validate body exists and has content (no strict word count - let LLM decide)
        word_count = len(email['body'].split())
        if word_count < 20:
            return False, f"Email {i} body too short ({word_count} words, min 20)"
        if word_count > 1000:
            return False, f"Email {i} body too long ({word_count} words, max 1000)"

        # Validate CTA exists and is reasonable
        if not email['cta'] or len(email['cta']) > 50:
            return False, f"Email {i} CTA invalid"

    return True, None


def create_status_stub(upload_id: str, total: int, execution_arn: str = "") -> Dict[str, Any]:
    """Create initial status JSON."""
    return {
        "upload_id": upload_id,
        "status": "processing",
        "total": total,
        "completed": 0,
        "failed": 0,
        "execution_arn": execution_arn,
        "started_at": datetime.utcnow().isoformat() + 'Z',
        "updated_at": datetime.utcnow().isoformat() + 'Z',
        "estimated_remaining_seconds": 0,
        "errors": []
    }
