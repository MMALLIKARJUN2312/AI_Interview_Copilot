import io
from sqlalchemy.orm import Session
from app.models.resume import Resume, ResumeStatus
from app.models.resume_analysis import (AnalysisStatus, ResumeAnalysis)

def _pdf_upload(
    target_role="Backend Engineer",
    filename="resume.pdf",
):
    files = {
        "file": (
            filename,
            io.BytesIO(b"%PDF-1.4 fake"),
            "application/pdf",
        )
    }
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
        
def test_list_resumes_searches_role_and_filename(
    client,
    auth_headers,
    fake_ai,
):
    resume_data = [
        (
            "backend-profile.pdf",
            "Backend Engineer",
        ),
        (
            "platform-profile.pdf",
            "Platform Engineer",
        ),
        (
            "architect-profile.pdf",
            "Solutions Architect",
        ),
    ]

    for filename, target_role in resume_data:
        files, data = _pdf_upload(
            target_role=target_role,
            filename=filename,
        )

        response = client.post(
            "/resume/analyze",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 200

    role_response = client.get(
        "/resume/?search=platform",
        headers=auth_headers,
    )

    assert role_response.status_code == 200
    assert [
        resume["target_role"]
        for resume in role_response.json()
    ] == ["Platform Engineer"]

    filename_response = client.get(
        "/resume/?search=architect-profile",
        headers=auth_headers,
    )

    assert filename_response.status_code == 200
    assert [
        resume["original_filename"]
        for resume in filename_response.json()
    ] == ["architect-profile.pdf"]


def test_list_resumes_supports_sort_order(
    client,
    auth_headers,
    fake_ai,
):
    created_ids = []

    for target_role in [
        "Backend Engineer",
        "Platform Engineer",
        "Staff Engineer",
    ]:
        files, data = _pdf_upload(
            target_role=target_role,
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

    newest_response = client.get(
        "/resume/?sort=newest",
        headers=auth_headers,
    )
    oldest_response = client.get(
        "/resume/?sort=oldest",
        headers=auth_headers,
    )

    assert newest_response.status_code == 200
    assert oldest_response.status_code == 200

    assert [
        resume["id"]
        for resume in newest_response.json()
    ] == list(reversed(created_ids))

    assert [
        resume["id"]
        for resume in oldest_response.json()
    ] == created_ids


def test_list_resumes_rejects_invalid_sort(
    client,
    auth_headers,
):
    response = client.get(
        "/resume/?sort=unsupported",
        headers=auth_headers,
    )

    assert response.status_code == 422
    
def test_list_resumes_filters_by_status(
    client,
    auth_headers,
    uploaded_resume,
    db_engine,
):
    with Session(db_engine) as db:
        db.add_all(
            [
                Resume(
                    user_id=1,
                    original_filename="pending.pdf",
                    stored_filename="pending-status.pdf",
                    mime_type="application/pdf",
                    file_size=10,
                    target_role="Platform Engineer",
                    status=ResumeStatus.UPLOADED,
                ),
                Resume(
                    user_id=1,
                    original_filename="failed.pdf",
                    stored_filename="failed-status.pdf",
                    mime_type="application/pdf",
                    file_size=10,
                    target_role="Staff Engineer",
                    status=ResumeStatus.FAILED,
                ),
            ]
        )
        db.commit()

    analyzed_response = client.get(
        "/resume/?status=analyzed",
        headers=auth_headers,
    )
    uploaded_response = client.get(
        "/resume/?status=uploaded",
        headers=auth_headers,
    )
    failed_response = client.get(
        "/resume/?status=failed",
        headers=auth_headers,
    )

    assert analyzed_response.status_code == 200
    assert uploaded_response.status_code == 200
    assert failed_response.status_code == 200

    assert [
        resume["status"]
        for resume in analyzed_response.json()
    ] == ["analyzed"]

    assert [
        resume["original_filename"]
        for resume in uploaded_response.json()
    ] == ["pending.pdf"]

    assert [
        resume["original_filename"]
        for resume in failed_response.json()
    ] == ["failed.pdf"]


def test_list_resumes_rejects_invalid_status(
    client,
    auth_headers,
):
    response = client.get(
        "/resume/?status=archived",
        headers=auth_headers,
    )

    assert response.status_code == 422
    
def test_retry_failed_resume_analysis(
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

    with Session(db_engine) as db:
        resume = Resume(
            user_id=1,
            original_filename="failed-resume.pdf",
            stored_filename="failed-resume.pdf",
            mime_type="application/pdf",
            file_size=10,
            target_role="Backend Engineer",
            job_description="Build reliable APIs",
            status=ResumeStatus.FAILED,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        db.add(
            ResumeAnalysis(
                resume_id=resume.id,
                ats_score=0,
                strengths=[],
                weaknesses=[],
                suggestions=[],
                provider="unknown",
                model="unknown",
                processing_time_ms=0,
                status=AnalysisStatus.FAILED,
                error_message="Temporary provider failure",
            )
        )
        db.commit()

        resume_id = resume.id

    response = client.post(
        f"/resume/{resume_id}/retry",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resume_id"] == resume_id
    assert body["target_role"] == "Backend Engineer"
    assert body["ats_score"] == 82

    with Session(db_engine) as db:
        updated_resume = db.get(
            Resume,
            resume_id,
        )

        assert updated_resume is not None
        assert updated_resume.status == ResumeStatus.ANALYZED

        analyses = (
            db.query(ResumeAnalysis)
            .filter(
                ResumeAnalysis.resume_id == resume_id,
            )
            .all()
        )

        assert len(analyses) == 2
        assert any(
            analysis.status == AnalysisStatus.SUCCESS
            for analysis in analyses
        )


def test_retry_resume_requires_a_failed_status(
    client,
    auth_headers,
    uploaded_resume,
):
    response = client.post(
        f"/resume/{uploaded_resume['resume_id']}/retry",
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Resume analysis can only be retried "
        "after a failed analysis"
    )


def test_retry_resume_hides_other_users_resume(
    client,
    auth_headers,
    other_auth_headers,
    db_engine,
):
    with Session(db_engine) as db:
        resume = Resume(
            user_id=1,
            original_filename="private.pdf",
            stored_filename="private.pdf",
            mime_type="application/pdf",
            file_size=10,
            target_role="Backend Engineer",
            status=ResumeStatus.FAILED,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        resume_id = resume.id

    response = client.post(
        f"/resume/{resume_id}/retry",
        headers=other_auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"
    
def test_list_resume_analysis_history(
    client,
    auth_headers,
    uploaded_resume,
    db_engine,
):
    resume_id = uploaded_resume["resume_id"]

    with Session(db_engine) as db:
        db.add(
            ResumeAnalysis(
                resume_id=resume_id,
                ats_score=0,
                strengths=[],
                weaknesses=[],
                suggestions=[],
                provider="unknown",
                model="unknown",
                processing_time_ms=0,
                status=AnalysisStatus.FAILED,
                error_message="Temporary provider failure",
            )
        )
        db.commit()

    response = client.get(
        f"/resume/{resume_id}/analyses",
        headers=auth_headers,
    )

    assert response.status_code == 200

    history = response.json()

    assert len(history) == 2
    assert history[0]["status"] == "failed"
    assert history[0]["error_message"] == (
        "Temporary provider failure"
    )
    assert history[1]["status"] == "success"
    assert history[1]["ats_score"] == 82


def test_list_resume_analysis_history_hides_other_users_resume(
    client,
    uploaded_resume,
    other_auth_headers,
):
    response = client.get(
        f"/resume/{uploaded_resume['resume_id']}/analyses",
        headers=other_auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"

def test_get_resume_statistics(
    client,
    auth_headers,
    fake_ai,
    db_engine,
):
    for target_role in [
        "Backend Engineer",
        "Platform Engineer",
    ]:
        files, data = _pdf_upload(
            target_role=target_role,
        )

        response = client.post(
            "/resume/analyze",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 200

    with Session(db_engine) as db:
        db.add_all(
            [
                Resume(
                    user_id=1,
                    original_filename="pending.pdf",
                    stored_filename="pending.pdf",
                    mime_type="application/pdf",
                    file_size=10,
                    target_role="Staff Engineer",
                    status=ResumeStatus.UPLOADED,
                ),
                Resume(
                    user_id=1,
                    original_filename="failed.pdf",
                    stored_filename="failed.pdf",
                    mime_type="application/pdf",
                    file_size=10,
                    target_role="Solutions Architect",
                    status=ResumeStatus.FAILED,
                ),
            ]
        )
        db.commit()

    response = client.get(
        "/resume/statistics",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_resumes": 4,
        "analyzed_resumes": 2,
        "uploaded_resumes": 1,
        "failed_resumes": 1,
        "average_ats_score": 82.0,
    }


def test_get_resume_statistics_is_user_scoped(
    client,
    auth_headers,
    other_auth_headers,
    fake_ai,
):
    files, data = _pdf_upload()

    response = client.post(
        "/resume/analyze",
        headers=auth_headers,
        files=files,
        data=data,
    )

    assert response.status_code == 200

    other_response = client.get(
        "/resume/statistics",
        headers=other_auth_headers,
    )

    assert other_response.status_code == 200
    assert other_response.json() == {
        "total_resumes": 0,
        "analyzed_resumes": 0,
        "uploaded_resumes": 0,
        "failed_resumes": 0,
        "average_ats_score": None,
    }
    
def test_reanalyze_resume_for_new_target_role(
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

    with Session(db_engine) as db:
        resume = Resume(
            user_id=1,
            original_filename="profile.pdf",
            stored_filename="profile.pdf",
            mime_type="application/pdf",
            file_size=10,
            target_role="Backend Engineer",
            job_description="Build backend APIs",
            status=ResumeStatus.ANALYZED,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        db.add(
            ResumeAnalysis(
                resume_id=resume.id,
                ats_score=80,
                strengths=["Python"],
                weaknesses=["Kubernetes"],
                suggestions=["Add cloud experience"],
                provider="fake",
                model="fake-model",
                processing_time_ms=1,
                status=AnalysisStatus.SUCCESS,
            )
        )
        db.commit()

        resume_id = resume.id

    response = client.post(
        f"/resume/{resume_id}/reanalyze",
        headers=auth_headers,
        json={
            "target_role": "Platform Engineer",
            "job_description": (
                "Build scalable internal developer platforms"
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["target_role"] == (
        "Platform Engineer"
    )
    assert response.json()["ats_score"] == 82

    with Session(db_engine) as db:
        updated_resume = db.get(
            Resume,
            resume_id,
        )

        assert updated_resume is not None
        assert updated_resume.target_role == (
            "Platform Engineer"
        )
        assert updated_resume.job_description == (
            "Build scalable internal developer platforms"
        )
        assert updated_resume.status == (
            ResumeStatus.ANALYZED
        )

        assert (
            db.query(ResumeAnalysis)
            .filter(
                ResumeAnalysis.resume_id == resume_id,
            )
            .count()
            == 2
        )


def test_reanalyze_resume_hides_other_users_resume(
    client,
    auth_headers,
    other_auth_headers,
    fake_ai,
    db_engine,
):
    with Session(db_engine) as db:
        resume = Resume(
            user_id=1,
            original_filename="private.pdf",
            stored_filename="private.pdf",
            mime_type="application/pdf",
            file_size=10,
            target_role="Backend Engineer",
            status=ResumeStatus.ANALYZED,
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        resume_id = resume.id

    response = client.post(
        f"/resume/{resume_id}/reanalyze",
        headers=other_auth_headers,
        json={
            "target_role": "Platform Engineer",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"