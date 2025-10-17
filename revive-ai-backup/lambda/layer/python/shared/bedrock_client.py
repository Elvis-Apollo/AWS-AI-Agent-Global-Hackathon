"""Shared Bedrock client for all Lambda functions."""
import json
import boto3
import re
from typing import Dict, Any, Optional

class BedrockClient:
    """Wrapper for AWS Bedrock API calls."""

    def __init__(self, model_id: str = "anthropic.claude-sonnet-4-5-20250929-v1:0", region: str = "us-east-1"):
        self.model_id = model_id
        self.client = boto3.client('bedrock-runtime', region_name=region)

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock with Claude model with exponential backoff retry.

        Args:
            system_prompt: System context for the AI
            user_prompt: User message
            temperature: 0.0-1.0, lower is more deterministic
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts on throttling

        Returns:
            Parsed JSON response from Claude
        """
        import time
        import random

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        })

        for attempt in range(max_retries):
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=body
                )

                response_body = json.loads(response['body'].read())

                # Extract text from Claude response
                if 'content' in response_body and len(response_body['content']) > 0:
                    return {
                        'text': response_body['content'][0]['text'],
                        'usage': response_body.get('usage', {})
                    }

                raise ValueError("Invalid response from Bedrock")

            except Exception as e:
                error_message = str(e)

                # Check if it's a throttling error
                if 'ThrottlingException' in error_message or 'throttlingException' in error_message or 'Too many requests' in error_message:
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2^attempt + random jitter
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"[BedrockClient Retry] Throttled on InvokeModel, waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue  # Retry
                    else:
                        print(f"[BedrockClient Retry] Max retries reached on InvokeModel")
                        raise
                else:
                    # Not a throttling error, raise immediately
                    raise

        # Should never reach here
        raise Exception("Unexpected retry loop exit in BedrockClient.invoke")

    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock and parse JSON response.

        Returns:
            Parsed JSON object from Claude's response
        """
        response = self.invoke(system_prompt, user_prompt, temperature, max_tokens)
        text = response['text'].strip()

        # Try to extract JSON from response
        # Sometimes Claude wraps JSON in markdown code blocks
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            text = text[start:end].strip()
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            text = text[start:end].strip()

        # Find JSON object/array boundaries
        json_start = -1
        for char in ['{', '[']:
            idx = text.find(char)
            if idx != -1 and (json_start == -1 or idx < json_start):
                json_start = idx

        if json_start != -1:
            text = text[json_start:]

        # Try parsing as-is first
        try:
            parsed = json.loads(text)
            return {
                'data': parsed,
                'usage': response.get('usage', {})
            }
        except json.JSONDecodeError:
            # If that fails, try to fix common issues
            # Fix unescaped newlines in string values by using json.dumps to re-escape
            # This is a heuristic approach: find string values and escape them
            try:
                # Use a more lenient JSON parser that can handle some malformed JSON
                import ast
                # Try to fix by escaping actual newlines within quoted strings
                fixed_text = []
                in_string = False
                escape_next = False

                for i, char in enumerate(text):
                    if escape_next:
                        fixed_text.append(char)
                        escape_next = False
                        continue

                    if char == '\\':
                        escape_next = True
                        fixed_text.append(char)
                        continue

                    if char == '"' and not escape_next:
                        in_string = not in_string
                        fixed_text.append(char)
                        continue

                    if in_string and char in '\n\r':
                        # Escape actual newlines inside strings
                        fixed_text.append('\\n' if char == '\n' else '\\r')
                    else:
                        fixed_text.append(char)

                text = ''.join(fixed_text)
                parsed = json.loads(text)
                return {
                    'data': parsed,
                    'usage': response.get('usage', {})
                }
            except Exception as e:
                raise ValueError(f"Failed to parse JSON from Claude response: {e}\nResponse: {text[:500]}")
