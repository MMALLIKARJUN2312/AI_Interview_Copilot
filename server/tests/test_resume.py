import io

def _pdf_upload(target_role="Backend Engineer"):
    files = {"file": ("resume.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")}
    data = {"target_role": target_role}
    return files, data

def test_upload_requires_auth(client, fake_ai):
    files, data = _pdf_upload()

    response = client.post("/resume/analyze", files=files, data=data)

    assert response.status_code == 401

def test_upload_rejects_non_pdf(client, auth_headers, fake_ai):
    files = {"file": ("resume.txt", io.BytesIO(b"not a pdf"), "text/plain")}
    data = {"target_role": "Backend Engineer"}

    response = client.post("/resume/analyze", headers=auth_headers, files=files, data=data)

    assert response.status_code == 400

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
