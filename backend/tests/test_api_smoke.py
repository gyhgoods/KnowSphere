from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_admin_can_login_and_read_rbac() -> None:
    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "ChangeMe123!"},
        )
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/v1/auth/me", headers=headers)
        roles = client.get("/api/v1/rbac/roles", headers=headers)

    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert roles.status_code == 200
    assert roles.json()[0]["code"] == "super_admin"

