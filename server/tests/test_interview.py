def test_start_interview_generates_role_aligned_questions(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]

    response = client.post("/interview/start", headers=auth_headers, json={"resume_id": resume_id, "num_questions": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["session"]["target_role"] == "Backend Engineer"
    assert body["session"]["total_questions"] == 3
    assert body["session"]["status"] == "in_progress"
    assert "Backend Engineer" in body["first_question"]["question_text"]

def test_start_interview_requires_owned_resume(client, other_auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]

    response = client.post("/interview/start", headers=other_auth_headers, json={"resume_id": resume_id})

    assert response.status_code == 400

def test_full_interview_lifecycle_produces_feedback_and_roadmap(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={"resume_id": resume_id, "num_questions": 3}).json()
    session_id = start["session"]["id"]

    question = start["first_question"]
    last_response = None
    while question is not None:
        last_response = client.post(f"/interview/{session_id}/answer", headers=auth_headers, json={
            "question_id": question["id"], "answer_text": "A detailed technical answer.",
        })
        assert last_response.status_code == 200
        question = last_response.json()["next_question"]

    assert last_response.json()["is_complete"] is True

    complete = client.post(f"/interview/{session_id}/complete", headers=auth_headers)

    assert complete.status_code == 200
    body = complete.json()
    assert body["session"]["status"] == "completed"
    assert body["session"]["overall_score"] == 72
    assert body["feedback"]["summary"] == "Decent performance."
    assert body["roadmap"]["items"][0]["topic"] == "System Design"

    detail = client.get(f"/interview/{session_id}", headers=auth_headers)
    assert detail.status_code == 200
    detail_body = detail.json()
    assert len(detail_body["questions"]) == 3
    assert all(q["answer"] is not None for q in detail_body["questions"])
    assert detail_body["feedback"] is not None
    assert detail_body["roadmap"] is not None

def test_cannot_answer_same_question_twice(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={"resume_id": resume_id, "num_questions": 3}).json()
    session_id = start["session"]["id"]
    question_id = start["first_question"]["id"]

    first = client.post(f"/interview/{session_id}/answer", headers=auth_headers, json={
        "question_id": question_id, "answer_text": "first answer",
    })
    second = client.post(f"/interview/{session_id}/answer", headers=auth_headers, json={
        "question_id": question_id, "answer_text": "second answer",
    })

    assert first.status_code == 200
    assert second.status_code == 400

def test_cannot_complete_without_any_answers(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={"resume_id": resume_id, "num_questions": 3}).json()
    session_id = start["session"]["id"]

    response = client.post(f"/interview/{session_id}/complete", headers=auth_headers)

    assert response.status_code == 400

def test_other_user_cannot_see_session(client, auth_headers, other_auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={"resume_id": resume_id, "num_questions": 3}).json()
    session_id = start["session"]["id"]

    response = client.get(f"/interview/{session_id}", headers=other_auth_headers)

    assert response.status_code == 404

def test_list_sessions_only_returns_own(client, auth_headers, other_auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    client.post("/interview/start", headers=auth_headers, json={"resume_id": resume_id, "num_questions": 3})

    own = client.get("/interview/sessions", headers=auth_headers)
    other = client.get("/interview/sessions", headers=other_auth_headers)

    assert len(own.json()) == 1
    assert len(other.json()) == 0
