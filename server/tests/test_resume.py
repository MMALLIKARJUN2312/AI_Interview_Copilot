import io
from sqlalchemy.orm import Session
from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis

def _pdf_upload(target_role="Backend Engineer"):
    files = {"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    data = {"target_role": target_role}
    return files, data

class FakeStorage:
    def __init__(
        self,
        fail_delete: bool = False,
    ):
        self.saved_keys: list[str] = []
        self.deleted_keys: list[str] = []
        self.fail_delete = fail_delete

    async def save(
        self,
        key: str,
        contents: bytes,
    ) -> None:
        self.saved_keys.append(key)

    async def read(
        self,
        key: str,
    ) -> bytes:
        return b"%PDF-1.4 fake"

    async def delete(
        self,
        key: str,
    ) -> None:
        if self.fail_delete:
            raise RuntimeError(
                "Storage unavailable"
            )

        self.deleted_keys.append(key)

def test_upload_requires_auth(client, fake_ai):
    files, data = _pdf_upload()

    response = client.post("/resume/analyze", files=files, data=data)

    assert response.status_code == 401

def test_upload_rejects_non_pdf(client, auth_headers, fake_ai):
    files = {"file": ("resume.txt", io.BytesIO(b"not a pdf"), "text/plain")}
    data = {"target_role": "Backend Engineer"}

    response = client.post("/resume/analyze", headers=auth_headers, files=files, data=data)

    assert response.status_code == 400

def test_upload_rejects_spoofed_content_type(client, auth_headers, fake_ai):
    files = {"file": ("resume.pdf", io.BytesIO(b"not actually a pdf"), "application/pdf")}
    data = {"target_role": "Backend Engineer"}

    response = client.post("/resume/analyze", headers=auth_headers, files=files, data=data)

    assert response.status_code == 400
    assert "valid PDF" in response.json()["detail"]

def test_upload_requires_target_role(client, auth_headers, fake_ai):
    files, _ = _pdf_upload()

    response = client.post("/resume/analyze", headers=auth_headers, files=files, data={})

    assert response.status_code == 422

def test_upload_and_analyze_persists_resume_and_role(client, auth_headers, fake_ai):
    files, data = _pdf_upload(target_role="Backend Engineer")

    response = client.post("/resume/analyze", headers=auth_headers, files=files, data=data)

    assert response.status_code == 200
    body = response.json()
    assert body["target_role"] == "Backend Engineer"
    assert body["ats_score"] == 82
    assert body["resume_id"] == 1
    assert body["analysis_id"] == 1

def test_list_resumes_only_returns_own(client, auth_headers, other_auth_headers, fake_ai):
    files, data = _pdf_upload()
    client.post("/resume/analyze", headers=auth_headers, files=files, data=data)

    own = client.get("/resume/", headers=auth_headers)
    other = client.get("/resume/", headers=other_auth_headers)

    assert len(own.json()) == 1
    assert len(other.json()) == 0

def test_get_resume_not_found_for_other_user(client, uploaded_resume, other_auth_headers):
    resume_id = uploaded_resume["resume_id"]

    response = client.get(f"/resume/{resume_id}", headers=other_auth_headers)

    assert response.status_code == 404

def test_get_own_resume_succeeds(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]

    response = client.get(f"/resume/{resume_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["target_role"] == "Backend Engineer"

def test_get_resume_analysis_returns_latest_analysis(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]

    response = client.get(f"/resume/{resume_id}/analysis", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["resume_id"] == resume_id
    assert body["ats_score"] == 82
    assert body["target_role"] == "Backend Engineer"

def test_get_resume_analysis_not_found_for_other_user(client, uploaded_resume, other_auth_headers):
    resume_id = uploaded_resume["resume_id"]

    response = client.get(f"/resume/{resume_id}/analysis", headers=other_auth_headers)

    assert response.status_code == 404

def test_get_resume_analysis_404_when_no_analysis_exists(client, auth_headers, db_engine):
    from sqlalchemy.orm import sessionmaker

    from app.models.resume import Resume, ResumeStatus

    session_local = sessionmaker(bind=db_engine)
    db = session_local()
    resume = Resume(
        user_id=1,
        original_filename="r.pdf",
        stored_filename="no-analysis.pdf",
        mime_type="application/pdf",
        file_size=10,
        target_role="Backend Engineer",
        status=ResumeStatus.UPLOADED,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    resume_id = resume.id
    db.close()

    response = client.get(f"/resume/{resume_id}/analysis", headers=auth_headers)

    assert response.status_code == 404

def test_delete_resume_requires_authentication(client):
    response = client.delete("/resume/1")

    assert response.status_code == 401


def test_delete_resume_hides_other_users_resume(
    client,
    auth_headers,
    other_auth_headers,
    fake_ai,
    monkeypatch,
):
    storage = FakeStorage()

    monkeypatch.setattr(
        "app.api.v1.resume.get_storage_backend",
        lambda: storage,
    )

    files, data = _pdf_upload()

    upload_response = client.post(
        "/resume/analyze",
        headers=auth_headers,
        files=files,
        data=data,
    )

    resume_id = upload_response.json()[
        "resume_id"
    ]

    response = client.delete(
        f"/resume/{resume_id}",
        headers=other_auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Resume not found"
    )
    assert storage.deleted_keys == []


def test_delete_resume_removes_file_and_database_records(
    client,
    auth_headers,
    fake_ai,
    db_engine,
    monkeypatch,
):
    storage = FakeStorage()

    monkeypatch.setattr(
        "app.api.v1.resume.get_storage_backend",
        lambda: storage,
    )

    files, data = _pdf_upload()

    upload_response = client.post(
        "/resume/analyze",
        headers=auth_headers,
        files=files,
        data=data,
    )

    assert upload_response.status_code == 200

    resume_id = upload_response.json()[
        "resume_id"
    ]

    assert len(storage.saved_keys) == 1

    response = client.delete(
        f"/resume/{resume_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Resume deleted permanently",
    }
    assert storage.deleted_keys == storage.saved_keys

    with Session(db_engine) as db:
        assert (
            db.query(Resume)
            .filter(Resume.id == resume_id)
            .first()
            is None
        )
        assert (
            db.query(ResumeAnalysis)
            .filter(
                ResumeAnalysis.resume_id
                == resume_id
            )
            .count()
            == 0
        )

    get_response = client.get(
        f"/resume/{resume_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 404


def test_delete_resume_rolls_back_when_storage_fails(
    client,
    auth_headers,
    fake_ai,
    monkeypatch,
):
    storage = FakeStorage(
        fail_delete=True,
    )

    monkeypatch.setattr(
        "app.api.v1.resume.get_storage_backend",
        lambda: storage,
    )

    files, data = _pdf_upload()

    upload_response = client.post(
        "/resume/analyze",
        headers=auth_headers,
        files=files,
        data=data,
    )

    resume_id = upload_response.json()[
        "resume_id"
    ]

    response = client.delete(
        f"/resume/{resume_id}",
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Unable to delete resume"
    )

    # The database transaction was rolled back.
    get_response = client.get(
        f"/resume/{resume_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 200
    
def test_list_resumes_supports_pagination(
    client,
    auth_headers,
    fake_ai,
    monkeypatch,
):
    storage = FakeStorage()

    monkeypatch.setattr(
        "app.api.v1.resume.get_storage_backend",
        lambda: storage,
    )

    created_ids = []

    for target_role in [
        "Backend Engineer",
        "Platform Engineer",
        "Staff Engineer",
    ]:
        files, data = _pdf_upload(
            target_role=target_role
        )

        response = client.post(
            "/resume/analyze",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 200
        created_ids.append(
            response.json()["resume_id"]
        )

    first_page = client.get(
        "/resume/?limit=2&offset=0",
        headers=auth_headers,
    )
    second_page = client.get(
        "/resume/?limit=2&offset=2",
        headers=auth_headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    assert [
        resume["id"]
        for resume in first_page.json()
    ] == list(reversed(created_ids))[:2]

    assert [
        resume["id"]
        for resume in second_page.json()
    ] == list(reversed(created_ids))[2:]


def test_list_resumes_rejects_invalid_pagination(
    client,
    auth_headers,
):
    invalid_requests = [
        "/resume/?limit=0",
        "/resume/?limit=51",
        "/resume/?offset=-1",
    ]

    for path in invalid_requests:
        response = client.get(
            path,
            headers=auth_headers,
        )

        assert response.status_code == 422