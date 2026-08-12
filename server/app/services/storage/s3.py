import boto3

from app.services.storage.base import StorageBackend

class S3StorageBackend(StorageBackend):
    """Stores files in an S3 bucket. Credentials are resolved via boto3's
    standard credential chain (env vars, IAM role, shared config, etc.) -
    never hardcoded here.
    """

    def __init__(self, bucket_name : str, region : str | None = None) -> None:
        self.bucket_name = bucket_name
        self.client = boto3.client("s3", region_name=region)

    async def save(self, key : str, contents : bytes) -> None:
        self.client.put_object(Bucket=self.bucket_name, Key=key, Body=contents)

    async def read(self, key : str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()
