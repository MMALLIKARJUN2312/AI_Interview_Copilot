import asyncio, pytest

from app.services.storage.local import LocalStorageBackend
from app.models.resume import Resume, ResumeStatus
from app.models.user import User

def test_local_storage_round_trip(tmp_path):
    backend = LocalStorageBackend(base_dir=str(tmp_path))

    asyncio.run(backend.save("some-key.pdf", b"hello world"))

    assert asyncio.run(backend.read("some-key.pdf")) == b"hello world"

def test_local_storage_creates_base_dir(tmp_path):
    target = tmp_path / "nested" / "resumes"

    LocalStorageBackend(base_dir=str(target))

    assert target.exists()

def test_local_storage_delete_removes_file(
    tmp_path,
):
    backend = LocalStorageBackend(
        base_dir=str(tmp_path)
    )

    asyncio.run(
        backend.save(
            "resume.pdf",
            b"resume contents",
        )
    )

    asyncio.run(
        backend.delete("resume.pdf")
    )

    assert not (tmp_path / "resume.pdf").exists()


def test_local_storage_delete_is_idempotent(
    tmp_path,
):
    backend = LocalStorageBackend(
        base_dir=str(tmp_path)
    )

    asyncio.run(
        backend.delete("missing.pdf")
    )


def test_local_storage_delete_rejects_path_traversal(
    tmp_path,
):
    backend = LocalStorageBackend(
        base_dir=str(tmp_path)
    )

    with pytest.raises(
        ValueError,
        match="Invalid storage key",
    ):
        asyncio.run(
            backend.delete("../outside.pdf")
        )