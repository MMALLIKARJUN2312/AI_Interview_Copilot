from app.core.config import settings
from app.services.storage.base import StorageBackend
from app.services.storage.local import LocalStorageBackend

def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        from app.services.storage.s3 import S3StorageBackend

        if not settings.S3_BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME must be set when STORAGE_BACKEND=s3")

        return S3StorageBackend(bucket_name=settings.S3_BUCKET_NAME, region=settings.AWS_REGION)

    return LocalStorageBackend(base_dir=settings.LOCAL_STORAGE_DIR)

__all__ = ["StorageBackend", "get_storage_backend"]
