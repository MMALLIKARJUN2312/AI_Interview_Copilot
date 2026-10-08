import pytest

from fastapi import Request

from app.core.jwt import create_access_token
from app.core.rate_limit import (
    account_or_ip_key,
    limiter,
)

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

def build_request(
    *,
    authorization: str | None = None,
    client_host: str = "203.0.113.10",
) -> Request:
    headers: list[tuple[bytes, bytes]] = []

    if authorization is not None:
        headers.append(
            (
                b"authorization",
                authorization.encode("utf-8"),
            )
        )

    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/quota-test",
            "raw_path": b"/quota-test",
            "query_string": b"",
            "headers": headers,
            "client": (client_host, 50000),
            "server": ("testserver", 443),
        }
    )
    
def test_account_quota_key_uses_access_token_subject():
    token = create_access_token(
        {
            "sub": "42",
        }
    )

    request = build_request(
        authorization=f"Bearer {token}",
    )

    assert account_or_ip_key(request) == "account:42"


def test_account_quota_key_separates_users():
    first_token = create_access_token(
        {
            "sub": "42",
        }
    )
    second_token = create_access_token(
        {
            "sub": "84",
        }
    )

    first_request = build_request(
        authorization=f"Bearer {first_token}",
        client_host="203.0.113.10",
    )
    second_request = build_request(
        authorization=f"Bearer {second_token}",
        client_host="203.0.113.10",
    )

    assert account_or_ip_key(
        first_request
    ) == "account:42"

    assert account_or_ip_key(
        second_request
    ) == "account:84"


def test_account_quota_key_is_stable_across_ip_addresses():
    token = create_access_token(
        {
            "sub": "42",
        }
    )

    first_request = build_request(
        authorization=f"Bearer {token}",
        client_host="203.0.113.10",
    )
    second_request = build_request(
        authorization=f"Bearer {token}",
        client_host="198.51.100.20",
    )

    assert account_or_ip_key(
        first_request
    ) == account_or_ip_key(
        second_request
    )


def test_account_quota_key_falls_back_to_ip_without_token():
    request = build_request(
        client_host="203.0.113.10",
    )

    assert account_or_ip_key(request) == (
        "ip:203.0.113.10"
    )


def test_account_quota_key_falls_back_to_ip_for_invalid_token():
    request = build_request(
        authorization="Bearer invalid-token",
        client_host="198.51.100.20",
    )

    assert account_or_ip_key(request) == (
        "ip:198.51.100.20"
    )