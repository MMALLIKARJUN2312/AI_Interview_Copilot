import pytest
from sqlalchemy.exc import IntegrityError
from jose import jwt

from app.core.config import settings
from app.services.user_service import UserService

from sqlalchemy.orm import Session

from app.core.tokens import hash_refresh_token
from app.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)

REGISTER_PAYLOAD = {
    "full_name": "Jane Dev",
    "email": "jane@example.com",
    "password": "hunter2pass",
}


def register_user(client, payload=None):
    response = client.post(
        "/auth/register",
        json=payload or REGISTER_PAYLOAD,
    )
    assert response.status_code == 200, response.text
    return response


def login_user(client, email="jane@example.com", password="hunter2pass"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_register_creates_user_without_authenticating(client):
    response = register_user(client)

    body = response.json()

    assert body["message"] == "User Registered Successfully"
    assert body["user_id"] == 1
    assert "access_token" not in body
    assert "refresh_token" not in body

    me_response = client.get("/auth/me")

    assert me_response.status_code == 401


def test_register_duplicate_email_is_rejected(client):
    register_user(client)

    response = client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Jane Dev",
            "email": "not-an-email",
            "password": "hunter2pass",
        },
    )

    assert response.status_code == 422

@pytest.mark.parametrize(
    "password",
    [
        "",
        "short",
        "1234567",
    ],
)
def test_register_rejects_short_password(client, password):
    response = client.post(
        "/auth/register",
        json={
            **REGISTER_PAYLOAD,
            "password": password,
        },
    )

    assert response.status_code == 422


def test_register_rejects_password_over_bcrypt_byte_limit(client):
    response = client.post(
        "/auth/register",
        json={
            **REGISTER_PAYLOAD,
            # Each character occupies two UTF-8 bytes.
            "password": "é" * 40,
        },
    )

    assert response.status_code == 422

    error_messages = [
        error["msg"]
        for error in response.json()["detail"]
    ]

    assert any(
        "Password must not exceed 72 bytes" in message
        for message in error_messages
    )


def test_register_accepts_long_passphrase(client):
    response = client.post(
        "/auth/register",
        json={
            **REGISTER_PAYLOAD,
            "password": "a secure memorable passphrase",
        },
    )

    assert response.status_code == 200

@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("jane@example.com", "wrong-password"),
        ("unknown@example.com", "hunter2pass"),
    ],
)
def test_login_rejects_invalid_credentials_without_email_enumeration(
    client,
    email,
    password,
):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Credentials"


def test_login_returns_access_token_without_exposing_refresh_token(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert "refresh_token" not in body
    assert client.cookies.get(REFRESH_COOKIE_NAME) is not None

def test_login_access_token_authenticates_user(client):
    register_user(client)
    tokens = login_user(client)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "full_name": REGISTER_PAYLOAD["full_name"],
        "email": REGISTER_PAYLOAD["email"],
        "role": "candidate",
    }

def test_access_token_contains_required_security_claims(client):
    register_user(client)
    tokens = login_user(client)

    payload = jwt.decode(
        tokens["access_token"],
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )

    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert payload["email"] == REGISTER_PAYLOAD["email"]
    assert payload["role"] == "candidate"
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert isinstance(payload["jti"], str)
    assert payload["jti"]


def test_me_rejects_token_without_access_type(client):
    register_user(client)

    token = jwt.encode(
        {
            "sub": "1",
            "email": REGISTER_PAYLOAD["email"],
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Token"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "subject",
    [
        None,
        "",
        "not-a-number",
        "-1",
        "1.5",
    ],
)
def test_me_rejects_invalid_token_subject(
    client,
    subject,
):
    register_user(client)

    payload = {
        "type": "access",
        "email": REGISTER_PAYLOAD["email"],
    }

    if subject is not None:
        payload["sub"] = subject

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Token"


def test_separate_logins_receive_different_token_ids(client):
    register_user(client)

    first_login = login_user(client)
    second_login = login_user(client)

    first_payload = jwt.decode(
        first_login["access_token"],
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
    second_payload = jwt.decode(
        second_login["access_token"],
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )

    assert first_payload["jti"] != second_payload["jti"]

def test_me_requires_access_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_access_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer not-a-valid-access-token",
        },
    )

    assert response.status_code == 401


