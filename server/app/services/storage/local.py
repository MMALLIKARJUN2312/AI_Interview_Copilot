from pathlib import Path

from app.services.storage.base import StorageBackend

class LocalStorageBackend(StorageBackend):
    """Stores files on the local filesystem. Fine for single-instance/dev use;
    does not survive across instances or ephemeral container filesystems.
    """

    def __init__(self, base_dir : str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, key : str, contents : bytes) -> None:
        (self.base_dir / key).write_bytes(contents)

    async def read(self, key : str) -> bytes:
        return (self.base_dir / key).read_bytes()
