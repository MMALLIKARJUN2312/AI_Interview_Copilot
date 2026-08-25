def test_start_interview_generates_role_aligned_questions(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]

    response = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "general", "num_questions": 3}],
    })

    assert response.status_code == 200
    body = response.json()
    assert body["session"]["target_role"] == "Backend Engineer"
    assert body["session"]["total_questions"] == 3
    assert body["session"]["status"] == "in_progress"
    assert "Backend Engineer" in body["first_question"]["question_text"]
    assert body["first_question"]["round_type"] == "general"

def test_start_interview_requires_owned_resume(client, other_auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]

    response = client.post("/interview/start", headers=other_auth_headers, json={"resume_id": resume_id})

    assert response.status_code == 400

def test_start_interview_uses_default_round_composition(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]

    response = client.post("/interview/start", headers=auth_headers, json={"resume_id": resume_id})

    assert response.status_code == 200
    body = response.json()
    # default composition: 2 dsa_coding + 1 machine_coding + 2 general = 5
    assert body["session"]["total_questions"] == 5
    assert body["first_question"]["round_type"] == "dsa_coding"
    assert len(body["first_question"]["test_cases"]) == 1  # only the visible test case, hidden one excluded

def test_full_interview_lifecycle_produces_feedback_and_roadmap(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "general", "num_questions": 3}],
    }).json()
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
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "general", "num_questions": 3}],
    }).json()
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
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "general", "num_questions": 3}],
    }).json()
    session_id = start["session"]["id"]

    response = client.post(f"/interview/{session_id}/complete", headers=auth_headers)

    assert response.status_code == 400

def test_cannot_complete_with_unanswered_questions(client, auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "general", "num_questions": 3}],
    }).json()
    session_id = start["session"]["id"]

    answer = client.post(f"/interview/{session_id}/answer", headers=auth_headers, json={
        "question_id": start["first_question"]["id"],
        "answer_text": "A detailed technical answer.",
    })
    assert answer.status_code == 200

    response = client.post(f"/interview/{session_id}/complete", headers=auth_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot complete an interview until all questions are answered"

def test_other_user_cannot_see_session(client, auth_headers, other_auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "general", "num_questions": 3}],
    }).json()
    session_id = start["session"]["id"]

    response = client.get(f"/interview/{session_id}", headers=other_auth_headers)

    assert response.status_code == 404

def test_list_sessions_only_returns_own(client, auth_headers, other_auth_headers, uploaded_resume):
    resume_id = uploaded_resume["resume_id"]
    client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "general", "num_questions": 3}],
    })

    own = client.get("/interview/sessions", headers=auth_headers)
    other = client.get("/interview/sessions", headers=other_auth_headers)

    assert len(own.json()) == 1
    assert len(other.json()) == 0

def test_dsa_round_run_code_only_executes_visible_test_cases(client, auth_headers, uploaded_resume, fake_code_execution):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "dsa_coding", "num_questions": 1}],
    }).json()
    question = start["first_question"]
    assert question["round_type"] == "dsa_coding"
    assert len(question["test_cases"]) == 1  # hidden test case is not exposed

    response = client.post(f"/interview/{start['session']['id']}/run-code", headers=auth_headers, json={
        "question_id": question["id"], "code": "correct solution", "language": "python",
    })

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 1  # only ran the visible case
    assert body["all_passed"] is True

def test_dsa_round_submit_scores_from_test_pass_rate(client, auth_headers, uploaded_resume, fake_code_execution):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "dsa_coding", "num_questions": 1}],
    }).json()
    session_id = start["session"]["id"]
    question_id = start["first_question"]["id"]

    response = client.post(f"/interview/{session_id}/answer", headers=auth_headers, json={
        "question_id": question_id, "code": "correct solution", "language": "python",
    })

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert answer["passed_test_count"] == 2  # both visible + hidden test cases run at submit time
    assert answer["total_test_count"] == 2
    assert answer["score"] == 92  # 0.7 * 100 (all tests passed) + 0.3 * 75 (fake AI score)

def test_dsa_round_submit_requires_code(client, auth_headers, uploaded_resume, fake_code_execution):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "dsa_coding", "num_questions": 1}],
    }).json()
    session_id = start["session"]["id"]
    question_id = start["first_question"]["id"]

    response = client.post(f"/interview/{session_id}/answer", headers=auth_headers, json={
        "question_id": question_id, "answer_text": "not code",
    })

    assert response.status_code == 400

def test_machine_coding_round_scores_from_ai_review_only(client, auth_headers, uploaded_resume, fake_code_execution):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id, "rounds": [{"round_type": "machine_coding", "num_questions": 1}],
    }).json()
    question = start["first_question"]
    assert question["round_type"] == "machine_coding"
    assert question["test_cases"] == []

    response = client.post(f"/interview/{start['session']['id']}/answer", headers=auth_headers, json={
        "question_id": question["id"], "code": "class RateLimiter: pass", "language": "python",
    })

    assert response.status_code == 200
    answer = response.json()["answer"]
    assert answer["score"] == 75  # pure AI score, no test cases to blend in
    assert answer["total_test_count"] is None

def test_mixed_round_interview_completes_with_all_round_types(client, auth_headers, uploaded_resume, fake_code_execution):
    resume_id = uploaded_resume["resume_id"]
    start = client.post("/interview/start", headers=auth_headers, json={
        "resume_id": resume_id,
        "rounds": [
            {"round_type": "dsa_coding", "num_questions": 1},
            {"round_type": "machine_coding", "num_questions": 1},
            {"round_type": "general", "num_questions": 1},
        ],
    }).json()
    session_id = start["session"]["id"]
    assert start["session"]["total_questions"] == 3

    detail = client.get(f"/interview/{session_id}", headers=auth_headers).json()
    round_types = [q["round_type"] for q in detail["questions"]]
    assert round_types == ["dsa_coding", "machine_coding", "general"]

    for question in detail["questions"]:
        if question["round_type"] == "general":
            payload = {"question_id": question["id"], "answer_text": "A thoughtful answer."}
        else:
            payload = {"question_id": question["id"], "code": "correct solution", "language": "python"}
        response = client.post(f"/interview/{session_id}/answer", headers=auth_headers, json=payload)
        assert response.status_code == 200

    complete = client.post(f"/interview/{session_id}/complete", headers=auth_headers)
    assert complete.status_code == 200
    assert complete.json()["session"]["status"] == "completed"
