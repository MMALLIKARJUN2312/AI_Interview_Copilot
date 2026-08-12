from abc import ABC, abstractmethod

class StorageBackend(ABC):
    """Abstract file storage backend. `key` is a backend-agnostic identifier
    (never a filesystem path or URL), so callers stay portable across backends.
    """

    @abstractmethod
    async def save(self, key : str, contents : bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    async def read(self, key : str) -> bytes:
        raise NotImplementedError
