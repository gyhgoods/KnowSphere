from fastapi.testclient import TestClient

from app.main import app


def test_local_development_origin_is_allowed() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://127.0.0.1:5174",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_unknown_origin_is_not_allowed() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "https://untrusted.example",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert "access-control-allow-origin" not in response.headers