def test_me_does_not_expose_password_hash(client, auth_headers):
    response = client.get(
        "/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == "user@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_refresh_rotates_refresh_token_without_exposing_it(client):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    original_refresh_token = client.cookies.get(
        REFRESH_COOKIE_NAME
    )
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

    assert original_refresh_token is not None
    assert csrf_token is not None

    response = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200

    body = response.json()
    rotated_refresh_token = client.cookies.get(
        REFRESH_COOKIE_NAME
    )

    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "refresh_token" not in body
    assert rotated_refresh_token is not None
    assert rotated_refresh_token != original_refresh_token

def test_cookie_refresh_rejects_reused_rotated_token(client):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    original_refresh_token = client.cookies.get(REFRESH_COOKIE_NAME)
    original_csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

    assert original_refresh_token is not None
    assert original_csrf_token is not None

    first_refresh = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": original_csrf_token},
    )

    assert first_refresh.status_code == 200

    client.cookies.clear()
    client.cookies.set(
        REFRESH_COOKIE_NAME,
        original_refresh_token,
        path="/auth",
    )
    client.cookies.set(
        CSRF_COOKIE_NAME,
        original_csrf_token,
        path="/",
    )

    reused_response = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": original_csrf_token},
    )

    assert reused_response.status_code == 401
    assert (
        reused_response.json()["detail"]
        == "Invalid or expired refresh token"
    )

def test_refresh_token_can_only_be_consumed_once(
    client,
    db_engine,
):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    raw_refresh_token = client.cookies.get(
        REFRESH_COOKIE_NAME
    )
    assert raw_refresh_token is not None

    token_hash = hash_refresh_token(raw_refresh_token)
    repository = RefreshTokenRepository()

    with Session(db_engine) as first_session:
        first_user_id = repository.consume_valid_token(
            first_session,
            token_hash,
        )
        first_session.commit()

    with Session(db_engine) as second_session:
        second_user_id = repository.consume_valid_token(
            second_session,
            token_hash,
        )
        second_session.commit()

    assert first_user_id == 1
    assert second_user_id is None

def test_refresh_does_not_accept_request_body_token(client):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    exposed_refresh_token = client.cookies.get(
        REFRESH_COOKIE_NAME
    )
    assert exposed_refresh_token is not None

    client.cookies.clear()

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": exposed_refresh_token,
        },
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Refresh token cookie is required"
    )

def test_refreshed_access_token_is_usable(client):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)
    assert csrf_token is not None

    refresh_response = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert refresh_response.status_code == 200
    assert "refresh_token" not in refresh_response.json()

    refreshed_access_token = refresh_response.json()[
        "access_token"
    ]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": (
                f"Bearer {refreshed_access_token}"
            ),
        },
    )

    assert me_response.status_code == 200
    assert (
        me_response.json()["email"]
        == REGISTER_PAYLOAD["email"]
    )

def test_logout_revokes_refresh_token(client):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = client.cookies.get(REFRESH_COOKIE_NAME)
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

    assert refresh_token is not None
    assert csrf_token is not None

    logout_response = client.post(
        "/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {
        "message": "Logged out",
    }

    # Restore the revoked credentials to verify that they cannot
    # create another authenticated session.
    client.cookies.set(
        REFRESH_COOKIE_NAME,
        refresh_token,
        path="/auth",
    )
    client.cookies.set(
        CSRF_COOKIE_NAME,
        csrf_token,
        path="/",
    )

    refresh_response = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert refresh_response.status_code == 401


def test_candidate_cannot_access_admin_endpoint(client, auth_headers):
    response = client.get(
        "/auth/admin",
        headers=auth_headers,
    )

    assert response.status_code == 403
    
