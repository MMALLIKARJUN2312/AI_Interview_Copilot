import pytest

from app.core.rate_limit import limiter

@pytest.fixture()
def rate_limiting_enabled():
    limiter.enabled = True
    limiter.reset()
    try:
        yield
    finally:
        limiter.enabled = False
        limiter.reset()

def test_register_endpoint_is_rate_limited(client, rate_limiting_enabled):
    for i in range(5):
        response = client.post("/auth/register", json={
            "full_name": "Spammer", "email": f"spam{i}@example.com", "password": "hunter2pass",
        })
        assert response.status_code == 200

    blocked = client.post("/auth/register", json={
        "full_name": "Spammer", "email": "spam-blocked@example.com", "password": "hunter2pass",
    })

    assert blocked.status_code == 429
