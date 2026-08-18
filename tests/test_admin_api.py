"""Endpoint-level tests for admin API auth: per-app settings, fail-closed."""

from fastapi.testclient import TestClient
from pydantic import SecretStr

from vpn_platform.api.app import create_app
from vpn_platform.config import Settings

TOKEN = "x" * 48


def _client(token: str | None = TOKEN) -> TestClient:
    settings = Settings(admin_api_token=SecretStr(token) if token else None)
    return TestClient(create_app(settings))


def test_valid_token_gets_200() -> None:
    response = _client().get("/admin/whoami", headers={"Authorization": f"Bearer {TOKEN}"})
    assert response.status_code == 200
    assert response.json() == {"admin": True}


def test_missing_header_is_rejected() -> None:
    response = _client().get("/admin/whoami")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_wrong_token_is_rejected() -> None:
    response = _client().get("/admin/whoami", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401


def test_wrong_scheme_is_rejected() -> None:
    response = _client().get("/admin/whoami", headers={"Authorization": f"Basic {TOKEN}"})
    assert response.status_code == 401


def test_empty_token_is_rejected() -> None:
    response = _client().get("/admin/whoami", headers={"Authorization": "Bearer"})
    assert response.status_code == 401


def test_app_without_configured_token_denies_everything() -> None:
    response = _client(token=None).get(
        "/admin/whoami", headers={"Authorization": f"Bearer {TOKEN}"}
    )
    assert response.status_code == 401
