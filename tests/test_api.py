from fastapi.testclient import TestClient

from vpn_platform.api.app import create_app
from vpn_platform.config import Settings


def test_liveness_does_not_expose_secrets() -> None:
    settings = Settings(app_env="test", telegram_bot_token="do-not-return")
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "do-not-return" not in response.text
