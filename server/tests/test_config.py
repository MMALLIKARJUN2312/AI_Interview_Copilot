import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": "sqlite:///:memory:",
        "JWT_SECRET": "test-secret",
        "REFRESH_COOKIE_SECURE": False,
        "REFRESH_COOKIE_SAMESITE": "lax",
        "REFRESH_COOKIE_DOMAIN": None,
    }
    values.update(overrides)

    return Settings(
        _env_file=None,
        **values,
    )


def test_development_allows_insecure_lax_cookie() -> None:
    settings = make_settings()

    assert settings.ENVIRONMENT == "development"
    assert settings.REFRESH_COOKIE_SECURE is False
    assert settings.REFRESH_COOKIE_SAMESITE == "lax"


def test_samesite_none_requires_secure_cookie() -> None:
    with pytest.raises(
        ValidationError,
        match="REFRESH_COOKIE_SECURE must be true",
    ):
        make_settings(
            REFRESH_COOKIE_SECURE=False,
            REFRESH_COOKIE_SAMESITE="none",
        )


def test_production_requires_secure_cookie() -> None:
    with pytest.raises(
        ValidationError,
        match="REFRESH_COOKIE_SECURE must be true in production",
    ):
        make_settings(
            ENVIRONMENT="production",
            REFRESH_COOKIE_SECURE=False,
            REFRESH_COOKIE_SAMESITE="lax",
        )


def test_secure_cross_site_production_configuration_is_valid() -> None:
    settings = make_settings(
        ENVIRONMENT="production",
        REFRESH_COOKIE_SECURE=True,
        REFRESH_COOKIE_SAMESITE="none",
    )

    assert settings.ENVIRONMENT == "production"
    assert settings.REFRESH_COOKIE_SECURE is True
    assert settings.REFRESH_COOKIE_SAMESITE == "none"


def test_blank_cookie_domain_becomes_none() -> None:
    settings = make_settings(
        REFRESH_COOKIE_DOMAIN="   ",
    )

    assert settings.REFRESH_COOKIE_DOMAIN is None