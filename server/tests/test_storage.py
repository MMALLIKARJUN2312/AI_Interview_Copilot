import asyncio

from app.services.storage.local import LocalStorageBackend

def test_local_storage_round_trip(tmp_path):
    backend = LocalStorageBackend(base_dir=str(tmp_path))

    asyncio.run(backend.save("some-key.pdf", b"hello world"))

    assert asyncio.run(backend.read("some-key.pdf")) == b"hello world"

def test_local_storage_creates_base_dir(tmp_path):
    target = tmp_path / "nested" / "resumes"

    LocalStorageBackend(base_dir=str(target))

    assert target.exists()
