"""S3 helper functions."""
import json
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


class S3Helper:
    """Helper class for S3 operations."""

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get JSON object from S3.

        Returns:
            Parsed JSON object or None if not found
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def put_json(self, key: str, data: Dict[str, Any]) -> None:
        """Put JSON object to S3."""
        content = json.dumps(data, indent=2)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType='application/json'
        )

    def get_text(self, key: str) -> Optional[str]:
        """Get text file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise

    def put_text(self, key: str, content: str) -> None:
        """Put text file to S3."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType='text/plain'
        )

    def exists(self, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def list_objects(self, prefix: str) -> list[str]:
        """List object keys with given prefix."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            if 'Contents' not in response:
                return []
            return [obj['Key'] for obj in response['Contents']]
        except ClientError:
            return []

    def update_status(self, upload_id: str, updates: Dict[str, Any]) -> None:
        """
        Atomically update status.json with new fields.

        Args:
            upload_id: Upload ID
            updates: Dictionary of fields to update
        """
        from datetime import datetime

        status_key = f"results/{upload_id}/status.json"

        # Get current status
        current = self.get_json(status_key)
        if not current:
            raise ValueError(f"Status file not found: {status_key}")

        # Update fields
        current.update(updates)
        current['updated_at'] = datetime.utcnow().isoformat() + 'Z'

        # Write back
        self.put_json(status_key, current)
