from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import (
    InterviewAnswer,
    InterviewFeedback,
    InterviewQuestion,
    InterviewSession,
    LearningRoadmap,
)
import io

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

def test_list_sessions_supports_pagination(
    client,
    auth_headers,
    uploaded_resume,
):
    resume_id = uploaded_resume["resume_id"]
    created_ids = []

    for _ in range(3):
        response = client.post(
            "/interview/start",
            headers=auth_headers,
            json={
                "resume_id": resume_id,
                "rounds": [
                    {
                        "round_type": "general",
                        "num_questions": 1,
                    }
                ],
            },
        )

        assert response.status_code == 200
        created_ids.append(
            response.json()["session"]["id"]
        )

    first_page = client.get(
        "/interview/sessions"
        "?limit=2&offset=0",
        headers=auth_headers,
    )
    second_page = client.get(
        "/interview/sessions"
        "?limit=2&offset=2",
        headers=auth_headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    assert [
        session["id"]
        for session in first_page.json()
    ] == list(reversed(created_ids))[:2]

    assert [
        session["id"]
        for session in second_page.json()
    ] == list(reversed(created_ids))[2:]


def test_list_sessions_rejects_invalid_pagination(
    client,
    auth_headers,
):
    invalid_requests = [
        "/interview/sessions?limit=0",
        "/interview/sessions?limit=51",
        "/interview/sessions?offset=-1",
    ]

    for path in invalid_requests:
        response = client.get(
            path,
            headers=auth_headers,
        )

        assert response.status_code == 422

def test_delete_interview_removes_related_records(
    client,
    auth_headers,
    uploaded_resume,
    db_engine,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert start_response.status_code == 200

    start_body = start_response.json()
    session_id = start_body["session"]["id"]
    question_id = start_body["first_question"]["id"]

    answer_response = client.post(
        f"/interview/{session_id}/answer",
        headers=auth_headers,
        json={
            "question_id": question_id,
            "answer_text": "A detailed technical answer.",
        },
    )

    assert answer_response.status_code == 200

    complete_response = client.post(
        f"/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_response.status_code == 200

    with Session(db_engine) as db:
        answer_id = db.scalar(
            select(InterviewAnswer.id).where(
                InterviewAnswer.question_id == question_id
            )
        )
        feedback_id = db.scalar(
            select(InterviewFeedback.id).where(
                InterviewFeedback.session_id == session_id
            )
        )
        roadmap_id = db.scalar(
            select(LearningRoadmap.id).where(
                LearningRoadmap.session_id == session_id
            )
        )

    delete_response = client.delete(
        f"/interview/{session_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Interview session deleted permanently",
    }

    with Session(db_engine) as db:
        assert db.get(InterviewSession, session_id) is None
        assert db.get(InterviewQuestion, question_id) is None
        assert db.get(InterviewAnswer, answer_id) is None
        assert db.get(InterviewFeedback, feedback_id) is None
        assert db.get(LearningRoadmap, roadmap_id) is None

    detail_response = client.get(
        f"/interview/{session_id}",
        headers=auth_headers,
    )

    assert detail_response.status_code == 404


def test_other_user_cannot_delete_interview(
    client,
    auth_headers,
    other_auth_headers,
    uploaded_resume,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert start_response.status_code == 200
    session_id = start_response.json()["session"]["id"]

    delete_response = client.delete(
        f"/interview/{session_id}",
        headers=other_auth_headers,
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == (
        "Interview session not found"
    )

    owner_response = client.get(
        f"/interview/{session_id}",
        headers=auth_headers,
    )

    assert owner_response.status_code == 200


def test_delete_interview_requires_authentication(
    client,
):
    response = client.delete("/interview/999999")

    assert response.status_code == 401
    
def test_list_sessions_filters_by_status(
    client,
    auth_headers,
    uploaded_resume,
):
    resume_id = uploaded_resume["resume_id"]

    in_progress_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": resume_id,
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert in_progress_response.status_code == 200
    in_progress_id = (
        in_progress_response.json()["session"]["id"]
    )

    completed_start = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": resume_id,
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert completed_start.status_code == 200

    completed_body = completed_start.json()
    completed_id = completed_body["session"]["id"]
    question_id = completed_body["first_question"]["id"]

    answer_response = client.post(
        f"/interview/{completed_id}/answer",
        headers=auth_headers,
        json={
            "question_id": question_id,
            "answer_text": "A detailed technical answer.",
        },
    )

    assert answer_response.status_code == 200

    complete_response = client.post(
        f"/interview/{completed_id}/complete",
        headers=auth_headers,
    )

    assert complete_response.status_code == 200

    completed_sessions = client.get(
        "/interview/sessions?status=completed",
        headers=auth_headers,
    )
    in_progress_sessions = client.get(
        "/interview/sessions?status=in_progress",
        headers=auth_headers,
    )

    assert completed_sessions.status_code == 200
    assert in_progress_sessions.status_code == 200

    assert [
        session["id"]
        for session in completed_sessions.json()
    ] == [completed_id]

    assert [
        session["id"]
        for session in in_progress_sessions.json()
    ] == [in_progress_id]


def test_list_sessions_rejects_invalid_status(
    client,
    auth_headers,
):
    response = client.get(
        "/interview/sessions?status=unknown",
        headers=auth_headers,
    )

    assert response.status_code == 422
    
def test_interview_statistics_are_empty_for_new_user(
    client,
    auth_headers,
):
    response = client.get(
        "/interview/statistics",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_sessions": 0,
        "in_progress_sessions": 0,
        "completed_sessions": 0,
        "average_score": None,
    }


def test_interview_statistics_summarize_user_sessions(
    client,
    auth_headers,
    uploaded_resume,
):
    resume_id = uploaded_resume["resume_id"]

    in_progress_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": resume_id,
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert in_progress_response.status_code == 200

    completed_start = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": resume_id,
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert completed_start.status_code == 200

    completed_body = completed_start.json()
    session_id = completed_body["session"]["id"]
    question_id = completed_body["first_question"]["id"]

    answer_response = client.post(
        f"/interview/{session_id}/answer",
        headers=auth_headers,
        json={
            "question_id": question_id,
            "answer_text": "A detailed technical answer.",
        },
    )

    assert answer_response.status_code == 200

    complete_response = client.post(
        f"/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_response.status_code == 200

    statistics_response = client.get(
        "/interview/statistics",
        headers=auth_headers,
    )

    assert statistics_response.status_code == 200
    assert statistics_response.json() == {
        "total_sessions": 2,
        "in_progress_sessions": 1,
        "completed_sessions": 1,
        "average_score": 72.0,
    }


def test_interview_statistics_require_authentication(client):
    response = client.get("/interview/statistics")

    assert response.status_code == 401
    
def test_abandon_interview_preserves_completed_answers(
    client,
    auth_headers,
    uploaded_resume,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 2,
                }
            ],
        },
    )

    assert start_response.status_code == 200

    start_body = start_response.json()
    session_id = start_body["session"]["id"]

    answer_response = client.post(
        f"/interview/{session_id}/answer",
        headers=auth_headers,
        json={
            "question_id": start_body["first_question"]["id"],
            "answer_text": "A detailed technical answer.",
        },
    )

    assert answer_response.status_code == 200
    next_question = answer_response.json()["next_question"]

    abandon_response = client.post(
        f"/interview/{session_id}/abandon",
        headers=auth_headers,
    )

    assert abandon_response.status_code == 200
    assert abandon_response.json()["status"] == "abandoned"
    assert abandon_response.json()["current_index"] == 1

    detail_response = client.get(
        f"/interview/{session_id}",
        headers=auth_headers,
    )

    assert detail_response.status_code == 200

    detail_body = detail_response.json()
    assert detail_body["session"]["status"] == "abandoned"
    assert detail_body["questions"][0]["answer"] is not None
    assert detail_body["questions"][1]["answer"] is None

    further_answer = client.post(
        f"/interview/{session_id}/answer",
        headers=auth_headers,
        json={
            "question_id": next_question["id"],
            "answer_text": "This must not be accepted.",
        },
    )

    assert further_answer.status_code == 400
    assert further_answer.json()["detail"] == (
        "This interview session is not in progress"
    )

    complete_response = client.post(
        f"/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_response.status_code == 400
    assert complete_response.json()["detail"] == (
        "Abandoned interview sessions cannot be completed"
    )


def test_abandon_interview_is_idempotent(
    client,
    auth_headers,
    uploaded_resume,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    session_id = start_response.json()["session"]["id"]

    first_response = client.post(
        f"/interview/{session_id}/abandon",
        headers=auth_headers,
    )
    second_response = client.post(
        f"/interview/{session_id}/abandon",
        headers=auth_headers,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "abandoned"


def test_completed_interview_cannot_be_abandoned(
    client,
    auth_headers,
    uploaded_resume,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    body = start_response.json()
    session_id = body["session"]["id"]

    client.post(
        f"/interview/{session_id}/answer",
        headers=auth_headers,
        json={
            "question_id": body["first_question"]["id"],
            "answer_text": "A detailed technical answer.",
        },
    )

    complete_response = client.post(
        f"/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_response.status_code == 200

    abandon_response = client.post(
        f"/interview/{session_id}/abandon",
        headers=auth_headers,
    )

    assert abandon_response.status_code == 409
    assert abandon_response.json()["detail"] == (
        "Only an in-progress interview can be abandoned"
    )


def test_other_user_cannot_abandon_interview(
    client,
    auth_headers,
    other_auth_headers,
    uploaded_resume,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    session_id = start_response.json()["session"]["id"]

    response = client.post(
        f"/interview/{session_id}/abandon",
        headers=other_auth_headers,
    )

    assert response.status_code == 404
    
def test_list_sessions_searches_target_role(
    client,
    auth_headers,
    uploaded_resume,
):
    backend_start = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert backend_start.status_code == 200

    frontend_resume = client.post(
        "/resume/analyze",
        headers=auth_headers,
        files={
            "file": (
                "frontend-resume.pdf",
                io.BytesIO(b"%PDF-1.4 fake"),
                "application/pdf",
            )
        },
        data={
            "target_role": "Frontend Engineer",
            "job_description": "Build accessible web applications",
        },
    )

    assert frontend_resume.status_code == 200

    frontend_start = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": frontend_resume.json()["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert frontend_start.status_code == 200

    response = client.get(
        "/interview/sessions?search=frontend",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["target_role"] == (
        "Frontend Engineer"
    )


def test_session_search_is_case_insensitive(
    client,
    auth_headers,
    uploaded_resume,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert start_response.status_code == 200

    response = client.get(
        "/interview/sessions?search=BACKEND",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["target_role"] == (
        "Backend Engineer"
    )


def test_session_search_combines_with_status_filter(
    client,
    auth_headers,
    uploaded_resume,
):
    start_response = client.post(
        "/interview/start",
        headers=auth_headers,
        json={
            "resume_id": uploaded_resume["resume_id"],
            "rounds": [
                {
                    "round_type": "general",
                    "num_questions": 1,
                }
            ],
        },
    )

    assert start_response.status_code == 200

    session_id = start_response.json()["session"]["id"]

    abandon_response = client.post(
        f"/interview/{session_id}/abandon",
        headers=auth_headers,
    )

    assert abandon_response.status_code == 200

    matching_response = client.get(
        "/interview/sessions"
        "?status=abandoned&search=backend",
        headers=auth_headers,
    )
    nonmatching_response = client.get(
        "/interview/sessions"
        "?status=completed&search=backend",
        headers=auth_headers,
    )

    assert matching_response.status_code == 200
    assert len(matching_response.json()) == 1
    assert matching_response.json()[0]["id"] == session_id

    assert nonmatching_response.status_code == 200
    assert nonmatching_response.json() == []


def test_session_search_rejects_excessive_length(
    client,
    auth_headers,
):
    response = client.get(
        f"/interview/sessions?search={'a' * 101}",
        headers=auth_headers,
    )

    assert response.status_code == 422