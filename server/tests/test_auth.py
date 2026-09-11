import pytest


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


def test_login_returns_bearer_tokens(client):
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
    assert isinstance(body["refresh_token"], str)
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


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


def test_refresh_rotates_refresh_token(client):
    register_user(client)
    login_tokens = login_user(client)

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_tokens["refresh_token"],
        },
    )

    assert response.status_code == 200

    refreshed_tokens = response.json()

    assert refreshed_tokens["token_type"] == "bearer"
    assert refreshed_tokens["access_token"]
    assert refreshed_tokens["refresh_token"]
    assert (
        refreshed_tokens["refresh_token"]
        != login_tokens["refresh_token"]
    )


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
def test_refresh_rejects_unknown_token(client):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "not-a-real-token",
        },
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Invalid or expired refresh token"
    )


def test_refreshed_access_token_is_usable(client):
    register_user(client)
    login_tokens = login_user(client)

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 200

    refreshed_access_token = refresh_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {refreshed_access_token}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == REGISTER_PAYLOAD["email"]


def test_logout_revokes_refresh_token(client):
    register_user(client)
    login_tokens = login_user(client)

    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": login_tokens["refresh_token"],
        },
    )

    assert logout_response.status_code == 200
    assert logout_response.json() == {
        "message": "Logged out",
    }

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 401


def test_logout_with_unknown_token_is_idempotent(client):
    first_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "unknown-refresh-token",
        },
    )

    second_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "unknown-refresh-token",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == {"message": "Logged out"}
    assert second_response.json() == {"message": "Logged out"}


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

def test_refresh_without_body_or_cookie_is_rejected(client):
    client.cookies.clear()

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is required"


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