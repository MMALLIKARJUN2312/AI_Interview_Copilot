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

def test_me_does_not_leak_password_hash(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert "hashed_password" not in response.json()
    assert response.json()["email"] == "user@example.com"

def test_me_requires_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
