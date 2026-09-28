from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from main import app as fastapi_app


REQUEST_ID_HEADER = "X-Request-ID"


def assert_valid_request_id(response) -> str:
    request_id = response.headers.get(
        REQUEST_ID_HEADER
    )

    assert request_id is not None
    assert str(UUID(request_id)) == request_id

    return request_id


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
    assert_valid_request_id(response)


def test_each_response_receives_unique_request_id(client):
    first_response = client.get("/health")
    second_response = client.get("/health")

    first_request_id = assert_valid_request_id(
        first_response
    )
    second_request_id = assert_valid_request_id(
        second_response
    )

    assert first_request_id != second_request_id


def test_caller_supplied_request_id_is_not_trusted(client):
    caller_request_id = "caller-controlled-value"

    response = client.get(
        "/health",
        headers={
            REQUEST_ID_HEADER: caller_request_id,
        },
    )

    generated_request_id = assert_valid_request_id(
        response
    )

    assert generated_request_id != caller_request_id


def test_cors_exposes_request_id_header(client):
    response = client.get(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
        },
    )

    assert response.status_code == 200
    assert_valid_request_id(response)

    exposed_headers = response.headers.get(
        "access-control-expose-headers",
        "",
    ).lower()

    assert REQUEST_ID_HEADER.lower() in exposed_headers


def test_readiness_check_reports_database_ready(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
    }
    assert_valid_request_id(response)


def test_readiness_check_reports_database_unavailable(
    client,
):
    class UnavailableDatabase:
        def execute(self, statement):
            raise SQLAlchemyError(
                "Database is unavailable"
            )

    def override_get_db():
        yield UnavailableDatabase()

    fastapi_app.dependency_overrides[
        get_db
    ] = override_get_db

    try:
        response = client.get("/health/ready")
    finally:
        fastapi_app.dependency_overrides.pop(
            get_db,
            None,
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database unavailable",
    }
    assert_valid_request_id(response)


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert_valid_request_id(response)