REFRESH_COOKIE_NAME = "aic_refresh_token"
CSRF_COOKIE_NAME = "aic_csrf_token"

def test_login_sets_httponly_refresh_cookie(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert response.status_code == 200

    set_cookie = response.headers["set-cookie"].lower()

    assert f"{REFRESH_COOKIE_NAME}=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert "path=/auth" in set_cookie
    assert client.cookies.get(REFRESH_COOKIE_NAME)


def test_refresh_accepts_protected_cookie_without_request_body(client):
    register_user(client)
    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    original_refresh_token = client.cookies.get(REFRESH_COOKIE_NAME)
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

    assert original_refresh_token
    assert csrf_token

    response = client.post(
        "/auth/refresh",
        headers={
            "X-CSRF-Token": csrf_token,
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"]

    rotated_refresh_token = client.cookies.get(REFRESH_COOKIE_NAME)
    rotated_csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

    assert rotated_refresh_token
    assert rotated_refresh_token != original_refresh_token
    assert rotated_csrf_token
    assert rotated_csrf_token != csrf_token

def test_logout_accepts_protected_cookie_and_clears_it(client):
    register_user(client)
    client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    refresh_token = client.cookies.get(REFRESH_COOKIE_NAME)
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

    assert refresh_token
    assert csrf_token

    logout_response = client.post(
        "/auth/logout",
        headers={
            "X-CSRF-Token": csrf_token,
        },
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Logged out"}
    assert client.cookies.get(REFRESH_COOKIE_NAME) is None
    assert client.cookies.get(CSRF_COOKIE_NAME) is None

    client.cookies.set(
        REFRESH_COOKIE_NAME,
        refresh_token,
        path="/auth",
    )
    client.cookies.set(
        CSRF_COOKIE_NAME,
        csrf_token,
        path="/",
    )

    refresh_response = client.post(
        "/auth/refresh",
        headers={
            "X-CSRF-Token": csrf_token,
        },
    )

    assert refresh_response.status_code == 401

def test_refresh_without_cookie_is_rejected(client):
    client.cookies.clear()

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Refresh token cookie is required"
    )

def test_logout_without_body_or_cookie_is_idempotent(client):
    client.cookies.clear()

    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}
    
def issue_csrf_token(client):
    response = client.get("/auth/csrf")

    assert response.status_code == 200

    csrf_token = response.json()["csrf_token"]

    assert csrf_token
    assert client.cookies.get(CSRF_COOKIE_NAME) == csrf_token

    return csrf_token

def test_csrf_endpoint_sets_httponly_cookie(client):
    response = client.get("/auth/csrf")

    assert response.status_code == 200

    csrf_token = response.json()["csrf_token"]
    set_cookie = response.headers["set-cookie"].lower()

    assert csrf_token
    assert f"{CSRF_COOKIE_NAME}=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie
    assert client.cookies.get(CSRF_COOKIE_NAME) == csrf_token


def test_cookie_refresh_rejects_missing_csrf_header(client):
    register_user(client)
    client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed"


def test_cookie_refresh_rejects_invalid_csrf_header(client):
    register_user(client)
    client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    response = client.post(
        "/auth/refresh",
        headers={
            "X-CSRF-Token": "incorrect-token",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed"


def test_cookie_logout_rejects_missing_csrf_header(client):
    register_user(client)
    client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    response = client.post("/auth/logout")

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed"
    
def test_logout_request_body_cannot_revoke_refresh_token(client):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = client.cookies.get(
        REFRESH_COOKIE_NAME
    )
    csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

    assert refresh_token is not None
    assert csrf_token is not None

    client.cookies.clear()

    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    # Logout without an authentication cookie remains idempotent.
    assert logout_response.status_code == 200

    # Restore the session to prove the JSON token was ignored and
    # therefore could not be used as an authentication credential.
    client.cookies.set(
        REFRESH_COOKIE_NAME,
        refresh_token,
        path="/auth",
    )
    client.cookies.set(
        CSRF_COOKIE_NAME,
        csrf_token,
        path="/",
    )

    refresh_response = client.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert refresh_response.status_code == 200
    
def test_register_normalizes_email_address(client):
    response = client.post(
        "/auth/register",
        json={
            **REGISTER_PAYLOAD,
            "email": "  Jane@Example.COM  ",
        },
    )

    assert response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": "jane@example.com",
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200
    assert (
        me_response.json()["email"]
        == "jane@example.com"
    )
    
def test_register_rejects_case_variant_duplicate_email(client):
    register_user(client)

    response = client.post(
        "/auth/register",
        json={
            **REGISTER_PAYLOAD,
            "email": "JANE@EXAMPLE.COM",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"
    
def test_login_accepts_case_variant_email(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "JANE@EXAMPLE.COM",
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    
def test_register_handles_database_duplicate_race(
    client,
    monkeypatch,
):
    rollback_called = False

    def raise_duplicate_error(db):
        raise IntegrityError(
            statement="INSERT INTO users",
            params={},
            orig=Exception("duplicate email"),
        )

    def record_rollback(db):
        nonlocal rollback_called
        rollback_called = True
        db.rollback()

    monkeypatch.setattr(
        UserService.repository,
        "commit",
        raise_duplicate_error,
    )
    monkeypatch.setattr(
        UserService.repository,
        "rollback",
        record_rollback,
    )

    response = client.post(
        "/auth/register",
        json=REGISTER_PAYLOAD,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"
    assert rollback_called is True
    
def test_logout_all_requires_access_token(client):
    response = client.post("/auth/logout-all")

    assert response.status_code == 401


def test_logout_all_requires_csrf_token(client):
    register_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/auth/logout-all",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "CSRF validation failed"


def test_logout_all_revokes_every_user_session(client):
    register_user(client)

    first_login = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert first_login.status_code == 200

    first_refresh_token = client.cookies.get(
        REFRESH_COOKIE_NAME
    )
    first_csrf_token = client.cookies.get(
        CSRF_COOKIE_NAME
    )

    second_login = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )

    assert second_login.status_code == 200

    second_refresh_token = client.cookies.get(
        REFRESH_COOKIE_NAME
    )
    second_csrf_token = client.cookies.get(
        CSRF_COOKIE_NAME
    )
    access_token = second_login.json()["access_token"]

    assert first_refresh_token is not None
    assert first_csrf_token is not None
    assert second_refresh_token is not None
    assert second_csrf_token is not None
    assert first_refresh_token != second_refresh_token

    logout_response = client.post(
        "/auth/logout-all",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-CSRF-Token": second_csrf_token,
        },
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {
        "message": "Logged out from all sessions",
        "revoked_sessions": 2,
    }
    assert client.cookies.get(REFRESH_COOKIE_NAME) is None
    assert client.cookies.get(CSRF_COOKIE_NAME) is None

    # Confirm the first session cannot be restored.
    client.cookies.set(
        REFRESH_COOKIE_NAME,
        first_refresh_token,
        path="/auth",
    )
    client.cookies.set(
        CSRF_COOKIE_NAME,
        first_csrf_token,
        path="/",
    )

    first_refresh_response = client.post(
        "/auth/refresh",
        headers={
            "X-CSRF-Token": first_csrf_token,
        },
    )

    assert first_refresh_response.status_code == 401

    # Confirm the second session cannot be restored.
    client.cookies.set(
        REFRESH_COOKIE_NAME,
        second_refresh_token,
        path="/auth",
    )
    client.cookies.set(
        CSRF_COOKIE_NAME,
        second_csrf_token,
        path="/",
    )

    second_refresh_response = client.post(
        "/auth/refresh",
        headers={
            "X-CSRF-Token": second_csrf_token,
        },
    )

    assert second_refresh_response.status_code == 401