def test_register_creates_user(client):
    response = client.post("/auth/register", json={
        "full_name": "Jane Dev", "email": "jane@example.com", "password": "hunter2pass",
    })

    assert response.status_code == 200
    assert response.json()["user_id"] == 1

def test_register_duplicate_email_rejected(client):
    payload = {"full_name": "Jane Dev", "email": "jane@example.com", "password": "hunter2pass"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400

def test_login_wrong_password_rejected(client):
    client.post("/auth/register", json={"full_name": "Jane Dev", "email": "jane@example.com", "password": "hunter2pass"})

    response = client.post("/auth/login", json={"email": "jane@example.com", "password": "wrong-password"})

    assert response.status_code == 401

def test_login_returns_bearer_token(client):
    client.post("/auth/register", json={"full_name": "Jane Dev", "email": "jane@example.com", "password": "hunter2pass"})

    response = client.post("/auth/login", json={"email": "jane@example.com", "password": "hunter2pass"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]

def test_refresh_issues_new_tokens_and_rotates_old_one(client):
    client.post("/auth/register", json={"full_name": "Jane Dev", "email": "jane@example.com", "password": "hunter2pass"})
    login = client.post("/auth/login", json={"email": "jane@example.com", "password": "hunter2pass"}).json()

    response = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"] != login["refresh_token"]

    reuse = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert reuse.status_code == 401

def test_refresh_rejects_unknown_token(client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401

def test_logout_revokes_refresh_token(client):
    client.post("/auth/register", json={"full_name": "Jane Dev", "email": "jane@example.com", "password": "hunter2pass"})
    login = client.post("/auth/login", json={"email": "jane@example.com", "password": "hunter2pass"}).json()

    logout = client.post("/auth/logout", json={"refresh_token": login["refresh_token"]})
    assert logout.status_code == 200

    response = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert response.status_code == 401

def test_new_access_token_from_refresh_is_usable(client):
    client.post("/auth/register", json={"full_name": "Jane Dev", "email": "jane@example.com", "password": "hunter2pass"})
    login = client.post("/auth/login", json={"email": "jane@example.com", "password": "hunter2pass"}).json()
    refreshed = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]}).json()

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {refreshed['access_token']}"})

    assert response.status_code == 200
    assert response.json()["email"] == "jane@example.com"

def test_me_does_not_leak_password_hash(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert "hashed_password" not in response.json()
    assert response.json()["email"] == "user@example.com"

def test_me_requires_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
