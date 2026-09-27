from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from main import app as fastapi_app


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_reports_database_ready(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_check_reports_database_unavailable(
    client,
):
    class UnavailableDatabase:
        def execute(self, statement):
            raise SQLAlchemyError("Database is unavailable")

    def override_get_db():
        yield UnavailableDatabase()

    fastapi_app.dependency_overrides[get_db] = override_get_db

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


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200