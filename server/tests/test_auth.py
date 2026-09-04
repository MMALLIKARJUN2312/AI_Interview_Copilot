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


def test_refresh_rejects_reused_rotated_token(client):
    register_user(client)
    login_tokens = login_user(client)

    first_refresh = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_tokens["refresh_token"],
        },
    )

    assert first_refresh.status_code == 200

    reused_token_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": login_tokens["refresh_token"],
        },
    )

    assert reused_token_response.status_code == 401
    assert (
        reused_token_response.json()["detail"]
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