from ninja.testing import TestClient

from taskflow.api import api, api_v2

client_v1 = TestClient(api)
client_v2 = TestClient(api_v2)


def test_v2_token_response(alice):
    response = client_v2.post("/auth/token", json={"username": "alice", "password": "wonderland-42"})
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900

    # Both versions accept the same access token
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    assert client_v1.get("/projects/", headers=headers).status_code == 200
    assert client_v2.get("/projects/", headers=headers).status_code == 200


def test_v2_refresh(alice):
    tokens = client_v2.post(
        "/auth/token", json={"username": "alice", "password": "wonderland-42"}
    ).json()
    response = client_v2.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    assert set(response.json()) == {"access_token", "refresh_token", "token_type", "expires_in"}

    response = client_v2.post("/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401
